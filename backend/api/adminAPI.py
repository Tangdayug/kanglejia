"""
登录API - 提供用户和管理员登录功能
"""
from json import JSONEncoder

from fastapi.encoders import jsonable_encoder
from fastapi.params import Depends

from common.enum import Role
from common.result import Result, ResultModel
from api import app
from model import get_db_session, Session
from model.account import AccountLogin
from model.admin import AdminModel
from service.adminService import AdminService
from service.userService import UserService


@app.post("/login", response_model=ResultModel)
async def login(account: AccountLogin, db_session: Session = Depends(get_db_session)):
    """用户/管理员登录"""
    # 规范化角色名称为 uppercase，避免大小写问题
    role_upper = account.role.upper() if account.role else ""

    if role_upper == "ADMIN" or Role.ADMIN.name.__eq__(account.role):
        db_account = AdminService.login(account, db_session)
    elif role_upper == "USER" or Role.USER.name.__eq__(account.role):
        db_account = UserService.login(account, db_session)
    else:
        return Result.error("角色错误")
    return Result.success(jsonable_encoder(db_account))
