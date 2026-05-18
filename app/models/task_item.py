"""子任务表 ORM 模型 - Agent拆解后的可执行任务单元"""
from datetime import datetime
from typing import Any, Optional

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, SmallInteger, String, Text, func

from app.db.base import Base


class TaskItem(Base):
    """子任务表 - Agent拆解的多级任务，支持三级结构"""

    id: Any = Column(Integer, primary_key=True, autoincrement=True, comment="任务ID")
    goal_id: Any = Column(
        Integer,
        ForeignKey("task_goal.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="所属目标ID",
    )
    parent_id: Any = Column(
        Integer,
        ForeignKey("task_item.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
        comment="父任务ID（支持多级嵌套）",
    )
    title: Any = Column(String(256), nullable=False, comment="任务标题")
    description: Any = Column(Text, nullable=True, comment="任务详细描述")
    priority: Any = Column(
        SmallInteger,
        default=1,
        nullable=False,
        comment="优先级：0-低 1-中 2-高",
    )
    estimated_hours: Any = Column(Float, nullable=True, comment="预估耗时（小时）")
    deadline: Any = Column(DateTime, nullable=True, comment="建议截止时间")
    status: Any = Column(
        SmallInteger,
        default=0,
        nullable=False,
        comment="状态：0-待执行 1-进行中 2-已完成 3-延期 4-作废",
    )
    sort_order: Any = Column(
        Integer, default=0, nullable=False, comment="排序权重（越小越靠前）"
    )
    tool_id: Any = Column(
        Integer,
        ForeignKey("agent_tool.id", ondelete="SET NULL"),
        nullable=True,
        comment="关联工具ID",
    )
    completed_at: Any = Column(DateTime, nullable=True, comment="实际完成时间")
    remarks: Any = Column(Text, nullable=True, comment="备注/执行记录")

    def __repr__(self) -> str:
        return f"<TaskItem(id={self.id}, title='{self.title}', status={self.status})>"
