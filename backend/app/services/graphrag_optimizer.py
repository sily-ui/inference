"""
GraphRAG 性能与存储优化服务

功能：
1. Embedding 缓存：缓存文档/实体的向量表示，避免重复向量化
2. 增量更新图谱：仅重新处理新增/修改的文档内容，而非全量重建
"""

import os
import json
import hashlib
import time
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime


@dataclass
class CacheEntry:
    """缓存条目"""

    content_hash: str
    embedding_key: str
    created_at: str
    expires_at: str


@dataclass
class DocumentVersion:
    """文档版本记录"""

    file_name: str
    file_hash: str
    chunk_count: int
    last_modified: str
    embedding_cached: bool


class EmbeddingCache:
    """
    Embedding 向量缓存
    基于内容哈希进行缓存，避免重复计算
    """

    def __init__(self, cache_dir: Optional[str] = None):
        """
        初始化缓存

        Args:
            cache_dir: 缓存目录路径，默认使用 backend/app/cache/embeddings
        """
        if cache_dir is None:
            cache_dir = os.path.join(os.path.dirname(__file__), "../cache/embeddings")
        self.cache_dir = cache_dir
        self._ensure_cache_dir()

    def _ensure_cache_dir(self):
        """确保缓存目录存在"""
        os.makedirs(self.cache_dir, exist_ok=True)

    def _get_file_hash(self, content: str) -> str:
        """计算内容哈希"""
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    def _get_cache_path(self, content_hash: str) -> str:
        """获取缓存文件路径"""
        # 使用哈希前两位作为子目录，避免单目录文件过多
        subdir = content_hash[:2]
        subdir_path = os.path.join(self.cache_dir, subdir)
        os.makedirs(subdir_path, exist_ok=True)
        return os.path.join(subdir_path, f"{content_hash}.json")

    def get(self, content: str) -> Optional[Dict[str, Any]]:
        """
        获取缓存的 embedding

        Args:
            content: 原始文本内容

        Returns:
            缓存的 embedding 数据，如果不存在则返回 None
        """
        content_hash = self._get_file_hash(content)
        cache_path = self._get_cache_path(content_hash)

        if not os.path.exists(cache_path):
            return None

        try:
            with open(cache_path, "r", encoding="utf-8") as f:
                cache_data = json.load(f)

            # 检查是否过期
            expires_at = cache_data.get("expires_at", "")
            if expires_at:
                expire_time = datetime.fromisoformat(expires_at)
                if datetime.now() > expire_time:
                    # 缓存过期，删除
                    os.remove(cache_path)
                    return None

            return cache_data.get("embedding_data")

        except (json.JSONDecodeError, KeyError, ValueError):
            # 缓存文件损坏，删除
            if os.path.exists(cache_path):
                os.remove(cache_path)
            return None

    def set(self, content: str, embedding_data: Dict[str, Any], ttl: int = 86400 * 30):
        """
        存储 embedding 到缓存

        Args:
            content: 原始文本内容
            embedding_data: 要缓存的 embedding 数据
            ttl: 缓存有效期（秒），默认30天
        """
        content_hash = self._get_file_hash(content)
        cache_path = self._get_cache_path(content_hash)

        now = datetime.now()
        expires_at = datetime.fromtimestamp(now.timestamp() + ttl)

        cache_data = {
            "content_hash": content_hash,
            "content_preview": content[:200],  # 保存预览用于调试
            "embedding_data": embedding_data,
            "created_at": now.isoformat(),
            "expires_at": expires_at.isoformat(),
        }

        with open(cache_path, "w", encoding="utf-8") as f:
            json.dump(cache_data, f, ensure_ascii=False, indent=2)

    def get_batch(self, contents: List[str]) -> Dict[str, Dict[str, Any]]:
        """
        批量获取缓存

        Args:
            contents: 文本内容列表

        Returns:
            字典，key 为内容哈希，value 为 embedding 数据
        """
        results = {}
        for content in contents:
            content_hash = self._get_file_hash(content)
            cached = self.get(content)
            if cached is not None:
                results[content_hash] = cached
        return results

    def set_batch(
        self,
        contents: List[str],
        embeddings: List[Dict[str, Any]],
        ttl: int = 86400 * 30,
    ):
        """
        批量存储缓存

        Args:
            contents: 文本内容列表
            embeddings: embedding 数据列表
            ttl: 缓存有效期（秒）
        """
        for content, embedding in zip(contents, embeddings):
            self.set(content, embedding, ttl)

    def get_cache_stats(self) -> Dict[str, Any]:
        """
        获取缓存统计信息

        Returns:
            缓存统计字典
        """
        total_files = 0
        total_size = 0
        expired_count = 0

        for root, dirs, files in os.walk(self.cache_dir):
            for file in files:
                if file.endswith(".json"):
                    file_path = os.path.join(root, file)
                    total_files += 1
                    total_size += os.path.getsize(file_path)

                    # 检查是否过期
                    try:
                        with open(file_path, "r", encoding="utf-8") as f:
                            cache_data = json.load(f)
                        expires_at = cache_data.get("expires_at", "")
                        if expires_at:
                            expire_time = datetime.fromisoformat(expires_at)
                            if datetime.now() > expire_time:
                                expired_count += 1
                    except:
                        pass

        return {
            "total_files": total_files,
            "total_size_mb": round(total_size / 1024 / 1024, 2),
            "expired_count": expired_count,
            "cache_dir": self.cache_dir,
        }

    def clear_expired(self) -> int:
        """
        清理过期缓存

        Returns:
            清理的缓存数量
        """
        cleared = 0

        for root, dirs, files in os.walk(self.cache_dir):
            for file in files:
                if file.endswith(".json"):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, "r", encoding="utf-8") as f:
                            cache_data = json.load(f)
                        expires_at = cache_data.get("expires_at", "")
                        if expires_at:
                            expire_time = datetime.fromisoformat(expires_at)
                            if datetime.now() > expire_time:
                                os.remove(file_path)
                                cleared += 1
                    except:
                        # 损坏的文件也删除
                        try:
                            os.remove(file_path)
                            cleared += 1
                        except:
                            pass

        return cleared


