from sqlalchemy import select, desc
from sqlalchemy.orm import Session

from model.healthRecord import HealthRecord, HealthRecordMapper
from exception.customException import NotFoundException


class HealthRecordService:
    @staticmethod
    def save_or_update(user_id: int, data: dict, record_id: int = None, is_draft: bool = True, db_session: Session = None):
        if record_id:
            query = select(HealthRecord).where(HealthRecord.id == record_id, HealthRecord.user_id == user_id)
            record = db_session.execute(query).scalar()
            if not record:
                raise NotFoundException("健康档案不存在")
        else:
            record = HealthRecord()
            record.user_id = user_id
            # 新建记录时给必填字段默认值，避免空值入库
            record.name = ''
            record.birth_date = ''
            record.gender = ''

        HealthRecordMapper.update_record_from_frontend(record, data, is_new=(not record_id))

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
