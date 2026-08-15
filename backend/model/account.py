from pydantic import BaseModel


class AccountLogin(BaseModel):
    """账号登录模型"""
    username: str
    password: str
    role: str

class AccountLoginResponse:
    """账号登录响应模型"""
    id: int
    username: str
    name: str
    role: str
    token: str

class AccountRegister(BaseModel):
    """账号注册模型"""
    username: str
    password: str