"""
OpenAI 兼容的 LLM 代理接口

用于让小智服务器（xiaozhi-esp32-server）把 second-nature 智能体的对话请求
转发到 SecondNature，由 SecondNature 提供面向老年人的健康咨询回复。

xiaozhi-server 的 LLM 配置指向：
  base_url: http://secondnature:7860/api/v1
  model: second-nature
"""
import json
import time
from typing import Any, Dict, Iterator, List, Optional

from fastapi import Depends, Header, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from api import app
from common.auth import auth_handler
from common import xiaozhi_prompts as prompts
from common.deepseek_client import get_deepseek_client
from common.result import ResultModel, Result
from model import get_db_session
from service.chatService import ChatService
from service import icope_test_service as icope


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatCompletionRequest(BaseModel):
    model: str = "second-nature"
    messages: List[ChatMessage]
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = None
    stream: bool = False
    user: Optional[str] = None


class ChatCompletionChoice(BaseModel):
    index: int = 0
    message: ChatMessage
    finish_reason: str = "stop"


class ChatCompletionUsage(BaseModel):
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


class ChatCompletionResponse(BaseModel):
    id: str = "sn-chatcmpl-001"
    object: str = "chat.completion"
    created: int = 0
    model: str = "second-nature"
    choices: List[ChatCompletionChoice]
    usage: ChatCompletionUsage


class ChatCompletionDelta(BaseModel):
    role: Optional[str] = None
    content: Optional[str] = None


class ChatCompletionChunkChoice(BaseModel):
    index: int = 0
    delta: ChatCompletionDelta
    finish_reason: Optional[str] = None


class ChatCompletionChunk(BaseModel):
    id: str = "sn-chatcmpl-001"
    object: str = "chat.completion.chunk"
    created: int = 0
    model: str = "second-nature"
    choices: List[ChatCompletionChunkChoice]


# 默认用户ID：当 xiaozhi-server 未传递明确用户标识时使用
DEFAULT_USER_ID = 1


def _build_system_prompt() -> str:
    """构造面向小智硬件对话的系统提示词（不含 ICOPE 流程，由后端状态机控制）。"""
    return prompts.HEALTH_CONSULT_SYSTEM_PROMPT


def _static_text_response(text: str, model: str) -> ChatCompletionResponse:
    """把固定文本包装成非流式 OpenAI 响应。"""
    return ChatCompletionResponse(
        model=model,
        choices=[
            ChatCompletionChoice(
                message=ChatMessage(role="assistant", content=text)
            )
        ],
        usage=ChatCompletionUsage()
    )


def _static_text_stream(text: str, model: str) -> Iterator[str]:
    """把固定文本包装成 SSE 流式响应。"""
    created = int(time.time())
    chunk_id = "sn-chatcmpl-001"

    yield _sse_chunk({
        "id": chunk_id,
        "object": "chat.completion.chunk",
        "created": created,
        "model": model,
        "choices": [{
            "index": 0,
            "delta": {"role": "assistant", "content": ""},
            "finish_reason": None
        }]
    })

    # 按句子切分，模拟流式输出
    parts = []
    start = 0
    for i, ch in enumerate(text):
        if ch in ("，", "。", "！", "？", "；") and i > start:
            parts.append(text[start:i + 1])
            start = i + 1
    if start < len(text):
        parts.append(text[start:])
    if not parts:
        parts = [text]

    for part in parts:
        yield _sse_chunk({
            "id": chunk_id,
            "object": "chat.completion.chunk",
            "created": created,
            "model": model,
            "choices": [{
                "index": 0,
                "delta": {"content": part},
                "finish_reason": None
            }]
        })

    yield _sse_chunk({
        "id": chunk_id,
        "object": "chat.completion.chunk",
        "created": created,
        "model": model,
        "choices": [{
            "index": 0,
            "delta": {},
            "finish_reason": "stop"
        }]
    })
    yield "data: [DONE]\n\n"


