"""
健康档案API - 提供健康档案管理功能
"""
import base64
import httpx

from fastapi import Depends, File, UploadFile
from pydantic import BaseModel
from typing import Optional, Dict, Any

from api import app
from common.auth import auth_handler
from common.result import ResultModel, Result
from model import get_db_session, Session
from service.healthRecordService import HealthRecordService

# 百度智能云 OCR 配置
BAIDU_OCR_APP_ID = 7946299
BAIDU_OCR_API_KEY = "hnxPPxHyoW0VyxzxVVhAlt1W"
BAIDU_OCR_SECRET_KEY = "n5rAjU4WnCiJtbiKErPqRec2Ryqr0ka1"


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
    """将数据库模型转换为字典格式"""
    basic_info = {
        'name': record.name,
        'birthDate': record.birth_date,
        'gender': record.gender,
        'height': record.height,
        'weight': record.weight,
        'bmi': record.bmi,
        'waist': record.waist,
        'abdomen': record.abdomen,
        'systolicBp': record.systolic_bp,
        'diastolicBp': record.diastolic_bp,
        'heartRate': record.heart_rate
    }

    sleep_issues = []
    if record.sleep_good:
        sleep_issues.append('good')
    if record.sleep_difficulty_falling:
        sleep_issues.append('difficulty_falling_asleep')
    if record.sleep_easily_wake:
        sleep_issues.append('easily_wake')
    if record.sleep_early_wake:
        sleep_issues.append('early_wake')
    if record.sleep_daytime_sleepiness:
        sleep_issues.append('daytime_sleepiness')
    if record.sleep_other:
        sleep_issues.append('other')

    sleep_status = {
        'sleepIssues': sleep_issues,
        'otherSleepIssue': record.sleep_other_desc or ''
    }

    diseases = []
    if record.disease_hypertension:
        diseases.append('hypertension')
    if record.disease_diabetes:
        diseases.append('diabetes')
    if record.disease_dyslipidemia:
        diseases.append('dyslipidemia')
    if record.disease_coronary:
        diseases.append('coronary_heart_disease')
    if record.disease_angina:
        diseases.append('angina')
    if record.disease_myocardial_infarction:
        diseases.append('myocardial_infarction')
    if record.disease_stroke:
        diseases.append('stroke')
    if record.disease_copd:
        diseases.append('copd')
    if record.disease_gout:
        diseases.append('gout')
    if record.disease_kidney:
        diseases.append('chronic_kidney_disease')
    if record.disease_hypothyroidism:
        diseases.append('hypothyroidism')
    if record.disease_hyperthyroidism:
        diseases.append('hyperthyroidism')
    if record.disease_osteoporosis:
        diseases.append('osteoporosis')
    if record.disease_parkinsons:
        diseases.append('parkinsons')
    if record.disease_alzheimers:
        diseases.append('alzheimers')
    if record.disease_tumor:
        diseases.append('tumor_history')
    if record.disease_other:
        diseases.append('other')
    if record.disease_none:
        diseases.append('none')

    chronic_disease = {
        'diseases': diseases,
        'tumorHistory': record.disease_tumor_site or '',
        'otherDisease': record.disease_other_desc or ''
    }

    medication = {
        'isMedication': record.is_medication,
        'medicationNames': record.medication_names or ''
    }

    lifestyle = {
        'smokingStatus': record.smoking_status or 'never',
        'smokingCount': record.smoking_count,
        'drinkingStatus': record.drinking_status or 'never',
        'drinkingFrequency': record.drinking_frequency,
        'drinkingAmount': record.drinking_amount
    }

    preferred_exercises = []
    if record.exercise_walking:
        preferred_exercises.append('walking')
    if record.exercise_jogging:
        preferred_exercises.append('jogging')
    if record.exercise_square_dance:
        preferred_exercises.append('square_dance')
    if record.exercise_tai_chi:
        preferred_exercises.append('tai_chi')
    if record.exercise_swimming:
        preferred_exercises.append('swimming')
    if record.exercise_cycling:
        preferred_exercises.append('cycling')
    if record.exercise_racket:
        preferred_exercises.append('racket_sports')
    if record.exercise_hiking:
        preferred_exercises.append('hiking')
    if record.exercise_gardening:
        preferred_exercises.append('gardening')
    if record.exercise_fishing:
        preferred_exercises.append('fishing')
    if record.exercise_gym:
        preferred_exercises.append('gym')
    if record.exercise_yoga:
        preferred_exercises.append('yoga')
    if record.exercise_no_preference:
        preferred_exercises.append('no_preference')
    if record.exercise_other:
        preferred_exercises.append('other')

    exercise = {
        'preferredExercises': preferred_exercises,
        'otherExercise': record.exercise_other_desc or '',
        'socialSupport': [],
        'otherSupport': record.support_other or ''
    }

    if record.support_equipment:
        exercise['socialSupport'].extend(['fitness_equipment', 'park', 'fitness_trail', 'community_room'])
    if record.support_organization:
        exercise['socialSupport'].extend(['dance_team', 'fitness_team', 'sports_club', 'interest_group'])
    if record.support_info:
        exercise['socialSupport'].extend(['health_lecture', 'fitness_guidance', 'digital_push', 'poster'])
    if record.support_policy:
        exercise['socialSupport'].extend(['free_facilities', 'insurance_benefit', 'subsidy'])
    if record.support_none:
        exercise['socialSupport'].append('none')

    co_residents = record.co_residents or ''
    if co_residents and isinstance(co_residents, str):
        co_residents = co_residents.split(',') if co_residents else []
    else:
        co_residents = []

    demographic = {
        'maritalStatus': record.marital_status or '',
        'address': record.address or '',
        'workStatus': record.work_status or '',
        'education': record.education or '',
        'ethnicity': record.ethnicity or 'han',
        'religion': record.religion or 'none',
        'residenceType': record.residence_type or 'urban',
        'coResidents': co_residents,
        'insuranceType': record.insurance_type or '',
        'occupation': record.occupation or '',
        'income': record.income or ''
    }

    return {
        'id': record.id,
        'basicInfo': basic_info,
        'sleepStatus': sleep_status,
        'chronicDisease': chronic_disease,
        'medication': medication,
        'lifestyle': lifestyle,
        'exercise': exercise,
        'demographic': demographic,
        'ocrText': record.ocr_text or '',
        'isDraft': record.is_draft,
        'isCompleted': record.is_completed,
        'createdAt': record.created_at.isoformat() if record.created_at else None,
        'updatedAt': record.updated_at.isoformat() if record.updated_at else None
    }


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
    return Result.success(data=None)


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


async def _get_baidu_ocr_token() -> str:
    """获取百度智能云 OCR access_token"""
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
