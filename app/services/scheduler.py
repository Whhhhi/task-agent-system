"""
定时调度服务 - 基于 APScheduler
功能：
1. 任务截止提醒：检查即将到期的任务并记录
2. 每日任务复盘提醒：汇总每日任务完成情况
3. 逾期任务标记：自动标记已逾期未完成的任务
"""
from datetime import datetime, timedelta

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from loguru import logger
from sqlalchemy import and_
from sqlalchemy.orm import Session

from app.config import settings
from app.db.session import SessionLocal
from app.models.task_item import TaskItem
from app.models.task_goal import TaskGoal
from app.crud.task import TaskItemCRUD


class SchedulerService:
    """APScheduler 调度服务管理器"""

    def __init__(self):
        self.scheduler = BackgroundScheduler(
            timezone=settings.SCHEDULER_TIMEZONE,
        )
        self._initialized = False

    def start(self) -> None:
        """启动所有定时任务"""
        if self._initialized:
            logger.warning("调度器已启动，跳过重复初始化")
            return

        # ── 定时检查逾期任务（每30分钟） ──
        self.scheduler.add_job(
            self.check_overdue_tasks,
            trigger=IntervalTrigger(
                minutes=settings.SCHEDULER_CHECK_INTERVAL_MINUTES
            ),
            id="check_overdue_tasks",
            name="检查并标记逾期任务",
            replace_existing=True,
        )

        # ── 每日任务状态汇总（每天早上 9:00） ──
        self.scheduler.add_job(
            self.daily_task_summary,
            trigger=CronTrigger(hour=9, minute=0),
            id="daily_task_summary",
            name="每日任务状态汇总",
            replace_existing=True,
        )

        # ── 每日截止提醒（每天早上 8:00 和晚上 20:00） ──
        self.scheduler.add_job(
            self.deadline_reminder,
            trigger=CronTrigger(hour=8, minute=0),
            id="deadline_reminder_morning",
            name="早上截止提醒",
            replace_existing=True,
        )
        self.scheduler.add_job(
            self.deadline_reminder,
            trigger=CronTrigger(hour=20, minute=0),
            id="deadline_reminder_evening",
            name="晚上截止提醒",
            replace_existing=True,
        )

        self.scheduler.start()
        self._initialized = True
        logger.info("APScheduler 定时调度器已启动")

    def stop(self) -> None:
        """停止调度器"""
        if self.scheduler.running:
            self.scheduler.shutdown(wait=False)
            logger.info("APScheduler 定时调度器已停止")

    # ─── 定时任务回调方法 ───

    def check_overdue_tasks(self) -> None:
        """
        检查并标记逾期任务
        将截止时间已过且状态为 待执行/进行中 的任务标记为 延期(3)
        """
        logger.info("开始检查逾期任务...")
        db: Session = SessionLocal()
        try:
            now = datetime.now()
            overdue_tasks = (
                db.query(TaskItem)
                .filter(
                    and_(
                        TaskItem.deadline.isnot(None),
                        TaskItem.deadline < now,
                        TaskItem.status.in_([0, 1]),  # 待执行或进行中
                    )
                )
                .all()
            )

            for task in overdue_tasks:
                old_status = task.status
                task.status = 3  # 标记为延期
                logger.info(
                    f"任务逾期标记 | task_id:{task.id} | "
                    f"'{task.title}' | 状态: {old_status} -> 3(延期)"
                )

            if overdue_tasks:
                db.commit()
                logger.info(f"共标记 {len(overdue_tasks)} 个逾期任务")
            else:
                logger.info("无逾期任务需要标记")
        except Exception as e:
            logger.error(f"检查逾期任务异常: {e}")
            db.rollback()
        finally:
            db.close()

    def deadline_reminder(self) -> None:
        """
        截止时间提醒
        检查未来24小时内到期的任务，记录提醒日志
        """
        logger.info("执行截止时间提醒检查...")
        db: Session = SessionLocal()
        try:
            now = datetime.now()
            tomorrow = now + timedelta(hours=24)

            coming_tasks = (
                db.query(TaskItem)
                .join(TaskGoal, TaskItem.goal_id == TaskGoal.id)
                .filter(
                    and_(
                        TaskItem.deadline.isnot(None),
                        TaskItem.deadline >= now,
                        TaskItem.deadline <= tomorrow,
                        TaskItem.status.in_([0, 1]),
                    )
                )
                .all()
            )

            if coming_tasks:
                logger.info(
                    f"📌 未来24小时内有 {len(coming_tasks)} 个任务即将到期："
                )
                for task in coming_tasks:
                    hours_left = (task.deadline - now).total_seconds() / 3600
                    logger.info(
                        f"  任务 '{task.title}' 将于 "
                        f"{task.deadline.strftime('%Y-%m-%d %H:%M')} 到期，"
                        f"剩余约 {hours_left:.1f} 小时"
                    )
            else:
                logger.info("未来24小时内无即将到期的任务")
        except Exception as e:
            logger.error(f"截止提醒异常: {e}")
        finally:
            db.close()

    def daily_task_summary(self) -> None:
        """
        每日任务状态汇总
        汇总所有用户的昨日任务完成情况
        """
        logger.info("生成每日任务汇总...")
        db: Session = SessionLocal()
        try:
            now = datetime.now()
            yesterday_start = now.replace(
                hour=0, minute=0, second=0, microsecond=0
            ) - timedelta(days=1)
            yesterday_end = now.replace(
                hour=0, minute=0, second=0, microsecond=0
            )

            # 昨日完成任务数
            completed_count = (
                db.query(TaskItem)
                .filter(
                    and_(
                        TaskItem.completed_at >= yesterday_start,
                        TaskItem.completed_at < yesterday_end,
                        TaskItem.status == 2,
                    )
                )
                .count()
            )

            # 昨日创建任务数
            created_count = (
                db.query(TaskItem)
                .filter(
                    and_(
                        TaskItem.created_at >= yesterday_start,
                        TaskItem.created_at < yesterday_end,
                    )
                )
                .count()
            )

            logger.info(
                f"📊 每日任务汇总 | 日期: {yesterday_start.date()} | "
                f"完成: {completed_count} | 新增: {created_count}"
            )
        except Exception as e:
            logger.error(f"每日汇总异常: {e}")
        finally:
            db.close()
