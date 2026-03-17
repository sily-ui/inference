"""
Redis缓存模块
用于LLM调用结果缓存
"""

import hashlib
import json
import os
from typing import Optional, Any
import redis

from ..config import Config


class CacheManager:
    """Redis缓存管理器"""

    _instance: Optional["CacheManager"] = None
    _client: Optional[redis.Redis] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if self._client is None:
            self._init_client()

    def _init_client(self):
        """初始化Redis客户端"""
        redis_url = os.environ.get("REDIS_URL")

        if not redis_url:
            print("[Cache] REDIS_URL 未配置，缓存功能不可用")
            return

        try:
            self._client = redis.from_url(redis_url, decode_responses=True)
            self._client.ping()
            print(f"[Cache] Redis连接成功")
        except Exception as e:
            print(f"[Cache] Redis连接失败: {e}")
            self._client = None

    @property
    def is_available(self) -> bool:
        """检查缓存是否可用"""
        return self._client is not None

    def _make_cache_key(self, prefix: str, **kwargs) -> str:
        """生成缓存键"""
        key_data = json.dumps(kwargs, sort_keys=True)
        key_hash = hashlib.md5(key_data.encode()).hexdigest()[:16]
        return f"mirofish:{prefix}:{key_hash}"

    def get(self, prefix: str, **kwargs) -> Optional[Any]:
        """获取缓存"""
        if not self.is_available:
            return None

        try:
            key = self._make_cache_key(prefix, **kwargs)
            value = self._client.get(key)
            if value:
                return json.loads(value)
        except Exception as e:
            print(f"[Cache] 获取缓存失败: {e}")
        return None

    def set(self, prefix: str, value: Any, ttl: int = 3600, **kwargs):
        """设置缓存

        Args:
            prefix: 缓存前缀
            value: 缓存值
            ttl: 过期时间(秒)，默认1小时
        """
        if not self.is_available:
            return

        try:
            key = self._make_cache_key(prefix, **kwargs)
            self._client.setex(key, ttl, json.dumps(value, ensure_ascii=False))
        except Exception as e:
            print(f"[Cache] 设置缓存失败: {e}")

    def delete(self, prefix: str, **kwargs):
        """删除缓存"""
        if not self.is_available:
            return

        try:
            key = self._make_cache_key(prefix, **kwargs)
            self._client.delete(key)
        except Exception as e:
            print(f"[Cache] 删除缓存失败: {e}")

    def clear_prefix(self, prefix: str):
        """清除指定前缀的所有缓存"""
        if not self.is_available:
            return

        try:
            pattern = f"mirofish:{prefix}:*"
            keys = self._client.keys(pattern)
            if keys:
                self._client.delete(*keys)
        except Exception as e:
            print(f"[Cache] 清除缓存失败: {e}")


def get_cache() -> CacheManager:
    """获取缓存管理器实例"""
    return CacheManager()
