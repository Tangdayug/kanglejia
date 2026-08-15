"""
用户API - 提供用户注册功能
"""
from fastapi import Depends

from api import app
from common.result import ResultModel, Result
from model import get_db_session, Session
from model.account import AccountRegister
from service.userService import UserService


@app.post("/register", response_model=ResultModel)
async def register(account: AccountRegister, db_session: Session = Depends(get_db_session)):
    """用户注册"""
    from fastapi.encoders import jsonable_encoder
    user_with_token = UserService.register(account, db_session)
    return Result.success(data=jsonable_encoder(user_with_token))
