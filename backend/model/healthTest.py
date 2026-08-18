from common.datetime_utils import get_now_naive
from sqlalchemy import Integer, String, DateTime, Boolean, Float, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column

from model import Base


class HealthTest(Base):
    """健康测试表 - 内在能力减退初筛"""
    __tablename__ = 'health_test'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, nullable=False, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True, comment='用户ID')

    q1_memory_issue: Mapped[bool] = mapped_column(Boolean, nullable=True)
    q1_1_recall_name: Mapped[str] = mapped_column(String(500), nullable=True)
    q1_2_today_date: Mapped[str] = mapped_column(String(50), nullable=True)
    q1_2_correct: Mapped[bool] = mapped_column(Boolean, nullable=True)
    q1_3_home_address: Mapped[str] = mapped_column(String(500), nullable=True)
    q1_3_correct: Mapped[bool] = mapped_column(Boolean, nullable=True)
    q1_4_current_location: Mapped[str] = mapped_column(String(500), nullable=True)
    q1_4_correct: Mapped[bool] = mapped_column(Boolean, nullable=True)

    q2_completed: Mapped[bool] = mapped_column(Boolean, nullable=True)
    q2_time_seconds: Mapped[float] = mapped_column(Float, nullable=True)

    q3_fatigued: Mapped[bool] = mapped_column(Boolean, nullable=True)

    q4_health_poor: Mapped[bool] = mapped_column(Boolean, nullable=True)

    q5_vision_issue: Mapped[bool] = mapped_column(Boolean, nullable=True)

    q6_reading_issue: Mapped[bool] = mapped_column(Boolean, nullable=True)

    q7_hearing_issue: Mapped[bool] = mapped_column(Boolean, nullable=True)

    q8_depressed: Mapped[bool] = mapped_column(Boolean, nullable=True)

    q9_anxious: Mapped[bool] = mapped_column(Boolean, nullable=True)

    assistance_mode: Mapped[str] = mapped_column(String(20), nullable=True, comment='协助模式: alone/assisted')

    score_cognitive: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    score_motor: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    score_vitality: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    score_vision: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    score_hearing: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    score_psychological: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    score_total: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    risk_cognitive: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    risk_motor: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    risk_vitality: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    risk_vision: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    risk_hearing: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    risk_psychological: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    recommendations: Mapped[JSON] = mapped_column(JSON, nullable=True)
    facilities: Mapped[JSON] = mapped_column(JSON, nullable=True)

    created_at: Mapped[DateTime] = mapped_column(DateTime, default=lambda: get_now_naive(), nullable=False)
    updated_at: Mapped[DateTime] = mapped_column(DateTime, default=lambda: get_now_naive(), onupdate=lambda: get_now_naive(), nullable=False)

    def to_dict(self) -> dict:
        """将数据库模型转换为前端展示用的字典。"""
        return {
            'id': self.id,
            'answers': {
                'q1MemoryIssue': self.q1_memory_issue,
                'q1_1Remembered': self.q1_1_recall_name,
                'q1_2TodayDate': self.q1_2_today_date,
                'q1_2Correct': self.q1_2_correct,
                'q1_3Location': self.q1_3_home_address,
                'q1_3Correct': self.q1_3_correct,
                'q1_4Recall': self.q1_4_current_location,
                'q2Completed': self.q2_completed,
                'q2TimeSeconds': self.q2_time_seconds,
                'q3WeightLoss': self.q3_fatigued,
                'q4AppetiteLoss': self.q4_health_poor,
                'q5VisionIssue': self.q5_vision_issue,
                'q6DiabetesHypertension': self.q6_reading_issue,
                'q7HearingIssue': self.q7_hearing_issue,
                'q8Depressed': self.q8_depressed,
                'q9InterestLoss': self.q9_anxious,
                'assistanceMode': self.assistance_mode,
            },
            'scores': {
                'cognitive': self.score_cognitive,
                'motor': self.score_motor,
                'vitality': self.score_vitality,
                'vision': self.score_vision,
                'hearing': self.score_hearing,
                'psychological': self.score_psychological,
                'total': self.score_total
            },
            'risks': {
                'cognitive': self.risk_cognitive,
                'motor': self.risk_motor,
                'vitality': self.risk_vitality,
                'vision': self.risk_vision,
                'hearing': self.risk_hearing,
                'psychological': self.risk_psychological
            },
            'recommendations': self.recommendations,
            'createdAt': self.created_at.isoformat() if self.created_at else None,
            'updatedAt': self.updated_at.isoformat() if self.updated_at else None
        }
