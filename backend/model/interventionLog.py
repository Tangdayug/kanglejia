from common.datetime_utils import get_now_naive
from sqlalchemy import Integer, String, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime

from model import Base


class InterventionLog(Base):
    """干预日志表 - 记录从对话中提取的干预建议"""
    __tablename__ = 'intervention_logs'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, nullable=False, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True, comment='用户ID')
    session_id: Mapped[int] = mapped_column(Integer, nullable=True, comment='关联的会话ID')
    intervention_suggestion: Mapped[str] = mapped_column(Text, nullable=True)
    user_feedback: Mapped[str] = mapped_column(Text, nullable=True)
    execution_status: Mapped[str] = mapped_column(String(50), default='pending', comment='执行状态: pending/completed/dismissed')
    created_at: Mapped[DateTime] = mapped_column(DateTime, default=lambda: get_now_naive(), nullable=False)
    updated_at: Mapped[DateTime] = mapped_column(DateTime, default=lambda: get_now_naive(), onupdate=lambda: get_now_naive(), nullable=False)
