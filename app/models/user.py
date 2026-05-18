"""用户表 ORM 模型"""
from datetime import datetime
from typing import Any, Optional

from sqlalchemy import Column, DateTime, Integer, String, Text, SmallInteger, func
from sqlalchemy.orm import Mapped

from app.db.base import Base


class User(Base):
    """用户表 - 存储用户基础信息和登录状态"""

    id: Mapped[int] = Column(Integer, primary_key=True, autoincrement=True, comment="用户ID")
    username: Mapped[str] = Column(
        String(64), unique=True, nullable=False, index=True, comment="用户名"
    )
    password_hash: Mapped[str] = Column(String(256), nullable=False, comment="密码（bcrypt加密）")
    email: Mapped[Optional[str]] = Column(String(128), unique=True, nullable=True, comment="邮箱")
    status: Mapped[int] = Column(
        SmallInteger, default=1, nullable=False, comment="状态：1-正常 0-禁用"
    )
    last_login_at: Mapped[Optional[datetime]] = Column(
        DateTime, nullable=True, comment="最后登录时间"
    )

    def __repr__(self) -> str:
        return f"<User(id={self.id}, username='{self.username}')>"
