"""数据库会话管理 - 异步引擎与会话工厂"""
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.config import DATABASE_URL

# 创建数据库引擎（连接池配置：池大小10，最大溢出20）
engine = create_engine(
    DATABASE_URL,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,      # 每次连接前校验连接是否有效
    echo=False,              # 生产环境关闭 SQL 日志
)

# 会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Session:
    """FastAPI 依赖注入：获取数据库会话，请求结束后自动关闭"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """初始化数据库表结构（生产环境建议使用 Alembic 管理迁移）"""
    from app.db.base import Base
    from app.models import user, task_goal, task_item, agent_tool, task_log  # noqa: F401
    Base.metadata.create_all(bind=engine)
