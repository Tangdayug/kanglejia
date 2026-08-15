from pydantic import BaseModel
from typing import Any, Dict

class ResultModel(BaseModel):
    data: Dict[str, Any] = {}
    msg: str = 'success'
    code: str = '200'

class Result:
    def __init__(self, data, msg, code):
        self.data = data
        self.msg = msg
        self.code = code

    @classmethod
    def success(cls,data:object=None, msg='success', code='200'):
        if not data:
            data = {}
        return cls(data=data, msg=msg, code=code)

    @classmethod
    def error(cls,data:object=None, msg='error', code='500'):
        if not data:
            data = {}
        return cls(data=data, msg=msg, code=code)