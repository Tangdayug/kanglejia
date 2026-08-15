"""
小智（XiaoZhi）硬件 WebSocket 与 REST API

提供：
- /ws/xiaozhi      硬件 WebSocket 接入端
- /xiaozhi/status  服务状态
- /xiaozhi/sessions 会话列表
- /xiaozhi/session/{id}/reset 重置会话
"""
import asyncio
import base64
import json
import traceback
from typing import Any, Dict, List, Optional

from fastapi import Depends, WebSocket, WebSocketDisconnect, Query
from pydantic import BaseModel
from sqlalchemy import select, desc
from sqlalchemy.orm import Session

from api import app
from common.auth import auth_handler
from common.constant import DISABLE_AUTH
from common.result import ResultModel, Result
from exception.customException import NotFoundException
from model import get_db_session
from model.xiaozhiSession import XiaozhiVoiceSession
from service.xiaozhiService import (
    XiaozhiDialogueManager,
    XiaozhiWebSocketClient,
    dialogue_manager,
    register_voiceprint
)


# ---------------------------------------------------------------------------
# 依赖与工具
# ---------------------------------------------------------------------------

def _extract_user_id_from_websocket(websocket: WebSocket) -> Optional[int]:
    """从 WebSocket header 解析用户ID，失败时返回 fallback。"""
    if DISABLE_AUTH:
        return 1

    authorization = websocket.headers.get("authorization")
    if not authorization or not authorization.startswith("Bearer "):
        return None

    try:
        token = authorization[7:]
        user_id = int(auth_handler.decode_token(token))
        return user_id
    except Exception:
        return None


class VoiceprintRegisterRequest(BaseModel):
    voiceprint_id: str
    user_id: Optional[int] = None  # 不传则默认绑定到当前登录账号
    display_name: Optional[str] = None


class DeviceAllowRequest(BaseModel):
    voiceprint_id: str
    user_id: Optional[int] = None  # 不传则默认操作当前登录账号的设备
    is_allowed: bool = True
    display_name: Optional[str] = None
    verification_status: Optional[str] = None


def _voice_session_to_dict(session: XiaozhiVoiceSession) -> Dict[str, Any]:
    return {
        "id": session.id,
        "user_id": session.user_id,
        "voiceprint_id": session.voiceprint_id,
        "session_type": session.session_type,
        "created_at": session.created_at.isoformat() if session.created_at else None,
        "updated_at": session.updated_at.isoformat() if session.updated_at else None,
        "last_active_at": session.last_active_at.isoformat() if session.last_active_at else None
    }


# ---------------------------------------------------------------------------
# WebSocket 接入端
# ---------------------------------------------------------------------------

