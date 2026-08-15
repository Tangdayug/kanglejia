"""
语音合成API - 使用Edge TTS提供文字转语音服务
"""
from fastapi import Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from api import app
from common.auth import auth_handler
from model import get_db_session
from service.edgeTTSService import get_edge_tts_service


class TTSRequest(BaseModel):
    text: str
    voice: str = None
    rate: str = '+0%'
    pitch: str = '+0Hz'
    volume: str = '+0%'


@app.post("/tts/speak")
async def text_to_speech(
    request: TTSRequest,
    user_id: Optional[int] = Depends(lambda: None),
    db_session: Optional[Session] = Depends(lambda: None)
):
    """将文字转换为语音，返回MP3音频数据（无需认证）"""
    tts_service = get_edge_tts_service()

    if not tts_service.is_available():
        raise HTTPException(
            status_code=503,
            detail="TTS服务不可用，请安装edge-tts: pip install edge-tts"
        )

    if len(request.text) > 1000:
        raise HTTPException(
            status_code=400,
            detail="文本过长（最多1000字符）"
        )

    audio_data = tts_service.synthesize(
        text=request.text,
        voice=request.voice,
        rate=request.rate,
        pitch=request.pitch,
        volume=request.volume
    )

    if audio_data is None:
        raise HTTPException(
            status_code=500,
            detail="语音合成失败"
        )

    return Response(
        content=audio_data,
        media_type="audio/mpeg",
        headers={
            "Content-Disposition": "inline; filename=speech.mp3",
            "Cache-Control": "public, max-age=86400"
        }
    )


@app.get("/tts/voices")
async def get_available_voices():
    """获取可用的语音选项列表（无需认证）"""
    tts_service = get_edge_tts_service()

    if not tts_service.is_available():
        return {
            "available": False,
            "voices": [],
            "message": "TTS服务不可用"
        }

    return {
        "available": True,
        "voices": tts_service.get_available_voices()
    }


@app.get("/tts/recommended")
async def get_recommended_voice(
    user_id: Optional[int] = Depends(lambda: None),
    db_session: Optional[Session] = Depends(lambda: None)
):
    """根据用户性别推荐合适的语音（无需认证，未登录时返回默认语音）"""
    from model.healthRecord import HealthRecord
    from sqlalchemy import select

    tts_service = get_edge_tts_service()

    if not tts_service.is_available():
        return {
            "available": False,
            "voice": None
        }

    user_gender = None

    # 如果有用户ID，尝试获取用户性别
    if user_id and db_session:
        try:
            query = select(HealthRecord).where(
                HealthRecord.user_id == user_id
            ).order_by(HealthRecord.updated_at.desc()).limit(1)

            record = db_session.execute(query).scalar_one_or_none()
            if record and record.gender:
                user_gender = record.gender
        except Exception:
            pass

    recommended_voice = tts_service.get_recommended_voice(user_gender)
    voices = tts_service.get_available_voices()

    return {
        "available": True,
        "voice": recommended_voice,
        "voiceInfo": voices.get(recommended_voice),
        "userGender": user_gender
    }
