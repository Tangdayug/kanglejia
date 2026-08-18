import logging
from datetime import datetime, timedelta

import jwt
import bcrypt
from fastapi import Header, HTTPException
from typing import Optional

from common.constant import TOKEN_EXPIRE_DAYS, TOKEN_EXPIRE_MINUTES, TOKEN_EXPIRE_SECONDS, JWT_SECRET_KEY, DISABLE_AUTH
from exception.customException import TokenException

logger = logging.getLogger(__name__)


class AuthHandler:
    secret = JWT_SECRET_KEY

    def get_password_hash(self, password):
        # bcrypt has a 72-byte limit, truncate password if necessary
        if isinstance(password, str):
            password = password.encode('utf-8')
        if len(password) > 72:
            password = password[:72]
        # Directly use bcrypt instead of passlib
        return bcrypt.hashpw(password, bcrypt.gensalt()).decode('utf-8')

    def verify_password(self, plain_password, hash_password):
        # bcrypt has a 72-byte limit, truncate password if necessary
        if isinstance(plain_password, str):
            plain_password = plain_password.encode('utf-8')
        if len(plain_password) > 72:
            plain_password = plain_password[:72]
        # Ensure hash_password is bytes
        if isinstance(hash_password, str):
            hash_password = hash_password.encode('utf-8')
        # Directly use bcrypt instead of passlib
        return bcrypt.checkpw(plain_password, hash_password)
    def encode_token(self,user_id):
        payload = {
            'exp': datetime.utcnow() + timedelta(days=TOKEN_EXPIRE_DAYS,
                                                 minutes=TOKEN_EXPIRE_MINUTES,
                                                 seconds=TOKEN_EXPIRE_SECONDS),
            'iat': datetime.utcnow(),
            'sub': str(user_id)  # 转换为字符串
        }
        token = jwt.encode(
            payload,
            self.secret,
            algorithm='HS256'
        )
        return token
    def decode_token(self,token):
        try:
            payload = jwt.decode(token, self.secret, algorithms=['HS256'])
            return payload['sub']
        except jwt.ExpiredSignatureError:
            raise TokenException("token过期")
        except jwt.InvalidTokenError as e:
            raise TokenException("token错误")

    def auth_required(self, authorization: Optional[str] = Header(None)):
        """
        认证装饰器

        如果 DISABLE_AUTH=True，直接返回 user_id=1
        否则验证 Authorization header 中的 JWT token
        """
        # 如果禁用认证，直接返回默认用户 ID
        if DISABLE_AUTH:
            logger.debug("auth_required called, returning user_id=1 (auth disabled)")
            return 1

        # 正常认证流程
        if authorization is None:
            logger.warning("auth_required called, but no Authorization header")
            raise HTTPException(status_code=401, detail="未提供认证信息")

        # 检查 Bearer 格式
        if not authorization.startswith("Bearer "):
            logger.warning("auth_required called, invalid Authorization format")
            raise HTTPException(status_code=401, detail="认证格式错误")

        # 提取 token
        token = authorization[7:]  # 跳过 "Bearer "
        logger.debug(f"auth_required called, token: {token[:20]}...")

        # 解码 token
        return self.decode_token(token)

auth_handler = AuthHandler()