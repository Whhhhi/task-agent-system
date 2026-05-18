"""
Agent 智能拆解服务 - 系统的核心亮点

核心功能：
1. 接收用户输入的模糊大目标
2. 调用大模型智能拆解为三级任务结构
3. 自动匹配工具
4. 考虑用户历史任务上下文
5. 将拆解结果持久化到数据库
"""
import json
from datetime import datetime
from typing import Any, Dict, List, Optional

from loguru import logger
from sqlalchemy.orm import Session

from app.crud.task import GoalCRUD, TaskItemCRUD
from app.crud.agent import AgentToolCRUD
from app.models.agent_tool import AgentTool
from app.services.llm_service import llm_service

# Agent 拆解任务的系统提示词
DECOMPOSE_SYSTEM_PROMPT = """你是一个专业的任务拆解AI助手，擅长将模糊的大目标拆解为结构清晰、可执行的层级任务。

## 你的核心能力
- 将用户的宏观目标拆解为「一级主任务 → 二级子任务 → 细分执行步骤」的三级结构
- 为每个任务自动匹配优先级、预估耗时、建议截止时间、任务标签、执行难度
- 根据任务类型推荐最合适的工具

## 输出格式要求
你必须以 **JSON 格式** 输出，格式如下：
```json
{
  "title": "目标标题",
  "description": "目标详细描述",
  "goal_type": "目标类型（学习/工作/备考/项目开发/求职规划/其他）",
  "tasks": [
    {
      "title": "一级主任务1",
      "description": "任务描述",
      "priority": 1,
      "estimated_hours": 8.0,
      "deadline": "2024-12-31",
      "difficulty": "中等",
      "tags": ["标签1", "标签2"],
      "tool_name": null,
      "children": [
        {
          "title": "二级子任务1.1",
          "description": "子任务描述",
          "priority": 2,
          "estimated_hours": 3.0,
          "deadline": "2024-12-20",
          "difficulty": "简单",
          "tags": ["标签1"],
          "tool_name": "学习大纲生成",
          "children": [
            {
              "title": "执行步骤1.1.1",
              "description": "具体执行步骤",
              "priority": 2,
              "estimated_hours": 1.0,
              "deadline": "2024-12-15",
              "difficulty": "简单",
              "tags": ["标签1"],
              "tool_name": null,
              "children": []
            }
          ]
        }
      ]
    }
  ]
}
```

## 任务拆解原则
1. **可执行性**：每个任务必须是一个具体的、可执行的动作
2. **粒度适中**：一级主任务 3-8 个，每个主任务下 2-5 个子任务
3. **时间合理**：预估耗时须切合实际，避免过于乐观
4. **优先级合理**：高(2) 中(1) 低(0)，基础任务优先、核心任务高优
5. **工具匹配**：根据任务类型推荐工具，可用的工具有：学习大纲生成、资料检索提示词生成、周报生成、任务复盘模板、时间规划模板、错题整理模板

## 优先级规则
- 2 = 高优先级：关键的、基础的、影响后续的任务
- 1 = 中优先级：重要的但不紧急的任务
- 0 = 低优先级：锦上添花、非关键路径的任务

请严格按照 JSON 格式输出，不要包含其他无关内容。"""


# 带上下文记忆的系统提示词增强
CONTEXT_AWARE_PROMPT_SUFFIX = """

## 用户历史上下文
你正在为以下用户拆解任务，请参考 TA 的历史任务记录，使拆解结果更贴合用户的习惯和风格：
- 避免重复规划用户已完成或已规划的内容
- 参考用户历史任务的时间估算习惯
- 考虑用户过去的目标类型偏好

用户历史任务摘要：
{history_context}
"""


