"""
智能任务拆解Agent系统 - 项目入口

启动命令:  uvicorn main:app --reload
生产部署:  uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from app.api.v1 import api_router
from app.config import settings
from app.core.exception import register_exception_handlers
from app.db.session import init_db
from app.utils.logger import setup_logger
from app.utils.redis_client import init_redis, close_redis
from app.services.scheduler import SchedulerService

# 全局调度器实例
scheduler_service = SchedulerService()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    应用生命周期管理
    - 启动时：初始化日志、数据库、Redis、调度器
    - 关闭时：清理资源
    """
    # ─── 启动逻辑 ───
    setup_logger()
    logger.info(f"{settings.APP_NAME} v{settings.APP_VERSION} 启动中...")

    # 初始化数据库表
    init_db()
    logger.info("数据库表结构初始化完成")

    # 初始化 Redis
    init_redis()

    # 启动定时调度器
    scheduler_service.start()

    yield

    # ─── 关闭逻辑 ───
    logger.info("应用关闭中...")
    scheduler_service.stop()
    close_redis()
    logger.info("应用已安全关闭")


# 创建 FastAPI 应用实例
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=settings.APP_DESCRIPTION,
    lifespan=lifespan,
    docs_url="/docs",          # Swagger 文档
    redoc_url="/redoc",        # ReDoc 文档
)

# ─── 注册中间件 ───

# CORS 跨域配置（允许前端跨域访问）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],       # 生产环境请替换为具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── 注册路由 ───
app.include_router(api_router)

# ─── 注册全局异常处理器 ───
register_exception_handlers(app)


# ─── 根路径健康检查 ───
@app.get("/", tags=["系统"])
def root():
    """系统健康检查接口"""
    return {
        "code": 200,
        "msg": "success",
        "data": {
            "name": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "status": "running",
        },
        "timestamp": __import__("time").time_ns() // 1_000_000,
    }


@app.get("/health", tags=["系统"])
def health_check():
    """健康检查接口"""
    return {"status": "healthy", "version": settings.APP_VERSION}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        workers=1 if settings.DEBUG else 4,
        log_level=settings.LOG_LEVEL.lower(),
    )
