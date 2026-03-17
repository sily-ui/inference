"""
B站平台插件

注意：此为模拟实现
实际接入需要：
1. 申请B站开放平台账号
2. 获取 App ID 和 App Secret
3. 实现 OAuth2.0 授权流程
4. 调用B站 Open API
"""

from typing import Dict, Any, List, Optional
from datetime import datetime

from .. import BaseSocialPlugin, SocialPost, SocialUser, PlatformType


class BilibiliPlugin(BaseSocialPlugin):
    """B站平台插件"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.platform_name = "B站"
        self.platform_type = PlatformType.BILIBILI
        self.app_id = self.config.get("app_id", "")
        self.app_secret = self.config.get("app_secret", "")

    def get_platform_info(self) -> Dict[str, Any]:
        return {
            "name": "B站",
            "platform": "bilibili",
            "enabled": bool(self.app_id and self.app_secret),
            "description": "年轻人潮流文化视频社区",
            "features": ["视频搜索", "UP主信息", "弹幕评论获取", "情感分析"],
            "rate_limit": "100次/分钟",
        }

    def fetch_posts(
        self,
        keyword: Optional[str] = None,
        user_id: Optional[str] = None,
        limit: int = 20,
        **kwargs,
    ) -> List[SocialPost]:
        """获取B站视频（模拟）"""
        posts = []

        sample_posts = [
            {
                "post_id": "bilibili_001",
                "author_id": "up_001",
                "author_name": "老番茄",
                "content": "【全站最强】2024年度盘点！这可能是你看过最燃的视频了！",
                "likes": 890000,
                "comments": 45600,
                "shares": 123000,
            },
            {
                "post_id": "bilibili_002",
                "author_id": "up_002",
                "author_name": "罗翔说刑法",
                "content": "张三到底算不算正当防卫？法律角度深度分析！",
                "likes": 456000,
                "comments": 23400,
                "shares": 67000,
            },
            {
                "post_id": "bilibili_003",
                "author_id": "up_003",
                "author_name": "影视飓风",
                "content": "【保姆级教程】如何用手机拍出电影级画面？",
                "likes": 678000,
                "comments": 34500,
                "shares": 89000,
            },
        ]

        for sample in sample_posts[:limit]:
            posts.append(
                SocialPost(
                    platform="bilibili",
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
        """获取UP主信息"""
        sample_users = {
            "up_001": {
                "user_id": "up_001",
                "username": "laofanqie",
                "display_name": "老番茄",
                "followers": 28900000,
                "following": 156,
                "bio": "B站2023年度百大UP主 | 搞笑分区",
                "verified": True,
            },
            "up_002": {
                "user_id": "up_002",
                "username": "luoxiang刑法",
                "display_name": "罗翔说刑法",
                "followers": 28900000,
                "following": 89,
                "bio": "中国政法大学教授 | 普法达人",
                "verified": True,
            },
        }

        user_data = sample_users.get(user_id)
        if not user_data:
            return None

        return SocialUser(platform="bilibili", **user_data, raw_data=user_data)

    def fetch_comments(
        self, post_id: str, limit: int = 50, **kwargs
    ) -> List[Dict[str, Any]]:
        """获取弹幕/评论列表"""
        comments = [
            {"comment_id": "bbc001", "user": "用户A", "content": "前方高能！"},
            {"comment_id": "bbc002", "user": "用户B", "content": "学到了！"},
            {"comment_id": "bbc003", "user": "用户C", "content": "太强了！"},
        ]
        return comments[:limit]
