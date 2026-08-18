from pydantic import BaseModel
from typing import Any, Optional

class ResultModel(BaseModel):
    data: Optional[Any] = {}
    msg: str = 'success'
    code: str = '200'

class Result:
    def __init__(self, data, msg, code):
        self.data = data
        self.msg = msg
        self.code = code

    @classmethod
    def success(cls, data: object = None, msg='success', code='200'):
        return cls(data=data, msg=msg, code=code)

    @classmethod
    def error(cls, data: object = None, msg='error', code='500'):
        return cls(data=data, msg=msg, code=code)
