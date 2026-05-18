"""总目标表 ORM 模型 - 用户输入的原始大目标"""
from datetime import datetime
from typing import Any

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, SmallInteger, String, Text, func

from app.db.base import Base


class TaskGoal(Base):
    """总目标表 - 存储用户输入的原始大目标和整体进度"""

    id: Any = Column(Integer, primary_key=True, autoincrement=True, comment="目标ID")
    user_id: Any = Column(
        Integer,
        ForeignKey("user.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="用户ID",
    )
    title: Any = Column(String(256), nullable=False, comment="目标标题")
    description: Any = Column(Text, nullable=True, comment="目标详细描述")
    goal_type: Any = Column(
        String(64), nullable=True, comment="目标类型：学习/工作/备考/项目开发/求职规划/其他"
    )
    deadline: Any = Column(DateTime, nullable=True, comment="整体截止时间")
    progress: Any = Column(
        Float, default=0.0, nullable=False, comment="整体完成进度（0.0 ~ 100.0）"
    )
    status: Any = Column(
        SmallInteger, default=0, nullable=False, comment="状态：0-进行中 1-已完成 2-已作废"
    )

    def __repr__(self) -> str:
        return f"<TaskGoal(id={self.id}, title='{self.title}')>"
