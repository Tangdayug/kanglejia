from common.datetime_utils import get_now_naive
from sqlalchemy import Integer, String, DateTime, Boolean, Float, Text
from sqlalchemy.orm import Mapped, mapped_column
from typing import Dict, Any, List, Optional

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

    created_at: Mapped[DateTime] = mapped_column(DateTime, default=get_now_naive, nullable=False)
    updated_at: Mapped[DateTime] = mapped_column(DateTime, default=get_now_naive, onupdate=get_now_naive, nullable=False)


class HealthRecordMapper:
    """健康档案字段映射器：统一维护前端 <-> 数据库 <-> LLM 提示词之间的转换。"""

    # (db_field, frontend_code, display_label)
    SLEEP_ITEMS = [
        ('sleep_good', 'good', '睡眠良好'),
        ('sleep_difficulty_falling', 'difficulty_falling_asleep', '入睡困难'),
        ('sleep_easily_wake', 'easily_wake', '易醒'),
        ('sleep_early_wake', 'early_wake', '早醒'),
        ('sleep_daytime_sleepiness', 'daytime_sleepiness', '白天犯困'),
        ('sleep_other', 'other', '其他'),
    ]

    # (db_field, frontend_code)
    DISEASE_ITEMS = [
        ('disease_hypertension', 'hypertension'),
        ('disease_diabetes', 'diabetes'),
        ('disease_dyslipidemia', 'dyslipidemia'),
        ('disease_coronary', 'coronary_heart_disease'),
        ('disease_angina', 'angina'),
        ('disease_myocardial_infarction', 'myocardial_infarction'),
        ('disease_stroke', 'stroke'),
        ('disease_copd', 'copd'),
        ('disease_gout', 'gout'),
        ('disease_kidney', 'chronic_kidney_disease'),
        ('disease_hypothyroidism', 'hypothyroidism'),
        ('disease_hyperthyroidism', 'hyperthyroidism'),
        ('disease_osteoporosis', 'osteoporosis'),
        ('disease_parkinsons', 'parkinsons'),
        ('disease_alzheimers', 'alzheimers'),
        ('disease_tumor', 'tumor_history'),
        ('disease_other', 'other'),
        ('disease_none', 'none'),
    ]

    # (db_field, frontend_code, display_label)
    EXERCISE_ITEMS = [
        ('exercise_walking', 'walking', '散步/健走'),
        ('exercise_jogging', 'jogging', '慢跑'),
        ('exercise_square_dance', 'square_dance', '广场舞'),
        ('exercise_tai_chi', 'tai_chi', '太极拳/八段锦'),
        ('exercise_swimming', 'swimming', '游泳'),
        ('exercise_cycling', 'cycling', '骑车'),
        ('exercise_racket', 'racket_sports', '乒乓球/羽毛球'),
        ('exercise_hiking', 'hiking', '爬山/爬楼梯'),
        ('exercise_gardening', 'gardening', '园艺'),
        ('exercise_fishing', 'fishing', '钓鱼'),
        ('exercise_gym', 'gym', '健身房器械'),
        ('exercise_yoga', 'yoga', '瑜伽/普拉提'),
        ('exercise_no_preference', 'no_preference', '无运动偏好'),
        ('exercise_other', 'other', '其他'),
    ]

    # (db_field, frontend_codes, display_label)
    SUPPORT_ITEMS = [
        ('support_equipment', ['fitness_equipment', 'park', 'fitness_trail', 'community_room'], '场地/器材支持'),
        ('support_organization', ['dance_team', 'fitness_team', 'sports_club', 'interest_group'], '组织/人群支持'),
        ('support_info', ['health_lecture', 'fitness_guidance', 'digital_push', 'poster'], '信息/指导支持'),
        ('support_policy', ['free_facilities', 'insurance_benefit', 'subsidy'], '政策/费用支持'),
        ('support_none', ['none'], '无支持'),
    ]

    BASIC_INFO_FIELDS = {
        'name': 'name',
        'birth_date': 'birthDate',
        'gender': 'gender',
        'height': 'height',
        'weight': 'weight',
        'bmi': 'bmi',
        'waist': 'waist',
        'abdomen': 'abdomen',
        'systolic_bp': 'systolicBp',
        'diastolic_bp': 'diastolicBp',
        'heart_rate': 'heartRate',
    }

    LIFESTYLE_FIELDS = {
        'smoking_status': 'smokingStatus',
        'smoking_count': 'smokingCount',
        'drinking_status': 'drinkingStatus',
        'drinking_frequency': 'drinkingFrequency',
        'drinking_amount': 'drinkingAmount',
    }

    DEMOGRAPHIC_FIELDS = {
        'marital_status': 'maritalStatus',
        'address': 'address',
        'work_status': 'workStatus',
        'education': 'education',
        'ethnicity': 'ethnicity',
        'religion': 'religion',
        'residence_type': 'residenceType',
        'insurance_type': 'insuranceType',
        'occupation': 'occupation',
        'income': 'income',
    }

    @staticmethod
    def _get_or_default(value, default=''):
        return value if value is not None else default

    @classmethod
    def to_frontend_dict(cls, record) -> dict:
        """将数据库模型转换为前端展示用的字典（保持与原 _record_to_dict 一致）。"""
        basic_info = {
            frontend_key: getattr(record, db_field)
            for db_field, frontend_key in cls.BASIC_INFO_FIELDS.items()
        }

        sleep_issues = [
            code for db_field, code, _ in cls.SLEEP_ITEMS
            if getattr(record, db_field)
        ]
        sleep_status = {
            'sleepIssues': sleep_issues,
            'otherSleepIssue': cls._get_or_default(record.sleep_other_desc)
        }

        diseases = [
            code for db_field, code in cls.DISEASE_ITEMS
            if getattr(record, db_field)
        ]
        chronic_disease = {
            'diseases': diseases,
            'tumorHistory': cls._get_or_default(record.disease_tumor_site),
            'otherDisease': cls._get_or_default(record.disease_other_desc)
        }

        medication = {
            'isMedication': record.is_medication,
            'medicationNames': cls._get_or_default(record.medication_names)
        }

        lifestyle = {
            'smokingStatus': cls._get_or_default(record.smoking_status, 'never'),
            'smokingCount': record.smoking_count,
            'drinkingStatus': cls._get_or_default(record.drinking_status, 'never'),
            'drinkingFrequency': record.drinking_frequency,
            'drinkingAmount': record.drinking_amount
        }

        preferred_exercises = [
            code for db_field, code, _ in cls.EXERCISE_ITEMS
            if code != 'other' and getattr(record, db_field)
        ]
        if record.exercise_other:
            preferred_exercises.append('other')

        social_support = []
        for db_field, codes, _ in cls.SUPPORT_ITEMS:
            if getattr(record, db_field):
                social_support.extend(codes)

        exercise = {
            'preferredExercises': preferred_exercises,
            'otherExercise': cls._get_or_default(record.exercise_other_desc),
            'socialSupport': social_support,
            'otherSupport': cls._get_or_default(record.support_other)
        }

        co_residents = record.co_residents or ''
        if isinstance(co_residents, str):
            co_residents = co_residents.split(',') if co_residents else []
        else:
            co_residents = []

        demographic = {
            frontend_key: cls._get_or_default(getattr(record, db_field))
            for db_field, frontend_key in cls.DEMOGRAPHIC_FIELDS.items()
        }
        demographic.update({
            'coResidents': co_residents,
            'ethnicity': cls._get_or_default(record.ethnicity, 'han'),
            'religion': cls._get_or_default(record.religion, 'none'),
            'residenceType': cls._get_or_default(record.residence_type, 'urban'),
        })

        return {
            'id': record.id,
            'basicInfo': basic_info,
            'sleepStatus': sleep_status,
            'chronicDisease': chronic_disease,
            'medication': medication,
            'lifestyle': lifestyle,
            'exercise': exercise,
            'demographic': demographic,
            'ocrText': cls._get_or_default(record.ocr_text),
            'isDraft': record.is_draft,
            'isCompleted': record.is_completed,
            'createdAt': record.created_at.isoformat() if record.created_at else None,
            'updatedAt': record.updated_at.isoformat() if record.updated_at else None
        }

    @classmethod
    def update_record_from_frontend(cls, record, data: dict, is_new: bool = False) -> None:
        """根据前端提交的数据更新数据库模型（保持与原 save_or_update 一致）。"""
        basic_info = data.get('basicInfo', {})
        sleep_status = data.get('sleepStatus', {})
        chronic_disease = data.get('chronicDisease', {})
        medication = data.get('medication', {})
        lifestyle = data.get('lifestyle', {})
        exercise = data.get('exercise', {})
        demographic = data.get('demographic', {})

        # 基本信息：与原始 save_or_update 保持一致的兜底逻辑
        # name / birth_date / gender 在更新时用原值兜底，新建时为空字符串
        # bmi 在新建/更新时都兜底为空字符串
        # 其他字段直接取传入值（允许 None）
        for db_field, frontend_key in cls.BASIC_INFO_FIELDS.items():
            value = basic_info.get(frontend_key)
            if db_field in ('name', 'birth_date', 'gender'):
                if is_new:
                    setattr(record, db_field, value if value is not None else '')
                else:
                    setattr(record, db_field, value if value else getattr(record, db_field))
            elif db_field == 'bmi':
                setattr(record, db_field, value if value else '')
            else:
                setattr(record, db_field, value)

        sleep_issues = sleep_status.get('sleepIssues', [])
        for db_field, code, _ in cls.SLEEP_ITEMS:
            setattr(record, db_field, code in sleep_issues)
        record.sleep_other_desc = sleep_status.get('otherSleepIssue', '')

        diseases = chronic_disease.get('diseases', [])
        for db_field, code in cls.DISEASE_ITEMS:
            setattr(record, db_field, code in diseases)
        record.disease_tumor_site = chronic_disease.get('tumorHistory', '')
        record.disease_other_desc = chronic_disease.get('otherDisease', '')

        record.is_medication = medication.get('isMedication', False)
        record.medication_names = medication.get('medicationNames', '')

        record.smoking_status = lifestyle.get('smokingStatus', 'never')
        record.smoking_count = lifestyle.get('smokingCount')
        record.drinking_status = lifestyle.get('drinkingStatus', 'never')
        record.drinking_frequency = lifestyle.get('drinkingFrequency')
        record.drinking_amount = lifestyle.get('drinkingAmount')

        preferred_exercises = exercise.get('preferredExercises', [])
        for db_field, code, _ in cls.EXERCISE_ITEMS:
            setattr(record, db_field, code in preferred_exercises)
        record.exercise_other_desc = exercise.get('otherExercise', '')

        social_support = exercise.get('socialSupport', [])
        for db_field, codes, _ in cls.SUPPORT_ITEMS:
            setattr(record, db_field, any(s in social_support for s in codes))
        record.support_other = exercise.get('otherSupport', '')

        for db_field, frontend_key in cls.DEMOGRAPHIC_FIELDS.items():
            value = demographic.get(frontend_key)
            if value is not None:
                setattr(record, db_field, value)

        co_residents = demographic.get('coResidents', [])
        if isinstance(co_residents, list):
            record.co_residents = ','.join(co_residents) if co_residents else ''
        else:
            record.co_residents = co_residents or ''

        record.ethnicity = demographic.get('ethnicity', 'han')
        record.religion = demographic.get('religion', 'none')
        record.residence_type = demographic.get('residenceType', 'urban')

        record.ocr_text = data.get('ocrText', '')

    @classmethod
    def to_llm_context(cls, record) -> Optional[dict]:
        """将健康档案转换为 LLM 提示词使用的上下文（保持与原 get_user_health_context 一致）。"""
        if record is None:
            return None

        basic_info = {}
        if record.name:
            basic_info['name'] = record.name
        if record.birth_date:
            basic_info['birthDate'] = record.birth_date
            basic_info['age'] = cls._calculate_age(record.birth_date)
        if record.gender:
            basic_info['gender'] = record.gender
        if record.height:
            basic_info['height'] = record.height
        if record.weight:
            basic_info['weight'] = record.weight
        if record.bmi:
            basic_info['bmi'] = record.bmi
        if record.waist:
            basic_info['waist'] = record.waist
        if record.abdomen:
            basic_info['abdomen'] = record.abdomen
        if record.systolic_bp:
            basic_info['systolic_bp'] = record.systolic_bp
        if record.diastolic_bp:
            basic_info['diastolic_bp'] = record.diastolic_bp
        if record.heart_rate:
            basic_info['heart_rate'] = record.heart_rate

        sleep_info = [
            label for db_field, _, label in cls.SLEEP_ITEMS
            if getattr(record, db_field) and db_field != 'sleep_other'
        ]
        if record.sleep_other and record.sleep_other_desc:
            sleep_info.append(f'其他: {record.sleep_other_desc}')

        diseases = cls._get_diseases_list(record)

        medication_info = None
        if record.is_medication and record.medication_names:
            medication_info = record.medication_names

        lifestyle = {}
        if record.smoking_status:
            lifestyle['smoking'] = {
                'status': record.smoking_status,
                'count': record.smoking_count if record.smoking_count else None
            }
        if record.drinking_status:
            lifestyle['drinking'] = {
                'status': record.drinking_status,
                'frequency': record.drinking_frequency if record.drinking_frequency else None,
                'amount': record.drinking_amount if record.drinking_amount else None
            }

        exercise_prefs = [
            label for db_field, _, label in cls.EXERCISE_ITEMS
            if db_field not in ('exercise_other', 'exercise_no_preference') and getattr(record, db_field)
        ]
        if record.exercise_other and record.exercise_other_desc:
            exercise_prefs.append(f'其他: {record.exercise_other_desc}')
        if record.exercise_no_preference:
            exercise_prefs.append('无运动偏好')

        social_support = [
            label for db_field, _, label in cls.SUPPORT_ITEMS
            if db_field != 'support_none' and getattr(record, db_field)
        ]
        if record.support_other:
            social_support.append(f'其他: {record.support_other}')
        if record.support_none:
            social_support.append('无支持')

        demographic = {}
        if record.marital_status:
            demographic['marital_status'] = record.marital_status
        if record.work_status:
            demographic['work_status'] = record.work_status
        if record.education:
            demographic['education'] = record.education
        if record.residence_type:
            demographic['residence_type'] = record.residence_type
        if record.co_residents:
            demographic['co_residents'] = record.co_residents

        if not (basic_info or diseases or sleep_info or lifestyle or exercise_prefs):
            return None

        record_data = {
            'basicInfo': basic_info,
            'chronicDisease': {'diseases': diseases}
        }
        if sleep_info:
            record_data['sleep'] = sleep_info
        if medication_info:
            record_data['medication'] = medication_info
        if lifestyle:
            record_data['lifestyle'] = lifestyle
        if exercise_prefs:
            record_data['exercise'] = exercise_prefs
        if social_support:
            record_data['socialSupport'] = social_support
        if demographic:
            record_data['demographic'] = demographic

        return record_data

    @classmethod
    def _get_diseases_list(cls, record: HealthRecord) -> List[str]:
        """返回慢性病英文编码列表（用于 LLM 上下文）。"""
        return [
            code for db_field, code in cls.DISEASE_ITEMS
            if code in (
                'hypertension', 'diabetes', 'dyslipidemia', 'coronary_heart_disease',
                'stroke', 'copd', 'gout', 'osteoporosis', 'parkinsons', 'alzheimers'
            ) and getattr(record, db_field)
        ]

    @staticmethod
    def _calculate_age(birth_date: str) -> Optional[int]:
        from datetime import datetime
        try:
            birth = datetime.strptime(birth_date, '%Y-%m-%d')
            today = get_now_naive()
            age = today.year - birth.year
            if (today.month, today.day) < (birth.month, birth.day):
                age -= 1
            return age
        except Exception:
            return None
