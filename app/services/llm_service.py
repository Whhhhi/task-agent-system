"""
大模型调用服务 - 支持 OpenAI 兼容接口
可自由切换 DeepSeek / 通义千问 / Claude（任意兼容接口）
"""
from typing import Any, Dict, List, Optional

import httpx
from loguru import logger

from app.config import settings


class LLMService:
    """
    通用大模型调用服务
    通过修改 .env 中的 LLM_BASE_URL 即可切换不同模型：
    - DeepSeek:   https://api.deepseek.com/v1
    - 通义千问:    https://dashscope.aliyuncs.com/compatible-mode/v1
    - Claude(OpenAI兼容): 需第三方代理或 Anthropic 官方 OpenAI 兼容端点
    """

    def __init__(self):
        self.api_key = settings.LLM_API_KEY
        self.base_url = settings.LLM_BASE_URL.rstrip("/")
        self.model = settings.LLM_MODEL_NAME
        self.max_tokens = settings.LLM_MAX_TOKENS
        self.temperature = settings.LLM_TEMPERATURE
        self._client: Optional[httpx.AsyncClient] = None

    async def _get_client(self) -> httpx.AsyncClient:
        """获取或创建异步 HTTP 客户端"""
        if self._client is None:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(120.0, connect=10.0),  # 大模型响应较慢，设置120秒超时
                follow_redirects=True,
            )
        return self._client

    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        response_format: Optional[Dict[str, str]] = None,
    ) -> str:
        """
        调用大模型 Chat Completion 接口

        Args:
            messages: 对话消息列表 [{"role": "user", "content": "..."}]
            system_prompt: 系统提示词（可选，会被放在消息列表最前面）
            temperature: 温度参数，覆盖默认值
            max_tokens: 最大输出 token 数
            response_format: 响应格式，如 {"type": "json_object"}

        Returns:
            模型响应的文本内容
        """
        client = await self._get_client()

        # 构建完整消息列表
        full_messages = []
        if system_prompt:
            full_messages.append({"role": "system", "content": system_prompt})
        full_messages.extend(messages)

        # 构建请求体
        payload: Dict[str, Any] = {
            "model": self.model,
            "messages": full_messages,
            "temperature": temperature or self.temperature,
            "max_tokens": max_tokens or self.max_tokens,
        }
        if response_format:
            payload["response_format"] = response_format

        # 发起请求
        url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        try:
            logger.debug(f"LLM 请求 | 模型: {self.model} | 消息数: {len(full_messages)}")
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            result = response.json()
            content = result["choices"][0]["message"]["content"]
            usage = result.get("usage", {})
            logger.debug(
                f"LLM 响应成功 | 输入token: {usage.get('prompt_tokens', 'N/A')} | "
                f"输出token: {usage.get('completion_tokens', 'N/A')}"
            )
            return content.strip()
        except httpx.HTTPStatusError as e:
            logger.error(f"LLM API HTTP 错误: {e.response.status_code} - {e.response.text}")
            raise RuntimeError(f"大模型服务调用失败 (HTTP {e.response.status_code})")
        except httpx.TimeoutException:
            logger.error("LLM API 请求超时")
            raise RuntimeError("大模型服务请求超时，请稍后重试")
        except Exception as e:
            logger.error(f"LLM API 未知错误: {str(e)}")
            raise RuntimeError(f"大模型服务调用异常: {str(e)}")

    async def close(self):
        """关闭 HTTP 客户端"""
        if self._client:
            await self._client.aclose()
            self._client = None


# 全局单例
llm_service = LLMService()
