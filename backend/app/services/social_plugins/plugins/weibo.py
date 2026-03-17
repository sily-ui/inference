"""
微博平台插件

注意：此为模拟实现
实际接入需要：
1. 申请微博开放平台账号
2. 获取 App Key 和 App Secret
3. 实现 OAuth2.0 授权流程
4. 调用微博 Open API
"""

from typing import Dict, Any, List, Optional
from datetime import datetime

from .. import BaseSocialPlugin, SocialPost, SocialUser, PlatformType


class WeiboPlugin(BaseSocialPlugin):
    """微博平台插件"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.platform_name = "微博"
        self.platform_type = PlatformType.WEIBO
        self.app_key = self.config.get("app_key", "")
        self.app_secret = self.config.get("app_secret", "")

    def get_platform_info(self) -> Dict[str, Any]:
        return {
            "name": "微博",
            "platform": "weibo",
            "enabled": bool(self.app_key and self.app_secret),
            "description": "中国最具影响力的社交媒体平台",
            "features": ["微博搜索", "用户信息", "评论获取", "情感分析", "热点话题"],
            "rate_limit": "100次/分钟",
        }

    def fetch_posts(
        self,
        keyword: Optional[str] = None,
        user_id: Optional[str] = None,
        limit: int = 20,
        **kwargs,
    ) -> List[SocialPost]:
        """获取微博"""
        posts = []

        sample_posts = [
            {
                "post_id": "weibo_001",
                "author_id": "user_w001",
                "author_name": "科技评测师",
                "content": "这款新手机太牛了！拍照效果吊打同价位所有竞品，性能也超级给力。",
                "likes": 8562,
                "comments": 1234,
                "shares": 3456,
            },
            {
                "post_id": "weibo_002",
                "author_id": "user_w002",
                "author_name": "娱乐圈八卦",
                "content": "独家消息：某顶流明星即将官宣新恋情？粉丝们准备好了吗？",
                "likes": 23456,
                "comments": 5678,
                "shares": 8901,
            },
            {
                "post_id": "weibo_003",
                "author_id": "user_w003",
                "author_name": "财经观察",
                "content": "今天的股市太刺激了！建议大家还是要谨慎投资，不要盲目跟风。",
                "likes": 3456,
                "comments": 567,
                "shares": 234,
            },
        ]

        for sample in sample_posts[:limit]:
            posts.append(
                SocialPost(
                    platform="weibo",
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
        """获取微博详情"""
        posts = self.fetch_posts(limit=10)
        for post in posts:
            if post.post_id == post_id:
                return post
        return None

    def fetch_user_info(self, user_id: str) -> Optional[SocialUser]:
        """获取用户信息"""
        sample_users = {
            "user_w001": {
                "user_id": "user_w001",
                "username": "tech_reviewer",
                "display_name": "科技评测师",
                "followers": 1256000,
                "following": 567,
                "bio": "数码科技博主 | 专注产品评测",
                "verified": True,
            },
            "user_w002": {
                "user_id": "user_w002",
                "username": "entertainment_news",
                "display_name": "娱乐圈八卦",
                "followers": 5678000,
                "following": 234,
                "bio": "娱乐圈第一手八卦资讯",
                "verified": True,
            },
        }

        user_data = sample_users.get(user_id)
        if not user_data:
            return None

        return SocialUser(platform="weibo", **user_data, raw_data=user_data)

    def fetch_comments(
        self, post_id: str, limit: int = 50, **kwargs
    ) -> List[Dict[str, Any]]:
        """获取评论列表"""
        comments = [
            {"comment_id": "wc001", "user": "用户A", "content": "说的太对了！"},
            {"comment_id": "wc002", "user": "用户B", "content": "期待已久！"},
            {"comment_id": "wc003", "user": "用户C", "content": "坐等官宣"},
        ]
        return comments[:limit]
