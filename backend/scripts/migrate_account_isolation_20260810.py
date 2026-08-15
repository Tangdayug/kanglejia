"""
2026-08-10 账号隔离与硬件-账号归属迁移

变更内容：
1. health_observations 表新增 user_id 字段，用于按账号隔离健康观察。
2. chat_messages 表新增 user_id 字段（冗余，防御纵深）。
3. 回填旧数据：
   - health_observations.user_id 根据 subject_voiceprint_id -> xiaozhi_voiceprints.user_id
   - chat_messages.user_id 根据 session_id -> chat_sessions.user_id
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from model import USE_SQLITE, database_url


def _sqlite_column_exists(conn, table_name: str, column_name: str) -> bool:
    result = conn.execute(text(f"PRAGMA table_info({table_name})"))
    rows = result.fetchall()
    return any(row[1] == column_name for row in rows)


def _mysql_column_exists(conn, table_name: str, column_name: str) -> bool:
    result = conn.execute(
        text("SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME=:table AND COLUMN_NAME=:col"),
        {"table": table_name, "col": column_name}
    )
    return result.fetchone() is not None


def migrate():
    print("=" * 60)
    print("2026-08-10 账号隔离与硬件-账号归属迁移")
    print("=" * 60)

    engine = create_engine(database_url, connect_args={"check_same_thread": False} if USE_SQLITE else {})

    try:
        with engine.connect() as conn:
            if USE_SQLITE:
                # 1. health_observations.user_id
                if not _sqlite_column_exists(conn, "health_observations", "user_id"):
                    conn.execute(text(
                        "ALTER TABLE health_observations ADD COLUMN user_id INTEGER NOT NULL DEFAULT 1"
                    ))
                    print("✅ health_observations.user_id 已添加")
                else:
                    print("⚠️ health_observations.user_id 已存在，跳过")

                # 根据 subject_voiceprint_id 回填 user_id
                conn.execute(text("""
                    UPDATE health_observations
                    SET user_id = COALESCE(
                        (SELECT user_id FROM xiaozhi_voiceprints WHERE xiaozhi_voiceprints.voiceprint_id = health_observations.subject_voiceprint_id),
                        1
                    )
                """))
                print("✅ health_observations.user_id 已回填")

                conn.execute(text(
                    "CREATE INDEX IF NOT EXISTS ix_health_observations_user_id ON health_observations (user_id)"
                ))

                # 2. chat_messages.user_id（防御纵深，允许 NULL 兼容旧数据）
                if not _sqlite_column_exists(conn, "chat_messages", "user_id"):
                    conn.execute(text(
                        "ALTER TABLE chat_messages ADD COLUMN user_id INTEGER"
                    ))
                    print("✅ chat_messages.user_id 已添加")
                else:
                    print("⚠️ chat_messages.user_id 已存在，跳过")

                conn.execute(text("""
                    UPDATE chat_messages
                    SET user_id = (
                        SELECT user_id FROM chat_sessions WHERE chat_sessions.id = chat_messages.session_id
                    )
                    WHERE user_id IS NULL
                """))
                print("✅ chat_messages.user_id 已回填")

                conn.execute(text(
                    "CREATE INDEX IF NOT EXISTS ix_chat_messages_user_id ON chat_messages (user_id)"
                ))

            else:
                # MySQL 分支
                if not _mysql_column_exists(conn, "health_observations", "user_id"):
                    conn.execute(text(
                        "ALTER TABLE health_observations ADD COLUMN user_id INT NOT NULL DEFAULT 1"
                    ))
                    print("✅ health_observations.user_id 已添加")
                else:
                    print("⚠️ health_observations.user_id 已存在，跳过")

                conn.execute(text("""
                    UPDATE health_observations h
                    JOIN xiaozhi_voiceprints v ON v.voiceprint_id = h.subject_voiceprint_id
                    SET h.user_id = v.user_id
                """))
                print("✅ health_observations.user_id 已回填")

                if not _mysql_column_exists(conn, "chat_messages", "user_id"):
                    conn.execute(text(
                        "ALTER TABLE chat_messages ADD COLUMN user_id INT NULL"
                    ))
                    print("✅ chat_messages.user_id 已添加")
                else:
                    print("⚠️ chat_messages.user_id 已存在，跳过")

                conn.execute(text("""
                    UPDATE chat_messages m
                    JOIN chat_sessions s ON s.id = m.session_id
                    SET m.user_id = s.user_id
                    WHERE m.user_id IS NULL
                """))
                print("✅ chat_messages.user_id 已回填")

            conn.commit()

        print("\n" + "=" * 60)
        print("✅ 迁移完成")
        print("=" * 60)
        return True

    except Exception as e:
        print(f"❌ 迁移失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    migrate()
