"""依赖注入模块 - 公共依赖"""
from typing import Optional

from fastapi import Depends
from redis import Redis
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.utils.redis_client import get_redis


def get_db_session() -> Session:
    """获取数据库会话（给 services 层使用）"""
    db = next(get_db())
    try:
        yield db
    finally:
        db.close()


def get_redis_client() -> Optional[Redis]:
    """获取 Redis 客户端（给 services 层使用）"""
    redis_client = get_redis()
    if redis_client is None:
        yield None
    else:
        try:
            yield redis_client
        finally:
            pass  # Redis 连接由连接池管理，无需手动关闭
