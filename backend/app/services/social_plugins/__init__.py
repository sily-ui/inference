"""
社交媒体插件系统

功能：
- 统一插件接口规范
- 支持多平台接入（小红书、微博、抖音、B站、知乎）
- MCP协议标准化LLM调用能力
- 跨LLM模型无感切换
- 情感分析能力

插件工作流程：
真实平台API对接 → 原始数据拉取 → MCP协议情感分析 → 统一格式输出
"""

import os
import json
import hashlib
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime

from ..utils.llm_client import LLMClient
from ..config import Config


class PlatformType(Enum):
    """支持的平台类型"""

    XIAOHONGSHU = "xiaohongshu"  # 小红书
    WEIBO = "weibo"  # 微博
    DOUYIN = "douyin"  # 抖音
    BILIBILI = "bilibili"  # B站
    ZHIHU = "zhihu"  # 知乎


@dataclass
class SocialPost:
    """社交媒体帖子统一格式"""

    platform: str  # 平台标识
    post_id: str  # 帖子ID
    author_id: str  # 作者ID
    author_name: str  # 作者名称
    content: str  # 文本内容
    created_at: str  # 创建时间
    likes: int = 0  # 点赞数
    comments: int = 0  # 评论数
    shares: int = 0  # 分享数
    raw_data: Dict[str, Any] = field(default_factory=dict)  # 原始数据
    sentiment: Optional[Dict[str, Any]] = field(default_factory=dict)  # 情感分析结果


@dataclass
class SocialUser:
    """社交媒体用户统一格式"""

    platform: str
    user_id: str
    username: str
    display_name: str
    followers: int = 0
    following: int = 0
    bio: str = ""
    verified: bool = False
    raw_data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SentimentResult:
    """情感分析结果"""

    label: str  # positive / negative / neutral
    score: float  # 置信度 0-1
    emotions: List[str]  # 情绪标签列表
    summary: str  # 情感摘要
    aspects: List[Dict[str, Any]] = field(default_factory=list)  # 方面情感


class MCPClient:
    """
    MCP (Model Context Protocol) 客户端
    标准化 LLM 调用能力，支持跨模型无感切换
    """

    def __init__(self, model_name: Optional[str] = None):
        """
        初始化MCP客户端

        Args:
            model_name: 使用的LLM模型名称，默认使用配置中的模型
        """
        self.llm_client = LLMClient()
        self.model_name = model_name or Config.LLM_MODEL_NAME
        self._model_cache = {}

    def set_model(self, model_name: str):
        """
        切换LLM模型

        Args:
            model_name: 模型名称
        """
        self.model_name = model_name

    def analyze_sentiment(
        self, text: str, context: Optional[str] = None
    ) -> SentimentResult:
        """
        情感分析（基于LLM）

        Args:
            text: 待分析文本
            context: 上下文信息（可选）

        Returns:
            SentimentResult 情感分析结果
        """
        system_prompt = """你是一个专业的情感分析专家。请分析给定文本的情感倾向。

要求：
1. 判断情感标签：positive（正面）、negative（负面）、neutral（中性）
2. 输出置信度分数（0-1之间的浮点数）
3. 识别主要情绪标签，如：喜悦、愤怒、悲伤、惊讶、恐惧、厌恶等
4. 给出简短的情感摘要（不超过50字）
5. 如果文本涉及多个方面，分析每个方面的情感（可选）

请以JSON格式返回结果：
{
    "label": "positive/negative/neutral",
    "score": 0.85,
    "emotions": ["喜悦", "期待"],
    "summary": "用户对产品表示满意，期待新品发布",
    "aspects": [
        {"aspect": "产品质量", "sentiment": "positive", "score": 0.9}
    ]
}
"""

        user_prompt = f"文本：{text}"
        if context:
            user_prompt += f"\n上下文：{context}"

        try:
            response = self.llm_client.chat(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.3,
                max_tokens=1000,
                response_format="json",
            )

            content = response.get("content", "{}")

            # 解析JSON响应
            try:
                # 处理可能的markdown代码块
                if "```json" in content:
                    content = content.split("```json")[1].split("```")[0]
                elif "```" in content:
                    content = content.split("```")[1].split("```")[0]

                result = json.loads(content)
                return SentimentResult(
                    label=result.get("label", "neutral"),
                    score=float(result.get("score", 0.5)),
                    emotions=result.get("emotions", []),
                    summary=result.get("summary", ""),
                    aspects=result.get("aspects", []),
                )
            except json.JSONDecodeError:
                # 解析失败，返回默认结果
                return SentimentResult(
                    label="neutral", score=0.5, emotions=[], summary="情感分析失败"
                )

        except Exception as e:
            return SentimentResult(
                label="neutral", score=0.0, emotions=[], summary=f"分析异常: {str(e)}"
            )

    def batch_analyze_sentiment(
        self, texts: List[str], context: Optional[str] = None
    ) -> List[SentimentResult]:
        """
        批量情感分析

        Args:
            texts: 文本列表
            context: 上下文信息

        Returns:
            情感分析结果列表
        """
        results = []
        for text in texts:
            result = self.analyze_sentiment(text, context)
            results.append(result)
        return results


