from sqlalchemy import Integer, String, DateTime, Text, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column

from model import Base
from common.datetime_utils import get_now_naive


class ChatSession(Base):
    """聊天会话表"""
    __tablename__ = 'chat_sessions'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, nullable=False, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True, comment='用户ID')
    title: Mapped[str] = mapped_column(String(200), default='新对话')
    created_at: Mapped[DateTime] = mapped_column(DateTime, default=lambda: get_now_naive(), nullable=False)
    updated_at: Mapped[DateTime] = mapped_column(DateTime, default=lambda: get_now_naive(), onupdate=lambda: get_now_naive(), nullable=False)

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'title': self.title,
            'createdAt': self.created_at.isoformat() if self.created_at else None,
            'updatedAt': self.updated_at.isoformat() if self.updated_at else None
        }


class ChatMessage(Base):
    """聊天消息表"""
    __tablename__ = 'chat_messages'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, nullable=False, autoincrement=True)
    session_id: Mapped[int] = mapped_column(Integer, ForeignKey('chat_sessions.id', ondelete='CASCADE'), nullable=False, index=True, comment='会话ID')
    user_id: Mapped[int] = mapped_column(Integer, nullable=True, index=True, comment='用户ID（冗余，用于账号隔离与防御纵深）')
    role: Mapped[str] = mapped_column(String(20), nullable=False, comment='角色: user/assistant')
    content: Mapped[str] = mapped_column(Text, nullable=False)
    sources: Mapped[dict] = mapped_column(JSON, nullable=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime, default=lambda: get_now_naive(), nullable=False)

    def to_dict(self) -> dict:
        return {
            'id': self.id,
            'sessionId': self.session_id,
            'role': self.role,
            'content': self.content,
            'sources': self.sources,
            'createdAt': self.created_at.isoformat() if self.created_at else None
        }
