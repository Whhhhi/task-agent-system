"""任务 CRUD 操作 - 总目标和子任务"""
from datetime import datetime
from typing import List, Optional, Tuple

from sqlalchemy import and_, desc, func
from sqlalchemy.orm import Session, joinedload

from app.models.task_goal import TaskGoal
from app.models.task_item import TaskItem
from app.models.task_log import TaskLog


class GoalCRUD:
    """总目标数据库操作"""

    @staticmethod
    def get_by_id(db: Session, goal_id: int) -> Optional[TaskGoal]:
        return db.query(TaskGoal).filter(TaskGoal.id == goal_id).first()

    @staticmethod
    def get_by_user_id(
        db: Session, user_id: int, page: int = 1, page_size: int = 20
    ) -> Tuple[List[TaskGoal], int]:
        query = db.query(TaskGoal).filter(TaskGoal.user_id == user_id)
        total = query.count()
        items = (
            query.order_by(desc(TaskGoal.created_at))
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )
        return items, total

    @staticmethod
    def create(
        db: Session,
        user_id: int,
        title: str,
        description: Optional[str] = None,
        goal_type: Optional[str] = None,
        deadline: Optional[datetime] = None,
    ) -> TaskGoal:
        goal = TaskGoal(
            user_id=user_id,
            title=title,
            description=description,
            goal_type=goal_type,
            deadline=deadline,
        )
        db.add(goal)
        db.commit()
        db.refresh(goal)
        return goal

    @staticmethod
    def update(
        db: Session,
        goal_id: int,
        **kwargs,
    ) -> Optional[TaskGoal]:
        goal = GoalCRUD.get_by_id(db, goal_id)
        if goal is None:
            return None
        for key, value in kwargs.items():
            if value is not None and hasattr(goal, key):
                setattr(goal, key, value)
        db.commit()
        db.refresh(goal)
        return goal

    @staticmethod
    def delete(db: Session, goal_id: int) -> bool:
        goal = GoalCRUD.get_by_id(db, goal_id)
        if goal is None:
            return False
        db.delete(goal)
        db.commit()
        return True

    @staticmethod
    def recalc_progress(db: Session, goal_id: int) -> float:
        """重新计算目标整体完成进度"""
        total = db.query(func.count(TaskItem.id)).filter(
            TaskItem.goal_id == goal_id
        ).scalar() or 0
        if total == 0:
            done = 0
        else:
            done = db.query(func.count(TaskItem.id)).filter(
                and_(
                    TaskItem.goal_id == goal_id,
                    TaskItem.status == 2,  # 已完成
                )
            ).scalar() or 0
            progress = round((done / total) * 100, 1)
        goal = GoalCRUD.get_by_id(db, goal_id)
        if goal:
            goal.progress = progress
            # 如果进度100%且状态未标记完成，自动标记
            if progress >= 100.0 and goal.status == 0:
                goal.status = 1  # 已完成
            db.commit()
        return progress


