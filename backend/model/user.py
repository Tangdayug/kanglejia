from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from model import Base


class User(Base):
    """用户表"""
    __tablename__ = 'user'
    id: Mapped[int] = mapped_column(Integer, primary_key=True, nullable=False)
    username: Mapped[String] = mapped_column(String(255), nullable=False)
    password: Mapped[String] = mapped_column(String(255), nullable=False)
    name: Mapped[String] = mapped_column(String(255), nullable=False)
    gender: Mapped[String] = mapped_column(String(255), nullable=False)
    role: Mapped[String] = mapped_column(String(255), nullable=False)