@app.websocket("/ws/xiaozhi")
async def xiaozhi_websocket_endpoint(websocket: WebSocket):
    """
    小智硬件 WebSocket 接入端。

    消息协议（JSON）：
    - { "type": "hello", "voiceprint_id": "...", "dialect_code": "mandarin" }
    - { "type": "stt", "text": "..." }
    - { "type": "audio", "data": "base64..." }
    - { "type": "interrupt" }
    - { "type": "speak_done" }   硬件端播报完成

    服务端下发：
    - { "type": "response", "text": "...", "audio": "base64...", "action": null, "mode": "..." }
    - { "type": "control", "action": "stop_speaking" }
    """
    await websocket.accept()

    session_id: Optional[int] = None
    outbound_client: Optional[XiaozhiWebSocketClient] = None
    user_id = _extract_user_id_from_websocket(websocket)

    # 优先从 WebSocket URL 查询参数获取系统 token 与智能体名称，hello 消息里也可覆盖
    system_token = websocket.query_params.get("token")
    agent_name = websocket.query_params.get("agent_name")

    # 启动清理循环（全局只启动一次）
    await dialogue_manager.start_cleanup_loop()

    async def forward_to_hardware(data: Dict[str, Any]):
        """把代理服务器消息转发给硬件。"""
        try:
            await websocket.send_json(data)
        except Exception as e:
            print(f"[XiaoZhi] forward to hardware failed: {e}")

    try:
        while True:
            # 正确解析 Starlette WebSocket 的 ASGI 消息帧
            raw = await websocket.receive()

            if raw.get("type") == "websocket.disconnect":
                raise WebSocketDisconnect()

            if "text" in raw:
                try:
                    message = json.loads(raw["text"])
                except json.JSONDecodeError:
                    await websocket.send_json({
                        "type": "error",
                        "message": "消息格式错误，请发送 JSON"
                    })
                    continue
            elif "bytes" in raw:
                # 二进制音频直接转发给代理服务器
                if outbound_client and outbound_client.connected:
                    await outbound_client.send_audio(raw["bytes"])
                continue
            else:
                continue

            msg_type = message.get("type")

            # hello：建立/复用会话
            if msg_type == "hello":
                voiceprint_id = message.get("voiceprint_id") or "anonymous"
                dialect_code = message.get("dialect_code", "mandarin")
                # hello 消息中的 token / agent_name 可覆盖 URL 中的值
                hello_token = message.get("system_token") or system_token
                hello_agent_name = message.get("agent_name") or agent_name

                db_session = next(get_db_session())
                try:
                    session_id, is_new = dialogue_manager.get_or_create_voice_session(
                        voiceprint_id=voiceprint_id,
                        db_session=db_session,
                        fallback_user_id=user_id,
                        dialect_code=dialect_code,
                        token=hello_token,
                        agent_name=hello_agent_name
                    )

                    # WebSocket 层账号隔离校验：
                    # 若硬件携带了用户 JWT，则必须与会话归属账号一致；
                    # 无 JWT 时由声纹绑定关系决定归属账号。
                    session_state = dialogue_manager.get_session_state(session_id)
                    session_user_id = session_state.get("user_id") if session_state else None
                    if user_id is not None and session_user_id is not None and session_user_id != user_id:
                        raise PermissionError("该声纹/设备已绑定到其他账号，无法接入本系统")

                    # 尝试连接出站代理桥（后台异步，避免阻塞 hello 响应）
                    outbound_client = XiaozhiWebSocketClient(token=hello_token)
                    outbound_client.set_inbound_callback(forward_to_hardware)
                    asyncio.create_task(outbound_client.connect())

                    state = dialogue_manager.get_session_state(session_id)
                    mode = state.get("mode", "idle") if state else "idle"

                    await websocket.send_json({
                        "type": "control",
                        "action": "session_ready",
                        "session_id": session_id,
                        "is_new": is_new,
                        "mode": mode
                    })
                except PermissionError as e:
                    await websocket.send_json({
                        "type": "error",
                        "action": "rejected",
                        "message": str(e)
                    })
                    break
                finally:
                    db_session.close()
                continue

            # 必须先 hello
            if session_id is None:
                await websocket.send_json({
                    "type": "error",
                    "message": "请先发送 hello 消息"
                })
                continue

            # 用户语音转文本
            if msg_type == "stt" or msg_type == "text":
                text = message.get("text", "")
                db_session = next(get_db_session())
                try:
                    response = await dialogue_manager.handle_text_message(
                        session_id=session_id,
                        text=text,
                        db_session=db_session
                    )
                    await _send_response(websocket, response)
                finally:
                    db_session.close()
                continue

            # 音频数据：本地处理不了时转发给代理服务器
            if msg_type == "audio":
                audio_data = message.get("data")
                if audio_data and outbound_client and outbound_client.connected:
                    try:
                        raw_audio = base64.b64decode(audio_data)
                        await outbound_client.send_audio(raw_audio)
                    except Exception as e:
                        print(f"[XiaoZhi] audio forward error: {e}")
                continue

            # 显式打断
            if msg_type == "interrupt":
                db_session = next(get_db_session())
                try:
                    response = await dialogue_manager.handle_interrupt(
                        session_id=session_id,
                        text=message.get("text", ""),
                        db_session=db_session
                    )
                    await _send_response(websocket, response)
                finally:
                    db_session.close()
                continue

            # 播报完成
            if msg_type == "speak_done":
                dialogue_manager.mark_speaking_done(session_id)
                continue

            # 未知类型
            await websocket.send_json({
                "type": "error",
                "message": f"未知消息类型: {msg_type}"
            })

    except WebSocketDisconnect:
        pass
    except Exception as e:
        print(f"[XiaoZhi] websocket error: {e}")
        traceback.print_exc()
    finally:
        if outbound_client:
            await outbound_client.close()
        if session_id is not None:
            db_session = next(get_db_session())
            try:
                dialogue_manager.close_session(session_id, db_session=db_session)
            finally:
                db_session.close()


async def _send_response(websocket: WebSocket, response: Dict[str, Any]):
    """将内部响应转换为 WebSocket 可发送的 JSON（音频 base64 编码）。"""
    payload = dict(response)
    audio = payload.pop("audio", None)
    if audio is not None:
        payload["audio"] = base64.b64encode(audio).decode("utf-8")
    else:
        payload["audio"] = None
    await websocket.send_json(payload)


# ---------------------------------------------------------------------------
# REST 端点
# ---------------------------------------------------------------------------

@app.get("/xiaozhi/status", response_model=ResultModel)
async def get_xiaozhi_status(
    user_id: int = Depends(auth_handler.auth_required)
):
    """获取小智服务当前状态与活跃会话概览。"""
    status = dialogue_manager.get_status()
    return Result.success(data=status)


