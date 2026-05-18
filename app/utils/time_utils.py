"""时间处理工具模块"""
from datetime import datetime, timezone, timedelta
from typing import Optional

import pytz

from app.config import settings


def now() -> datetime:
    """获取当前时间（配置时区）"""
    tz = pytz.timezone(settings.SCHEDULER_TIMEZONE)
    return datetime.now(tz)


def now_utc() -> datetime:
    """获取当前 UTC 时间"""
    return datetime.now(timezone.utc)


def to_timezone(dt: datetime, tz_name: Optional[str] = None) -> datetime:
    """将 datetime 转换为指定时区"""
    tz = pytz.timezone(tz_name or settings.SCHEDULER_TIMEZONE)
    if dt.tzinfo is None:
        return tz.localize(dt)
    return dt.astimezone(tz)


def format_datetime(dt: datetime, fmt: str = "%Y-%m-%d %H:%M:%S") -> str:
    """格式化时间为字符串"""
    return dt.strftime(fmt)


def parse_datetime(
    date_str: str, fmt: str = "%Y-%m-%d %H:%M:%S"
) -> Optional[datetime]:
    """解析时间字符串为 datetime"""
    try:
        return datetime.strptime(date_str, fmt)
    except (ValueError, TypeError):
        return None


def is_overdue(deadline: datetime) -> bool:
    """判断是否已逾期"""
    return now() > deadline


def remaining_days(deadline: datetime) -> float:
    """计算剩余天数"""
    diff = deadline - now()
    return max(0.0, diff.total_seconds() / 86400)
