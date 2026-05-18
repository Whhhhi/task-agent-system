from fastapi import APIRouter

from app.api.v1 import user, task, agent, stats

# 总路由 - 所有 v1 接口统一挂载
api_router = APIRouter(prefix="/api/v1")

api_router.include_router(user.router, prefix="/user", tags=["用户模块"])
api_router.include_router(task.router, prefix="/task", tags=["任务管理"])
api_router.include_router(agent.router, prefix="/agent", tags=["Agent智能拆解"])
api_router.include_router(stats.router, prefix="/stats", tags=["数据统计"])
