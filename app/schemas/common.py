"""公共 Pydantic 模型 - 分页、通用响应"""
from typing import Any, Generic, List, Optional, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class PaginationParams(BaseModel):
    """分页查询参数"""
    page: int = 1
    page_size: int = 20


class PaginatedResult(BaseModel, Generic[T]):
    """分页结果包装"""
    items: List[T]
    total: int
    page: int
    page_size: int
    total_pages: int


class ResponseWrapper(BaseModel):
    """统一响应格式"""
    code: int
    msg: str
    data: Any = None
    timestamp: int
