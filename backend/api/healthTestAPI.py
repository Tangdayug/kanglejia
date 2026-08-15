"""
健康测试API - 提供健康评估测试功能
"""
from fastapi import Depends
from pydantic import BaseModel
from typing import Optional

from api import app
from common.auth import auth_handler
from common.result import ResultModel, Result
from model import get_db_session, Session
from service.healthTestService import HealthTestService


class SubmitHealthTestRequest(BaseModel):
    """健康测试请求模型"""
    q1MemoryIssue: Optional[bool] = None
    q1_1Remembered: Optional[bool] = None
    q1_2TodayDate: Optional[str] = None
    q1_2Correct: Optional[bool] = None
    q1_3Location: Optional[str] = None
    q1_3Correct: Optional[bool] = None
    q1_4Recall: Optional[str] = None
    q2Completed: Optional[bool] = None
    q2TimeSeconds: Optional[float] = None
    q3WeightLoss: Optional[bool] = None
    q4AppetiteLoss: Optional[bool] = None
    q5VisionIssue: Optional[bool] = None
    q6DiabetesHypertension: Optional[bool] = None
    q7HearingIssue: Optional[bool] = None
    q8Depressed: Optional[bool] = None
    q9InterestLoss: Optional[bool] = None
    assistanceMode: Optional[str] = None
    location: Optional[str] = None


def _test_to_dict(test) -> dict:
    """将数据库模型转换为字典格式"""
    return {
        'id': test.id,
        'answers': {
            'q1MemoryIssue': test.q1_memory_issue,
            'q1_1Remembered': test.q1_1_recall_name,
            'q1_2TodayDate': test.q1_2_today_date,
            'q1_2Correct': test.q1_2_correct,
            'q1_3Location': test.q1_3_home_address,
            'q1_3Correct': test.q1_3_correct,
            'q1_4Recall': test.q1_4_current_location,
            'q2Completed': test.q2_completed,
            'q2TimeSeconds': test.q2_time_seconds,
            'q3WeightLoss': test.q3_fatigued,
            'q4AppetiteLoss': test.q4_health_poor,
            'q5VisionIssue': test.q5_vision_issue,
            'q6DiabetesHypertension': test.q6_reading_issue,
            'q7HearingIssue': test.q7_hearing_issue,
            'q8Depressed': test.q8_depressed,
            'q9InterestLoss': test.q9_anxious,
            'assistanceMode': test.assistance_mode,
        },
        'scores': {
            'cognitive': test.score_cognitive,
            'motor': test.score_motor,
            'vitality': test.score_vitality,
            'vision': test.score_vision,
            'hearing': test.score_hearing,
            'psychological': test.score_psychological,
            'total': test.score_total
        },
        'risks': {
            'cognitive': test.risk_cognitive,
            'motor': test.risk_motor,
            'vitality': test.risk_vitality,
            'vision': test.risk_vision,
            'hearing': test.risk_hearing,
            'psychological': test.risk_psychological
        },
        'recommendations': test.recommendations,
        'createdAt': test.created_at.isoformat() if test.created_at else None,
        'updatedAt': test.updated_at.isoformat() if test.updated_at else None
    }


@app.post("/health-test/submit", response_model=ResultModel)
async def submit_health_test(
    request: SubmitHealthTestRequest,
    user_id: int = Depends(auth_handler.auth_required),
    db_session: Session = Depends(get_db_session)
):
    """提交健康测试"""
    test = HealthTestService.save_test(
        user_id=user_id,
        data=request.model_dump(),
        db_session=db_session
    )
    return Result.success(data=_test_to_dict(test))


@app.get("/health-test/list", response_model=ResultModel)
async def get_health_test_list(
    user_id: int = Depends(auth_handler.auth_required),
    db_session: Session = Depends(get_db_session)
):
    """获取当前用户的所有健康测试记录"""
    tests = HealthTestService.get_user_tests(user_id=user_id, db_session=db_session)
    tests_data = []
    for test in tests:
        tests_data.append({
            'id': test.id,
            'scoreTotal': test.score_total,
            'createdAt': test.created_at.isoformat() if test.created_at else None,
            'updatedAt': test.updated_at.isoformat() if test.updated_at else None
        })
    return Result.success(data={'tests': tests_data})


@app.get("/health-test/{test_id}", response_model=ResultModel)
async def get_health_test(
    test_id: int,
    user_id: int = Depends(auth_handler.auth_required),
    db_session: Session = Depends(get_db_session)
):
    """获取指定ID的健康测试详情"""
    test = HealthTestService.get_test_by_id(
        test_id=test_id,
        user_id=user_id,
        db_session=db_session
    )
    return Result.success(data=_test_to_dict(test))


@app.post("/health-test/recommendation", response_model=ResultModel)
async def get_recommendation(
    request: SubmitHealthTestRequest,
    user_id: int = Depends(auth_handler.auth_required)
):
    """获取个性化建议（不保存测试记录）"""
    scores = HealthTestService.calculate_scores(request.model_dump())
    risks = HealthTestService.determine_risks(scores)
    recommendations = HealthTestService.generate_recommendations(
        scores=scores,
        risks=risks,
        data=request.model_dump()
    )

    return Result.success(data={
        'scores': scores,
        'risks': risks,
        'recommendations': recommendations
    })