def _get_user_id_from_request(request: ChatCompletionRequest) -> int:
    """
    尝试从请求中识别用户。
    xiaozhi-server 目前不会传 device-id，这里先用默认值，
    后续可扩展为按 model 名或 user 字段映射。
    """
    if request.user and request.user.isdigit():
        return int(request.user)
    return DEFAULT_USER_ID


def _extract_text_content(text: str) -> str:
    """
    从小智硬件发来的 JSON 格式消息中提取真正的文本内容。
    硬件 ASR 结果可能是：{"content": "...", "language": "zh", "emotion": "😶"}
    """
    if not text or not text.strip().startswith("{"):
        return text
    try:
        data = json.loads(text)
        if isinstance(data, dict) and "content" in data and isinstance(data["content"], str):
            return data["content"]
    except (json.JSONDecodeError, TypeError):
        pass
    return text


def _messages_to_conversation_history(messages: List[ChatMessage]) -> List[Dict[str, str]]:
    """把 OpenAI 格式消息转成 SecondNature 内部格式，并过滤 system。"""
    return [
        {"role": m.role, "content": _extract_text_content(m.content)}
        for m in messages
        if m.role in ("user", "assistant")
    ]


def _extract_user_message(messages: List[ChatMessage]) -> str:
    """取最后一条用户消息作为当前输入，并解析硬件 JSON 格式。"""
    for m in reversed(messages):
        if m.role == "user":
            return _extract_text_content(m.content)
    return ""


def _build_llm_messages(
    system_prompt: str,
    user_message: str,
    conversation_history: List[Dict[str, str]]
) -> List[Dict[str, str]]:
    """组装符合 OpenAI 格式的消息列表。"""
    messages: List[Dict[str, str]] = [{"role": "system", "content": system_prompt}]
    if conversation_history:
        # 去掉最后一条用户消息，避免重复
        messages.extend(conversation_history[:-1])
    messages.append({"role": "user", "content": user_message})
    return messages


def _sse_chunk(payload: Dict[str, Any]) -> str:
    return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"


def _stream_response(
    client,
    messages: List[Dict[str, str]],
    temperature: float,
    max_tokens: Optional[int],
    model: str
) -> Iterator[str]:
    """以 OpenAI SSE 格式流式返回 DeepSeek 生成的内容。"""
    created = int(time.time())
    chunk_id = "sn-chatcmpl-001"

    # 首帧：返回 assistant role
    yield _sse_chunk({
        "id": chunk_id,
        "object": "chat.completion.chunk",
        "created": created,
        "model": model,
        "choices": [{
            "index": 0,
            "delta": {"role": "assistant", "content": ""},
            "finish_reason": None
        }]
    })

    full_text = ""
    try:
        for delta in client.stream_chat_completion(
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        ):
            if not delta:
                continue
            full_text += delta
            yield _sse_chunk({
                "id": chunk_id,
                "object": "chat.completion.chunk",
                "created": created,
                "model": model,
                "choices": [{
                    "index": 0,
                    "delta": {"content": delta},
                    "finish_reason": None
                }]
            })
    except Exception as e:
        print(f"[LLM API] streaming error: {e}")
        yield _sse_chunk({
            "id": chunk_id,
            "object": "chat.completion.chunk",
            "created": created,
            "model": model,
            "choices": [{
                "index": 0,
                "delta": {"content": ""},
                "finish_reason": "stop"
            }]
        })
    else:
        yield _sse_chunk({
            "id": chunk_id,
            "object": "chat.completion.chunk",
            "created": created,
            "model": model,
            "choices": [{
                "index": 0,
                "delta": {},
                "finish_reason": "stop"
            }]
        })

    yield "data: [DONE]\n\n"


