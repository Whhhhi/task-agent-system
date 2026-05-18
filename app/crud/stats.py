"""数据统计 CRUD 操作"""
from datetime import datetime, timedelta
from typing import Any, Dict, List, Tuple

from sqlalchemy import and_, extract, func
from sqlalchemy.orm import Session

from app.models.task_goal import TaskGoal
from app.models.task_item import TaskItem


class StatsCRUD:
    """统计查询操作类"""

    @staticmethod
    def get_task_summary(db: Session, user_id: int) -> Dict[str, Any]:
        """获取用户任务概览统计数据"""
        # 总目标数
        total_goals = (
            db.query(func.count(TaskGoal.id))
            .filter(TaskGoal.user_id == user_id)
            .scalar() or 0
        )
        # 已完成目标数
        completed_goals = (
            db.query(func.count(TaskGoal.id))
            .filter(
                and_(TaskGoal.user_id == user_id, TaskGoal.status == 1)
            )
            .scalar() or 0
        )
        # 进行中目标数
        active_goals = (
            db.query(func.count(TaskGoal.id))
            .filter(
                and_(TaskGoal.user_id == user_id, TaskGoal.status == 0)
            )
            .scalar() or 0
        )

        # 统计所有子任务（通过目标关联用户）
        total_tasks = (
            db.query(func.count(TaskItem.id))
            .join(TaskGoal, TaskItem.goal_id == TaskGoal.id)
            .filter(TaskGoal.user_id == user_id)
            .scalar() or 0
        )
        # 各状态任务数
        completed_tasks = (
            db.query(func.count(TaskItem.id))
            .join(TaskGoal, TaskItem.goal_id == TaskGoal.id)
            .filter(
                and_(TaskGoal.user_id == user_id, TaskItem.status == 2)
            )
            .scalar() or 0
        )
        pending_tasks = (
            db.query(func.count(TaskItem.id))
            .join(TaskGoal, TaskItem.goal_id == TaskGoal.id)
            .filter(
                and_(TaskGoal.user_id == user_id, TaskItem.status == 0)
            )
            .scalar() or 0
        )
        in_progress_tasks = (
            db.query(func.count(TaskItem.id))
            .join(TaskGoal, TaskItem.goal_id == TaskGoal.id)
            .filter(
                and_(TaskGoal.user_id == user_id, TaskItem.status == 1)
            )
            .scalar() or 0
        )
        # 逾期任务（截止时间已过且未完成）
        now = datetime.now()
        overdue_tasks = (
            db.query(func.count(TaskItem.id))
            .join(TaskGoal, TaskItem.goal_id == TaskGoal.id)
            .filter(
                and_(
                    TaskGoal.user_id == user_id,
                    TaskItem.deadline.isnot(None),
                    TaskItem.deadline < now,
                    TaskItem.status.notin_([2, 4]),  # 未完成且未作废
                )
            )
            .scalar() or 0
        )
        cancelled_tasks = (
            db.query(func.count(TaskItem.id))
            .join(TaskGoal, TaskItem.goal_id == TaskGoal.id)
            .filter(
                and_(TaskGoal.user_id == user_id, TaskItem.status == 4)
            )
            .scalar() or 0
        )

        # 计算比率
        completion_rate = round(
            (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0, 1
        )
        overdue_rate = round(
            (overdue_tasks / total_tasks * 100) if total_tasks > 0 else 0, 1
        )

        return {
            "total_goals": total_goals,
            "completed_goals": completed_goals,
            "active_goals": active_goals,
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "pending_tasks": pending_tasks,
            "in_progress_tasks": in_progress_tasks,
            "overdue_tasks": overdue_tasks,
            "cancelled_tasks": cancelled_tasks,
            "completion_rate": completion_rate,
            "overdue_rate": overdue_rate,
        }

    @staticmethod
    def get_monthly_stats(
        db: Session, user_id: int, months: int = 6
    ) -> List[Dict[str, Any]]:
        """获取近N个月的月度任务统计"""
        results = []
        now = datetime.now()
        for i in range(months - 1, -1, -1):
            # 计算月份起始和结束
            month_start = datetime(now.year, now.month, 1) - timedelta(days=30 * i)
            month_start = month_start.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            if month_start.month == 12:
                month_end = datetime(month_start.year + 1, 1, 1)
            else:
                month_end = datetime(month_start.year, month_start.month + 1, 1)

            # 当月创建的任务数
            created = (
                db.query(func.count(TaskItem.id))
                .join(TaskGoal, TaskItem.goal_id == TaskGoal.id)
                .filter(
                    and_(
                        TaskGoal.user_id == user_id,
                        TaskItem.created_at >= month_start,
                        TaskItem.created_at < month_end,
                    )
                )
                .scalar() or 0
            )
            # 当月完成的任务数
            completed = (
                db.query(func.count(TaskItem.id))
                .join(TaskGoal, TaskItem.goal_id == TaskGoal.id)
                .filter(
                    and_(
                        TaskGoal.user_id == user_id,
                        TaskItem.completed_at >= month_start,
                        TaskItem.completed_at < month_end,
                        TaskItem.status == 2,
                    )
                )
                .scalar() or 0
            )
            # 当月应处理的总任务数（截止时间在当月或创建时间在当月的）
            total = (
                db.query(func.count(TaskItem.id))
                .join(TaskGoal, TaskItem.goal_id == TaskGoal.id)
                .filter(
                    and_(
                        TaskGoal.user_id == user_id,
                        TaskItem.created_at < month_end,
                        TaskItem.status != 4,
                    )
                )
                .scalar() or 0
            )

            results.append({
                "month": month_start.strftime("%Y-%m"),
                "total": total,
                "completed": completed,
                "created": created,
            })
        return results

    @staticmethod
    def get_goal_distribution(db: Session, user_id: int) -> List[Dict[str, Any]]:
        """获取用户目标类型分布"""
        results = (
            db.query(
                TaskGoal.goal_type,
                func.count(TaskGoal.id).label("count"),
            )
            .filter(
                and_(
                    TaskGoal.user_id == user_id,
                    TaskGoal.goal_type.isnot(None),
                )
            )
            .group_by(TaskGoal.goal_type)
            .all()
        )
        return [
            {"goal_type": row.goal_type, "count": row.count}
            for row in results
        ]
