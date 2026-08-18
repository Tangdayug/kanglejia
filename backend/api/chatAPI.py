"""
聊天API - 提供AI聊天功能的REST端点和SSE流式传输
"""
import asyncio
import json
import logging
from typing import List, Dict, Any, Optional

from fastapi import Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from api import app
from common.auth import auth_handler
from common.result import ResultModel, Result
from model import get_db_session
from service.chatService import ChatService
from exception.customException import NotFoundException

logger = logging.getLogger(__name__)


async def _extract_intervention_async(
    user_id: int,
    session_id: int,
    user_message: str,
    assistant_response: str
):
    """异步提取健康干预建议，不阻塞前端 SSE 流。"""
    try:
        db = next(get_db_session())
        try:
            await asyncio.to_thread(
                ChatService.extract_and_save_intervention,
                user_id=user_id,
                session_id=session_id,
                user_message=user_message,
                assistant_response=assistant_response,
                db_session=db
            )
        finally:
            db.close()
    except Exception:
        # 干预提取失败不应影响对话体验
        pass


class CreateSessionRequest(BaseModel):
    title: Optional[str] = None


class SendMessageRequest(BaseModel):
    session_id: int
    message: str


class ChatMessageResponse(BaseModel):
    id: int
    session_id: int
    role: str
    content: str
    sources: Optional[Dict[str, Any]] = None
    created_at: str


def _message_to_dict(message) -> dict:
    """将ChatMessage模型转换为字典（由模型自身维护）。"""
    return message.to_dict()


def _session_to_dict(session) -> dict:
    """将ChatSession模型转换为字典（由模型自身维护）。"""
    return session.to_dict()

@app.post("/chat/sessions", response_model=ResultModel)
async def create_chat_session(
    request: CreateSessionRequest = None,
    user_id: int = Depends(auth_handler.auth_required),
    db_session: Session = Depends(get_db_session)
):
    """创建新的聊天会话"""
    title = request.title if request else None
    session = ChatService.create_session(user_id=user_id, title=title, db_session=db_session)
    return Result.success(data=_session_to_dict(session))


@app.get("/chat/sessions", response_model=ResultModel)
async def get_chat_sessions(
    user_id: int = Depends(auth_handler.auth_required),
    db_session: Session = Depends(get_db_session)
):
    """获取当前用户的所有聊天会话"""
    sessions = ChatService.get_user_sessions(user_id=user_id, db_session=db_session)
    return Result.success(data={
        'sessions': [_session_to_dict(s) for s in sessions]
    })


@app.get("/chat/sessions/{session_id}", response_model=ResultModel)
async def get_chat_session(
    session_id: int,
    user_id: int = Depends(auth_handler.auth_required),
    db_session: Session = Depends(get_db_session)
):
    """获取指定ID的聊天会话"""
    sessions = ChatService.get_user_sessions(user_id=user_id, db_session=db_session)
    session = next((s for s in sessions if s.id == session_id), None)

    if not session:
        raise NotFoundException("会话不存在")

    return Result.success(data=_session_to_dict(session))

@app.get("/chat/sessions/{session_id}/messages", response_model=ResultModel)
async def get_chat_messages(
    session_id: int,
    user_id: int = Depends(auth_handler.auth_required),
    db_session: Session = Depends(get_db_session)
):
    """获取会话的所有消息"""
    messages = ChatService.get_session_messages(
        session_id=session_id,
        user_id=user_id,
        db_session=db_session
    )
    return Result.success(data={
        'messages': [_message_to_dict(m) for m in messages]
    })


@app.post("/chat/send", response_model=ResultModel)
async def send_chat_message(
    request: SendMessageRequest,
    user_id: int = Depends(auth_handler.auth_required),
    db_session: Session = Depends(get_db_session)
):
    """发送消息并获取非流式响应"""
    result = ChatService.generate_chat_response(
        user_id=user_id,
        session_id=request.session_id,
        user_message=request.message,
        db_session=db_session
    )
    return Result.success(data={
        'response': result['response'],
        'sources': result['sources']
    })


