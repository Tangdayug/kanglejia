"""
日常关怀API - 提供每日关怀和反馈功能
"""
from fastapi import Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel

from api import app
from common.auth import auth_handler
from common.result import ResultModel, Result
from model import get_db_session
from service.careService import CareService


class FeedbackRequest(BaseModel):
    interventionId: int
    feedback: str
    sessionId: int


@app.get("/care/daily-message", response_model=ResultModel)
async def get_daily_care_message(
    user_id: int = Depends(auth_handler.auth_required),
    db_session: Session = Depends(get_db_session)
):
    """获取每日关怀消息（基于近7天干预记录、3天对话历史和健康档案）"""
    message_data = CareService.generate_daily_care(user_id, db_session)
    return Result.success(data=message_data)


@app.post("/care/submit-feedback", response_model=ResultModel)
async def submit_feedback(
    request: FeedbackRequest,
    user_id: int = Depends(auth_handler.auth_required),
    db_session: Session = Depends(get_db_session)
):
    """提交干预建议的用户反馈"""
    success = CareService.save_feedback(
        user_id,
        request.interventionId,
        request.feedback,
        request.sessionId,
        db_session
    )

    if success:
        return Result.success(data={'updated': True})
    else:
        return Result.error(message="更新反馈失败")
