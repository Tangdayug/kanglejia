from fastapi.encoders import jsonable_encoder
from sqlalchemy import select, String

from common.auth import auth_handler
from common.enum import Role
from common.utils import set_attrs
from exception.customException import UserNotFoundException, PasswordNotMatchException, UserExistException
from model import Session
from model.account import AccountLogin, AccountLoginResponse, AccountRegister
from model.user import User


class UserService:
    """用户服务类"""

    @staticmethod
    def login(account: AccountLogin, db_session: Session) -> AccountLoginResponse:
        query = select(User).where(User.username == account.username)
        exist_user: User = db_session.execute(query).scalar()
        if not exist_user:
            raise UserNotFoundException("用户不存在")
        if not auth_handler.verify_password(account.password, exist_user.password):
            raise PasswordNotMatchException("密码错误")
        account_login_response = AccountLoginResponse()
        set_attrs(account_login_response, jsonable_encoder(exist_user))
        account_login_response.token = auth_handler.encode_token(exist_user.id)
        return account_login_response

    @staticmethod
    def register(account: AccountRegister, db_session: Session) -> AccountLoginResponse:
        query = select(User).where(User.username == account.username)
        exist_user: User = db_session.execute(query).scalar()
        if exist_user:
            raise UserExistException("用户已注册")
        new_user = User()
        account.password = auth_handler.get_password_hash(account.password)
        set_attrs(new_user, jsonable_encoder(account))
        if not new_user.name:
            new_user.name = new_user.username
        # 设置默认 gender 为 "未设置"
        if not new_user.gender:
            new_user.gender = "未设置"
        new_user.role = Role.USER.name
        db_session.add(new_user)
        db_session.commit()

        # 注册成功后生成token并返回用户信息
        account_login_response = AccountLoginResponse()
        set_attrs(account_login_response, jsonable_encoder(new_user))
        account_login_response.token = auth_handler.encode_token(new_user.id)
        return account_login_response
