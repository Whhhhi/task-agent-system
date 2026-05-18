"""日志配置模块 - 基于 loguru"""
import os
import sys
from pathlib import Path

from loguru import logger

from app.config import settings


def setup_logger() -> None:
    """配置全局日志器"""
    # 确保日志目录存在
    log_path = Path(settings.LOG_FILE_PATH)
    log_dir = log_path.parent
    if not log_dir.exists():
        os.makedirs(str(log_dir), exist_ok=True)

    # 移除默认的 handler
    logger.remove()

    # 控制台输出（带颜色）
    logger.add(
        sys.stdout,
        level=settings.LOG_LEVEL,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
        "<level>{message}</level>",
        enqueue=True,
    )

    # 文件输出（JSON格式，方便日志分析）
    logger.add(
        str(log_path),
        level=settings.LOG_LEVEL,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}",
        rotation="10 MB",       # 每10MB轮转
        retention="30 days",    # 保留30天
        compression="gz",       # 轮转后压缩
        enqueue=True,
        backtrace=True,
        diagnose=True,
    )

    logger.info("日志系统初始化完成")


# 模块级导出
__all__ = ["logger", "setup_logger"]
