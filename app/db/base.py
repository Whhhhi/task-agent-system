"""SQLAlchemy 基础模型声明 - 所有 ORM 模型的基类"""
from datetime import datetime
from typing import Any

from sqlalchemy import Column, DateTime, func
from sqlalchemy.orm import DeclarativeBase, Mapped, declared_attr


class Base(DeclarativeBase):
    """所有模型类的基类，自动处理表名和公共字段"""

    @declared_attr
    def __tablename__(cls) -> str:
        # 自动将驼峰类名转为小写下划线表名（如 TaskGoal -> task_goal）
        name = cls.__name__
        result = [name[0].lower()]
        for ch in name[1:]:
            if ch.isupper():
                result.extend(["_", ch.lower()])
            else:
                result.append(ch)
        return "".join(result)

    # 所有表统一创建时间字段
    created_at: Mapped[datetime] = Column(
        DateTime,
        server_default=func.now(),
        nullable=False,
        comment="创建时间",
    )
