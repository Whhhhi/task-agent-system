"""用户 CRUD 操作"""
from datetime import datetime
from typing import Optional

from sqlalchemy.orm import Session

from app.models.user import User
from app.core.security import hash_password, verify_password


class UserCRUD:
    """用户表数据库操作类"""

    @staticmethod
    def get_by_id(db: Session, user_id: int) -> Optional[User]:
        """根据用户ID查询用户"""
        return db.query(User).filter(User.id == user_id).first()

    @staticmethod
    def get_by_username(db: Session, username: str) -> Optional[User]:
        """根据用户名查询用户"""
        return db.query(User).filter(User.username == username).first()

    @staticmethod
    def get_by_email(db: Session, email: str) -> Optional[User]:
        """根据邮箱查询用户"""
        return db.query(User).filter(User.email == email).first()

    @staticmethod
    def create(db: Session, username: str, password: str, email: Optional[str] = None) -> User:
        """创建新用户"""
        user = User(
            username=username,
            password_hash=hash_password(password),
            email=email,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def authenticate(db: Session, username: str, password: str) -> Optional[User]:
        """用户登录认证"""
        user = UserCRUD.get_by_username(db, username)
        if user is None:
            return None
        if user.status == 0:
            return None  # 账号已禁用
        if not verify_password(password, user.password_hash):
            return None
        # 更新最后登录时间
        user.last_login_at = datetime.now()
        db.commit()
        return user

    @staticmethod
    def update(
        db: Session,
        user_id: int,
        email: Optional[str] = None,
        password: Optional[str] = None,
    ) -> Optional[User]:
        """更新用户信息"""
        user = UserCRUD.get_by_id(db, user_id)
        if user is None:
            return None
        if email is not None:
            user.email = email
        if password is not None:
            user.password_hash = hash_password(password)
        db.commit()
        db.refresh(user)
        return user
