"""数据统计模块路由"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.security import get_current_user_id
from app.crud.stats import StatsCRUD
from app.db.session import get_db
from app.utils.response import success

router = APIRouter()


@router.get("/summary", summary="获取任务统计概览")
def get_task_summary(
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """获取个人任务完成率、逾期率等统计概览"""
    data = StatsCRUD.get_task_summary(db, user_id)
    return success(data=data)


@router.get("/monthly", summary="获取月度任务统计")
def get_monthly_stats(
    months: int = 6,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """获取近 N 个月的月度任务统计（完成趋势）"""
    data = StatsCRUD.get_monthly_stats(db, user_id, months=min(months, 24))
    return success(data=data)


@router.get("/goal-distribution", summary="获取目标类型分布")
def get_goal_distribution(
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """获取用户目标类型分布统计"""
    data = StatsCRUD.get_goal_distribution(db, user_id)
    return success(data=data)


@router.get("/full", summary="获取完整统计数据")
def get_full_stats(
    months: int = 6,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """获取完整统计数据（概览+月度+类型分布）"""
    summary = StatsCRUD.get_task_summary(db, user_id)
    monthly = StatsCRUD.get_monthly_stats(db, user_id, months=min(months, 24))
    distribution = StatsCRUD.get_goal_distribution(db, user_id)
    return success(
        data={
            "summary": summary,
            "monthly_stats": monthly,
            "goal_distribution": distribution,
        }
    )
