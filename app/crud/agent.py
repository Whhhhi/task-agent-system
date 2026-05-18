"""Agent 工具 CRUD 操作"""
from typing import List, Optional

from sqlalchemy.orm import Session

from app.models.agent_tool import AgentTool


class AgentToolCRUD:
    """Agent 工具表数据库操作"""

    @staticmethod
    def get_by_id(db: Session, tool_id: int) -> Optional[AgentTool]:
        return db.query(AgentTool).filter(AgentTool.id == tool_id).first()

    @staticmethod
    def get_by_name(db: Session, name: str) -> Optional[AgentTool]:
        return db.query(AgentTool).filter(AgentTool.name == name).first()

    @staticmethod
    def get_all(db: Session) -> List[AgentTool]:
        return db.query(AgentTool).order_by(AgentTool.id).all()

    @staticmethod
    def get_by_scenario(db: Session, scenario: str) -> List[AgentTool]:
        return (
            db.query(AgentTool)
            .filter(AgentTool.scenario.contains(scenario))
            .all()
        )

    @staticmethod
    def create(
        db: Session,
        name: str,
        description: str,
        prompt_template: str,
        scenario: Optional[str] = None,
    ) -> AgentTool:
        tool = AgentTool(
            name=name,
            description=description,
            prompt_template=prompt_template,
            scenario=scenario,
        )
        db.add(tool)
        db.commit()
        db.refresh(tool)
        return tool

    @staticmethod
    def seed_default_tools(db: Session) -> List[AgentTool]:
        """初始化种子工具数据 - 内置工具库"""
        default_tools = [
            {
                "name": "学习大纲生成",
                "description": "根据学习目标自动生成结构化学习大纲",
                "prompt_template": "请为以下学习目标生成一份详细的学习大纲，包含章节划分、重点知识点、推荐学习顺序：{content}",
                "scenario": "学习,考试,备考",
            },
            {
                "name": "资料检索提示词生成",
                "description": "为特定主题生成高效的资料检索关键词和搜索策略",
                "prompt_template": "针对以下主题，生成10组高效的资料检索关键词和搜索策略：{content}",
                "scenario": "学习,研究,开发",
            },
            {
                "name": "周报生成",
                "description": "根据本周任务完成情况自动生成工作周报",
                "prompt_template": "根据以下任务完成情况，生成一份专业的工作周报：{content}",
                "scenario": "工作,项目开发",
            },
            {
                "name": "任务复盘模板",
                "description": "生成结构化的任务复盘文档，含完成情况、问题总结、改进计划",
                "prompt_template": "请基于以下任务信息，生成一份完整的复盘文档模板：{content}",
                "scenario": "工作,学习,项目开发",
            },
            {
                "name": "时间规划模板",
                "description": "根据任务清单生成合理的时间规划和日程安排",
                "prompt_template": "请根据以下任务清单，生成一份合理的时间规划和每日日程安排：{content}",
                "scenario": "工作,学习,备考,求职规划",
            },
            {
                "name": "错题整理模板",
                "description": "生成错题整理模板，包含题目、错误原因、正确解法、知识点归纳",
                "prompt_template": "请根据以下错题信息，生成结构化的错题整理模板：{content}",
                "scenario": "学习,备考",
            },
        ]
        tools = []
        for tool_data in default_tools:
            existing = self.get_by_name(db, tool_data["name"])
            if existing is None:
                tool = AgentTool(**tool_data)
                db.add(tool)
                tools.append(tool)
        db.commit()
        for tool in tools:
            db.refresh(tool)
        return tools