class BaseSocialPlugin(ABC):
    """
    社交媒体插件基类

    所有平台插件必须继承此类并实现抽象方法
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化插件

        Args:
            config: 插件配置（如API密钥等）
        """
        self.config = config or {}
        self.platform_name = ""
        self.platform_type = None
        self.mcp_client = MCPClient()

    @abstractmethod
    def get_platform_info(self) -> Dict[str, Any]:
        """
        获取平台信息

        Returns:
            平台信息字典
        """
        pass

    @abstractmethod
    def fetch_posts(
        self,
        keyword: Optional[str] = None,
        user_id: Optional[str] = None,
        limit: int = 20,
        **kwargs,
    ) -> List[SocialPost]:
        """
        获取帖子列表

        Args:
            keyword: 搜索关键词
            user_id: 用户ID
            limit: 返回数量限制
            **kwargs: 其他参数

        Returns:
            SocialPost 列表
        """
        pass

    @abstractmethod
    def fetch_post_detail(self, post_id: str) -> Optional[SocialPost]:
        """
        获取帖子详情

        Args:
            post_id: 帖子ID

        Returns:
            SocialPost 或 None
        """
        pass

    @abstractmethod
    def fetch_user_info(self, user_id: str) -> Optional[SocialUser]:
        """
        获取用户信息

        Args:
            user_id: 用户ID

        Returns:
            SocialUser 或 None
        """
        pass

    @abstractmethod
    def fetch_comments(
        self, post_id: str, limit: int = 50, **kwargs
    ) -> List[Dict[str, Any]]:
        """
        获取评论列表

        Args:
            post_id: 帖子ID
            limit: 返回数量限制

        Returns:
            评论列表
        """
        pass

    def analyze_post_sentiment(self, post: SocialPost) -> SocialPost:
        """
        分析帖子情感

        Args:
            post: 帖子对象

        Returns:
            带情感分析结果的帖子
        """
        sentiment = self.mcp_client.analyze_sentiment(post.content)
        post.sentiment = {
            "label": sentiment.label,
            "score": sentiment.score,
            "emotions": sentiment.emotions,
            "summary": sentiment.summary,
            "aspects": sentiment.aspects,
        }
        return post

    def batch_analyze_posts_sentiment(
        self, posts: List[SocialPost], progress_callback: Optional[Callable] = None
    ) -> List[SocialPost]:
        """
        批量分析帖子情感

        Args:
            posts: 帖子列表
            progress_callback: 进度回调函数

        Returns:
            带情感分析结果的帖子列表
        """
        for i, post in enumerate(posts):
            post = self.analyze_post_sentiment(post)
            if progress_callback:
                progress_callback(i + 1, len(posts))
        return posts

    def search_and_analyze(
        self, keyword: str, limit: int = 20, analyze_sentiment: bool = True
    ) -> Dict[str, Any]:
        """
        搜索并分析（完整流程）

        Args:
            keyword: 搜索关键词
            limit: 返回数量
            analyze_sentiment: 是否进行情感分析

        Returns:
            统一格式的搜索结果
        """
        # 1. 获取帖子
        posts = self.fetch_posts(keyword=keyword, limit=limit)

        # 2. 情感分析
        if analyze_sentiment:
            posts = self.batch_analyze_posts_sentiment(posts)

        # 3. 统计分析
        sentiment_stats = self._calculate_sentiment_stats(posts)

        # 4. 格式化输出
        return {
            "platform": self.platform_name,
            "keyword": keyword,
            "total_posts": len(posts),
            "posts": [self._format_post(p) for p in posts],
            "sentiment_stats": sentiment_stats,
            "fetched_at": datetime.now().isoformat(),
        }

    def _calculate_sentiment_stats(self, posts: List[SocialPost]) -> Dict[str, Any]:
        """计算情感统计"""
        total = len(posts)
        if total == 0:
            return {"positive": 0, "negative": 0, "neutral": 0}

        stats = {"positive": 0, "negative": 0, "neutral": 0}
        total_score = 0.0

        for post in posts:
            label = post.sentiment.get("label", "neutral")
            if label in stats:
                stats[label] += 1
            total_score += post.sentiment.get("score", 0.5)

        # 转换为百分比
        stats_pct = {k: round(v / total * 100, 2) for k, v in stats.items()}

        return {**stats, **stats_pct, "average_score": round(total_score / total, 3)}

    def _format_post(self, post: SocialPost) -> Dict[str, Any]:
        """格式化帖子输出"""
        return {
            "post_id": post.post_id,
            "author": {"id": post.author_id, "name": post.author_name},
            "content": post.content,
            "metrics": {
                "likes": post.likes,
                "comments": post.comments,
                "shares": post.shares,
            },
            "created_at": post.created_at,
            "sentiment": post.sentiment,
        }


