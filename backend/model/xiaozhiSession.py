"""
小智（XiaoZhi）硬件语音会话模型

定义硬件 WebSocket 会话与声纹身份映射表，用于：
- 同一天同一声纹复用健康咨询档案，避免重复询问基础病史
- 持久化 ICOPE 筛查进度与健康咨询状态
"""
from sqlalchemy import Integer, String, DateTime, JSON, Text
from sqlalchemy.orm import Mapped, mapped_column

from model import Base
from common.datetime_utils import get_now_naive


class XiaozhiVoiceSession(Base):
    """小智硬件语音会话表"""
    __tablename__ = 'xiaozhi_voice_sessions'

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        nullable=False,
        autoincrement=True,
        comment='会话ID'
    )
    user_id: Mapped[int] = mapped_column(
        Integer,
        nullable=True,
        index=True,
        comment='关联用户ID，未识别时为空'
    )
    voiceprint_id: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
        comment='声纹/设备标识'
    )
    session_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default='idle',
        comment='会话类型: idle/icope_test/health_consult'
    )
    state_json: Mapped[dict] = mapped_column(
        JSON,
        nullable=True,
        comment='运行时状态JSON'
    )
    created_at: Mapped[DateTime] = mapped_column(
        DateTime,
        default=lambda: get_now_naive(),
        nullable=False,
        comment='创建时间'
    )
    updated_at: Mapped[DateTime] = mapped_column(
        DateTime,
        default=lambda: get_now_naive(),
        onupdate=lambda: get_now_naive(),
        nullable=False,
        comment='更新时间'
    )
    last_active_at: Mapped[DateTime] = mapped_column(
        DateTime,
        default=lambda: get_now_naive(),
        onupdate=lambda: get_now_naive(),
        nullable=False,
        comment='最后活跃时间'
    )


class XiaozhiVoiceprint(Base):
    """小智声纹身份映射表"""
    __tablename__ = 'xiaozhi_voiceprints'

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        nullable=False,
        autoincrement=True,
        comment='声纹映射ID'
    )
    voiceprint_id: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,
        index=True,
        comment='声纹/设备标识'
    )
    user_id: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        index=True,
        comment='关联用户ID'
    )
    display_name: Mapped[str] = mapped_column(
        String(100),
        nullable=True,
        index=True,
        comment='声纹对应的显示名称，如“张阿姨”'
    )
    is_allowed: Mapped[bool] = mapped_column(
        default=True,
        nullable=False,
        comment='是否允许接入本系统（兼容字段）'
    )
    verification_status: Mapped[str] = mapped_column(
        String(20),
        default="pending",
        nullable=False,
        comment='验证状态：pending/allowed/blocked'
    )
    last_connected_at: Mapped[DateTime] = mapped_column(
        DateTime,
        nullable=True,
        comment='最近一次接入时间'
    )
    created_at: Mapped[DateTime] = mapped_column(
        DateTime,
        default=lambda: get_now_naive(),
        nullable=False,
        comment='创建时间'
    )
    updated_at: Mapped[DateTime] = mapped_column(
        DateTime,
        default=lambda: get_now_naive(),
        onupdate=lambda: get_now_naive(),
        nullable=False,
        comment='更新时间'
    )


class HealthObservation(Base):
    """健康观察记录表

    用于最小可用设计的健康归属：
    - observer_voiceprint_id：说话人（谁说的）
    - subject_voiceprint_id：描述对象（说的是谁）
    这样 A 描述 B 时，健康观察可以记在 B 身上。
    """
    __tablename__ = 'health_observations'

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        nullable=False,
        autoincrement=True,
        comment='观察记录ID'
    )
    observer_voiceprint_id: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
        comment='观察者声纹ID'
    )
    subject_voiceprint_id: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
        comment='被描述对象声纹ID'
    )
    source_session_id: Mapped[int] = mapped_column(
        Integer,
        nullable=True,
        index=True,
        comment='来源会话ID'
    )
    user_id: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        index=True,
        comment='被描述对象所属的用户ID，用于账号隔离'
    )
    category: Mapped[str] = mapped_column(
        String(50),
        nullable=True,
        comment='观察类别，如 sleep/emotion/symptom/general'
    )
    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment='观察内容原文或摘要'
    )
    created_at: Mapped[DateTime] = mapped_column(
        DateTime,
        default=lambda: get_now_naive(),
        nullable=False,
        comment='创建时间'
    )
    updated_at: Mapped[DateTime] = mapped_column(
        DateTime,
        default=lambda: get_now_naive(),
        onupdate=lambda: get_now_naive(),
        nullable=False,
        comment='更新时间'
    )