class TaskItemCRUD:
    """子任务数据库操作"""

    STATUS_MAP = {
        0: "待执行",
        1: "进行中",
        2: "已完成",
        3: "延期",
        4: "作废",
    }

    @staticmethod
    def get_by_id(db: Session, task_id: int) -> Optional[TaskItem]:
        return db.query(TaskItem).filter(TaskItem.id == task_id).first()

    @staticmethod
    def get_by_goal_id(
        db: Session, goal_id: int, parent_id: Optional[int] = None
    ) -> List[TaskItem]:
        """获取目标下的所有子任务，可选指定父任务ID"""
        query = db.query(TaskItem).filter(
            TaskItem.goal_id == goal_id,
        )
        if parent_id is not None:
            query = query.filter(TaskItem.parent_id == parent_id)
        else:
            query = query.filter(TaskItem.parent_id.is_(None))
        return query.order_by(TaskItem.sort_order, TaskItem.id).all()

    @staticmethod
    def get_all_by_goal_id(db: Session, goal_id: int) -> List[TaskItem]:
        """获取目标下所有任务（平铺，不考虑层级）"""
        return (
            db.query(TaskItem)
            .filter(TaskItem.goal_id == goal_id)
            .order_by(TaskItem.sort_order, TaskItem.id)
            .all()
        )

    @staticmethod
    def create(
        db: Session,
        goal_id: int,
        title: str,
        parent_id: Optional[int] = None,
        description: Optional[str] = None,
        priority: int = 1,
        estimated_hours: Optional[float] = None,
        deadline: Optional[datetime] = None,
        tool_id: Optional[int] = None,
        sort_order: int = 0,
    ) -> TaskItem:
        task = TaskItem(
            goal_id=goal_id,
            parent_id=parent_id,
            title=title,
            description=description,
            priority=priority,
            estimated_hours=estimated_hours,
            deadline=deadline,
            tool_id=tool_id,
            sort_order=sort_order,
        )
        db.add(task)
        db.commit()
        db.refresh(task)
        # 记录创建日志
        TaskLogCRUD.create(db, task.id, "create", f"创建任务: {title}")
        return task

    @staticmethod
    def update(db: Session, task_id: int, **kwargs) -> Optional[TaskItem]:
        task = TaskItemCRUD.get_by_id(db, task_id)
        if task is None:
            return None
        # 捕获状态变更以记录日志
        old_status = task.status
        for key, value in kwargs.items():
            if value is not None and hasattr(task, key):
                setattr(task, key, value)
        # 如果状态变更，记录日志
        if "status" in kwargs and kwargs["status"] is not None and kwargs["status"] != old_status:
            # 如果标记为已完成，记录完成时间
            if kwargs["status"] == 2:
                task.completed_at = datetime.now()
            TaskLogCRUD.create(
                db,
                task_id,
                "status_change",
                f"状态变更: {TaskItemCRUD.STATUS_MAP.get(old_status, '未知')} -> "
                f"{TaskItemCRUD.STATUS_MAP.get(kwargs['status'], '未知')}",
            )
        db.commit()
        db.refresh(task)
        # 重新计算所属目标的进度
        GoalCRUD.recalc_progress(db, task.goal_id)
        return task

    @staticmethod
    def delete(db: Session, task_id: int) -> bool:
        task = TaskItemCRUD.get_by_id(db, task_id)
        if task is None:
            return False
        goal_id = task.goal_id
        db.delete(task)
        db.commit()
        GoalCRUD.recalc_progress(db, goal_id)
        return True

    @staticmethod
    def batch_update_status(db: Session, task_ids: List[int], status: int) -> int:
        """批量修改任务状态，返回影响行数"""
        now = datetime.now()
        count = 0
        for task_id in task_ids:
            task = TaskItemCRUD.get_by_id(db, task_id)
            if task is None:
                continue
            old_status = task.status
            task.status = status
            if status == 2:
                task.completed_at = now
            TaskLogCRUD.create(
                db,
                task_id,
                "status_change",
                f"批量状态变更: {TaskItemCRUD.STATUS_MAP.get(old_status, '未知')} -> "
                f"{TaskItemCRUD.STATUS_MAP.get(status, '未知')}",
            )
            count += 1
        db.commit()
        # 重新计算相关目标的进度
        goal_ids = set(
            db.query(TaskItem.goal_id).filter(TaskItem.id.in_(task_ids)).all()
        )
        for (gid,) in goal_ids:
            GoalCRUD.recalc_progress(db, gid)
        return count


class TaskLogCRUD:
    """任务日志数据库操作"""

    @staticmethod
    def create(
        db: Session, task_id: int, action_type: str, content: str
    ) -> TaskLog:
        log = TaskLog(
            task_id=task_id,
            action_type=action_type,
            content=content,
        )
        db.add(log)
        db.commit()
        return log

    @staticmethod
    def get_by_task_id(
        db: Session, task_id: int, page: int = 1, page_size: int = 20
    ) -> Tuple[List[TaskLog], int]:
        query = (
            db.query(TaskLog)
            .filter(TaskLog.task_id == task_id)
            .order_by(desc(TaskLog.created_at))
        )
        total = query.count()
        items = query.offset((page - 1) * page_size).limit(page_size).all()
        return items, total
