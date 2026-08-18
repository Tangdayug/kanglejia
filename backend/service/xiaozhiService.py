"""
小智（XiaoZhi）硬件 WebSocket 桥接与老年人对话系统

架构说明
========
本模块作为 SecondNature 后端与 XiaoZhi 小智硬件代理服务器之间的双向桥接：

1.  inbound WebSocket  (/ws/xiaozhi)
    由 api/xiaozhiAPI.py 暴露，接收来自硬件设备的 JSON 消息：
    - hello            : 携带声纹/设备标识 voiceprint_id，用于身份识别与会话复用
    - stt/text         : 硬件端语音识别后的文本，交给 XiaozhiDialogueManager 处理
    - audio            : 硬件端采集的音频数据，可转发给云端 XiaoZhi 代理服务器
    - interrupt        : 用户打断 AI 说话，立即中断当前 TTS 并处理最新输入

2.  outbound WebSocket (XiaoZhiWebSocketClient)
    连接到 XIAOZHI_SERVER_URL（默认 ws://localhost:8000/xiaozhi，可通过环境变量覆盖）。
    负责把本地无法处理的音频/文本转发给小智代理服务器，并把代理返回的消息回传给硬件。

3.  XiaozhiDialogueManager（内存会话管理）
    - 维护活跃会话状态
    - 识别唤醒词“我要测试”、退出词“我要退出”
    - 驱动 ICOPE 筛查流程
    - 自动启动并延续健康咨询（目标 10+ 轮）
    - 情绪续命：检测到哭泣/呼吸急促关键词时延长超时，优先安抚
    - 高打断敏感度：收到 interrupt 立即停掉当前播报并响应
    - 同一天同一声纹复用健康档案，避免重复询问基础病史

4.  语音能力
    - 方言分类 stub + 云端方言模型 stub
    - 方言规则映射到 TTS 语音参数
    - 轻量级声纹识别：通过 voiceprint_id 查找已注册用户
    - TTS 复用 EdgeTTSService

所有持久化状态通过 model/xiaozhiSession.py 落库；本模块仅在内存中保留活跃副本，
并在关键状态变化时同步回数据库，确保硬件重连或同一天复用时状态不丢失。
"""
import asyncio
import base64
import copy
import json
import logging
import os
import re
import time
from datetime import date, datetime, timedelta
from typing import Any, Callable, Dict, List, Optional, Tuple

from sqlalchemy import select, and_
from sqlalchemy.orm import Session

from common.datetime_utils import get_now_naive
from common import xiaozhi_prompts as prompts
from model.xiaozhiSession import XiaozhiVoiceSession, XiaozhiVoiceprint, HealthObservation
from service.edgeTTSService import EdgeTTSService

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# 配置与常量
# ---------------------------------------------------------------------------

XIAOZHI_SERVER_URL = os.environ.get(
    "XIAOZHI_SERVER_URL",
    "ws://localhost:8000/xiaozhi"
)

# 会话超时（秒）
IDLE_TIMEOUT_SECONDS = 60
HEALTH_TIMEOUT_SECONDS = 180
EMOTION_RENEWAL_SECONDS = 600  # 检测到情绪异常时续命时长
ICOPE_TIMEOUT_SECONDS = 300

# 健康咨询目标轮数
HEALTH_TARGET_ROUNDS = 12


# ---------------------------------------------------------------------------
# 方言映射（stub）
# ---------------------------------------------------------------------------

DIALECT_VOICE_MAP = {
    "mandarin": {
        "voice": "xiaoxiao",
        "rate": "-5%",
        "pitch": "+0Hz",
        "volume": "+0%",
        "style": "standard"
    },
    "cantonese": {
        "voice": "xiaoxiao",
        "rate": "-5%",
        "pitch": "+0Hz",
        "volume": "+0%",
        "style": "cantonese_stub"
    },
    "sichuan": {
        "voice": "xiaoyi",
        "rate": "-5%",
        "pitch": "+0Hz",
        "volume": "+0%",
        "style": "sichuan_stub"
    },
    "shanghainese": {
        "voice": "xiaochen",
        "rate": "-5%",
        "pitch": "+0Hz",
        "volume": "+0%",
        "style": "shanghainese_stub"
    },
    "hunan": {
        "voice": "xiaoyi",
        "rate": "-5%",
        "pitch": "+0Hz",
        "volume": "+0%",
        "style": "hunan_stub"
    },
    "unknown": {
        "voice": "xiaoxiao",
        "rate": "-8%",
        "pitch": "+0Hz",
        "volume": "+0%",
        "style": "standard"
    }
}


# ---------------------------------------------------------------------------
# 轻量级声纹识别
# ---------------------------------------------------------------------------

def recognize_voiceprint(voiceprint_id: str, db_session: Session) -> Tuple[Optional[int], Optional[str]]:
    """
    根据声纹/设备标识查询已绑定的用户ID与验证状态。

    Args:
        voiceprint_id: 硬件上报的声纹或设备特征标识
        db_session: 数据库会话

    Returns:
        (用户ID, verification_status)，未识别返回 (None, None)
    """
    if not voiceprint_id or not db_session:
        return None, None

    query = select(XiaozhiVoiceprint).where(
        XiaozhiVoiceprint.voiceprint_id == voiceprint_id
    )
    mapping = db_session.execute(query).scalar_one_or_none()
    if mapping is None:
        return None, None
    return mapping.user_id, mapping.verification_status