@app.post("/v1/chat/completions")
async def create_chat_completion(
    request: ChatCompletionRequest,
    db_session: Session = Depends(get_db_session)
):
    """
    OpenAI 兼容的聊天补全接口。

    xiaozhi-server 会把 second-nature 智能体的对话历史 POST 到这里，
    SecondNature 基于健康咨询提示词生成回复。
    """
    user_id = _get_user_id_from_request(request)
    user_message = _extract_user_message(request.messages)
    conversation_history = _messages_to_conversation_history(request.messages)

    # 创建或复用聊天会话（按用户维度）
    try:
        sessions = ChatService.get_user_sessions(user_id, db_session)
        if sessions:
            chat_session = sessions[0]
        else:
            chat_session = ChatService.create_session(
                user_id=user_id,
                title="小智健康咨询",
                db_session=db_session
            )
        session_id = chat_session.id
    except Exception as e:
        # 数据库异常时降级到无状态回复
        print(f"[LLM API] session error: {e}")
        session_id = None

    # -----------------------------------------------------------------
    # ICOPE 测试状态机优先处理
    # -----------------------------------------------------------------
    icope_reply: Optional[str] = None
    if icope.is_active(user_id):
        icope_reply = icope.process_answer(user_id, user_message)
    elif icope.is_trigger(user_message):
        icope_reply = icope.start_test(user_id)

    if icope_reply is not None:
        # 保存对话记录
        if session_id:
            try:
                ChatService.save_message(session_id, "user", user_message, db_session=db_session)
                ChatService.save_message(session_id, "assistant", icope_reply, db_session=db_session)
            except Exception as e:
                print(f"[LLM API] save message error: {e}")

        if request.stream:
            return StreamingResponse(
                _static_text_stream(icope_reply, request.model or "second-nature"),
                media_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "X-Accel-Buffering": "no",
                }
            )
        return _static_text_response(icope_reply, request.model or "second-nature")

    # -----------------------------------------------------------------
    # 普通健康咨询：调用 LLM
    # -----------------------------------------------------------------
    system_prompt = _build_system_prompt()
    client = get_deepseek_client()
    messages = _build_llm_messages(system_prompt, user_message, conversation_history)

    # 流式响应：xiaozhi-server 默认使用 stream=True
    if request.stream:
        def generate():
            full_text = ""
            for chunk_text in _stream_response(
                client=client,
                messages=messages,
                temperature=request.temperature or 0.7,
                max_tokens=request.max_tokens,
                model=request.model or "second-nature"
            ):
                # 收集完整回复用于保存记录
                if chunk_text.startswith("data: {") and '"delta":' in chunk_text and '"content":' in chunk_text:
                    try:
                        data = json.loads(chunk_text[6:].strip())
                        delta_content = data.get("choices", [{}])[0].get("delta", {}).get("content", "")
                        full_text += delta_content
                    except Exception:
                        pass
                yield chunk_text

            # 保存对话记录
            if session_id:
                try:
                    ChatService.save_message(session_id, "user", user_message, db_session=db_session)
                    ChatService.save_message(session_id, "assistant", full_text, db_session=db_session)
                except Exception as e:
                    print(f"[LLM API] save message error: {e}")

        return StreamingResponse(
            generate(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            }
        )

    # 非流式响应（兼容测试）
    response_text = client.generate_chat_response(
        system_prompt=system_prompt,
        user_message=user_message,
        conversation_history=conversation_history[:-1] if conversation_history else [],
        temperature=request.temperature or 0.7
    )

    # 如果会话创建成功，保存对话记录
    if session_id:
        try:
            ChatService.save_message(session_id, "user", user_message, db_session=db_session)
            ChatService.save_message(session_id, "assistant", response_text, db_session=db_session)
        except Exception as e:
            print(f"[LLM API] save message error: {e}")

    return ChatCompletionResponse(
        model=request.model or "second-nature",
        choices=[
            ChatCompletionChoice(
                message=ChatMessage(role="assistant", content=response_text)
            )
        ],
        usage=ChatCompletionUsage()
    )


@app.get("/v1/models", response_model=ResultModel)
async def list_models():
    """OpenAI 兼容的模型列表接口。"""
    return Result.success(data={
        "object": "list",
        "data": [
            {
                "id": "second-nature",
                "object": "model",
                "created": 0,
                "owned_by": "secondnature"
            }
        ]
    })
