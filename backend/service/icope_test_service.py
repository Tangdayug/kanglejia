"""
ICOPTE（内在能力减退初筛）测试状态机

流程与前端 HealthTest.vue 保持一致，包含 q1 记忆问题分流、
三个词回忆、起立计时、以及 6 个维度的二选一问题。

状态按 user_id 保存在内存中，容器重启后丢失。
如需跨重启保留，可改用数据库表持久化。
"""
import re
from typing import Dict, List, Optional

from common import xiaozhi_prompts as prompts
from service.icope_scoring import calculate_scores_for_voice, determine_risks


class IcopeTestState:
    def __init__(self):
        self.active: bool = False
        self.step: Optional[str] = None
        self.answers: Dict[str, any] = {}


# 内存状态存储：user_id -> IcopeTestState
_states: Dict[int, IcopeTestState] = {}

TRIGGER_KEYWORDS = ["测试", "做测试", "开始测试", "我要测", "我想测", "内在能力"]
EXIT_KEYWORDS = ["退出", "不做了", "结束", "停止", "不测了", "取消"]


def _get_state(user_id: int) -> IcopeTestState:
    if user_id not in _states:
        _states[user_id] = IcopeTestState()
    return _states[user_id]


def reset_state(user_id: int) -> None:
    """重置指定用户的测试状态。"""
    _states[user_id] = IcopeTestState()


def is_trigger(text: str) -> bool:
    """判断用户输入是否是开始测试的触发词。"""
    if not text:
        return False
    return any(kw in text for kw in TRIGGER_KEYWORDS)


def is_exit(text: str) -> bool:
    """判断用户输入是否是退出测试的表达。"""
    if not text:
        return False
    return any(kw in text for kw in EXIT_KEYWORDS)


def is_active(user_id: int) -> bool:
    """判断指定用户是否处于测试流程中。"""
    return _get_state(user_id).active


def _yes_no(answer: str) -> Optional[bool]:
    """从回答中判断是/否。"""
    ans = answer.strip().lower()
    if not ans:
        return None

    # 完整否定表达优先
    if ans in ("否", "不对", "不能", "没有", "不是", "不可以"):
        return False
    # 完整肯定表达
    if ans in ("是", "对", "能", "可以", "有", "没错"):
        return True

    # 包含否定关键字
    if any(k in ans for k in ("不能", "没有", "不是", "不可以", "否")):
        return False
    # 包含肯定关键字
    if any(k in ans for k in ("是", "有", "对", "能", "可以", "没错")):
        return True
    return None


def _extract_number(answer: str) -> Optional[int]:
    """从回答中提取数字。"""
    nums = re.findall(r"\d+", answer)
    if nums:
        return int(nums[0])
    return None


def start_test(user_id: int) -> str:
    """开始测试，返回开场白 + 第一个问题。"""
    state = _get_state(user_id)
    state.active = True
    state.step = "q1_memory_issue"
    state.answers = {}
    return (
        f"{prompts.ICOPE_WELCOME_TEXT} 咱们一个一个来。"
        f"{prompts.ICOPE_QUESTIONS['q1_memory_issue']}"
    )


def _question_text(step: str) -> str:
    """获取指定步骤的问题文本。"""
    return prompts.ICOPE_QUESTIONS.get(step, "")


def _move_to(state: IcopeTestState, next_step: str) -> str:
    """推进到下一步并返回问题。"""
    state.step = next_step
    return _question_text(next_step)


