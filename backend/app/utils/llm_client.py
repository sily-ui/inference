"""
LLM客户端封装
统一使用OpenAI格式调用
支持Redis缓存
支持Token使用统计
"""

import hashlib
import json
import os
import threading
from typing import Optional, Dict, Any, List
from openai import OpenAI

from ..config import Config
from .cache import get_cache


class TokenStats:
    """Token使用统计单例"""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._stats = {
            "total_tokens": 0,
            "prompt_tokens": 0,
            "completion_tokens": 0,
            "total_calls": 0,
            "cached_tokens": 0,
            "model_name": "",
        }
        self._lock = threading.Lock()

    def reset(self):
        """重置统计"""
        with self._lock:
            self._stats = {
                "total_tokens": 0,
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "total_calls": 0,
                "cached_tokens": 0,
                "model_name": "",
            }

    def record(self, usage: Dict, cached: bool = False, model: str = ""):
        """记录Token使用"""
        with self._lock:
            if model:
                self._stats["model_name"] = model
            self._stats["total_calls"] += 1
            if cached:
                self._stats["cached_tokens"] += usage.get("total_tokens", 0)
            else:
                self._stats["prompt_tokens"] += usage.get("prompt_tokens", 0)
                self._stats["completion_tokens"] += usage.get("completion_tokens", 0)
                self._stats["total_tokens"] += usage.get("total_tokens", 0)

    def get_stats(self) -> Dict:
        """获取统计"""
        with self._lock:
            return self._stats.copy()


def get_token_stats() -> TokenStats:
    """获取Token统计实例"""
    return TokenStats()


class LLMClient:
    """LLM客户端"""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
    ):
        self.api_key = api_key or Config.LLM_API_KEY
        self.base_url = base_url or Config.LLM_BASE_URL
        self.model = model or Config.LLM_MODEL_NAME
        self.cache = get_cache()
        self.cache_ttl = int(os.environ.get("LLM_CACHE_TTL", "3600"))

        if not self.api_key:
            raise ValueError("LLM_API_KEY 未配置")

        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url,
            timeout=120.0,  # 设置120秒超时
            max_retries=2,  # 最多重试2次
        )

    def _make_cache_key(
        self, messages: List[Dict], temperature: float, max_tokens: int
    ) -> str:
        """生成缓存键"""
        cache_data = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        key_str = json.dumps(cache_data, sort_keys=True)
        return hashlib.sha256(key_str.encode()).hexdigest()

    def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 4096,
        response_format: Optional[Dict] = None,
        use_cache: bool = True,
    ) -> str:
        """
        发送聊天请求

        Args:
            messages: 消息列表
            temperature: 温度参数
            max_tokens: 最大token数
            response_format: 响应格式（如JSON模式）
            use_cache: 是否使用缓存

        Returns:
            模型响应文本
        """
        cache_key = None
        if use_cache and response_format is None:
            cache_key = self._make_cache_key(messages, temperature, max_tokens)
            cached = self.cache.get("llm", key=cache_key)
            if cached:
                return cached

        kwargs = {
            "model": self.model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        if response_format:
            kwargs["response_format"] = response_format

        response = self.client.chat.completions.create(**kwargs)
        result = response.choices[0].message.content

        # 记录Token使用统计
        if hasattr(response, "usage") and response.usage:
            token_stats = get_token_stats()
            is_cached = (
                use_cache and cache_key and bool(self.cache.get("llm", key=cache_key))
            )
            token_stats.record(
                usage={
                    "prompt_tokens": response.usage.prompt_tokens or 0,
                    "completion_tokens": response.usage.completion_tokens or 0,
                    "total_tokens": response.usage.total_tokens or 0,
                },
                cached=is_cached,
                model=self.model,
            )

        if use_cache and result:
            self.cache.set("llm", result, ttl=self.cache_ttl, key=cache_key)

        return result

    def chat_json(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.3,
        max_tokens: int = 4096,
        use_cache: bool = True,
    ) -> Dict[str, Any]:
        """
        发送聊天请求并返回JSON

        Args:
            messages: 消息列表
            temperature: 温度参数
            max_tokens: 最大token数
            use_cache: 是否使用缓存

        Returns:
            解析后的JSON对象
        """
        response = self.chat(
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            response_format={"type": "json_object"},
            use_cache=use_cache,
        )

        return json.loads(response)