class SocialPluginManager:
    """
    社交媒体插件管理器

    负责插件的注册、加载和调度
    """

    _plugins: Dict[str, BaseSocialPlugin] = {}
    _initialized = False

    @classmethod
    def register_plugin(cls, platform: str, plugin: BaseSocialPlugin):
        """
        注册插件

        Args:
            platform: 平台标识
            plugin: 插件实例
        """
        cls._plugins[platform] = plugin

    @classmethod
    def get_plugin(cls, platform: str) -> Optional[BaseSocialPlugin]:
        """
        获取插件

        Args:
            platform: 平台标识

        Returns:
            插件实例或None
        """
        return cls._plugins.get(platform)

    @classmethod
    def get_all_plugins(cls) -> Dict[str, BaseSocialPlugin]:
        """获取所有已注册的插件"""
        return cls._plugins.copy()

    @classmethod
    def get_supported_platforms(cls) -> List[Dict[str, Any]]:
        """
        获取支持的平台列表

        Returns:
            平台信息列表
        """
        platforms = []
        for platform, plugin in cls._plugins.items():
            info = plugin.get_platform_info()
            info["platform"] = platform
            platforms.append(info)
        return platforms

    @classmethod
    def initialize_plugins(cls):
        """
        初始化所有插件

        从配置中读取各平台API密钥并初始化插件
        """
        if cls._initialized:
            return

        # 这里会导入各个插件并注册
        # 实际初始化由具体的插件模块完成
        cls._initialized = True

    @classmethod
    def search_all_platforms(
        cls,
        keyword: str,
        platforms: Optional[List[str]] = None,
        limit_per_platform: int = 20,
        analyze_sentiment: bool = True,
    ) -> Dict[str, Any]:
        """
        跨平台搜索

        Args:
            keyword: 搜索关键词
            platforms: 平台列表，None表示所有平台
            limit_per_platform: 每个平台返回数量
            analyze_sentiment: 是否情感分析

        Returns:
            跨平台搜索结果
        """
        results = {
            "keyword": keyword,
            "platforms_searched": [],
            "total_posts": 0,
            "posts": [],
            "sentiment_stats": {},
            "fetched_at": datetime.now().isoformat(),
        }

        target_platforms = platforms or list(cls._plugins.keys())

        for platform in target_platforms:
            plugin = cls.get_plugin(platform)
            if not plugin:
                continue

            try:
                result = plugin.search_and_analyze(
                    keyword=keyword,
                    limit=limit_per_platform,
                    analyze_sentiment=analyze_sentiment,
                )

                results["platforms_searched"].append(platform)
                results["total_posts"] += result["total_posts"]
                results["posts"].extend(result["posts"])
                results["sentiment_stats"][platform] = result["sentiment_stats"]

            except Exception as e:
                results["sentiment_stats"][platform] = {"error": str(e)}

        # 汇总情感统计
        if results["posts"]:
            all_sentiments = [
                p.get("sentiment", {}).get("label", "neutral") for p in results["posts"]
            ]
            results["overall_sentiment"] = {
                "positive": all_sentiments.count("positive"),
                "negative": all_sentiments.count("negative"),
                "neutral": all_sentiments.count("neutral"),
            }

        return results


