import os
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from common.constant import *

class Base(DeclarativeBase):
    pass

# 自动检测使用 MySQL 还是 SQLite
# 如果配置了 MYSQL_HOST 且不为 localhost，则使用 MySQL
# 否则使用 SQLite（适用于轻量级部署）
USE_SQLITE = (
    MYSQL_HOST == "localhost" or
    not MYSQL_HOST or
    MYSQL_HOST == "${MYSQL_HOST}"
)

if USE_SQLITE:
    # 使用 SQLite
    db_path = Path(__file__).parent.parent / "data" / "secondnature.db"
    db_path.parent.mkdir(parents=True, exist_ok=True)
    database_url = f"sqlite:///{db_path}"
    print(f"📦 使用 SQLite 数据库: {db_path}")
else:
    # 使用 MySQL
    database_url = f"{MYSQL_DIALECT}://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}?charset=utf8mb4"
    print(f"🗄️ 使用 MySQL 数据库: {MYSQL_HOST}/{MYSQL_DATABASE}")

engine = create_engine(
    database_url,
    echo=False,  # 生产环境关闭 SQL 日志
    connect_args={"check_same_thread": False} if USE_SQLITE else {}
)

Session = sessionmaker(bind=engine)

def get_db_session():
    session = Session()
    try:
        yield session
    finally:
        session.close()

# 初始化数据库表
def init_db():
    """初始化数据库表"""
    from model import admin, user, healthRecord, healthTest, chatHistory, interventionLog, xiaozhiSession
    # account 是别名表，不需要单独创建
    Base.metadata.create_all(bind=engine)
    print("✅ 数据库表初始化完成")
