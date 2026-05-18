"""
工具调用服务 - 内置工具库执行逻辑
支持工具列表：学习大纲生成、资料检索提示词生成、周报生成、任务复盘模板、时间规划模板、错题整理模板
"""
from typing import Any, Dict, Optional

from loguru import logger
from sqlalchemy.orm import Session

from app.crud.agent import AgentToolCRUD
from app.crud.task import TaskItemCRUD
from app.services.llm_service import llm_service


class ToolService:
    """内置工具调用服务"""

    @staticmethod
    async def execute_tool(
        db: Session,
        tool_id: int,
        task_id: int,
        params: Dict[str, Any],
    ) -> str:
        """
        执行指定工具的调用

        Args:
            db: 数据库会话
            tool_id: 工具ID
            task_id: 关联的任务ID
            params: 工具参数

        Returns:
            工具执行结果文本
        """
        # 1. 获取工具定义
        tool = AgentToolCRUD.get_by_id(db, tool_id)
        if tool is None:
            raise ValueError(f"工具不存在 (id={tool_id})")

        # 2. 获取任务信息
        task = TaskItemCRUD.get_by_id(db, task_id)
        if task is None:
            raise ValueError(f"任务不存在 (id={task_id})")

        logger.info(f"执行工具 | tool:{tool.name} | task:{task.title}")

        # 3. 构建 Prompt
        content = params.get("content", task.title)
        prompt = tool.prompt_template.replace("{content}", content)

        # 4. 调用大模型生成结果
        result = await llm_service.chat_completion(
            messages=[{"role": "user", "content": prompt}],
            system_prompt=f"你是一个{tool.name}工具，请根据用户输入生成专业内容。",
        )

        return result

    @staticmethod
    async def generate_study_outline(topic: str) -> str:
        """学习大纲生成"""
        prompt = f"请为以下学习目标生成一份详细的学习大纲，包含章节划分、重点知识点、推荐学习顺序：{topic}"
        return await llm_service.chat_completion(
            messages=[{"role": "user", "content": prompt}],
            system_prompt="你是一个教育专家，擅长制定学习大纲。",
        )

    @staticmethod
    async def generate_search_keywords(topic: str) -> str:
        """资料检索提示词生成"""
        prompt = f"针对以下主题，生成10组高效的资料检索关键词和搜索策略：{topic}"
        return await llm_service.chat_completion(
            messages=[{"role": "user", "content": prompt}],
            system_prompt="你是一个信息检索专家。",
        )

    @staticmethod
    async def generate_weekly_report(tasks_summary: str) -> str:
        """周报生成"""
        prompt = f"根据以下任务完成情况，生成一份专业的工作周报：{tasks_summary}"
        return await llm_service.chat_completion(
            messages=[{"role": "user", "content": prompt}],
            system_prompt="你是一个职场效率专家，擅长撰写周报。",
        )

    @staticmethod
    async def generate_review_template(task_info: str) -> str:
        """任务复盘模板生成"""
        prompt = f"请基于以下任务信息，生成一份完整的复盘文档模板：{task_info}"
        return await llm_service.chat_completion(
            messages=[{"role": "user", "content": prompt}],
            system_prompt="你是一个项目复盘专家。",
        )

    @staticmethod
    async def generate_schedule(tasks_info: str) -> str:
        """时间规划模板生成"""
        prompt = f"请根据以下任务清单，生成一份合理的时间规划和每日日程安排：{tasks_info}"
        return await llm_service.chat_completion(
            messages=[{"role": "user", "content": prompt}],
            system_prompt="你是一个时间管理专家。",
        )

    @staticmethod
    async def generate_error_review(error_info: str) -> str:
        """错题整理模板生成"""
        prompt = f"请根据以下错题信息，生成结构化的错题整理模板：{error_info}"
        return await llm_service.chat_completion(
            messages=[{"role": "user", "content": prompt}],
            system_prompt="你是一个学习辅导专家。",
        )