# 全局MCP客户端实例
_mcp_client: Optional[MCPClient] = None


def get_mcp_client() -> MCPClient:
    """获取全局MCP客户端"""
    global _mcp_client
    if _mcp_client is None:
        _mcp_client = MCPClient()
    return _mcp_client


def initialize_social_plugins():
    """
    初始化所有社交媒体插件

    调用此函数注册所有支持的平台插件
    从环境变量读取各平台API配置
    """
    from .plugins.xiaohongshu import XiaohongshuPlugin
    from .plugins.weibo import WeiboPlugin
    from .plugins.douyin import DouyinPlugin
    from .plugins.bilibili import BilibiliPlugin
    from .plugins.zhihu import ZhihuPlugin

    # 各平台配置从环境变量读取
    xiaohongshu_config = {
        "app_key": os.environ.get("XIAOHONGSHU_APP_KEY", ""),
        "app_secret": os.environ.get("XIAOHONGSHU_APP_SECRET", "")
    }
    weibo_config = {
        "app_key": os.environ.get("WEIBO_APP_KEY", ""),
        "app_secret": os.environ.get("WEIBO_APP_SECRET", "")
    }
    douyin_config = {
        "app_key": os.environ.get("DOUYIN_APP_KEY", ""),
        "app_secret": os.environ.get("DOUYIN_APP_SECRET", "")
    }
    bilibili_config = {
        "app_key": os.environ.get("BILIBILI_APP_KEY", ""),
        "app_secret": os.environ.get("BILIBILI_APP_SECRET", "")
    }
    zhihu_config = {
        "app_key": os.environ.get("ZHIHU_APP_KEY", ""),
        "app_secret": os.environ.get("ZHIHU_APP_SECRET", "")
    }

    # 注册所有插件
    SocialPluginManager.register_plugin("xiaohongshu", XiaohongshuPlugin(xiaohongshu_config))
    SocialPluginManager.register_plugin("weibo", WeiboPlugin(weibo_config))
    SocialPluginManager.register_plugin("douyin", DouyinPlugin(douyin_config))
    SocialPluginManager.register_plugin("bilibili", BilibiliPlugin(bilibili_config))
    SocialPluginManager.register_plugin("zhihu", ZhihuPlugin(zhihu_config))

    SocialPluginManager._initialized = True
