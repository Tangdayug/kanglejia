"""
干预记录API - 提供干预记录管理功能
"""
from datetime import datetime
from typing import Optional
from fastapi import Depends, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel

from api import app
from common.auth import auth_handler
from common.result import ResultModel, Result
from model import get_db_session
from service.chatService import ChatService


class UpdateStatusRequest(BaseModel):
    interventionId: int
    status: str


class AddFeedbackRequest(BaseModel):
    interventionId: int
    feedback: str
    executed: Optional[bool] = None
    effectiveness: Optional[str] = None


def _intervention_to_dict(intervention) -> dict:
    """将InterventionLog模型转换为字典"""
    return {
        'id': intervention.id,
        'userId': intervention.user_id,
        'sessionId': intervention.session_id,
        'suggestion': intervention.intervention_suggestion,
        'feedback': intervention.user_feedback,
        'status': intervention.execution_status,
        'createdAt': intervention.created_at.isoformat() if intervention.created_at else None,
        'updatedAt': intervention.updated_at.isoformat() if intervention.updated_at else None
    }


@app.get("/intervention/user", response_model=ResultModel)
async def get_user_interventions(
    status: Optional[str] = Query(None),
    limit: int = Query(50),
    user_id: int = Depends(auth_handler.auth_required),
    db_session: Session = Depends(get_db_session)
):
    """获取用户的干预记录（可按状态筛选）"""
    interventions = ChatService.get_user_interventions(
        user_id=user_id,
        db_session=db_session,
        status=status,
        limit=limit
    )

    return Result.success(data={
        'interventions': [_intervention_to_dict(i) for i in interventions]
    })


@app.put("/intervention/status", response_model=ResultModel)
async def update_intervention_status(
    request: UpdateStatusRequest,
    user_id: int = Depends(auth_handler.auth_required),
    db_session: Session = Depends(get_db_session)
):
    """更新干预执行状态（pending/completed/dismissed）"""
    from model.interventionLog import InterventionLog
    from sqlalchemy import select

    query = select(InterventionLog).where(
        InterventionLog.id == request.interventionId,
        InterventionLog.user_id == user_id
    )
    intervention = db_session.execute(query).scalar_one_or_none()

    if not intervention:
        return Result.error(message="干预记录不存在")

    valid_statuses = ['pending', 'completed', 'dismissed']
    if request.status not in valid_statuses:
        return Result.error(message=f"无效的状态值，允许的值: {', '.join(valid_statuses)}")

    intervention.execution_status = request.status
    intervention.updated_at = datetime.now()
    db_session.commit()

    return Result.success(data=_intervention_to_dict(intervention))


@app.post("/intervention/feedback", response_model=ResultModel)
async def add_intervention_feedback(
    request: AddFeedbackRequest,
    user_id: int = Depends(auth_handler.auth_required),
    db_session: Session = Depends(get_db_session)
):
    """添加用户反馈到干预记录"""
    from model.interventionLog import InterventionLog
    from sqlalchemy import select
    from datetime import datetime

    query = select(InterventionLog).where(
        InterventionLog.id == request.interventionId,
        InterventionLog.user_id == user_id
    )
    intervention = db_session.execute(query).scalar_one_or_none()

    if not intervention:
        return Result.error(message="干预记录不存在")

    intervention.user_feedback = request.feedback
    intervention.execution_status = 'completed'
    intervention.updated_at = datetime.now()
    db_session.commit()

    return Result.success(data=_intervention_to_dict(intervention))


@app.delete("/intervention/{intervention_id}", response_model=ResultModel)
async def delete_intervention(
    intervention_id: int,
    user_id: int = Depends(auth_handler.auth_required),
    db_session: Session = Depends(get_db_session)
):
    """删除干预记录"""
    from model.interventionLog import InterventionLog
    from sqlalchemy import select

    query = select(InterventionLog).where(
        InterventionLog.id == intervention_id,
        InterventionLog.user_id == user_id
    )
    intervention = db_session.execute(query).scalar_one_or_none()

    if not intervention:
        return Result.error(message="干预记录不存在")

    db_session.delete(intervention)
    db_session.commit()

    return Result.success(data={'deleted': intervention_id})
