"""
抖音平台插件

注意：此为模拟实现
实际接入需要：
1. 申请抖音开放平台账号
2. 获取 Client Key 和 Client Secret
3. 实现 OAuth2.0 授权流程
4. 调用抖音 Open API
"""

from typing import Dict, Any, List, Optional
from datetime import datetime

from .. import BaseSocialPlugin, SocialPost, SocialUser, PlatformType


class DouyinPlugin(BaseSocialPlugin):
    """抖音平台插件"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.platform_name = "抖音"
        self.platform_type = PlatformType.DOUYIN
        self.client_key = self.config.get("client_key", "")
        self.client_secret = self.config.get("client_secret", "")

    def get_platform_info(self) -> Dict[str, Any]:
        return {
            "name": "抖音",
            "platform": "douyin",
            "enabled": bool(self.client_key and self.client_secret),
            "description": "短视频社交平台",
            "features": ["视频搜索", "用户信息", "评论获取", "情感分析", "热点话题"],
            "rate_limit": "100次/分钟",
        }

    def fetch_posts(
        self,
        keyword: Optional[str] = None,
        user_id: Optional[str] = None,
        limit: int = 20,
        **kwargs,
    ) -> List[SocialPost]:
        """获取抖音视频（模拟）"""
        posts = []

        sample_posts = [
            {
                "post_id": "dy_001",
                "author_id": "user_dy001",
                "author_name": "搞笑达人",
                "content": "今天的快乐是这只好看的猫给的！太萌了哈哈哈",
                "likes": 156000,
                "comments": 8900,
                "shares": 23000,
            },
            {
                "post_id": "dy_002",
                "author_id": "user_dy002",
                "author_name": "美食日记",
                "content": "在家做了一道超级简单的家常菜，学会了秒变大厨！",
                "likes": 89000,
                "comments": 4500,
                "shares": 12000,
            },
            {
                "post_id": "dy_003",
                "author_id": "user_dy003",
                "author_name": "健身教练",
                "content": "每天5分钟，轻松瘦全身！跟着我做起来",
                "likes": 234000,
                "comments": 12000,
                "shares": 45000,
            },
        ]

        for sample in sample_posts[:limit]:
            posts.append(
                SocialPost(
                    platform="douyin",
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
        """获取视频详情"""
        posts = self.fetch_posts(limit=10)
        for post in posts:
            if post.post_id == post_id:
                return post
        return None

    def fetch_user_info(self, user_id: str) -> Optional[SocialUser]:
        """获取用户信息"""
        sample_users = {
            "user_dy001": {
                "user_id": "user_dy001",
                "username": "funny_cat",
                "display_name": "搞笑达人",
                "followers": 2560000,
                "following": 123,
                "bio": "每天分享快乐 | 记得关注哦",
                "verified": True,
            },
            "user_dy002": {
                "user_id": "user_dy002",
                "username": "food_diary",
                "display_name": "美食日记",
                "followers": 1890000,
                "following": 234,
                "bio": "美食教程 | 家常菜做法",
                "verified": True,
            },
        }

        user_data = sample_users.get(user_id)
        if not user_data:
            return None

        return SocialUser(platform="douyin", **user_data, raw_data=user_data)

    def fetch_comments(
        self, post_id: str, limit: int = 50, **kwargs
    ) -> List[Dict[str, Any]]:
        """获取评论列表"""
        comments = [
            {"comment_id": "dyc001", "user": "用户A", "content": "太可爱了！"},
            {"comment_id": "dyc002", "user": "用户B", "content": "学会了！"},
            {"comment_id": "dyc003", "user": "用户C", "content": "支持！"},
        ]
        return comments[:limit]
