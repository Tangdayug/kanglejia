import logging
from sqlalchemy import select, desc
from sqlalchemy.orm import Session

from model.healthTest import HealthTest
from exception.customException import NotFoundException
from service.icope_scoring import (
    calculate_scores_for_rest,
    determine_risks,
    generate_recommendations,
)

logger = logging.getLogger(__name__)


class HealthTestService:
    """健康测试服务 - 内在能力减退初筛"""

    @staticmethod
    def calculate_scores(data: dict) -> dict:
        """基于前端表单提交的数据计算各维度分数（兼容旧接口）。"""
        return calculate_scores_for_rest(data)

    @staticmethod
    def determine_risks(scores: dict) -> dict:
        return determine_risks(scores)

    @staticmethod
    def generate_recommendations(scores: dict, risks: dict, data: dict) -> dict:
        return generate_recommendations(scores, risks, data)

    @staticmethod
    def get_nearby_facilities(location: str = None) -> list:
        """附近医疗机构占位数据。TODO: 后续可接入真实地图服务。"""
        return [
            {
                'name': '市人民医院',
                'address': '市中心大街123号',
                'distance': '1.2km',
                'phone': '010-12345678',
                'type': '综合医院'
            },
            {
                'name': '社区卫生服务中心',
                'address': '建设路456号',
                'distance': '0.5km',
                'phone': '010-87654321',
                'type': '社区医院'
            },
            {
                'name': '中医院',
                'address': '健康路789号',
                'distance': '2.1km',
                'phone': '010-11112222',
                'type': '专科医院'
            },
            {
                'name': '康复医院',
                'address': '康复路321号',
                'distance': '3.5km',
                'phone': '010-33334444',
                'type': '专科医院'
            },
            {
                'name': '老年病医院',
                'address': '长寿路654号',
                'distance': '4.2km',
                'phone': '010-55556666',
                'type': '专科医院'
            }
        ]

    @staticmethod
    def save_test(user_id: int, data: dict, db_session: Session) -> HealthTest:
        try:
            test = HealthTest()
            test.user_id = user_id

            test.q1_memory_issue = data.get('q1MemoryIssue')
            test.q1_1_recall_name = data.get('q1_1Remembered')
            test.q1_2_today_date = data.get('q1_2TodayDate')
            test.q1_2_correct = data.get('q1_2Correct')
            test.q1_3_home_address = data.get('q1_3Location')
            test.q1_3_correct = data.get('q1_3Correct')
            test.q1_4_current_location = data.get('q1_4Recall')
            q1_4_recall = data.get('q1_4Recall', '')
            test.q1_4_correct = (q1_4_recall == 'flower_door_rice')
            test.q2_completed = data.get('q2Completed')
            test.q2_time_seconds = data.get('q2TimeSeconds')
            test.q3_fatigued = data.get('q3WeightLoss')
            test.q4_health_poor = data.get('q4AppetiteLoss')
            test.q5_vision_issue = data.get('q5VisionIssue')
            test.q6_reading_issue = data.get('q6DiabetesHypertension')
            test.q7_hearing_issue = data.get('q7HearingIssue')
            test.q8_depressed = data.get('q8Depressed')
            test.q9_anxious = data.get('q9InterestLoss')
            test.assistance_mode = data.get('assistanceMode')

            scores = calculate_scores_for_rest(data)
            test.score_cognitive = scores.get('cognitive', 0)
            test.score_motor = scores.get('motor', 0)
            test.score_vitality = scores.get('vitality', 0)
            test.score_vision = scores.get('vision', 0)
            test.score_hearing = scores.get('hearing', 0)
            test.score_psychological = scores.get('psychological', 0)
            test.score_total = scores.get('total', 0)

            risks = determine_risks(scores)
            test.risk_cognitive = risks.get('cognitive', False)
            test.risk_motor = risks.get('motor', False)
            test.risk_vitality = risks.get('vitality', False)
            test.risk_vision = risks.get('vision', False)
            test.risk_hearing = risks.get('hearing', False)
            test.risk_psychological = risks.get('psychological', False)

            recommendations = generate_recommendations(scores, risks, data)
            test.recommendations = recommendations

            db_session.add(test)
            db_session.commit()
            db_session.refresh(test)
            return test
        except Exception as e:
            db_session.rollback()
            logger.exception("保存健康测试失败")
            raise e

    @staticmethod
    def get_user_tests(user_id: int, db_session: Session) -> list:
        query = select(HealthTest).where(
            HealthTest.user_id == user_id
        ).order_by(desc(HealthTest.created_at))
        result = db_session.execute(query).scalars().all()
        return list(result)

    @staticmethod
    def get_test_by_id(test_id: int, user_id: int, db_session: Session) -> HealthTest:
        query = select(HealthTest).where(
            HealthTest.id == test_id,
            HealthTest.user_id == user_id
        )
        test = db_session.execute(query).scalar()
        if not test:
            raise NotFoundException("健康测试记录不存在")
        return test
