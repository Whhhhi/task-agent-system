"""Agent 模块 Pydantic 模型"""
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class AgentDecomposeRequest(BaseModel):
    """Agent 目标拆解请求"""
    goal_title: str = Field(..., min_length=1, max_length=256, description="目标标题")
    goal_description: Optional[str] = Field(None, description="目标详细描述")
    goal_type: Optional[str] = Field(None, description="目标类型")
    deadline: Optional[str] = Field(None, description="期望截止时间（如：2024-12-31）")


class SubTaskSchema(BaseModel):
    """Agent 拆解返回的子任务结构"""
    title: str = Field(..., description="任务标题")
    description: Optional[str] = Field(None, description="任务描述")
    priority: int = Field(..., ge=0, le=2, description="优先级")
    estimated_hours: float = Field(..., ge=0, description="预估耗时（小时）")
    deadline: Optional[str] = Field(None, description="建议截止时间")
    difficulty: Optional[str] = Field(None, description="执行难度")
    tags: Optional[List[str]] = Field(None, description="任务标签")
    tool_name: Optional[str] = Field(None, description="推荐调用的工具名称")
    children: Optional[List["SubTaskSchema"]] = Field(None, description="下级子任务")


class AgentDecomposeResponse(BaseModel):
    """Agent 拆解结果响应"""
    goal_id: int
    title: str
    description: Optional[str] = None
    goal_type: Optional[str] = None
    tasks: List[SubTaskSchema]


class AgentToolResponse(BaseModel):
    """工具信息响应"""
    id: int
    name: str
    description: Optional[str] = None
    prompt_template: str
    scenario: Optional[str] = None

    class Config:
        from_attributes = True


class ToolCallRequest(BaseModel):
    """工具调用请求"""
    tool_id: int = Field(..., description="工具ID")
    task_id: int = Field(..., description="关联任务ID")
    params: Dict[str, Any] = Field(default_factory=dict, description="工具参数")


class ToolCallResponse(BaseModel):
    """工具调用响应"""
    tool_name: str
    task_id: int
    result: str


class AgentChatRequest(BaseModel):
    """Agent 对话请求（基于历史上下文进一步优化）"""
    goal_id: int = Field(..., description="目标ID")
    user_message: str = Field(..., min_length=1, description="用户消息")


class AgentChatResponse(BaseModel):
    """Agent 对话响应"""
    reply: str
    suggested_tasks: Optional[List[SubTaskSchema]] = None