@app.get("/xiaozhi/sessions", response_model=ResultModel)
async def list_xiaozhi_sessions(
    limit: int = Query(20, ge=1, le=100),
    user_id: int = Depends(auth_handler.auth_required),
    db_session: Session = Depends(get_db_session)
):
    """列出当前用户的语音会话（按最后活跃时间倒序）。"""
    query = select(XiaozhiVoiceSession).where(
        XiaozhiVoiceSession.user_id == user_id
    ).order_by(desc(XiaozhiVoiceSession.last_active_at)).limit(limit)

    sessions = db_session.execute(query).scalars().all()
    return Result.success(data={
        "sessions": [_voice_session_to_dict(s) for s in sessions]
    })


@app.post("/xiaozhi/session/{session_id}/reset", response_model=ResultModel)
async def reset_xiaozhi_session(
    session_id: int,
    user_id: int = Depends(auth_handler.auth_required),
    db_session: Session = Depends(get_db_session)
):
    """重置指定语音会话状态。"""
    session = db_session.get(XiaozhiVoiceSession, session_id)
    if not session:
        raise NotFoundException("会话不存在")

    if session.user_id != user_id:
        raise NotFoundException("会话不存在")

    dialogue_manager.reset_session(session_id, db_session=db_session)
    return Result.success(data={"reset": True, "session_id": session_id})


@app.post("/xiaozhi/voiceprint/register", response_model=ResultModel)
async def register_xiaozhi_voiceprint(
    request: VoiceprintRegisterRequest,
    user_id: int = Depends(auth_handler.auth_required),
    db_session: Session = Depends(get_db_session)
):
    """注册声纹与用户的映射关系，可指定显示名称。只能绑定到当前登录账号。"""
    # 账号隔离：禁止把声纹注册到他人账号
    target_user_id = request.user_id if request.user_id is not None else user_id
    if target_user_id != user_id:
        raise PermissionError("只能把声纹/设备绑定到当前登录账号")

    mapping = register_voiceprint(
        voiceprint_id=request.voiceprint_id,
        user_id=target_user_id,
        db_session=db_session,
        current_user_id=user_id
    )
    if request.display_name:
        mapping.display_name = request.display_name
        db_session.add(mapping)
        db_session.commit()
        db_session.refresh(mapping)
    return Result.success(data={
        "id": mapping.id,
        "voiceprint_id": mapping.voiceprint_id,
        "user_id": mapping.user_id,
        "display_name": mapping.display_name,
        "is_allowed": mapping.is_allowed,
        "verification_status": mapping.verification_status
    })


@app.post("/xiaozhi/device/allow", response_model=ResultModel)
async def allow_xiaozhi_device(
    request: DeviceAllowRequest,
    user_id: int = Depends(auth_handler.auth_required),
    db_session: Session = Depends(get_db_session)
):
    """允许、禁止或更新某个小智设备/声纹的接入状态。只能操作当前登录账号的设备。"""
    # 账号隔离：禁止操作他人账号的设备
    target_user_id = request.user_id if request.user_id is not None else user_id
    if target_user_id != user_id:
        raise PermissionError("只能操作当前登录账号的设备")

    mapping = register_voiceprint(
        voiceprint_id=request.voiceprint_id,
        user_id=target_user_id,
        db_session=db_session,
        current_user_id=user_id
    )
    mapping.is_allowed = request.is_allowed
    if request.display_name:
        mapping.display_name = request.display_name
    if request.verification_status in ("pending", "allowed", "blocked"):
        mapping.verification_status = request.verification_status
    elif request.is_allowed is False:
        mapping.verification_status = "blocked"
    elif request.is_allowed is True:
        mapping.verification_status = "allowed"
    db_session.add(mapping)
    db_session.commit()
    db_session.refresh(mapping)

    return Result.success(data={
        "id": mapping.id,
        "voiceprint_id": mapping.voiceprint_id,
        "user_id": mapping.user_id,
        "display_name": mapping.display_name,
        "is_allowed": mapping.is_allowed,
        "verification_status": mapping.verification_status
    })


@app.get("/xiaozhi/devices", response_model=ResultModel)
async def list_xiaozhi_devices(
    user_id: int = Depends(auth_handler.auth_required),
    db_session: Session = Depends(get_db_session)
):
    """列出当前登录账号已注册的小智设备/声纹。"""
    from sqlalchemy import desc
    from model.xiaozhiSession import XiaozhiVoiceprint

    query = select(XiaozhiVoiceprint).where(
        XiaozhiVoiceprint.user_id == user_id
    ).order_by(desc(XiaozhiVoiceprint.last_connected_at))
    devices = db_session.execute(query).scalars().all()

    return Result.success(data={
        "devices": [
            {
                "id": d.id,
                "voiceprint_id": d.voiceprint_id,
                "display_name": d.display_name,
                "user_id": d.user_id,
                "is_allowed": d.is_allowed,
                "verification_status": d.verification_status,
                "last_connected_at": d.last_connected_at.isoformat() if d.last_connected_at else None,
                "created_at": d.created_at.isoformat() if d.created_at else None
            }
            for d in devices
        ]
    })