def register_voiceprint(
    voiceprint_id: str,
    user_id: int,
    db_session: Session,
    current_user_id: Optional[int] = None
) -> XiaozhiVoiceprint:
    """
    注册或更新声纹与用户的映射关系。

    账号隔离：只有当前登录用户本人才能把自己的声纹绑定到自己账号；
    管理员也无法通过此接口把他人声纹绑定到另一账号。

    Args:
        voiceprint_id: 声纹/设备标识
        user_id: 要绑定的目标用户ID
        db_session: 数据库会话
        current_user_id: 当前操作者用户ID，用于所有权校验

    Returns:
        声纹映射记录
    """
    if current_user_id is not None and user_id != current_user_id:
        raise PermissionError("只能把声纹/设备绑定到当前登录账号")

    query = select(XiaozhiVoiceprint).where(
        XiaozhiVoiceprint.voiceprint_id == voiceprint_id
    )
    mapping = db_session.execute(query).scalar_one_or_none()

    if mapping is None:
        mapping = XiaozhiVoiceprint()
        mapping.voiceprint_id = voiceprint_id
    elif current_user_id is not None and mapping.user_id != current_user_id:
        # 声纹已绑定到他人账号，当前用户无权覆盖
        raise PermissionError("该声纹/设备已绑定到其他账号")

    mapping.user_id = user_id
    mapping.is_allowed = True
    db_session.add(mapping)
    db_session.commit()
    db_session.refresh(mapping)
    return mapping


# ---------------------------------------------------------------------------
# 接入鉴权：判定是否允许该小智设备/声纹连接本系统
# ---------------------------------------------------------------------------

def validate_xiaozhi_token(token: Optional[str]) -> bool:
    """
    校验小智系统接入令牌。

    规则：
    - 若环境变量 XIAOZHI_SYSTEM_TOKEN 未设置，则不对 token 做强制校验（开发环境兼容）。
    - 若已设置，则必须完全匹配才允许接入。
    """
    from common.constant import XIAOZHI_SYSTEM_TOKEN

    if not XIAOZHI_SYSTEM_TOKEN:
        return True

    return token == XIAOZHI_SYSTEM_TOKEN


def validate_xiaozhi_agent_name(agent_name: Optional[str]) -> bool:
    """
    校验小智硬件请求的智能体名称是否指向本系统。

    规则：
    - 若环境变量 XIAOZHI_AGENT_NAME 未设置，则不对 agent_name 做强制校验（兼容模式）。
    - 若已设置，则硬件声明的 agent_name 必须与本系统名称一致才允许接入。

    这解决了“凡是连上这台机器的小智都进入本系统”的问题：
    只有被配置为连接 SecondNature 这个智能体的设备才会路由到这里。
    """
    from common.constant import XIAOZHI_AGENT_NAME

    if not XIAOZHI_AGENT_NAME:
        return True

    if not agent_name:
        return False

    return agent_name.strip().lower() == XIAOZHI_AGENT_NAME.strip().lower()


def _get_or_create_default_hardware_user(db_session: Session) -> int:
    """
    为未绑定账号的小智硬件自动创建/复用默认用户。

    当系统不依赖声纹做账号归属（XIAOZHI_DEVICE_WHITELIST_ENABLED=false）且硬件未携带
    用户 JWT 时，自动把设备归到默认账号，实现“不注册也能聊”。
    """
    from model.user import User
    from common.auth import auth_handler

    user = db_session.get(User, 1)
    if user is not None:
        return user.id

    user = User()
    user.id = 1
    user.username = "hardware_default"
    user.password = auth_handler.get_password_hash("hardware_default")
    user.name = "默认硬件用户"
    user.gender = "未设置"
    user.role = "USER"
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user.id


def is_voiceprint_allowed(
    voiceprint_id: str,
    db_session: Session,
    current_user_id: Optional[int] = None
) -> bool:
    """
    校验该声纹/设备是否被允许接入本系统。

    规则：
    - 若未开启白名单（XIAOZHI_DEVICE_WHITELIST_ENABLED=false），允许所有声纹。
    - 若开启白名单：
      - 已存在的声纹：blocked 状态拒绝；非 blocked 且属于当前用户则允许；
      - 不存在的声纹：自动登记为 pending 状态并绑定到当前用户。

    Args:
        voiceprint_id: 声纹/设备标识
        db_session: 数据库会话
        current_user_id: 当前登录用户ID，新声纹自动登记时归属该用户

    Returns:
        是否允许接入
    """
    from common.constant import XIAOZHI_DEVICE_WHITELIST_ENABLED

    if not voiceprint_id or not db_session:
        return False

    query = select(XiaozhiVoiceprint).where(
        XiaozhiVoiceprint.voiceprint_id == voiceprint_id
    )
    mapping = db_session.execute(query).scalar_one_or_none()

    # 声纹已存在：明确 blocked 拒绝；不属于当前用户也拒绝
    if mapping is not None:
        if mapping.verification_status == "blocked":
            return False
        if current_user_id is not None and mapping.user_id != current_user_id:
            return False
        return True

    # 未开启白名单且不存在记录：直接允许，但不自动创建记录
    if not XIAOZHI_DEVICE_WHITELIST_ENABLED:
        return True

    # 开启白名单：新声纹自动登记为 pending，绑定到当前用户
    new_mapping = XiaozhiVoiceprint()
    new_mapping.voiceprint_id = voiceprint_id
    new_mapping.user_id = current_user_id if current_user_id is not None else _get_or_create_default_hardware_user(db_session)
    new_mapping.is_allowed = True
    new_mapping.verification_status = "pending"
    db_session.add(new_mapping)
    db_session.commit()
    return True


def record_voiceprint_connection(voiceprint_id: str, db_session: Session):
    """记录声纹最近一次接入时间。"""
    if not voiceprint_id or not db_session:
        return

    query = select(XiaozhiVoiceprint).where(
        XiaozhiVoiceprint.voiceprint_id == voiceprint_id
    )
    mapping = db_session.execute(query).scalar_one_or_none()
    if mapping:
        mapping.last_connected_at = get_now_naive()
        db_session.add(mapping)
        db_session.commit()


# ---------------------------------------------------------------------------
# 最小可用健康归属：识别“这句话说的是谁”
# ---------------------------------------------------------------------------

# 简单人称指代词，用于判断说话人是否在描述自己
_SELF_REFERRING_WORDS = {"我", "俺", "本人", "自己"}


