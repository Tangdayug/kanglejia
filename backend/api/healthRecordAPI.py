"""
健康档案API - 提供健康档案管理功能
"""
import base64
import httpx
import logging

from fastapi import Depends, File, UploadFile
from pydantic import BaseModel
from typing import Optional, Dict, Any

from api import app
from common.auth import auth_handler
from common.constant import BAIDU_OCR_APP_ID, BAIDU_OCR_API_KEY, BAIDU_OCR_SECRET_KEY
from common.result import ResultModel, Result
from model import get_db_session, Session
from model.healthRecord import HealthRecordMapper
from service.healthRecordService import HealthRecordService

logger = logging.getLogger(__name__)


class HealthRecordData(BaseModel):
    basicInfo: Optional[Dict[str, Any]] = None
    sleepStatus: Optional[Dict[str, Any]] = None
    chronicDisease: Optional[Dict[str, Any]] = None
    medication: Optional[Dict[str, Any]] = None
    lifestyle: Optional[Dict[str, Any]] = None
    exercise: Optional[Dict[str, Any]] = None
    demographic: Optional[Dict[str, Any]] = None
    ocrText: Optional[str] = None


class SaveHealthRecordRequest(BaseModel):
    record_id: Optional[int] = None
    data: HealthRecordData
    is_draft: bool = True


def _record_to_dict(record) -> dict:
    """将数据库模型转换为字典格式（由 HealthRecordMapper 集中维护）。"""
    return HealthRecordMapper.to_frontend_dict(record)


@app.post("/health-record/save", response_model=ResultModel)
async def save_health_record(
    request: SaveHealthRecordRequest,
    user_id: int = Depends(auth_handler.auth_required),
    db_session: Session = Depends(get_db_session)
):
    """保存或更新健康档案（草稿或完成）"""
    record = HealthRecordService.save_or_update(
        user_id=user_id,
        data=request.data.model_dump(),
        record_id=request.record_id,
        is_draft=request.is_draft,
        db_session=db_session
    )
    return Result.success(data={
        'record_id': record.id,
        'is_draft': record.is_draft,
        'updated_at': record.updated_at.isoformat()
    })


@app.get("/health-record/draft", response_model=ResultModel)
async def get_draft(
    user_id: int = Depends(auth_handler.auth_required),
    db_session: Session = Depends(get_db_session)
):
    """获取当前用户的最新草稿"""
    draft = HealthRecordService.get_draft(user_id=user_id, db_session=db_session)
    if draft:
        return Result.success(data=_record_to_dict(draft))
    return Result.success(data={})


@app.get("/health-record/list", response_model=ResultModel)
async def get_health_record_list(
    user_id: int = Depends(auth_handler.auth_required),
    db_session: Session = Depends(get_db_session)
):
    """获取当前用户的所有健康档案"""
    records = HealthRecordService.get_user_records(user_id=user_id, db_session=db_session)
    records_data = []
    for record in records:
        records_data.append({
            'id': record.id,
            'isDraft': record.is_draft,
            'isCompleted': record.is_completed,
            'createdAt': record.created_at.isoformat() if record.created_at else None,
            'updatedAt': record.updated_at.isoformat() if record.updated_at else None
        })
    return Result.success(data={'records': records_data})


@app.get("/health-record/{record_id}", response_model=ResultModel)
async def get_health_record(
    record_id: int,
    user_id: int = Depends(auth_handler.auth_required),
    db_session: Session = Depends(get_db_session)
):
    """获取指定ID的健康档案详情"""
    record = HealthRecordService.get_by_id(
        record_id=record_id,
        user_id=user_id,
        db_session=db_session
    )
    return Result.success(data=_record_to_dict(record))


def _has_baidu_ocr_config() -> bool:
    return bool(BAIDU_OCR_APP_ID and BAIDU_OCR_API_KEY and BAIDU_OCR_SECRET_KEY)


async def _get_baidu_ocr_token() -> str:
    """获取百度智能云 OCR access_token"""
    if not _has_baidu_ocr_config():
        raise RuntimeError("百度 OCR 未配置，请在 .env 中设置 BAIDU_OCR_APP_ID / API_KEY / SECRET_KEY")

    url = "https://aip.baidubce.com/oauth/2.0/token"
    params = {
        "grant_type": "client_credentials",
        "client_id": BAIDU_OCR_API_KEY,
        "client_secret": BAIDU_OCR_SECRET_KEY,
    }
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(url, params=params)
        resp.raise_for_status()
        data = resp.json()
        return data.get("access_token", "")


@app.post("/health-record/ocr", response_model=ResultModel)
async def ocr_health_record_image(
    file: UploadFile = File(...),
    user_id: int = Depends(auth_handler.auth_required)
):
    """上传图片并调用百度智能云 OCR 识别文字"""
    contents = await file.read()
    if not contents:
        return Result.error(msg="上传文件为空")

    if not _has_baidu_ocr_config():
        logger.warning("百度 OCR 未配置，请在 .env 中设置 BAIDU_OCR_APP_ID / API_KEY / SECRET_KEY")
        return Result.error(msg="OCR 服务未配置")

    # 百度 OCR 对图片大小有限制，base64 后不超过 4M
    if len(contents) > 4 * 1024 * 1024:
        return Result.error(msg="图片大小超过 4MB，请压缩后重新上传")

    image_b64 = base64.b64encode(contents).decode("utf-8")

    try:
        access_token = await _get_baidu_ocr_token()
        if not access_token:
            return Result.error(msg="获取百度 OCR 授权失败")

        url = "https://aip.baidubce.com/rest/2.0/ocr/v1/general_basic"
        params = {"access_token": access_token}
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        payload = {"image": image_b64}

        async with httpx.AsyncClient(timeout=60) as client:
            resp = await client.post(url, params=params, data=payload, headers=headers)
            resp.raise_for_status()
            result = resp.json()

        if "error_code" in result:
            return Result.error(msg=f"百度 OCR 错误：{result.get('error_msg')}")

        words = [item.get("words", "") for item in result.get("words_result", [])]
        return Result.success(data={"text": "\n".join(words), "words": words})
    except httpx.HTTPError as e:
        return Result.error(msg=f"OCR 请求失败：{str(e)}")
    except Exception as e:
        return Result.error(msg=f"OCR 处理异常：{str(e)}")



@app.post("/health-record/{record_id}/submit", response_model=ResultModel)
async def submit_health_record(
    record_id: int,
    user_id: int = Depends(auth_handler.auth_required),
    db_session: Session = Depends(get_db_session)
):
    """提交/完成草稿健康档案"""
    record = HealthRecordService.submit(
        record_id=record_id,
        user_id=user_id,
        db_session=db_session
    )
    return Result.success(data={
        'record_id': record.id,
        'is_draft': record.is_draft,
        'is_completed': record.is_completed,
        'updated_at': record.updated_at.isoformat()
    })