def process_answer(user_id: int, answer: str) -> Optional[str]:
    """
    处理测试中的用户回答。

    返回值：
    - str：应回复给用户的话（下一个问题或总结）
    - None：状态异常或不应由状态机处理
    """
    state = _get_state(user_id)
    if not state.active or not state.step:
        return None

    if is_exit(answer):
        reset_state(user_id)
        return prompts.ICOPE_EXIT_TEXT

    step = state.step

    # -----------------------------------------------------------------
    # Q1 记忆/定向问题分流
    # -----------------------------------------------------------------
    if step == "q1_memory_issue":
        yn = _yes_no(answer)
        if yn is None:
            return "请回答“是”或“否”。" + _question_text(step)
        state.answers["q1MemoryIssue"] = yn
        if yn:
            return _move_to(state, "q2_chair_stand")
        return _move_to(state, "q1_1_remember_words")

    # -----------------------------------------------------------------
    # Q1.1 - Q1.4 记忆细节
    # -----------------------------------------------------------------
    if step == "q1_1_remember_words":
        state.answers["q1_1Remembered"] = True
        return _move_to(state, "q1_2_today_date")

    if step == "q1_2_today_date":
        state.answers["q1_2TodayDate"] = answer.strip()
        return _move_to(state, "q1_3_location")

    if step == "q1_3_location":
        state.answers["q1_3Location"] = answer.strip()
        return _move_to(state, "q1_4_recall")

    if step == "q1_4_recall":
        state.answers["q1_4Recall"] = answer.strip()
        return _move_to(state, "q2_chair_stand")

    # -----------------------------------------------------------------
    # Q2 起立测试
    # -----------------------------------------------------------------
    if step == "q2_chair_stand":
        yn = _yes_no(answer)
        if yn is None:
            return "请回答“能”或“不能”。" + _question_text(step)
        if yn:
            return _move_to(state, "q2_time_seconds")
        state.answers["q2Completed"] = False
        state.answers["q2TimeSeconds"] = 999
        return _move_to(state, "q3_weight_loss")

    if step == "q2_time_seconds":
        seconds = _extract_number(answer)
        if seconds is None:
            return "请说一个数字，比如“8秒”。" + _question_text(step)
        state.answers["q2Completed"] = True
        state.answers["q2TimeSeconds"] = seconds
        return _move_to(state, "q3_weight_loss")

    # -----------------------------------------------------------------
    # Q3 - Q9 二选一问题
    # -----------------------------------------------------------------
    field_map = {
        "q3_weight_loss": "q3WeightLoss",
        "q4_appetite_loss": "q4AppetiteLoss",
        "q5_vision_issue": "q5VisionIssue",
        "q6_diseases": "q6DiabetesHypertension",
        "q7_hearing_issue": "q7HearingIssue",
        "q8_depressed": "q8Depressed",
        "q9_interest_loss": "q9InterestLoss",
    }

    if step in field_map:
        yn = _yes_no(answer)
        if yn is None:
            return "请回答“是”或“否”。" + _question_text(step)
        state.answers[field_map[step]] = yn

        # 推进到下一题或总结
        next_step = _next_step_after(step)
        if next_step is None:
            return _finish_test(user_id, state)
        return _move_to(state, next_step)

    return None


def _next_step_after(step: str) -> Optional[str]:
    """获取下一个步骤。"""
    order = [
        "q3_weight_loss",
        "q4_appetite_loss",
        "q5_vision_issue",
        "q6_diseases",
        "q7_hearing_issue",
        "q8_depressed",
        "q9_interest_loss",
    ]
    try:
        idx = order.index(step)
        if idx + 1 < len(order):
            return order[idx + 1]
        return None
    except ValueError:
        return None


def _finish_test(user_id: int, state: IcopeTestState) -> str:
    """完成测试，计算分数并给出总结。"""
    scores, risks = _calculate_scores_and_risks(state.answers)

    risk_labels = []
    label_map = {
        "cognitive": "认知",
        "motor": "行动",
        "vitality": "活力",
        "vision": "视力",
        "hearing": "听力",
        "psychological": "心理",
    }
    for dim, has_risk in risks.items():
        if has_risk:
            risk_labels.append(label_map.get(dim, dim))

    if risk_labels:
        summary = (
            "测试完成。您在"
            f"{'、'.join(risk_labels)}"
            "方面可能需要多关注，建议和家人或医生聊聊，做进一步检查。"
        )
    else:
        summary = "测试完成。您的整体状态看起来不错，请继续保持规律作息和适度活动。"

    reset_state(user_id)
    return f"{summary} {prompts.ICOPE_THANKS_SELF_TEXT} 还有其他想聊的吗？"


def _calculate_scores_and_risks(answers: Dict[str, any]) -> tuple:
    """
    复用统一评分模块中的语音对话评分逻辑。
    分数 > 0 表示该维度存在风险。
    """
    scores = calculate_scores_for_voice(answers)
    risks = determine_risks(scores)
    return scores, risks
