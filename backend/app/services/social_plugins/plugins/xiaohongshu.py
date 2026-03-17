"""
小红书平台插件

注意：此为模拟实现
实际接入需要：
1. 申请小红书开放平台账号
2. 获取 AppKey 和 AppSecret
3. 实现 OAuth2.0 授权流程
4. 调用小红书 Open API
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
import hashlib
import time

from .. import BaseSocialPlugin, SocialPost, SocialUser, PlatformType


class XiaohongshuPlugin(BaseSocialPlugin):
    """小红书平台插件"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.platform_name = "小红书"
        self.platform_type = PlatformType.XIAOHONGSHU
        self.app_key = self.config.get("app_key", "")
        self.app_secret = self.config.get("app_secret", "")

    def get_platform_info(self) -> Dict[str, Any]:
        return {
            "name": "小红书",
            "platform": "xiaohongshu",
            "enabled": bool(self.app_key and self.app_secret),
            "description": "生活方式分享平台",
            "features": ["笔记搜索", "用户信息", "评论获取", "情感分析"],
            "rate_limit": "100次/分钟",
        }

    def fetch_posts(
        self,
        keyword: Optional[str] = None,
        user_id: Optional[str] = None,
        limit: int = 20,
        **kwargs,
    ) -> List[SocialPost]:
        """
        获取小红书笔记

        注意：此处为模拟实现
        实际应调用小红书开放平台 API
        """
        # 模拟API调用
        posts = []

        # 模拟数据
        sample_posts = [
            {
                "post_id": "xhs_001",
                "author_id": "user_001",
                "author_name": "美妆博主Lily",
                "content": "这款护肤品真的太好用了！用了两周皮肤明显变好了，强烈推荐！",
                "likes": 1523,
                "comments": 89,
                "shares": 234,
            },
            {
                "post_id": "xhs_002",
                "author_id": "user_002",
                "author_name": "美食探店小分队",
                "content": "今天去了一家超火的餐厅，排队两小时但味道真的值得！",
                "likes": 3421,
                "comments": 156,
                "shares": 567,
            },
            {
                "post_id": "xhs_003",
                "author_id": "user_003",
                "author_name": "旅行达人Jack",
                "content": "这个景点人少景美，拍照超级出片！",
                "likes": 2156,
                "comments": 78,
                "shares": 189,
            },
        ]

        for i, sample in enumerate(sample_posts[:limit]):
            posts.append(
                SocialPost(
                    platform="xiaohongshu",
                    post_id=sample["post_id"],
                    author_id=sample["author_id"],
                    author_name=sample["author_name"],
                    content=sample["content"],
                    created_at=datetime.now().isoformat(),
                    likes=sample["likes"],
                    comments=sample["comments"],
                    shares=sample["shares"],
                    raw_data=sample,
                )
            )

        return posts

    def fetch_post_detail(self, post_id: str) -> Optional[SocialPost]:
        """获取笔记详情"""
        posts = self.fetch_posts(limit=10)
        for post in posts:
            if post.post_id == post_id:
                return post
        return None

    def fetch_user_info(self, user_id: str) -> Optional[SocialUser]:
        """获取用户信息"""
        # 模拟用户数据
        sample_users = {
            "user_001": {
                "user_id": "user_001",
                "username": "beauty_lily",
                "display_name": "美妆博主Lily",
                "followers": 256000,
                "following": 1234,
                "bio": "美妆博主 | 分享变美干货",
                "verified": True,
            },
            "user_002": {
                "user_id": "user_002",
                "username": "food_explorer",
                "display_name": "美食探店小分队",
                "followers": 189000,
                "following": 892,
                "bio": "吃遍全球美食 | 探店达人",
                "verified": True,
            },
        }

        user_data = sample_users.get(user_id)
        if not user_data:
            return None

        return SocialUser(platform="xiaohongshu", **user_data, raw_data=user_data)

    def fetch_comments(
        self, post_id: str, limit: int = 50, **kwargs
    ) -> List[Dict[str, Any]]:
        """获取评论列表"""
        # 模拟评论数据
        comments = [
            {"comment_id": "c001", "user": "用户A", "content": "求推荐具体产品！"},
            {"comment_id": "c002", "user": "用户B", "content": "真的好用吗？"},
            {"comment_id": "c003", "user": "用户C", "content": "谢谢分享～"},
        ]
        return comments[:limit]
