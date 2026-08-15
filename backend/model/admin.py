import bcrypt
from pydantic import BaseModel
from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped,mapped_column

from model import Base


class Admin(Base):
    """管理员表"""
    __tablename__ = 'admin'
    id:Mapped[int] = mapped_column(Integer, primary_key=True,nullable=False)
    username:Mapped[String] = mapped_column(String(255), nullable=False)
    password:Mapped[String] = mapped_column(String(255), nullable=False)
    name: Mapped[String] = mapped_column(String(255), nullable=False)
    role: Mapped[String] = mapped_column(String(255), nullable=False)

    def password_check(self,password:str)->bool:
        """验证密码"""
        return bcrypt.checkpw(password.encode(),self.password.encode())

class AdminModel(BaseModel):
    """管理员登录模型"""
    username: str
    password: str

class AdminLoginResponse(BaseModel):
    """管理员登录响应模型"""
    id: int
    username: str
    token: str
