"""
时间工具函数 - 统一处理时区
"""
from datetime import datetime, timezone, timedelta
from typing import Optional

# 中国时区 (UTC+8)
CHINA_TZ = timezone(timedelta(hours=8))


def get_now() -> datetime:
    """
    获取中国时区的当前时间

    Returns:
        带时区信息的datetime对象
    """
    return datetime.now(CHINA_TZ)


def get_now_naive() -> datetime:
    """
    获取中国时区的当前时间（不带时区信息）

    用于数据库存储，因为SQLite不需要时区信息

    Returns:
        不带时区信息的datetime对象
    """
    return datetime.now(CHINA_TZ).replace(tzinfo=None)