class AgentService:
    """Agent 智能拆解服务"""

    # 工具名称映射，用于自动匹配
    TOOL_MAP = {
        "学习": "学习大纲生成",
        "资料": "资料检索提示词生成",
        "检索": "资料检索提示词生成",
        "搜索": "资料检索提示词生成",
        "周报": "周报生成",
        "复盘": "任务复盘模板",
        "总结": "任务复盘模板",
        "时间": "时间规划模板",
        "规划": "时间规划模板",
        "日程": "时间规划模板",
        "错题": "错题整理模板",
        "考试": "错题整理模板",
    }

    @staticmethod
    def _build_history_context(db: Session, user_id: int, max_goals: int = 5) -> str:
        """
        构建用户历史任务上下文摘要
        用于让 Agent 了解用户的历史习惯，避免重复规划
        """
        from app.models.task_goal import TaskGoal
        from app.models.task_item import TaskItem

        goals = (
            db.query(TaskGoal)
            .filter(TaskGoal.user_id == user_id)
            .order_by(TaskGoal.created_at.desc())
            .limit(max_goals)
            .all()
        )

        if not goals:
            return "（暂无历史任务记录）"

        lines = []
        for g in goals:
            task_count = (
                db.query(TaskItem)
                .filter(TaskItem.goal_id == g.id)
                .count()
            )
            lines.append(
                f"- 目标: {g.title} (类型: {g.goal_type or '未分类'}, "
                f"进度: {g.progress}%, 子任务数: {task_count})"
            )
        return "\n".join(lines)

    @staticmethod
    async def decompose_goal(
        db: Session,
        user_id: int,
        goal_title: str,
        goal_description: Optional[str] = None,
        goal_type: Optional[str] = None,
        deadline: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        核心方法：将用户目标通过 AI Agent 拆解为结构化任务树

        Args:
            db: 数据库会话
            user_id: 用户ID
            goal_title: 目标标题
            goal_description: 目标描述
            goal_type: 目标类型
            deadline: 截止时间

        Returns:
            包含 goal_id 和任务树的字典
        """
        logger.info(f"Agent开始拆解目标 | 用户:{user_id} | 目标:{goal_title}")

        # ── 第1步：构建提示词上下文 ──
        history = AgentService._build_history_context(db, user_id)
        system_prompt = DECOMPOSE_SYSTEM_PROMPT + CONTEXT_AWARE_PROMPT_SUFFIX.format(
            history_context=history
        )

        # ── 第2步：构建用户消息 ──
        deadline_str = f"\n期望截止时间: {deadline}" if deadline else ""
        user_message = (
            f"请帮我拆解以下目标：\n"
            f"目标标题: {goal_title}\n"
            f"目标描述: {goal_description or '无'}"
            f"{deadline_str}\n\n"
            f"请输出完整的JSON任务拆解结果。"
        )

        # ── 第3步：调用大模型 ──
        raw_result = await llm_service.chat_completion(
            messages=[{"role": "user", "content": user_message}],
            system_prompt=system_prompt,
            response_format={"type": "json_object"},
        )

        # ── 第4步：解析 JSON 结果 ──
        try:
            parsed = json.loads(raw_result)
        except json.JSONDecodeError as e:
            logger.error(f"AI返回结果JSON解析失败: {e}\n原始内容: {raw_result}")
            raise ValueError("AI返回格式异常，请重试")

        # ── 第5步：保存总目标到数据库 ──
        parsed_deadline = None
        if deadline:
            try:
                parsed_deadline = datetime.strptime(deadline, "%Y-%m-%d")
            except ValueError:
                pass

        goal = GoalCRUD.create(
            db=db,
            user_id=user_id,
            title=parsed.get("title", goal_title),
            description=parsed.get("description", goal_description),
            goal_type=parsed.get("goal_type", goal_type),
            deadline=parsed_deadline,
        )

        # ── 第6步：递归保存子任务树 ──
        tasks_data = parsed.get("tasks", [])
        if not tasks_data:
            logger.warning(f"AI未返回任何任务数据: {raw_result}")
            raise ValueError("AI未能生成任务拆解，请提供更详细的目标描述")

        AgentService._save_task_tree(db, goal.id, None, tasks_data)

        # ── 第7步：计算初始进度并返回结果 ──
        GoalCRUD.recalc_progress(db, goal.id)
        db.refresh(goal)

        logger.info(f"目标拆解完成 | goal_id:{goal.id} | 一级任务数:{len(tasks_data)}")
        return {
            "goal_id": goal.id,
            "title": goal.title,
            "description": goal.description,
            "goal_type": goal.goal_type,
            "tasks": tasks_data,
        }

    @staticmethod
    def _save_task_tree(
        db: Session,
        goal_id: int,
        parent_id: Optional[int],
        tasks: List[Dict[str, Any]],
        sort_start: int = 0,
    ) -> None:
        """
        递归保存任务树到数据库
        根据任务标题自动匹配内置工具
        """
        for idx, task_data in enumerate(tasks):
            title = task_data.get("title", "")
            description = task_data.get("description", "")
            priority = task_data.get("priority", 1)
            estimated_hours = task_data.get("estimated_hours")
            deadline_str = task_data.get("deadline")

            # 解析截止时间
            parsed_deadline = None
            if deadline_str:
                try:
                    parsed_deadline = datetime.strptime(deadline_str, "%Y-%m-%d")
                except ValueError:
                    try:
                        parsed_deadline = datetime.strptime(deadline_str, "%Y-%m-%d %H:%M:%S")
                    except ValueError:
                        pass

            # 自动匹配工具
            tool_name = task_data.get("tool_name")
            tool_id = None
            if tool_name:
                tool = AgentToolCRUD.get_by_name(db, tool_name)
                if tool:
                    tool_id = tool.id
            else:
                # 根据任务标题关键词自动匹配工具
                tool_id = AgentService._auto_match_tool(db, title)

            # 创建任务记录
            task = TaskItemCRUD.create(
                db=db,
                goal_id=goal_id,
                parent_id=parent_id,
                title=title,
                description=description,
                priority=priority,
                estimated_hours=estimated_hours,
                deadline=parsed_deadline,
                tool_id=tool_id,
                sort_order=sort_start + idx,
            )

            # 递归处理子任务
            children = task_data.get("children", [])
            if children:
                AgentService._save_task_tree(
                    db=db,
                    goal_id=goal_id,
                    parent_id=task.id,
                    tasks=children,
                )

    @staticmethod
    def _auto_match_tool(db: Session, task_title: str) -> Optional[int]:
        """根据任务标题自动匹配最合适的工具"""
        for keyword, tool_name in AgentService.TOOL_MAP.items():
            if keyword in task_title:
                tool = AgentToolCRUD.get_by_name(db, tool_name)
                if tool:
                    return tool.id
        return None

    @staticmethod
    async def chat_with_agent(
        db: Session,
        user_id: int,
        goal_id: int,
        user_message: str,
    ) -> Dict[str, Any]:
        """
        与 Agent 对话交互，基于已有目标进一步优化或细化任务
        """
        goal = GoalCRUD.get_by_id(db, goal_id)
        if goal is None:
            raise ValueError("目标不存在")
        if goal.user_id != user_id:
            raise ValueError("无权操作此目标")

        # 获取现有任务作为上下文
        existing_tasks = TaskItemCRUD.get_all_by_goal_id(db, goal_id)
        task_summary = "\n".join(
            [
                f"- {t.title} (状态: {t.status})"
                for t in existing_tasks[:20]
            ]
        )

        system_prompt = (
            "你是智能任务拆解助手，正在与用户讨论已有目标的任务拆解方案。\n"
            "你可以：\n"
            "1. 回答用户对任务的疑问\n"
            "2. 根据用户反馈调整任务拆解方案\n"
            "3. 推荐新增或修改子任务\n"
            "4. 提供任务执行建议\n\n"
            "如果用户要求调整任务，请输出包含 suggested_tasks 字段的JSON，格式同任务拆解。"
        )

        context_message = (
            f"当前目标: {goal.title}\n"
            f"目标描述: {goal.description or '无'}\n"
            f"现有任务列表:\n{task_summary}\n\n"
            f"用户消息: {user_message}\n\n"
            f"请回复用户的咨询，如果有新的任务建议，在回复末尾附上JSON格式的suggested_tasks。"
        )

        reply = await llm_service.chat_completion(
            messages=[{"role": "user", "content": context_message}],
            system_prompt=system_prompt,
            response_format={"type": "json_object"},
        )

        try:
            parsed_reply = json.loads(reply)
            suggested = parsed_reply.get("suggested_tasks", None)
            return {
                "reply": parsed_reply.get("reply", reply),
                "suggested_tasks": suggested,
            }
        except json.JSONDecodeError:
            return {
                "reply": reply,
                "suggested_tasks": None,
            }