@app.get("/chat/stream/{session_id}")
async def stream_chat_message(
    session_id: int,
    message: str,
    user_id: int = Depends(auth_handler.auth_required),
    db_session: Session = Depends(get_db_session)
):
    """使用SSE流式传输聊天响应"""

    async def event_generator():
        """生成SSE事件"""
        try:
            from model.chatHistory import ChatMessage
            from sqlalchemy import select, desc

            chunk_count = 0
            for chunk in ChatService.stream_chat_response(
                user_id=user_id,
                session_id=session_id,
                user_message=message,
                db_session=db_session
            ):
                chunk_count += 1
                yield f"data: {json.dumps({'content': chunk}, ensure_ascii=False)}\n\n"
                await asyncio.sleep(0)

            message_query = select(ChatMessage).where(
                ChatMessage.session_id == session_id,
                ChatMessage.role == 'assistant'
            ).order_by(desc(ChatMessage.created_at)).limit(1)
            assistant_message = db_session.execute(message_query).scalar_one_or_none()

            sources_data = None
            if assistant_message and assistant_message.sources:
                sources_data = assistant_message.sources

            yield f"data: {json.dumps({'done': True, 'sources': sources_data}, ensure_ascii=False)}\n\n"

            # 流结束后异步提取干预建议，避免阻塞前端
            asyncio.create_task(_extract_intervention_async(
                user_id=user_id,
                session_id=session_id,
                user_message=message,
                assistant_response=assistant_message.content if assistant_message else ""
            ))

        except Exception as e:
            logger.exception("[Chat] stream chat failed")
            yield f"data: {json.dumps({'error': str(e)}, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-transform",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
            "Pragma": "no-cache"
        }
    )


@app.get("/chat/sessions/{session_id}/recommendations", response_model=ResultModel)
async def get_recommendations(
    session_id: int,
    user_id: int = Depends(auth_handler.auth_required),
    db_session: Session = Depends(get_db_session)
):
    """获取推荐的提问"""
    recommendations = ChatService.generate_recommendations(
        user_id=user_id,
        session_id=session_id,
        db_session=db_session
    )
    return Result.success(data={
        'recommendations': recommendations
    })


@app.get("/chat/readiness", response_model=ResultModel)
async def check_readiness(
    user_id: int = Depends(auth_handler.auth_required),
    db_session: Session = Depends(get_db_session)
):
    """检查用户是否已完成健康档案和健康测试"""
    readiness = ChatService.check_user_readiness(user_id=user_id, db_session=db_session)
    return Result.success(data=readiness)


@app.delete("/chat/sessions/{session_id}", response_model=ResultModel)
async def delete_chat_session(
    session_id: int,
    user_id: int = Depends(auth_handler.auth_required),
    db_session: Session = Depends(get_db_session)
):
    """删除聊天会话及其所有消息"""
    from model.chatHistory import ChatSession, ChatMessage

    query = db_session.query(ChatSession).filter(
        ChatSession.id == session_id,
        ChatSession.user_id == user_id
    )
    session = query.first()

    if not session:
        raise NotFoundException("会话不存在")

    # 显式删除消息：SQLite 默认不开启外键级联，保留手动删除以保证兼容性
    db_session.query(ChatMessage).filter(
        ChatMessage.session_id == session_id
    ).delete()

    db_session.delete(session)
    db_session.commit()

    return Result.success(data={'deleted': session_id})


@app.put("/chat/sessions/{session_id}/title", response_model=ResultModel)
async def update_session_title(
    session_id: int,
    title: str,
    user_id: int = Depends(auth_handler.auth_required),
    db_session: Session = Depends(get_db_session)
):
    """更新会话标题"""
    from model.chatHistory import ChatSession

    query = db_session.query(ChatSession).filter(
        ChatSession.id == session_id,
        ChatSession.user_id == user_id
    )
    session = query.first()

    if not session:
        raise NotFoundException("会话不存在")

    session.title = title
    db_session.commit()

    return Result.success(data=_session_to_dict(session))


class AnalyzeHealthHistoryRequest(BaseModel):
    history: List[Dict[str, Any]]


@app.post("/chat/analyze-health-history", response_model=ResultModel)
async def analyze_health_history(
    request: AnalyzeHealthHistoryRequest,
    user_id: int = Depends(auth_handler.auth_required),
    db_session: Session = Depends(get_db_session)
):
    """分析健康历史记录"""
    analysis = ChatService.analyze_health_history(history=request.history)
    return Result.success(data={'analysis': analysis})