def _extract_self_referencing(text: str) -> bool:
    """简单判断文本是否以自我为第一主语（不含明确第三人称名字时）。"""
    if not text:
        return False
    for word in _SELF_REFERRING_WORDS:
        if word in text:
            return True
    return False


def resolve_subject_voiceprint(
    speaker_voiceprint_id: str,
    text: str,
    db_session: Session,
    current_user_id: Optional[int] = None
) -> Tuple[str, Optional[str]]:
    """
    判定一句话描述的对象声纹。

    最小可用规则：
    1. 只在当前用户的声纹范围内匹配 display_name（如“张阿姨睡眠不好”），避免跨账号泄露。
    2. 若文本以自我指代为主，且未提到别人，则默认描述说话人自己。
    3. 若无法判断，保守归属说话人自己。

    Returns:
        (subject_voiceprint_id, subject_display_name)
    """
    if not text or not db_session:
        return speaker_voiceprint_id, None

    # 只加载当前用户下的声纹 display_name
    query = select(XiaozhiVoiceprint)
    if current_user_id is not None:
        query = query.where(XiaozhiVoiceprint.user_id == current_user_id)
    all_voiceprints = db_session.execute(query).scalars().all()

    name_to_voiceprint = {}
    for vp in all_voiceprints:
        if vp.display_name:
            name_to_voiceprint[vp.display_name] = vp

    # 按名字长度降序匹配，避免“张阿姨”被“阿姨”误匹配
    sorted_names = sorted(name_to_voiceprint.keys(), key=len, reverse=True)
    for name in sorted_names:
        if name in text:
            vp = name_to_voiceprint[name]
            if vp.voiceprint_id != speaker_voiceprint_id:
                return vp.voiceprint_id, vp.display_name

    # 没有匹配到其他人名，默认归属说话人自己
    return speaker_voiceprint_id, None


def record_health_observation(
    observer_voiceprint_id: str,
    subject_voiceprint_id: str,
    content: str,
    db_session: Session,
    source_session_id: Optional[int] = None,
    category: Optional[str] = None,
    subject_user_id: Optional[int] = None
) -> Optional[HealthObservation]:
    """
    记录一条健康观察。

    当 A 描述 B 时，observer=A，subject=B，内容记在 B 的档案上，
    同时必须写入 B 所属账号的 user_id，实现账号隔离。
    """
    if not observer_voiceprint_id or not subject_voiceprint_id or not content or not db_session:
        return None

    observation = HealthObservation()
    observation.observer_voiceprint_id = observer_voiceprint_id
    observation.subject_voiceprint_id = subject_voiceprint_id
    observation.content = content
    observation.source_session_id = source_session_id
    observation.category = category or "general"

    # 如果调用方未传入被描述对象的 user_id，尝试从声纹绑定关系中推导
    if subject_user_id is None:
        vp_query = select(XiaozhiVoiceprint).where(
            XiaozhiVoiceprint.voiceprint_id == subject_voiceprint_id
        )
        vp = db_session.execute(vp_query).scalar_one_or_none()
        subject_user_id = vp.user_id if vp else 1
    observation.user_id = subject_user_id

    db_session.add(observation)
    db_session.commit()
    db_session.refresh(observation)
    return observation


def get_recent_health_observations(
    subject_voiceprint_id: str,
    db_session: Session,
    current_user_id: Optional[int] = None,
    limit: int = 10
) -> List[HealthObservation]:
    """获取某个声纹最近被观察/自述的健康记录，按当前登录账号过滤。"""
    if not subject_voiceprint_id or not db_session:
        return []

    filters = [HealthObservation.subject_voiceprint_id == subject_voiceprint_id]
    if current_user_id is not None:
        filters.append(HealthObservation.user_id == current_user_id)

    query = select(HealthObservation).where(and_(*filters)).order_by(
        HealthObservation.created_at.desc()
    ).limit(limit)
    return list(db_session.execute(query).scalars().all())


# ---------------------------------------------------------------------------
# 出站 WebSocket 客户端（连接 XiaoZhi 代理服务器）
# ---------------------------------------------------------------------------

class XiaozhiWebSocketClient:
    """
    出站 WebSocket 客户端，用于连接 XiaoZhi 小智代理服务器。

    主要能力：
    - 连接/断开 XIAOZHI_SERVER_URL
    - 发送 JSON 或二进制消息
    - 接收循环：将代理返回的消息通过 inbound_callback 回传给硬件端
    """

    def __init__(self, server_url: Optional[str] = None, token: Optional[str] = None):
        self.server_url = server_url or XIAOZHI_SERVER_URL
        self.token = token
        self.ws = None
        self.connected = False
        self._receive_task: Optional[asyncio.Task] = None
        self._inbound_callback: Optional[Callable[[Dict[str, Any]], Any]] = None
        self._lock = asyncio.Lock()

    def set_inbound_callback(self, callback: Callable[[Dict[str, Any]], Any]):
        """设置收到代理消息时的回调函数。"""
        self._inbound_callback = callback

    async def connect(self) -> bool:
        """建立出站 WebSocket 连接，自动附加系统 token。"""
        try:
            import websockets
        except ImportError:
            logger.warning("[XiaoZhi] websockets not installed, outbound bridge disabled")
            return False

        async with self._lock:
            if self.connected:
                return True

            try:
                # 把 token 拼到 URL 查询参数，供小智代理服务器鉴权
                connect_url = self.server_url
                if self.token:
                    separator = "&" if "?" in connect_url else "?"
                    connect_url = f"{connect_url}{separator}token={self.token}"

                self.ws = await websockets.connect(connect_url)
                self.connected = True
                self._receive_task = asyncio.create_task(self._receive_loop())
                logger.info(f"[XiaoZhi] outbound connected to {self.server_url}")
                return True
            except Exception as e:
                logger.warning(f"[XiaoZhi] outbound connect failed: {e}")
                self.connected = False
                return False

    async def _receive_loop(self):
        """持续接收代理服务器消息并回传。"""
        try:
            async for message in self.ws:
                try:
                    if isinstance(message, str):
                        data = json.loads(message)
                    else:
                        data = {"type": "audio", "data": base64.b64encode(message).decode("utf-8")}

                    if self._inbound_callback:
                        await self._inbound_callback(data)
                except Exception as e:
                    logger.warning(f"[XiaoZhi] outbound message handling error: {e}")
        except Exception as e:
            logger.warning(f"[XiaoZhi] outbound receive error: {e}")
        finally:
            self.connected = False

    async def send(self, data: Dict[str, Any]):
        """向代理服务器发送 JSON 消息。"""
        if not self.connected or self.ws is None:
            return
        try:
            await self.ws.send(json.dumps(data, ensure_ascii=False))
        except Exception as e:
            logger.warning(f"[XiaoZhi] outbound send error: {e}")
            self.connected = False

    async def send_audio(self, audio_bytes: bytes):
        """向代理服务器发送二进制音频数据。"""
        if not self.connected or self.ws is None:
            return
        try:
            await self.ws.send(audio_bytes)
        except Exception as e:
            logger.warning(f"[XiaoZhi] outbound audio send error: {e}")
            self.connected = False

    async def close(self):
        """关闭出站连接。"""
        if self._receive_task:
            self._receive_task.cancel()
            try:
                await self._receive_task
            except asyncio.CancelledError:
                pass
            self._receive_task = None

        if self.ws:
            try:
                await self.ws.close()
            except Exception:
                pass
            self.ws = None

        self.connected = False


