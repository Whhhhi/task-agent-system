"""Agent 智能拆解模块路由 - AI拆解、工具调用、对话"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.security import get_current_user_id
from app.crud.agent import AgentToolCRUD
from app.crud.task import GoalCRUD
from app.db.session import get_db
from app.schemas.agent import (
    AgentChatRequest,
    AgentChatResponse,
    AgentDecomposeRequest,
    AgentDecomposeResponse,
    AgentToolResponse,
    ToolCallRequest,
    ToolCallResponse,
)
from app.models.task_item import TaskItem
from app.services.agent_service import AgentService
from app.services.tool_service import ToolService
from app.utils.response import fail, success

router = APIRouter()


@router.post("/decompose", summary="AI智能拆解目标")
async def decompose_goal(
    request: AgentDecomposeRequest,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """
    【核心功能】AI Agent 自动将用户输入的模糊大目标拆解为三级任务结构

    支持任意自然语言输入，Agent会：
    1. 分析目标内容并分类
    2. 拆解为一级主任务 → 二级子任务 → 执行步骤
    3. 自动匹配优先级、预估耗时、截止时间
    4. 根据任务类型推荐工具
    5. 参考用户历史任务上下文
    """
    try:
        result = await AgentService.decompose_goal(
            db=db,
            user_id=user_id,
            goal_title=request.goal_title,
            goal_description=request.goal_description,
            goal_type=request.goal_type,
            deadline=request.deadline,
        )
        return success(
            data=AgentDecomposeResponse(**result),
            msg="目标拆解成功",
        )
    except ValueError as e:
        return fail(msg=str(e), code=400)
    except RuntimeError as e:
        return fail(msg=str(e), code=500)


@router.post("/chat", summary="与Agent对话优化任务")
async def chat_with_agent(
    request: AgentChatRequest,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """
    与 Agent 对话，基于已有任务目标进一步讨论和优化

    可用于：
    - 对拆解结果提出调整意见
    - 要求进一步细化某个子任务
    - 咨询任务执行建议
    """
    try:
        result = await AgentService.chat_with_agent(
            db=db,
            user_id=user_id,
            goal_id=request.goal_id,
            user_message=request.user_message,
        )
        return success(data=AgentChatResponse(**result), msg="回复成功")
    except ValueError as e:
        return fail(msg=str(e), code=400)
    except RuntimeError as e:
        return fail(msg=str(e), code=500)


@router.post("/tool/call", summary="执行工具调用")
async def call_tool(
    request: ToolCallRequest,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """
    调用内置工具执行任务

    可用工具：
    - 学习大纲生成
    - 资料检索提示词生成
    - 周报生成
    - 任务复盘模板
    - 时间规划模板
    - 错题整理模板
    """
    try:
        # 校验任务归属
        task = db.query(TaskItem).filter(TaskItem.id == request.task_id).first()
        if task is None:
            return fail(msg="任务不存在", code=404)
        goal = GoalCRUD.get_by_id(db, task.goal_id)
        if goal is None or goal.user_id != user_id:
            return fail(msg="无权操作此任务", code=403)

        result = await ToolService.execute_tool(
            db=db,
            tool_id=request.tool_id,
            task_id=request.task_id,
            params=request.params,
        )

        # 获取工具名称
        tool = AgentToolCRUD.get_by_id(db, request.tool_id)
        tool_name = tool.name if tool else "未知工具"

        return success(
            data=ToolCallResponse(
                tool_name=tool_name,
                task_id=request.task_id,
                result=result,
            ),
            msg="工具调用成功",
        )
    except ValueError as e:
        return fail(msg=str(e), code=400)
    except RuntimeError as e:
        return fail(msg=str(e), code=500)


@router.get("/tools", summary="获取工具列表")
def list_tools(
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """获取所有可用的内置工具列表"""
    tools = AgentToolCRUD.get_all(db)
    return success(
        data=[AgentToolResponse.model_validate(t) for t in tools]
    )


@router.post("/tools/seed", summary="初始化种子工具数据")
def seed_tools(
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """初始化/重置内置工具库数据（仅首次部署时使用）"""
    tools = AgentToolCRUD.seed_default_tools(db)
    return success(
        data=[AgentToolResponse.model_validate(t) for t in tools],
        msg=f"已初始化 {len(tools)} 个内置工具",
    )
