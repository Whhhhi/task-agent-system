"""Redis 客户端管理"""
from typing import Optional

import redis
from loguru import logger

from app.config import REDIS_URL, settings

# 全局 Redis 连接实例
_redis_client: Optional[redis.Redis] = None


def init_redis() -> Optional[redis.Redis]:
    """初始化 Redis 连接池"""
    global _redis_client
    try:
        _redis_client = redis.Redis.from_url(
            REDIS_URL,
            decode_responses=True,       # 自动解码为字符串
            socket_connect_timeout=3,    # 连接超时3秒
            socket_timeout=5,            # 读写超时5秒
            max_connections=20,          # 连接池最大连接数
        )
        # 测试连接是否正常
        _redis_client.ping()
        logger.info("Redis 连接成功")
    except redis.ConnectionError as e:
        logger.warning(f"Redis 连接失败（系统将继续运行，缓存功能不可用）: {e}")
        _redis_client = None
    return _redis_client


def get_redis() -> Optional[redis.Redis]:
    """获取 Redis 客户端实例"""
    return _redis_client


def close_redis() -> None:
    """关闭 Redis 连接池"""
    global _redis_client
    if _redis_client is not None:
        try:
            _redis_client.close()
            logger.info("Redis 连接已关闭")
        except Exception as e:
            logger.warning(f"Redis 关闭异常: {e}")
        finally:
            _redis_client = None
