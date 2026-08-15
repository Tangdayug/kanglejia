"""
2026-08-07 小智桥接与最小健康归属数据库迁移

变更内容：
1. xiaozhi_voiceprints 表新增 display_name、verification_status 字段
2. 新增 health_observations 表，用于记录“谁描述了谁”的健康观察
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from model import Base, USE_SQLITE, database_url
from model.xiaozhiSession import XiaozhiVoiceprint, HealthObservation


def _sqlite_table_exists(conn, table_name: str) -> bool:
    result = conn.execute(
        text("SELECT name FROM sqlite_master WHERE type='table' AND name=:name"),
        {"name": table_name}
    )
    return result.fetchone() is not None


def _sqlite_column_exists(conn, table_name: str, column_name: str) -> bool:
    result = conn.execute(text(f"PRAGMA table_info({table_name})"))
    rows = result.fetchall()
    return any(row[1] == column_name for row in rows)


def _mysql_table_exists(conn, table_name: str) -> bool:
    result = conn.execute(
        text("SHOW TABLES LIKE :name"),
        {"name": table_name}
    )
    return result.fetchone() is not None


def _mysql_column_exists(conn, table_name: str, column_name: str) -> bool:
    result = conn.execute(
        text("SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME=:table AND COLUMN_NAME=:col"),
        {"table": table_name, "col": column_name}
    )
    return result.fetchone() is not None


def migrate():
    print("=" * 60)
    print("2026-08-07 小智桥接与健康归属迁移")
    print("=" * 60)

    engine = create_engine(database_url, connect_args={"check_same_thread": False} if USE_SQLITE else {})
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()

    try:
        with engine.connect() as conn:
            if USE_SQLITE:
                # 新增 display_name 字段
                if _sqlite_table_exists(conn, "xiaozhi_voiceprints"):
                    if not _sqlite_column_exists(conn, "xiaozhi_voiceprints", "display_name"):
                        conn.execute(text(
                            "ALTER TABLE xiaozhi_voiceprints ADD COLUMN display_name VARCHAR(100)"
                        ))
                        print("✅ xiaozhi_voiceprints.display_name 已添加")
                    else:
                        print("⚠️ xiaozhi_voiceprints.display_name 已存在，跳过")

                    if not _sqlite_column_exists(conn, "xiaozhi_voiceprints", "verification_status"):
                        conn.execute(text(
                            "ALTER TABLE xiaozhi_voiceprints ADD COLUMN verification_status VARCHAR(20) DEFAULT 'pending' NOT NULL"
                        ))
                        print("✅ xiaozhi_voiceprints.verification_status 已添加")
                    else:
                        print("⚠️ xiaozhi_voiceprints.verification_status 已存在，跳过")
                else:
                    print("⚠️ xiaozhi_voiceprints 表不存在，将由 SQLAlchemy 自动创建")

                if not _sqlite_table_exists(conn, "health_observations"):
                    print("✅ health_observations 表将由 SQLAlchemy 自动创建")
                else:
                    print("⚠️ health_observations 表已存在，跳过")
            else:
                # MySQL 分支
                if _mysql_table_exists(conn, "xiaozhi_voiceprints"):
                    if not _mysql_column_exists(conn, "xiaozhi_voiceprints", "display_name"):
                        conn.execute(text(
                            "ALTER TABLE xiaozhi_voiceprints ADD COLUMN display_name VARCHAR(100)"
                        ))
                        print("✅ xiaozhi_voiceprints.display_name 已添加")
                    else:
                        print("⚠️ xiaozhi_voiceprints.display_name 已存在，跳过")

                    if not _mysql_column_exists(conn, "xiaozhi_voiceprints", "verification_status"):
                        conn.execute(text(
                            "ALTER TABLE xiaozhi_voiceprints ADD COLUMN verification_status VARCHAR(20) DEFAULT 'pending' NOT NULL"
                        ))
                        print("✅ xiaozhi_voiceprints.verification_status 已添加")
                    else:
                        print("⚠️ xiaozhi_voiceprints.verification_status 已存在，跳过")

            conn.commit()

        # 创建新表
        Base.metadata.create_all(bind=engine, tables=[
            XiaozhiVoiceprint.__table__,
            HealthObservation.__table__
        ])

        # 兼容旧数据：已有的声纹记录 verification_status 设为 allowed
        updated = db.execute(
            text("UPDATE xiaozhi_voiceprints SET verification_status='allowed' WHERE verification_status IS NULL OR verification_status=''")
        )
        db.commit()
        print(f"✅ 已兼容旧声纹记录: {updated.rowcount} 条")

        print("\n" + "=" * 60)
        print("✅ 迁移完成")
        print("=" * 60)
        return True

    except Exception as e:
        db.rollback()
        print(f"❌ 迁移失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()


if __name__ == "__main__":
    migrate()
