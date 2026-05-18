"""数据统计模块 Pydantic 模型"""
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class TaskStatsSummary(BaseModel):
    """任务统计概览"""
    total_goals: int = 0
    completed_goals: int = 0
    active_goals: int = 0
    total_tasks: int = 0
    completed_tasks: int = 0
    pending_tasks: int = 0
    in_progress_tasks: int = 0
    overdue_tasks: int = 0
    cancelled_tasks: int = 0
    completion_rate: float = 0.0       # 完成率（百分比）
    overdue_rate: float = 0.0           # 逾期率（百分比）


class MonthlyTaskStats(BaseModel):
    """月度任务统计"""
    month: str  # 格式: "2024-01"
    total: int
    completed: int
    created: int


class GoalTypeDistribution(BaseModel):
    """目标类型分布"""
    goal_type: str
    count: int


class StatsResponse(BaseModel):
    """完整统计数据响应"""
    summary: TaskStatsSummary
    monthly_stats: List[MonthlyTaskStats]
    goal_distribution: List[GoalTypeDistribution]
