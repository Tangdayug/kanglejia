"""ICOPTE（内在能力减退初筛）评分模块

统一维护 6 维度评分、风险判定与建议生成。
由于 REST 表单提交与语音对话的输入形态不同，分别提供：
- calculate_scores_for_rest: 接收前端结构化答案
- calculate_scores_for_voice: 接收语音状态机收集的原始回答
"""
from datetime import datetime
from typing import Dict, Any


DIMENSIONS = ['cognitive', 'motor', 'vitality', 'vision', 'hearing', 'psychological']


def _empty_scores() -> Dict[str, int]:
    return {dim: 0 for dim in DIMENSIONS}


def _today_date_str() -> str:
    now = datetime.now()
    return f"{now.month}月{now.day}日"


def calculate_scores_for_rest(data: Dict[str, Any]) -> Dict[str, int]:
    """基于前端表单提交的数据计算各维度分数（REST /health-test/submit 使用）。"""
    scores = _empty_scores()

    # 认知维度
    q1_memory_issue = data.get('q1MemoryIssue')
    if q1_memory_issue:
        scores['cognitive'] += 1

    if q1_memory_issue is False:
        if data.get('q1_2Correct') is False:
            scores['cognitive'] += 1
        if data.get('q1_3Correct') is False:
            scores['cognitive'] += 1
        q1_4_recall = data.get('q1_4Recall', '')
        if q1_4_recall != 'flower_door_rice':
            scores['cognitive'] += 1

    # 运动维度
    if data.get('q2Completed') is False:
        scores['motor'] = 1

    # 活力维度
    if data.get('q3WeightLoss'):
        scores['vitality'] += 1
    if data.get('q4AppetiteLoss'):
        scores['vitality'] += 1

    # 视力维度
    if data.get('q5VisionIssue'):
        scores['vision'] += 1
    if data.get('q6DiabetesHypertension'):
        scores['vision'] += 1

    # 听力维度
    if data.get('q7HearingIssue'):
        scores['hearing'] = 1

    # 心理维度
    if data.get('q8Depressed'):
        scores['psychological'] += 1
    if data.get('q9InterestLoss'):
        scores['psychological'] += 1

    scores['total'] = sum(scores.values())
    return scores


def calculate_scores_for_voice(answers: Dict[str, Any]) -> Dict[str, int]:
    """基于语音状态机收集的原始回答计算各维度分数（小智硬件对话使用）。

    与 REST 版本的区别：
    - 认知：直接比较用户回答文本（日期/地点/三个词回忆），而不是依赖前端的正确性标记。
    - 运动：若用户完成起立测试但用时超过 14 秒，也计为风险。
    """
    scores = _empty_scores()

    q1 = answers.get("q1MemoryIssue")
    if q1:
        scores["cognitive"] += 1
    if q1 is False:
        today_str = _today_date_str()
        q1_2 = answers.get("q1_2TodayDate", "")
        if today_str not in q1_2:
            scores["cognitive"] += 1

        q1_3 = answers.get("q1_3Location", "")
        if not q1_3.strip() or "不知道" in q1_3:
            scores["cognitive"] += 1

        q1_4 = answers.get("q1_4Recall", "")
        recall_text = q1_4.lower()
        if not ("花" in recall_text and "门" in recall_text and ("饭" in recall_text or "米" in recall_text)):
            scores["cognitive"] += 1

    q2_completed = answers.get("q2Completed")
    if q2_completed is False:
        scores["motor"] = 1
    elif q2_completed is True:
        q2_time = answers.get("q2TimeSeconds", 0)
        if q2_time and q2_time > 14:
            scores["motor"] = 1

    if answers.get("q3WeightLoss"):
        scores["vitality"] += 1
    if answers.get("q4AppetiteLoss"):
        scores["vitality"] += 1

    if answers.get("q5VisionIssue"):
        scores["vision"] += 1
    if answers.get("q6DiabetesHypertension"):
        scores["vision"] += 1

    if answers.get("q7HearingIssue"):
        scores["hearing"] = 1

    if answers.get("q8Depressed"):
        scores["psychological"] += 1
    if answers.get("q9InterestLoss"):
        scores["psychological"] += 1

    scores['total'] = sum(scores.values())
    return scores


def determine_risks(scores: Dict[str, int]) -> Dict[str, bool]:
    """根据各维度分数判定是否存在风险（分数 > 0 即风险）。"""
    return {dim: scores.get(dim, 0) > 0 for dim in DIMENSIONS}


def generate_recommendations(scores: Dict[str, int], risks: Dict[str, bool], data: Dict[str, Any]) -> Dict[str, list]:
    """根据分数与风险生成个性化建议。"""
    recommendations = {dim: [] for dim in DIMENSIONS}
    recommendations['overall'] = []

    if risks.get('cognitive'):
        recommendations['cognitive'].extend([
            '建议进行认知功能详细评估',
            '保持社交活动，多与人交流',
            '进行益智类游戏和活动',
            '保证充足睡眠，维持规律作息'
        ])
        if scores.get('cognitive', 0) >= 3:
            recommendations['cognitive'].append('风险较高，建议尽快就医咨询神经内科')

    if risks.get('motor'):
        recommendations['motor'].extend([
            '建议进行平衡能力和步态评估',
            '进行适度的肌肉力量训练',
            '注意居家环境防跌倒改造',
            '可考虑使用助行器具'
        ])
        q2_time = data.get('q2TimeSeconds')
        if q2_time is not None and q2_time > 14:
            recommendations['motor'].append('起立测试时间超过14秒，建议咨询康复科医生')

    if risks.get('vitality'):
        recommendations['vitality'].extend([
            '建议进行营养状况评估',
            '增加优质蛋白质摄入',
            '保证规律三餐，定时定量',
            '适当增加户外活动'
        ])
        if scores.get('vitality', 0) >= 2:
            recommendations['vitality'].append('体重下降和食欲减退较明显，建议咨询营养科或老年科医生')

    if risks.get('vision'):
        recommendations['vision'].extend([
            '建议到眼科进行全面检查',
            '定期检查眼底、眼压等',
            '如有糖尿病或高血压，注意控制血糖血压',
            '注意阅读光线充足，避免用眼过度'
        ])
        if scores.get('vision', 0) >= 2:
            recommendations['vision'].append('视力风险因素较多，建议尽快就医')

    if risks.get('hearing'):
        recommendations['hearing'].extend([
            '建议到耳鼻喉科进行听力检查',
            '排除耳部疾病',
            '必要时配戴助听器',
            '交流时注意面对面，语速适中'
        ])

    if risks.get('psychological'):
        recommendations['psychological'].extend([
            '建议关注心理健康状况',
            '多参加社区活动和社交互动',
            '与家人朋友多交流沟通',
            '培养兴趣爱好，保持积极心态'
        ])
        if scores.get('psychological', 0) >= 2:
            recommendations['psychological'].append('情绪和兴趣问题较明显，建议咨询心理医生或精神科医生')

    if scores.get('total', 0) == 0:
        recommendations['overall'].append('您的各项功能状态良好，请继续保持健康的生活方式！')
    else:
        recommendations['overall'].append('建议根据上述具体建议，对有风险的方面进行关注和干预')
        recommendations['overall'].append('定期复查，监测功能状态变化')

    return recommendations
