"""Agent工具表 ORM 模型 - 内置工具库"""
from typing import Any

from sqlalchemy import Column, Integer, String, Text

from app.db.base import Base


class AgentTool(Base):
    """Agent工具表 - 可被 Agent 调用的内置工具定义"""

    id: Any = Column(Integer, primary_key=True, autoincrement=True, comment="工具ID")
    name: Any = Column(String(128), unique=True, nullable=False, comment="工具名称")
    description: Any = Column(Text, nullable=True, comment="工具描述")
    prompt_template: Any = Column(Text, nullable=False, comment="工具Prompt模板")
    scenario: Any = Column(String(256), nullable=True, comment="适用场景标签")

    def __repr__(self) -> str:
        return f"<AgentTool(id={self.id}, name='{self.name}')>"
