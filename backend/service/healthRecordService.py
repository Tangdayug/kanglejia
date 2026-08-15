from sqlalchemy import select, desc
from sqlalchemy.orm import Session

from model.healthRecord import HealthRecord
from exception.customException import NotFoundException


class HealthRecordService:
    @staticmethod
    def save_or_update(user_id: int, data: dict, record_id: int = None, is_draft: bool = True, db_session: Session = None):
        basic_info = data.get('basicInfo', {})
        sleep_status = data.get('sleepStatus', {})
        chronic_disease = data.get('chronicDisease', {})
        medication = data.get('medication', {})
        lifestyle = data.get('lifestyle', {})
        exercise = data.get('exercise', {})
        demographic = data.get('demographic', {})
        ocr_text = data.get('ocrText', '')

        if record_id:
            query = select(HealthRecord).where(HealthRecord.id == record_id, HealthRecord.user_id == user_id)
            record = db_session.execute(query).scalar()
            if not record:
                raise NotFoundException("健康档案不存在")
        else:
            record = HealthRecord()
            record.user_id = user_id

        record.name = basic_info.get('name') or record.name if record_id else ''
        record.birth_date = basic_info.get('birthDate') or record.birth_date if record_id else ''
        record.gender = basic_info.get('gender') or record.gender if record_id else ''
        record.height = basic_info.get('height')
        record.weight = basic_info.get('weight')
        record.bmi = basic_info.get('bmi') or ''
        record.waist = basic_info.get('waist')
        record.abdomen = basic_info.get('abdomen')
        record.systolic_bp = basic_info.get('systolicBp')
        record.diastolic_bp = basic_info.get('diastolicBp')
        record.heart_rate = basic_info.get('heartRate')

        # 睡眠状况
        sleep_issues = sleep_status.get('sleepIssues', [])
        record.sleep_good = 'good' in sleep_issues
        record.sleep_difficulty_falling = 'difficulty_falling_asleep' in sleep_issues
        record.sleep_easily_wake = 'easily_wake' in sleep_issues
        record.sleep_early_wake = 'early_wake' in sleep_issues
        record.sleep_daytime_sleepiness = 'daytime_sleepiness' in sleep_issues
        record.sleep_other = 'other' in sleep_issues
        record.sleep_other_desc = sleep_status.get('otherSleepIssue', '')

        # 慢性病情况
        diseases = chronic_disease.get('diseases', [])
        record.disease_hypertension = 'hypertension' in diseases
        record.disease_diabetes = 'diabetes' in diseases
        record.disease_dyslipidemia = 'dyslipidemia' in diseases
        record.disease_coronary = 'coronary_heart_disease' in diseases
        record.disease_angina = 'angina' in diseases
        record.disease_myocardial_infarction = 'myocardial_infarction' in diseases
        record.disease_stroke = 'stroke' in diseases
        record.disease_copd = 'copd' in diseases
        record.disease_gout = 'gout' in diseases
        record.disease_kidney = 'chronic_kidney_disease' in diseases
        record.disease_hypothyroidism = 'hypothyroidism' in diseases
        record.disease_hyperthyroidism = 'hyperthyroidism' in diseases
        record.disease_osteoporosis = 'osteoporosis' in diseases
        record.disease_parkinsons = 'parkinsons' in diseases
        record.disease_alzheimers = 'alzheimers' in diseases
        record.disease_tumor = 'tumor_history' in diseases
        record.disease_tumor_site = chronic_disease.get('tumorHistory', '')
        record.disease_other = 'other' in diseases
        record.disease_other_desc = chronic_disease.get('otherDisease', '')
        record.disease_none = 'none' in diseases

        # 用药情况
        record.is_medication = medication.get('isMedication', False)
        record.medication_names = medication.get('medicationNames', '')

        # 生活习惯 - 吸烟
        record.smoking_status = lifestyle.get('smokingStatus', 'never')
        record.smoking_count = lifestyle.get('smokingCount')

        # 生活习惯 - 喝酒
        record.drinking_status = lifestyle.get('drinkingStatus', 'never')
        record.drinking_frequency = lifestyle.get('drinkingFrequency')
        record.drinking_amount = lifestyle.get('drinkingAmount')

        # 运动偏好
        preferred_exercises = exercise.get('preferredExercises', [])
        record.exercise_walking = 'walking' in preferred_exercises
        record.exercise_jogging = 'jogging' in preferred_exercises
        record.exercise_square_dance = 'square_dance' in preferred_exercises
        record.exercise_tai_chi = 'tai_chi' in preferred_exercises
        record.exercise_swimming = 'swimming' in preferred_exercises
        record.exercise_cycling = 'cycling' in preferred_exercises
        record.exercise_racket = 'racket_sports' in preferred_exercises
        record.exercise_hiking = 'hiking' in preferred_exercises
        record.exercise_gardening = 'gardening' in preferred_exercises
        record.exercise_fishing = 'fishing' in preferred_exercises
        record.exercise_gym = 'gym' in preferred_exercises
        record.exercise_yoga = 'yoga' in preferred_exercises
        record.exercise_no_preference = 'no_preference' in preferred_exercises
        record.exercise_other = 'other' in preferred_exercises
        record.exercise_other_desc = exercise.get('otherExercise', '')

        social_support = exercise.get('socialSupport', [])
        record.support_equipment = any(s in social_support for s in ['fitness_equipment', 'park', 'fitness_trail', 'community_room'])
        record.support_organization = any(s in social_support for s in ['dance_team', 'fitness_team', 'sports_club', 'interest_group'])
        record.support_info = any(s in social_support for s in ['health_lecture', 'fitness_guidance', 'digital_push', 'poster'])
        record.support_policy = any(s in social_support for s in ['free_facilities', 'insurance_benefit', 'subsidy'])
        record.support_none = 'none' in social_support
        record.support_other = exercise.get('otherSupport', '')

        record.marital_status = demographic.get('maritalStatus', '')
        record.address = demographic.get('address', '')
        record.work_status = demographic.get('workStatus', '')
        record.education = demographic.get('education', '')
        record.ethnicity = demographic.get('ethnicity', 'han')
        record.religion = demographic.get('religion', 'none')
        record.residence_type = demographic.get('residenceType', 'urban')

        co_residents = demographic.get('coResidents', [])
        if isinstance(co_residents, list):
            record.co_residents = ','.join(co_residents) if co_residents else ''
        else:
            record.co_residents = co_residents or ''

        record.insurance_type = demographic.get('insuranceType', '')
        record.occupation = demographic.get('occupation', '')
        record.income = demographic.get('income', '')
        record.ocr_text = ocr_text or ''

        record.is_draft = is_draft
        if not is_draft:
            record.is_completed = True

        if not record_id:
            db_session.add(record)

        db_session.commit()
        db_session.refresh(record)
        return record

    @staticmethod
    def get_draft(user_id: int, db_session: Session):
        query = select(HealthRecord).where(
            HealthRecord.user_id == user_id,
            HealthRecord.is_draft == True
        ).order_by(desc(HealthRecord.updated_at)).limit(1)
        return db_session.execute(query).scalar()

    @staticmethod
    def get_by_id(record_id: int, user_id: int, db_session: Session):
        query = select(HealthRecord).where(
            HealthRecord.id == record_id,
            HealthRecord.user_id == user_id
        )
        record = db_session.execute(query).scalar()
        if not record:
            raise NotFoundException("健康档案不存在")
        return record

    @staticmethod
    def get_user_records(user_id: int, db_session: Session):
        query = select(HealthRecord).where(
            HealthRecord.user_id == user_id
        ).order_by(desc(HealthRecord.updated_at))
        result = db_session.execute(query).scalars().all()
        return list(result)

    @staticmethod
    def submit(record_id: int, user_id: int, db_session: Session):
        query = select(HealthRecord).where(
            HealthRecord.id == record_id,
            HealthRecord.user_id == user_id
        )
        record = db_session.execute(query).scalar()
        if not record:
            raise NotFoundException("健康档案不存在")

        record.is_draft = False
        record.is_completed = True
        db_session.commit()
        db_session.refresh(record)
        return record
