from common.datetime_utils import get_now_naive
from sqlalchemy import Integer, String, DateTime, Boolean, Float, Text
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime

from model import Base


class HealthRecord(Base):
    """健康档案表"""
    __tablename__ = 'health_record'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, nullable=False, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True, comment='用户ID')

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    birth_date: Mapped[str] = mapped_column(String(20), nullable=False)
    gender: Mapped[str] = mapped_column(String(10), nullable=False)
    height: Mapped[float] = mapped_column(Float, nullable=True)
    weight: Mapped[float] = mapped_column(Float, nullable=True)
    bmi: Mapped[str] = mapped_column(String(10), nullable=True)
    waist: Mapped[float] = mapped_column(Float, nullable=True)
    abdomen: Mapped[float] = mapped_column(Float, nullable=True)
    systolic_bp: Mapped[int] = mapped_column(Integer, nullable=True)
    diastolic_bp: Mapped[int] = mapped_column(Integer, nullable=True)
    heart_rate: Mapped[int] = mapped_column(Integer, nullable=True)

    sleep_good: Mapped[bool] = mapped_column(Boolean, default=False)
    sleep_difficulty_falling: Mapped[bool] = mapped_column(Boolean, default=False)
    sleep_easily_wake: Mapped[bool] = mapped_column(Boolean, default=False)
    sleep_early_wake: Mapped[bool] = mapped_column(Boolean, default=False)
    sleep_daytime_sleepiness: Mapped[bool] = mapped_column(Boolean, default=False)
    sleep_other: Mapped[bool] = mapped_column(Boolean, default=False)
    sleep_other_desc: Mapped[str] = mapped_column(Text, nullable=True)

    disease_hypertension: Mapped[bool] = mapped_column(Boolean, default=False)
    disease_diabetes: Mapped[bool] = mapped_column(Boolean, default=False)
    disease_dyslipidemia: Mapped[bool] = mapped_column(Boolean, default=False)
    disease_coronary: Mapped[bool] = mapped_column(Boolean, default=False)
    disease_angina: Mapped[bool] = mapped_column(Boolean, default=False)
    disease_myocardial_infarction: Mapped[bool] = mapped_column(Boolean, default=False)
    disease_stroke: Mapped[bool] = mapped_column(Boolean, default=False)
    disease_copd: Mapped[bool] = mapped_column(Boolean, default=False)
    disease_gout: Mapped[bool] = mapped_column(Boolean, default=False)
    disease_kidney: Mapped[bool] = mapped_column(Boolean, default=False)
    disease_hypothyroidism: Mapped[bool] = mapped_column(Boolean, default=False)
    disease_hyperthyroidism: Mapped[bool] = mapped_column(Boolean, default=False)
    disease_osteoporosis: Mapped[bool] = mapped_column(Boolean, default=False)
    disease_parkinsons: Mapped[bool] = mapped_column(Boolean, default=False)
    disease_alzheimers: Mapped[bool] = mapped_column(Boolean, default=False)
    disease_tumor: Mapped[bool] = mapped_column(Boolean, default=False)
    disease_tumor_site: Mapped[str] = mapped_column(String(200), nullable=True)
    disease_other: Mapped[bool] = mapped_column(Boolean, default=False)
    disease_other_desc: Mapped[str] = mapped_column(String(200), nullable=True)
    disease_none: Mapped[bool] = mapped_column(Boolean, default=False)

    is_medication: Mapped[bool] = mapped_column(Boolean, default=False)
    medication_names: Mapped[str] = mapped_column(Text, nullable=True)

    smoking_status: Mapped[str] = mapped_column(String(50), nullable=True)
    smoking_count: Mapped[int] = mapped_column(Integer, nullable=True)

    drinking_status: Mapped[str] = mapped_column(String(50), nullable=True)
    drinking_frequency: Mapped[int] = mapped_column(Integer, nullable=True)
    drinking_amount: Mapped[int] = mapped_column(Integer, nullable=True)

    exercise_walking: Mapped[bool] = mapped_column(Boolean, default=False)
    exercise_jogging: Mapped[bool] = mapped_column(Boolean, default=False)
    exercise_square_dance: Mapped[bool] = mapped_column(Boolean, default=False)
    exercise_tai_chi: Mapped[bool] = mapped_column(Boolean, default=False)
    exercise_swimming: Mapped[bool] = mapped_column(Boolean, default=False)
    exercise_cycling: Mapped[bool] = mapped_column(Boolean, default=False)
    exercise_racket: Mapped[bool] = mapped_column(Boolean, default=False)
    exercise_hiking: Mapped[bool] = mapped_column(Boolean, default=False)
    exercise_gardening: Mapped[bool] = mapped_column(Boolean, default=False)
    exercise_fishing: Mapped[bool] = mapped_column(Boolean, default=False)
    exercise_gym: Mapped[bool] = mapped_column(Boolean, default=False)
    exercise_yoga: Mapped[bool] = mapped_column(Boolean, default=False)
    exercise_no_preference: Mapped[bool] = mapped_column(Boolean, default=False)
    exercise_other: Mapped[bool] = mapped_column(Boolean, default=False)
    exercise_other_desc: Mapped[str] = mapped_column(String(200), nullable=True)

    support_equipment: Mapped[bool] = mapped_column(Boolean, default=False)
    support_organization: Mapped[bool] = mapped_column(Boolean, default=False)
    support_info: Mapped[bool] = mapped_column(Boolean, default=False)
    support_policy: Mapped[bool] = mapped_column(Boolean, default=False)
    support_none: Mapped[bool] = mapped_column(Boolean, default=False)
    support_other: Mapped[str] = mapped_column(String(500), nullable=True)

    marital_status: Mapped[str] = mapped_column(String(50), nullable=True)
    address: Mapped[str] = mapped_column(String(500), nullable=True)
    work_status: Mapped[str] = mapped_column(String(50), nullable=True)
    education: Mapped[str] = mapped_column(String(50), nullable=True)
    ethnicity: Mapped[str] = mapped_column(String(50), nullable=True)
    religion: Mapped[str] = mapped_column(String(50), nullable=True)
    residence_type: Mapped[str] = mapped_column(String(50), nullable=True)
    co_residents: Mapped[str] = mapped_column(String(50), nullable=True)
    insurance_type: Mapped[str] = mapped_column(String(50), nullable=True)
    occupation: Mapped[str] = mapped_column(String(100), nullable=True)
    income: Mapped[str] = mapped_column(String(50), nullable=True)

    ocr_text: Mapped[str] = mapped_column(Text, nullable=True, default='')

    is_draft: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_completed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    created_at: Mapped[DateTime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[DateTime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
