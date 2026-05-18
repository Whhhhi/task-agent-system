"""全局异常处理模块 - 统一异常捕获与返回格式"""
import traceback
from typing import Any, Union

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from starlette.responses import JSONResponse

from app.utils.logger import logger


class AppException(Exception):
    """自定义业务异常基类"""

    def __init__(self, code: int = 400, message: str = "请求失败", data: Any = None):
        self.code = code
        self.message = message
        self.data = data


def register_exception_handlers(app: FastAPI) -> None:
    """向 FastAPI 应用注册所有全局异常处理器"""

    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException):
        """自定义业务异常处理"""
        return JSONResponse(
            status_code=200,  # 业务层异常统一 200，前端通过 code 判断
            content={
                "code": exc.code,
                "msg": exc.message,
                "data": exc.data,
                "timestamp": _now_timestamp(),
            },
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ):
        """请求参数校验异常处理"""
        errors = exc.errors()
        # 提取首个校验失败的详细信息
        first_error = errors[0] if errors else {}
        field = " -> ".join(str(loc) for loc in first_error.get("loc", []))
        msg = first_error.get("msg", "参数校验失败")
        logger.warning(f"参数校验失败 | 字段: {field} | 错误: {msg} | 路径: {request.url.path}")
        return JSONResponse(
            status_code=200,
            content={
                "code": 422,
                "msg": f"参数校验失败: {field} {msg}",
                "data": None,
                "timestamp": _now_timestamp(),
            },
        )

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        """全局兜底异常捕获 - 防止后端报错暴露给前端"""
        logger.error(
            f"未捕获异常 | 路径: {request.url.path} | 错误: {str(exc)}\n"
            f"{traceback.format_exc()}"
        )
        return JSONResponse(
            status_code=200,
            content={
                "code": 500,
                "msg": "服务器内部错误，请稍后重试",
                "data": None,
                "timestamp": _now_timestamp(),
            },
        )


def _now_timestamp() -> int:
    """获取当前时间戳（毫秒）"""
    import time
    return int(time.time() * 1000)
