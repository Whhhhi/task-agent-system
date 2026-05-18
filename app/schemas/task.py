"""任务模块 Pydantic 模型"""
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ─── 总目标 ───

class GoalCreateRequest(BaseModel):
    """创建总目标请求"""
    title: str = Field(..., min_length=1, max_length=256, description="目标标题")
    description: Optional[str] = Field(None, description="目标详细描述")
    goal_type: Optional[str] = Field(None, description="目标类型")
    deadline: Optional[datetime] = Field(None, description="整体截止时间")


class GoalUpdateRequest(BaseModel):
    """更新总目标请求"""
    title: Optional[str] = Field(None, max_length=256)
    description: Optional[str] = None
    goal_type: Optional[str] = None
    deadline: Optional[datetime] = None
    status: Optional[int] = Field(None, ge=0, le=2)


class GoalResponse(BaseModel):
    """总目标响应"""
    id: int
    user_id: int
    title: str
    description: Optional[str] = None
    goal_type: Optional[str] = None
    deadline: Optional[datetime] = None
    progress: float
    status: int
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ─── 子任务 ───

class TaskItemCreateRequest(BaseModel):
    """手动创建子任务请求"""
    goal_id: int = Field(..., description="所属目标ID")
    parent_id: Optional[int] = Field(None, description="父任务ID")
    title: str = Field(..., min_length=1, max_length=256, description="任务标题")
    description: Optional[str] = None
    priority: int = Field(1, ge=0, le=2, description="优先级")
    estimated_hours: Optional[float] = Field(None, ge=0, description="预估耗时")
    deadline: Optional[datetime] = None


class TaskItemUpdateRequest(BaseModel):
    """更新子任务请求"""
    title: Optional[str] = Field(None, max_length=256)
    description: Optional[str] = None
    priority: Optional[int] = Field(None, ge=0, le=2)
    estimated_hours: Optional[float] = Field(None, ge=0)
    deadline: Optional[datetime] = None
    status: Optional[int] = Field(None, ge=0, le=4)
    remarks: Optional[str] = None
    sort_order: Optional[int] = None


class TaskItemBatchStatusRequest(BaseModel):
    """批量修改任务状态请求"""
    task_ids: List[int] = Field(..., min_length=1, description="任务ID列表")
    status: int = Field(..., ge=0, le=4, description="目标状态")


class TaskItemResponse(BaseModel):
    """子任务响应"""
    id: int
    goal_id: int
    parent_id: Optional[int] = None
    title: str
    description: Optional[str] = None
    priority: int
    estimated_hours: Optional[float] = None
    deadline: Optional[datetime] = None
    status: int
    sort_order: int
    tool_id: Optional[int] = None
    completed_at: Optional[datetime] = None
    remarks: Optional[str] = None
    created_at: Optional[datetime] = None
    children: Optional[List["TaskItemResponse"]] = None  # 子任务嵌套

    class Config:
        from_attributes = True


# ─── 任务日志 ───

class TaskLogResponse(BaseModel):
    """任务操作日志响应"""
    id: int
    task_id: int
    action_type: str
    content: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True