# ---------------------------------------------------------------------------
# 对话管理器
# ---------------------------------------------------------------------------

class XiaozhiDialogueManager:
    """
    小智对话管理器：管理内存中的活跃会话，处理 STT 文本，驱动 ICOPE 与健康咨询流程。
    """

    def __init__(self):
        # 内存中的活跃会话，key 为数据库 XiaozhiVoiceSession.id
        self._sessions: Dict[int, Dict[str, Any]] = {}
        self._speaking: Dict[int, bool] = {}  # 当前是否正在播报
        self._cleanup_task: Optional[asyncio.Task] = None

    # -----------------------------------------------------------------------
    # 会话生命周期
    # -----------------------------------------------------------------------

    def _default_state(self, voiceprint_id: str, user_id: Optional[int] = None) -> Dict[str, Any]:
        return {
            "voiceprint_id": voiceprint_id,
            "user_id": user_id,
            "mode": "idle",               # idle / icope_test / health_consult
            "dialect_code": "mandarin",
            "icope_step": 0,              # 0:选择协助方式, 1~6:问题
            "icope_assistance": None,     # "self" / "assisted"
            "icope_answers": [],
            "health_round": 0,
            "chat_session_id": None,
            "profile_loaded": False,
            "history_asked": [],
            "last_user_text": None,
            "last_assistant_text": None,
            "emotion_detected_at": None,
            "interrupt_count": 0,
            "created_at": get_now_naive().isoformat(),
            "last_active_at": get_now_naive().isoformat(),
        }

    def _load_state(self, db_session: XiaozhiVoiceSession) -> Dict[str, Any]:
        state = copy.deepcopy(db_session.state_json) if db_session.state_json else {}
        state.setdefault("voiceprint_id", db_session.voiceprint_id)
        state.setdefault("user_id", db_session.user_id)
        state.setdefault("mode", db_session.session_type)
        state["last_active_at"] = get_now_naive().isoformat()
        return state

    def _save_state(self, session_id: int, db_session: Session):
        """把内存状态同步回数据库。"""
        if session_id not in self._sessions or db_session is None:
            return

        state = self._sessions[session_id]
        record = db_session.get(XiaozhiVoiceSession, session_id)
        if record is None:
            return

        record.session_type = state.get("mode", "idle")
        record.state_json = copy.deepcopy(state)
        record.user_id = state.get("user_id")
        record.last_active_at = get_now_naive()
        db_session.add(record)
        db_session.commit()

    def get_or_create_voice_session(
        self,
        voiceprint_id: str,
        db_session: Optional[Session] = None,
        fallback_user_id: Optional[int] = None,
        dialect_code: str = "mandarin",
        token: Optional[str] = None,
        agent_name: Optional[str] = None
    ) -> Tuple[int, bool]:
        """
        获取或创建语音会话，同一天同 voiceprint_id 复用已有会话。

        接入前会校验：
        1. 系统 token（如果配置了 XIAOZHI_SYSTEM_TOKEN）
        2. 智能体名称 agent_name（如果配置了 XIAOZHI_AGENT_NAME）
        3. 设备/声纹白名单

        Returns:
            (session_id, is_new)
        """
        # 1. 系统级 token 鉴权
        if not validate_xiaozhi_token(token):
            raise PermissionError("小智系统接入令牌无效")

        # 2. 智能体名称路由：只有被配置为连接本系统的设备才允许接入
        from common.constant import XIAOZHI_AGENT_NAME
        if not validate_xiaozhi_agent_name(agent_name):
            raise PermissionError(
                f"智能体名称不匹配，本系统名为 {XIAOZHI_AGENT_NAME}"
            )

        # 3. 设备/声纹白名单鉴权（开启后新设备自动登记为 pending，不直接拒绝）
        #    fallback_user_id 在此处语义为“当前登录用户”，用于新声纹绑定和归属校验
        if db_session and not is_voiceprint_allowed(voiceprint_id, db_session, fallback_user_id):
            raise PermissionError("该设备或声纹未被授权接入本系统")

        user_id = None
        if db_session:
            recognized_user_id, _ = recognize_voiceprint(voiceprint_id, db_session)
            record_voiceprint_connection(voiceprint_id, db_session)

            # 账号隔离：已绑定声纹必须属于当前登录用户（若有 JWT）才能接入
            if recognized_user_id is not None and fallback_user_id is not None \
                    and recognized_user_id != fallback_user_id:
                raise PermissionError("该声纹/设备已绑定到其他账号，无法接入本系统")

            user_id = recognized_user_id if recognized_user_id is not None else fallback_user_id

            # 未开启声纹白名单且无 JWT 时，自动归到默认硬件账号，实现“免绑定接入”
            if user_id is None:
                from common.constant import XIAOZHI_DEVICE_WHITELIST_ENABLED
                if not XIAOZHI_DEVICE_WHITELIST_ENABLED:
                    user_id = _get_or_create_default_hardware_user(db_session)
                    # 同时把该设备标识绑定到默认账号，便于后续会话复用
                    mapping = db_session.execute(
                        select(XiaozhiVoiceprint).where(XiaozhiVoiceprint.voiceprint_id == voiceprint_id)
                    ).scalar_one_or_none()
                    if mapping is None:
                        mapping = XiaozhiVoiceprint()
                        mapping.voiceprint_id = voiceprint_id
                    mapping.user_id = user_id
                    mapping.is_allowed = True
                    mapping.verification_status = "allowed"
                    db_session.add(mapping)
                    db_session.commit()

        # 账号隔离：无法识别归属账号时拒绝接入，避免数据落入默认账号
        if user_id is None:
            raise PermissionError("无法识别该声纹/设备所属账号，请先绑定")

        today = get_now_naive().date()
        tomorrow = today + timedelta(days=1)

        if db_session:
            query = select(XiaozhiVoiceSession).where(
                and_(
                    XiaozhiVoiceSession.voiceprint_id == voiceprint_id,
                    XiaozhiVoiceSession.created_at >= today,
                    XiaozhiVoiceSession.created_at < tomorrow
                )
            ).order_by(XiaozhiVoiceSession.last_active_at.desc())
            existing = db_session.execute(query).scalars().first()

            if existing:
                # 若已有同账号会话被绑定到不同用户，拒绝复用（理论上不会发生，防御性校验）
                if user_id is not None and existing.user_id is not None and existing.user_id != user_id:
                    raise PermissionError("该声纹/设备已绑定到其他账号，无法接入本系统")

                state = self._load_state(existing)
                state["dialect_code"] = dialect_code or state.get("dialect_code", "mandarin")
                if user_id and existing.user_id is None:
                    existing.user_id = user_id
                    state["user_id"] = user_id
                self._sessions[existing.id] = state
                db_session.commit()
                return existing.id, False

        # 新建数据库记录
        record = XiaozhiVoiceSession()
        record.voiceprint_id = voiceprint_id
        record.user_id = user_id
        record.session_type = "idle"
        record.state_json = self._default_state(voiceprint_id, user_id)
        record.state_json["dialect_code"] = dialect_code or "mandarin"

        if db_session:
            db_session.add(record)
            db_session.commit()
            db_session.refresh(record)

        self._sessions[record.id] = copy.deepcopy(record.state_json)
        return record.id, True

    def get_session_state(self, session_id: int) -> Optional[Dict[str, Any]]:
        return self._sessions.get(session_id)

    def reset_session(self, session_id: int, db_session: Optional[Session] = None):
        """重置指定会话状态。"""
        state = self._sessions.get(session_id)
        if state is None and db_session:
            record = db_session.get(XiaozhiVoiceSession, session_id)
            if record:
                state = self._load_state(record)

        if state is None:
            return

        voiceprint_id = state.get("voiceprint_id", "")
        user_id = state.get("user_id")
        dialect = state.get("dialect_code", "mandarin")
        self._sessions[session_id] = self._default_state(voiceprint_id, user_id)
        self._sessions[session_id]["dialect_code"] = dialect
        self._speaking[session_id] = False
        self._save_state(session_id, db_session)

    def close_session(self, session_id: int, db_session: Optional[Session] = None):
        """关闭并清理内存中的会话。"""
        self._save_state(session_id, db_session)
        self._sessions.pop(session_id, None)
        self._speaking.pop(session_id, None)

    # -----------------------------------------------------------------------
    # 识别与检测
    # -----------------------------------------------------------------------

    @staticmethod
    def detect_wake_word(text: str) -> bool:
        """
        检测 ICOPE 唤醒词“我要测试”及其冗余变体。
        """
        if not text:
            return False
        pattern = r"我(?:要|想|来)?(?:测|做|参加)(?:试|一测|一下|个试)|开始测试|做测试"
        return bool(re.search(pattern, text))

    @staticmethod
    def detect_exit(text: str) -> bool:
        """
        检测退出词“我要退出”及其冗余变体。
        """
        if not text:
            return False
        pattern = r"我?(?:要|想)?(?:退出|结束|关闭|停止|不(?:做|测|问)|再见|拜拜)"
        return bool(re.search(pattern, text))

    @staticmethod
    def detect_emotion(text: str) -> Tuple[bool, Optional[str]]:
        """
        检测用户情绪异常（哭泣、呼吸急促等）。

        Returns:
            (是否异常, 异常类型)
        """
        if not text:
            return False, None

        crying_keywords = ["哭", "流泪", "伤心", "难过", "憋不住", "好难受"]
        rapid_breath_keywords = ["喘", "呼吸急促", "喘不上气", "气短", "胸闷", "喘不过气"]

        for kw in crying_keywords:
            if kw in text:
                return True, "crying"
        for kw in rapid_breath_keywords:
            if kw in text:
                return True, "rapid_breathing"

        return False, None

    @staticmethod
    def classify_dialect_stub(text: str) -> str:
        """
        方言分类 stub：基于简单关键词规则返回方言代码。
        实际部署可替换为云端方言模型。
        """
        if not text:
            return "unknown"

        rules = {
            "cantonese": ["係", "嘅", "咁", "乜", "冇", "點解"],
            "sichuan": ["啥子", "咋个", "要得", "巴适", "啷个"],
            "shanghainese": ["侬", "阿拉", "啥", "覅", "哪能"],
            "hunan": ["咯", "哒", "咯样", "何解"]
        }

        for dialect, keywords in rules.items():
            for kw in keywords:
                if kw in text:
                    return dialect
        return "mandarin"

    @staticmethod
    def cloud_dialect_model_stub(text: str) -> str:
        """
        云端方言模型 stub：返回默认普通话或简单规则结果。
        接入真实模型后，可调用外部 API。
        """
        return XiaozhiDialogueManager.classify_dialect_stub(text)

    def get_dialect_voice_params(self, session_id: int) -> Dict[str, Any]:
        """获取当前会话的方言 TTS 参数。"""
        state = self._sessions.get(session_id, {})
        dialect = state.get("dialect_code", "unknown")
        return DIALECT_VOICE_MAP.get(dialect, DIALECT_VOICE_MAP["unknown"]).copy()

    # -----------------------------------------------------------------------
    # 文本处理主入口
    # -----------------------------------------------------------------------

    async def handle_text_message(
        self,
        session_id: int,
        text: str,
        db_session: Optional[Session] = None
    ) -> Dict[str, Any]:
        """
        处理来自硬件的 STT 文本，返回包含回复文本与音频的响应。

        Returns:
            {
                "type": "response",
                "text": str,
                "audio": Optional[bytes],
                "action": Optional[str],
                "interrupt": bool,
                "emotion": Optional[str]
            }
        """
        state = self._sessions.get(session_id)
        if state is None:
            return self._build_response("会话已失效，请重新连接。", session_id=session_id)

        self._touch(session_id)
        text = text.strip()
        state["last_user_text"] = text

        # 高敏感打断：正在播报时收到用户语音，立即中断
        if self._speaking.get(session_id, False) and text:
            state["interrupt_count"] = state.get("interrupt_count", 0) + 1
            return await self._handle_interrupt(session_id, text, db_session)

        # 情绪检测与续命
        has_emotion, emotion_type = self.detect_emotion(text)
        if has_emotion:
            state["emotion_detected_at"] = get_now_naive().isoformat()
            if state.get("mode") == "idle":
                # 情绪异常时自动进入健康咨询并优先安抚
                state["mode"] = "health_consult"
                return await self._build_health_response(
                    session_id,
                    self._emotion_comfort_text(emotion_type),
                    db_session=db_session,
                    emotion=emotion_type
                )

        # 唤醒词
        if self.detect_wake_word(text):
            return await self._start_icope(session_id, db_session)

        # 退出词
        if self.detect_exit(text):
            return await self._handle_exit(session_id, db_session)

        # 根据当前模式分发
        mode = state.get("mode", "idle")
        if mode == "icope_test":
            return await self._handle_icope_flow(session_id, text, db_session)
        elif mode == "health_consult":
            return await self._handle_health_consult_flow(session_id, text, db_session)
        else:
            # idle 默认自动启动健康咨询
            state["mode"] = "health_consult"
            self._save_state(session_id, db_session)
            return await self._handle_health_consult_flow(session_id, text, db_session)

    async def handle_interrupt(
        self,
        session_id: int,
        text: str,
        db_session: Optional[Session] = None
    ) -> Dict[str, Any]:
        """显式打断处理。"""
        return await self._handle_interrupt(session_id, text, db_session)

    async def _handle_interrupt(
        self,
        session_id: int,
        text: str,
        db_session: Optional[Session] = None
    ) -> Dict[str, Any]:
        state = self._sessions.get(session_id)
        if state is None:
            return self._build_response("会话已失效。", session_id=session_id)

        self._speaking[session_id] = False
        state["interrupt_count"] = state.get("interrupt_count", 0) + 1
        self._touch(session_id)

        # 打断后仍需优先识别唤醒词、退出词
        if self.detect_wake_word(text):
            return await self._start_icope(session_id, db_session)

        if self.detect_exit(text):
            return await self._handle_exit(session_id, db_session)

        mode = state.get("mode", "idle")
        if mode == "icope_test":
            return await self._handle_icope_flow(session_id, text, db_session, interrupt=True)
        elif mode == "health_consult":
            return await self._handle_health_consult_flow(session_id, text, db_session, interrupt=True)
        else:
            state["mode"] = "health_consult"
            self._save_state(session_id, db_session)
            return await self._handle_health_consult_flow(session_id, text, db_session, interrupt=True)

    # -----------------------------------------------------------------------
    # ICOPE 流程
    # -----------------------------------------------------------------------

    async def _start_icope(self, session_id: int, db_session: Optional[Session]) -> Dict[str, Any]:
        state = self._sessions[session_id]
        state["mode"] = "icope_test"
        state["icope_step"] = 0
        state["icope_assistance"] = None
        state["icope_answers"] = []
        self._save_state(session_id, db_session)

        reply = f"{prompts.ICOPE_WELCOME_TEXT} {prompts.ICOPE_ASSISTANCE_CHOICE_TEXT}"
        return await self._build_health_response(session_id, reply, db_session=db_session)

    async def _handle_icope_flow(
        self,
        session_id: int,
        text: str,
        db_session: Optional[Session] = None,
        interrupt: bool = False
    ) -> Dict[str, Any]:
        state = self._sessions[session_id]
        step = state.get("icope_step", 0)

        if step == 0:
            # 选择协助方式
            if re.search(r"独自|自己|我(?:一个人|自个儿)", text):
                state["icope_assistance"] = "self"
            elif re.search(r"他人|家属|家人|协助|帮忙|子女", text):
                state["icope_assistance"] = "assisted"
            else:
                return await self._build_health_response(
                    session_id,
                    "没听清楚，请说“独自回答”或者“他人协助”。",
                    db_session=db_session
                )

            state["icope_step"] = 1
            self._save_state(session_id, db_session)
            first_question = prompts.ICOPE_QUESTIONS[0]
            reply = f"{first_question['text']} {first_question['hint']}"
            return await self._build_health_response(session_id, reply, db_session=db_session)

        # 记录当前步骤答案
        q_index = step - 1
        if 0 <= q_index < len(prompts.ICOPE_QUESTIONS):
            question_id = prompts.ICOPE_QUESTIONS[q_index]["id"]
            answer = self._normalize_yes_no(text)
            # 认知题“能清楚说出”答“能”为正常，其余题答“有/是”为异常
            is_risk = self._is_icope_risk_answer(question_id, answer)
            state["icope_answers"].append({
                "question_id": question_id,
                "answer": answer,
                "is_risk": is_risk,
                "raw": text
            })

        if step >= len(prompts.ICOPE_QUESTIONS):
            # 完成
            summary = self._summarize_icope(state["icope_answers"])
            state["mode"] = "health_consult"  # 完成后回到健康咨询
            state["icope_step"] = 0
            self._save_state(session_id, db_session)

            assistance = state.get("icope_assistance")
            thanks = (
                prompts.ICOPE_THANKS_ASSISTED_TEXT
                if assistance == "assisted"
                else prompts.ICOPE_THANKS_SELF_TEXT
            )
            reply = f"{thanks} 本次筛查结果：{summary}。请问您还有什么想咨询的吗？"
            return await self._build_health_response(session_id, reply, db_session=db_session)

        # 下一题
        next_step = step + 1
        state["icope_step"] = next_step
        self._save_state(session_id, db_session)
        question = prompts.ICOPE_QUESTIONS[next_step - 1]
        reply = f"{question['text']} {question['hint']}"
        if interrupt:
            reply = "好的，您先说。" + reply
        return await self._build_health_response(session_id, reply, db_session=db_session)

    def _normalize_yes_no(self, text: str) -> Optional[str]:
        if re.search(r"能|有|是|好|可以|没问题|行", text):
            return "yes"
        if re.search(r"不能|没有|否|不|不行|不会|不太好", text):
            return "no"
        return "unknown"

    def _is_icope_risk_answer(self, question_id: str, answer: Optional[str]) -> bool:
        """判断某题答案是否代表异常风险。"""
        if answer is None or answer == "unknown":
            return False
        if question_id == "cognitive":
            return answer == "no"  # 不能清楚说出日期为异常
        return answer == "yes"

    def _summarize_icope(self, answers: List[Dict[str, Any]]) -> str:
        risk_count = sum(1 for a in answers if a.get("is_risk"))
        total = len(prompts.ICOPE_QUESTIONS)
        if risk_count == 0:
            return "目前未发现明显异常"
        elif risk_count <= 2:
            return f"有 {risk_count} 项需要关注，建议近期咨询医生"
        else:
            return f"有 {risk_count} 项异常，建议尽快就医进一步检查"

    # -----------------------------------------------------------------------
    # 健康咨询流程
    # -----------------------------------------------------------------------

    async def _handle_health_consult_flow(
        self,
        session_id: int,
        text: str,
        db_session: Optional[Session] = None,
        interrupt: bool = False
    ) -> Dict[str, Any]:
        state = self._sessions[session_id]
        user_id = state.get("user_id")
        voiceprint_id = state.get("voiceprint_id", "anonymous")

        # 无用户身份时给出通用回复
        if not user_id or not db_session:
            state["health_round"] = state.get("health_round", 0) + 1
            self._save_state(session_id, db_session)
            reply = "您好，我暂时还没识别到您的身份。您可以先告诉我哪里不舒服，我会尽力帮您。"
            if interrupt:
                reply = "您先说。" + reply
            return await self._build_health_response(session_id, reply, db_session=db_session)

        # 最小可用健康归属：判断这句话描述的是谁（只在当前用户下的声纹中匹配）
        subject_voiceprint_id, subject_name = resolve_subject_voiceprint(
            speaker_voiceprint_id=voiceprint_id,
            text=text,
            db_session=db_session,
            current_user_id=user_id
        )

        # 如果被描述的是别人，用那个人的健康档案来回答
        subject_user_id = user_id
        if subject_voiceprint_id and subject_voiceprint_id != voiceprint_id:
            resolved_user_id, _ = recognize_voiceprint(subject_voiceprint_id, db_session)
            if resolved_user_id:
                subject_user_id = resolved_user_id

        # 记录健康观察：A 描述 B 时，记在 B 身上，并带上 B 所属账号的 user_id
        if text:
            record_health_observation(
                observer_voiceprint_id=voiceprint_id,
                subject_voiceprint_id=subject_voiceprint_id,
                content=text,
                db_session=db_session,
                source_session_id=session_id,
                category="general",
                subject_user_id=subject_user_id
            )

        # 首次进入健康咨询，创建/复用聊天会话（聊天会话仍归属说话人，保证对话连续性）
        chat_session_id = state.get("chat_session_id")
        if chat_session_id is None:
            try:
                from service.chatService import ChatService
                chat_session = ChatService.create_session(
                    user_id=user_id,
                    title="小智健康咨询",
                    db_session=db_session
                )
                chat_session_id = chat_session.id
                state["chat_session_id"] = chat_session_id
                self._save_state(session_id, db_session)
            except Exception as e:
                logger.exception("[XiaoZhi] create chat session failed")
                reply = "抱歉，健康咨询启动失败，请稍后再试。"
                return await self._build_health_response(session_id, reply, db_session=db_session)

        # 第一轮或空输入时给出开场白，不直接调用大模型
        current_round = state.get("health_round", 0)
        if current_round == 0 or not text:
            reply = prompts.HEALTH_CONSULT_RESUME_OPENING if current_round > 0 else prompts.HEALTH_CONSULT_OPENING
            if text and text not in ("你好", "您好", "在吗"):
                # 用户确实说了内容，先回应开场再进入后续轮次
                pass
        else:
            # 调用 ChatService 生成回复，传入 subject_user_id 用于健康上下文
            try:
                from service.chatService import ChatService
                result = ChatService.generate_chat_response(
                    user_id=user_id,
                    session_id=chat_session_id,
                    user_message=text,
                    db_session=db_session,
                    subject_user_id=subject_user_id
                )
                reply = result.get("response", "")
            except Exception as e:
                logger.exception("[XiaoZhi] generate_chat_response failed")
                reply = "抱歉，我刚才没听清楚，您能再说一遍吗？"

        if interrupt:
            reply = "您先说。" + reply

        state["health_round"] = current_round + 1
        self._save_state(session_id, db_session)

        return await self._build_health_response(session_id, reply, db_session=db_session)

    async def _handle_exit(self, session_id: int, db_session: Optional[Session]) -> Dict[str, Any]:
        state = self._sessions.get(session_id)
        if state is None:
            return self._build_response("会话已结束。", session_id=session_id)

        mode = state.get("mode", "idle")
        if mode == "icope_test":
            reply = prompts.ICOPE_EXIT_TEXT
        else:
            reply = "好的，会话已结束。如果您还有问题，随时叫我。再见。"

        state["mode"] = "idle"
        state["icope_step"] = 0
        self._save_state(session_id, db_session)

        response = await self._build_health_response(session_id, reply, db_session=db_session)
        response["action"] = "exit"
        return response

    # -----------------------------------------------------------------------
    # 响应构造与 TTS
    # -----------------------------------------------------------------------

    def _emotion_comfort_text(self, emotion_type: str) -> str:
        if emotion_type == "rapid_breathing":
            return prompts.RAPID_BREATHING_COMFORT_TEXT
        return prompts.EMOTION_COMFORT_TEXT

    async def _build_health_response(
        self,
        session_id: int,
        text: str,
        db_session: Optional[Session] = None,
        emotion: Optional[str] = None
    ) -> Dict[str, Any]:
        state = self._sessions.get(session_id)
        if state:
            state["last_assistant_text"] = text
            self._touch(session_id)
            self._save_state(session_id, db_session)

        audio = await self._synthesize(session_id, text)
        self._speaking[session_id] = True
        return self._build_response(text, audio=audio, session_id=session_id, emotion=emotion)

    async def _synthesize(self, session_id: int, text: str) -> Optional[bytes]:
        params = self.get_dialect_voice_params(session_id)
        try:
            audio = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: EdgeTTSService.synthesize(
                    text=text,
                    voice=params.get("voice"),
                    rate=params.get("rate"),
                    pitch=params.get("pitch"),
                    volume=params.get("volume")
                )
            )
            return audio
        except Exception as e:
            logger.warning(f"[XiaoZhi] TTS failed: {e}")
            return None

    def _build_response(
        self,
        text: str,
        audio: Optional[bytes] = None,
        session_id: Optional[int] = None,
        emotion: Optional[str] = None,
        action: Optional[str] = None
    ) -> Dict[str, Any]:
        result = {
            "type": "response",
            "text": text,
            "emotion": emotion,
            "action": action,
            "interrupt": False,
            "audio": audio
        }
        if session_id is not None:
            state = self._sessions.get(session_id, {})
            result["session_id"] = session_id
            result["mode"] = state.get("mode", "idle")
            result["health_round"] = state.get("health_round", 0)
        return result

    def mark_speaking_done(self, session_id: int):
        """硬件端播报完成后调用，解除打断锁。"""
        self._speaking[session_id] = False

    def _touch(self, session_id: int):
        state = self._sessions.get(session_id)
        if state:
            state["last_active_at"] = get_now_naive().isoformat()

    # -----------------------------------------------------------------------
    # 超时与清理
    # -----------------------------------------------------------------------

    def is_session_expired(self, session_id: int) -> bool:
        state = self._sessions.get(session_id)
        if state is None:
            return True

        last_active = datetime.fromisoformat(state.get("last_active_at", "2000-01-01T00:00:00"))
        elapsed = (get_now_naive() - last_active).total_seconds()

        # 情绪异常时续命
        if state.get("emotion_detected_at"):
            return elapsed > EMOTION_RENEWAL_SECONDS

        mode = state.get("mode", "idle")
        if mode == "icope_test":
            return elapsed > ICOPE_TIMEOUT_SECONDS
        elif mode == "health_consult":
            return elapsed > HEALTH_TIMEOUT_SECONDS
        else:
            return elapsed > IDLE_TIMEOUT_SECONDS

    async def start_cleanup_loop(self):
        """启动后台超时清理任务。"""
        if self._cleanup_task is not None:
            return
        self._cleanup_task = asyncio.create_task(self._cleanup_worker())

    async def stop_cleanup_loop(self):
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
            self._cleanup_task = None

    async def _cleanup_worker(self):
        while True:
            try:
                await asyncio.sleep(30)
                expired = [sid for sid in list(self._sessions.keys()) if self.is_session_expired(sid)]
                for sid in expired:
                    logger.info(f"[XiaoZhi] session {sid} expired")
                    self._sessions.pop(sid, None)
                    self._speaking.pop(sid, None)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.warning(f"[XiaoZhi] cleanup error: {e}")

    # -----------------------------------------------------------------------
    # 状态查询
    # -----------------------------------------------------------------------

    def get_status(self) -> Dict[str, Any]:
        return {
            "active_sessions": len(self._sessions),
            "speaking_sessions": sum(1 for v in self._speaking.values() if v),
            "server_url": XIAOZHI_SERVER_URL,
            "modes": {
                sid: {
                    "mode": s.get("mode"),
                    "voiceprint_id": s.get("voiceprint_id"),
                    "health_round": s.get("health_round", 0),
                    "icope_step": s.get("icope_step", 0),
                    "interrupt_count": s.get("interrupt_count", 0),
                    "last_active_at": s.get("last_active_at")
                }
                for sid, s in self._sessions.items()
            }
        }


# 全局单例
dialogue_manager = XiaozhiDialogueManager()
