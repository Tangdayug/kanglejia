import logging
import traceback

from fastapi import Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from starlette.responses import JSONResponse

from api import app
from common.result import Result
from exception.customException import UserNotFoundException, PasswordNotMatchException, TokenException, UserExistException

logger = logging.getLogger(__name__)


@app.exception_handler(Exception)
async def exception_handler(request: Request, exc: Exception):
    # 记录详细的错误信息
    logger.error(f"Exception occurred: {type(exc).__name__}: {str(exc)}")
    logger.error(f"Traceback:\n{traceback.format_exc()}")

    # 尝试创建安全的错误响应
    try:
        result = Result.error(code='500', msg=str(exc))
        return JSONResponse(status_code=500, content=jsonable_encoder(result))
    except Exception as e:
        # 如果序列化失败，返回简单的错误信息
        logger.error(f"Failed to serialize error: {e}")
        return JSONResponse(
            status_code=500,
            content={"code": "500", "msg": "Internal server error", "data": {}}
        )

@app.exception_handler(UserNotFoundException)
async def user_not_found_exception_handler(request: Request, exc: UserNotFoundException):
    result = Result.error(code='404',msg=exc.message)
    return JSONResponse(status_code=404,content=jsonable_encoder(result))

@app.exception_handler(PasswordNotMatchException)
async def password_not_match_exception_handler(request: Request, exc: PasswordNotMatchException):
    result = Result.error(code='401',msg=exc.message)
    return JSONResponse(status_code=401,content=jsonable_encoder(result))

@app.exception_handler(TokenException)
async def token_exception_handler(request: Request, exc: TokenException):
    result = Result.error(code='401',msg=exc.message)
    return JSONResponse(status_code=401,content=jsonable_encoder(result))


@app.exception_handler(UserExistException)
async def user_exist_exception_handler(request: Request, exc: UserExistException):
    result = Result.error(code='400',msg=exc.message)
    return JSONResponse(status_code=400,content=jsonable_encoder(result))


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    result = Result.error(code='422', msg=str(exc.errors()))
    return JSONResponse(status_code=422, content=jsonable_encoder(result))