class DocumentVersionManager:
    """
    文档版本管理器
    追踪文档变更，支持增量更新
    """

    def __init__(self, versions_dir: Optional[str] = None):
        """
        初始化版本管理器

        Args:
            versions_dir: 版本记录目录，默认使用 backend/app/cache/versions
        """
        if versions_dir is None:
            versions_dir = os.path.join(os.path.dirname(__file__), "../cache/versions")
        self.versions_dir = versions_dir
        self._ensure_dir()

    def _ensure_dir(self):
        """确保目录存在"""
        os.makedirs(self.versions_dir, exist_ok=True)

    def _get_project_path(self, project_id: str) -> str:
        """获取项目的版本记录文件路径"""
        return os.path.join(self.versions_dir, f"{project_id}_versions.json")

    def _get_file_hash(self, file_content: bytes) -> str:
        """计算文件内容哈希"""
        return hashlib.sha256(file_content).hexdigest()

    def register_document(
        self, project_id: str, file_name: str, file_content: bytes, chunk_count: int
    ) -> Tuple[str, bool]:
        """
        注册/更新文档版本

        Args:
            project_id: 项目ID
            file_name: 文件名
            file_content: 文件内容（字节）
            chunk_count: 分块数量

        Returns:
            (file_hash, is_new): 文件哈希和是否是新增/修改
        """
        file_hash = self._get_file_hash(file_content)
        version_path = self._get_project_path(project_id)

        # 加载现有版本记录
        versions = {}
        if os.path.exists(version_path):
            try:
                with open(version_path, "r", encoding="utf-8") as f:
                    versions = json.load(f)
            except json.JSONDecodeError:
                versions = {}

        # 检查是否是新增或修改
        is_new = file_name not in versions
        is_modified = False

        if not is_new:
            existing = versions.get(file_name, {})
            if existing.get("file_hash") != file_hash:
                is_modified = True

        # 更新版本记录
        versions[file_name] = {
            "file_name": file_name,
            "file_hash": file_hash,
            "chunk_count": chunk_count,
            "last_modified": datetime.now().isoformat(),
            "embedding_cached": False,  # 新文档需要生成 embedding
            "is_new": is_new,
            "is_modified": is_modified,
        }

        # 保存版本记录
        with open(version_path, "w", encoding="utf-8") as f:
            json.dump(versions, f, ensure_ascii=False, indent=2)

        return file_hash, is_new or is_modified

    def get_document_status(
        self, project_id: str, file_name: str
    ) -> Optional[Dict[str, Any]]:
        """
        获取文档状态

        Args:
            project_id: 项目ID
            file_name: 文件名

        Returns:
            文档状态信息，如果不存在则返回 None
        """
        version_path = self._get_project_path(project_id)

        if not os.path.exists(version_path):
            return None

        try:
            with open(version_path, "r", encoding="utf-8") as f:
                versions = json.load(f)
            return versions.get(file_name)
        except:
            return None

    def get_changed_documents(self, project_id: str) -> Dict[str, Dict[str, Any]]:
        """
        获取所有变更的文档

        Args:
            project_id: 项目ID

        Returns:
            变更文档的字典
        """
        version_path = self._get_project_path(project_id)

        if not os.path.exists(version_path):
            return {}

        try:
            with open(version_path, "r", encoding="utf-8") as f:
                versions = json.load(f)

            changed = {}
            for file_name, info in versions.items():
                if info.get("is_new") or info.get("is_modified"):
                    changed[file_name] = info

            return changed
        except:
            return {}

    def mark_embedding_cached(self, project_id: str, file_name: str):
        """
        标记文档的 embedding 已缓存

        Args:
            project_id: 项目ID
            file_name: 文件名
        """
        version_path = self._get_project_path(project_id)

        if not os.path.exists(version_path):
            return

        try:
            with open(version_path, "r", encoding="utf-8") as f:
                versions = json.load(f)

            if file_name in versions:
                versions[file_name]["embedding_cached"] = True
                versions[file_name]["is_new"] = False
                versions[file_name]["is_modified"] = False

                with open(version_path, "w", encoding="utf-8") as f:
                    json.dump(versions, f, ensure_ascii=False, indent=2)
        except:
            pass

    def get_project_stats(self, project_id: str) -> Dict[str, Any]:
        """
        获取项目文档统计

        Args:
            project_id: 项目ID

        Returns:
            统计信息
        """
        version_path = self._get_project_path(project_id)

        if not os.path.exists(version_path):
            return {"total_files": 0, "cached_files": 0, "changed_files": 0}

        try:
            with open(version_path, "r", encoding="utf-8") as f:
                versions = json.load(f)

            total = len(versions)
            cached = sum(1 for v in versions.values() if v.get("embedding_cached"))
            changed = sum(
                1 for v in versions.values() if v.get("is_new") or v.get("is_modified")
            )

            return {
                "total_files": total,
                "cached_files": cached,
                "changed_files": changed,
            }
        except:
            return {"total_files": 0, "cached_files": 0, "changed_files": 0}


# 全局缓存实例
_embedding_cache: Optional[EmbeddingCache] = None
_version_manager: Optional[DocumentVersionManager] = None


def get_embedding_cache() -> EmbeddingCache:
    """获取全局 Embedding 缓存实例"""
    global _embedding_cache
    if _embedding_cache is None:
        _embedding_cache = EmbeddingCache()
    return _embedding_cache


def get_version_manager() -> DocumentVersionManager:
    """获取全局版本管理器实例"""
    global _version_manager
    if _version_manager is None:
        _version_manager = DocumentVersionManager()
    return _version_manager
