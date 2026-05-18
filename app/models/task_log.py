"""任务操作日志表 ORM 模型 - 记录所有状态变更和操作"""
from datetime import datetime
from typing import Any

from sqlalchemy import Column, DateTime, ForeignKey, Integer, SmallInteger, String, Text, func

from app.db.base import Base


class TaskLog(Base):
    """任务操作日志表 - 记录任务状态变更和用户操作"""

    id: Any = Column(Integer, primary_key=True, autoincrement=True, comment="日志ID")
    task_id: Any = Column(
        Integer,
        ForeignKey("task_item.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="关联任务ID",
    )
    action_type: Any = Column(
        String(32), nullable=False, comment="操作类型：create/status_change/update/delete"
    )
    content: Any = Column(Text, nullable=True, comment="操作内容/变更详情")
    created_at: Any = Column(
        DateTime,
        server_default=func.now(),
        nullable=False,
        comment="操作时间",
    )

    def __repr__(self) -> str:
        return f"<TaskLog(id={self.id}, task_id={self.task_id}, action='{self.action_type}')>"
