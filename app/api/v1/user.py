"""用户模块路由 - 注册、登录、个人信息管理"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.security import (
    create_access_token,
    get_current_user_id,
)
from app.crud.user import UserCRUD
from app.db.session import get_db
from app.schemas.user import (
    LoginResponse,
    UserLoginRequest,
    UserRegisterRequest,
    UserResponse,
    UserUpdateRequest,
)
from app.utils.response import success, fail

router = APIRouter()


@router.post("/register", summary="用户注册")
def register(request: UserRegisterRequest, db: Session = Depends(get_db)):
    """注册新用户"""
    # 检查用户名是否已存在
    existing_user = UserCRUD.get_by_username(db, request.username)
    if existing_user:
        return fail(msg="用户名已存在", code=400)

    # 检查邮箱是否已存在
    if request.email:
        existing_email = UserCRUD.get_by_email(db, request.email)
        if existing_email:
            return fail(msg="邮箱已被注册", code=400)

    # 创建用户
    user = UserCRUD.create(
        db=db,
        username=request.username,
        password=request.password,
        email=request.email,
    )
    return success(
        data=UserResponse.model_validate(user),
        msg="注册成功",
    )


@router.post("/login", summary="用户登录")
def login(request: UserLoginRequest, db: Session = Depends(get_db)):
    """用户登录，返回JWT令牌"""
    user = UserCRUD.authenticate(db, request.username, request.password)
    if user is None:
        return fail(msg="用户名或密码错误", code=401)

    # 生成JWT令牌
    token = create_access_token(user_id=user.id)
    return success(
        data=LoginResponse(
            access_token=token,
            user=UserResponse.model_validate(user),
        ),
        msg="登录成功",
    )


@router.get("/info", summary="获取当前用户信息")
def get_user_info(
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """获取已登录用户的个人信息"""
    user = UserCRUD.get_by_id(db, user_id)
    if user is None:
        return fail(msg="用户不存在", code=404)
    return success(data=UserResponse.model_validate(user))


@router.put("/info", summary="更新用户信息")
def update_user_info(
    request: UserUpdateRequest,
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """更新当前用户的信息（邮箱/密码）"""
    if request.email is None and request.password is None:
        return fail(msg="请提供要更新的字段", code=400)

    # 检查邮箱是否已被其他用户使用
    if request.email:
        existing = UserCRUD.get_by_email(db, request.email)
        if existing and existing.id != user_id:
            return fail(msg="邮箱已被其他账号使用", code=400)

    user = UserCRUD.update(
        db=db,
        user_id=user_id,
        email=request.email,
        password=request.password,
    )
    if user is None:
        return fail(msg="用户不存在", code=404)
    return success(data=UserResponse.model_validate(user), msg="更新成功")


@router.post("/check-login", summary="校验登录态")
def check_login(
    user_id: int = Depends(get_current_user_id),
    db: Session = Depends(get_db),
):
    """校验当前令牌是否有效，返回用户基本信息"""
    user = UserCRUD.get_by_id(db, user_id)
    if user is None:
        return fail(msg="用户不存在", code=404)
    return success(
        data={"is_login": True, "user_id": user.id, "username": user.username},
        msg="登录态有效",
    )
