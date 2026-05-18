"""统一接口返回格式工具"""
from typing import Any, Optional

from fastapi import status
from fastapi.responses import JSONResponse


def success(
    data: Any = None,
    msg: str = "操作成功",
    code: int = 200,
) -> JSONResponse:
    """成功响应"""
    return JSONResponse(
        content={
            "code": code,
            "msg": msg,
            "data": data,
            "timestamp": _now(),
        }
    )


def fail(
    msg: str = "操作失败",
    code: int = 400,
    data: Any = None,
) -> JSONResponse:
    """失败响应"""
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "code": code,
            "msg": msg,
            "data": data,
            "timestamp": _now(),
        },
    )


def _now() -> int:
    """当前毫秒时间戳"""
    import time
    return int(time.time() * 1000)
