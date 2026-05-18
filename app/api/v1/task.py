"""任务管理模块路由 - 总目标与子任务的增删改查"""
from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.security import get_current_user_id
from app.crud.task import GoalCRUD, TaskItemCRUD, TaskLogCRUD
from app.db.session import get_db
from app.schemas.task import (
    GoalCreateRequest,
    GoalResponse,
    GoalUpdateRequest,
    TaskItemBatchStatusRequest,
    TaskItemCreateRequest,
    TaskItemResponse,
    TaskItemUpdateRequest,
    TaskLogResponse,
)
from app.utils.response import fail, success

router = APIRouter()


# ════════════════════════════════════════
# 总目标接口
# ════════════════════════════════════════

@router.post("/goal", summary="创建总目标")
def create_goal(
    request: GoalCreateRequest,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """手动创建总目标"""
    goal = GoalCRUD.create(
        db=db,
        user_id=user_id,
        title=request.title,
        description=request.description,
        goal_type=request.goal_type,
        deadline=request.deadline,
    )
    return success(data=GoalResponse.model_validate(goal), msg="目标创建成功")


@router.get("/goal/list", summary="获取总目标列表")
def list_goals(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """获取当前用户的所有总目标列表"""
    items, total = GoalCRUD.get_by_user_id(db, user_id, page, page_size)
    return success(
        data={
            "items": [GoalResponse.model_validate(g) for g in items],
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size,
        }
    )


@router.get("/goal/{goal_id}", summary="获取总目标详情")
def get_goal(
    goal_id: int,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """获取指定总目标的详细信息"""
    goal = GoalCRUD.get_by_id(db, goal_id)
    if goal is None:
        return fail(msg="目标不存在", code=404)
    if goal.user_id != user_id:
        return fail(msg="无权访问", code=403)
    return success(data=GoalResponse.model_validate(goal))


@router.put("/goal/{goal_id}", summary="更新总目标")
def update_goal(
    goal_id: int,
    request: GoalUpdateRequest,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """更新总目标的字段信息"""
    goal = GoalCRUD.get_by_id(db, goal_id)
    if goal is None:
        return fail(msg="目标不存在", code=404)
    if goal.user_id != user_id:
        return fail(msg="无权操作", code=403)

    update_data = request.model_dump(exclude_none=True)
    if not update_data:
        return fail(msg="请提供要更新的字段", code=400)

    goal = GoalCRUD.update(db, goal_id, **update_data)
    return success(data=GoalResponse.model_validate(goal), msg="更新成功")


@router.delete("/goal/{goal_id}", summary="删除总目标")
def delete_goal(
    goal_id: int,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """删除指定的总目标及其所有子任务"""
    goal = GoalCRUD.get_by_id(db, goal_id)
    if goal is None:
        return fail(msg="目标不存在", code=404)
    if goal.user_id != user_id:
        return fail(msg="无权操作", code=403)

    GoalCRUD.delete(db, goal_id)
    return success(msg="目标已删除")


# ════════════════════════════════════════
# 子任务接口
# ════════════════════════════════════════

@router.post("/item", summary="创建子任务")
def create_task_item(
    request: TaskItemCreateRequest,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """手动创建子任务（支持多级嵌套）"""
    # 校验目标归属
    goal = GoalCRUD.get_by_id(db, request.goal_id)
    if goal is None:
        return fail(msg="目标不存在", code=404)
    if goal.user_id != user_id:
        return fail(msg="无权操作此目标", code=403)

    task = TaskItemCRUD.create(
        db=db,
        goal_id=request.goal_id,
        parent_id=request.parent_id,
        title=request.title,
        description=request.description,
        priority=request.priority,
        estimated_hours=request.estimated_hours,
        deadline=request.deadline,
    )
    return success(data=TaskItemResponse.model_validate(task), msg="任务创建成功")


@router.get("/item/list/{goal_id}", summary="获取目标下的任务树")
def list_task_items(
    goal_id: int,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """获取指定目标下的完整任务树（含层级结构）"""
    goal = GoalCRUD.get_by_id(db, goal_id)
    if goal is None:
        return fail(msg="目标不存在", code=404)
    if goal.user_id != user_id:
        return fail(msg="无权访问", code=403)

    # 获取所有一级任务
    top_level = TaskItemCRUD.get_by_goal_id(db, goal_id, parent_id=None)
    task_tree = []
    for item in top_level:
        task_tree.append(_build_task_tree(db, item))

    return success(data=task_tree)


@router.get("/item/{task_id}", summary="获取子任务详情")
def get_task_item(
    task_id: int,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """获取指定子任务的详细信息"""
    task = TaskItemCRUD.get_by_id(db, task_id)
    if task is None:
        return fail(msg="任务不存在", code=404)
    # 校验归属
    goal = GoalCRUD.get_by_id(db, task.goal_id)
    if goal is None or goal.user_id != user_id:
        return fail(msg="无权访问", code=403)

    return success(data=TaskItemResponse.model_validate(task))


@router.put("/item/{task_id}", summary="更新子任务")
def update_task_item(
    task_id: int,
    request: TaskItemUpdateRequest,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """更新子任务信息（含状态变更）"""
    task = TaskItemCRUD.get_by_id(db, task_id)
    if task is None:
        return fail(msg="任务不存在", code=404)
    goal = GoalCRUD.get_by_id(db, task.goal_id)
    if goal is None or goal.user_id != user_id:
        return fail(msg="无权操作", code=403)

    update_data = request.model_dump(exclude_none=True)
    if not update_data:
        return fail(msg="请提供要更新的字段", code=400)

    task = TaskItemCRUD.update(db, task_id, **update_data)
    return success(data=TaskItemResponse.model_validate(task), msg="更新成功")


@router.delete("/item/{task_id}", summary="删除子任务")
def delete_task_item(
    task_id: int,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """删除指定的子任务"""
    task = TaskItemCRUD.get_by_id(db, task_id)
    if task is None:
        return fail(msg="任务不存在", code=404)
    goal = GoalCRUD.get_by_id(db, task.goal_id)
    if goal is None or goal.user_id != user_id:
        return fail(msg="无权操作", code=403)

    TaskItemCRUD.delete(db, task_id)
    return success(msg="任务已删除")


@router.put("/item/batch-status", summary="批量修改任务状态")
def batch_update_status(
    request: TaskItemBatchStatusRequest,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """批量修改多个子任务的状态"""
    # 校验所有任务归属
    for tid in request.task_ids:
        task = TaskItemCRUD.get_by_id(db, tid)
        if task is None:
            return fail(msg=f"任务不存在 (id={tid})", code=404)
        goal = GoalCRUD.get_by_id(db, task.goal_id)
        if goal is None or goal.user_id != user_id:
            return fail(msg=f"无权操作任务 (id={tid})", code=403)

    count = TaskItemCRUD.batch_update_status(db, request.task_ids, request.status)
    return success(data={"affected_count": count}, msg=f"已更新 {count} 个任务状态")


# ════════════════════════════════════════
# 任务日志接口
# ════════════════════════════════════════

@router.get("/log/{task_id}", summary="获取任务操作日志")
def list_task_logs(
    task_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """获取指定任务的操作日志"""
    task = TaskItemCRUD.get_by_id(db, task_id)
    if task is None:
        return fail(msg="任务不存在", code=404)
    goal = GoalCRUD.get_by_id(db, task.goal_id)
    if goal is None or goal.user_id != user_id:
        return fail(msg="无权访问", code=403)

    items, total = TaskLogCRUD.get_by_task_id(db, task_id, page, page_size)
    return success(
        data={
            "items": [TaskLogResponse.model_validate(log) for log in items],
            "total": total,
            "page": page,
            "page_size": page_size,
        }
    )


# ════════════════════════════════════════
# 辅助函数
# ════════════════════════════════════════

def _build_task_tree(db: Session, item) -> dict:
    """递归构建任务树"""
    children = TaskItemCRUD.get_by_goal_id(db, item.goal_id, parent_id=item.id)
    return {
        "id": item.id,
        "goal_id": item.goal_id,
        "parent_id": item.parent_id,
        "title": item.title,
        "description": item.description,
        "priority": item.priority,
        "estimated_hours": item.estimated_hours,
        "deadline": item.deadline.isoformat() if item.deadline else None,
        "status": item.status,
        "sort_order": item.sort_order,
        "tool_id": item.tool_id,
        "completed_at": item.completed_at.isoformat() if item.completed_at else None,
        "remarks": item.remarks,
        "created_at": item.created_at.isoformat() if item.created_at else None,
        "children": [_build_task_tree(db, child) for child in children],
    }
