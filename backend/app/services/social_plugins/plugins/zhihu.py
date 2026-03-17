"""
知乎平台插件

注意：此为模拟实现
实际接入需要：
1. 申请知乎开放平台账号
2. 获取 App ID 和 App Secret
3. 实现 OAuth2.0 授权流程
4. 调用知乎 Open API
"""

from typing import Dict, Any, List, Optional
from datetime import datetime

from .. import BaseSocialPlugin, SocialPost, SocialUser, PlatformType


class ZhihuPlugin(BaseSocialPlugin):
    """知乎平台插件"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.platform_name = "知乎"
        self.platform_type = PlatformType.ZHIHU
        self.app_id = self.config.get("app_id", "")
        self.app_secret = self.config.get("app_secret", "")

    def get_platform_info(self) -> Dict[str, Any]:
        return {
            "name": "知乎",
            "platform": "zhihu",
            "enabled": bool(self.app_id and self.app_secret),
            "description": "中文互联网高质量问答社区",
            "features": ["问答搜索", "用户信息", "回答评论获取", "情感分析"],
            "rate_limit": "100次/分钟",
        }

    def fetch_posts(
        self,
        keyword: Optional[str] = None,
        user_id: Optional[str] = None,
        limit: int = 20,
        **kwargs,
    ) -> List[SocialPost]:
        """获取知乎回答（模拟）"""
        posts = []

        sample_posts = [
            {
                "post_id": "zhihu_001",
                "author_id": "zhihu_001",
                "author_name": "张亮",
                "content": "作为一个从业10年的产品经理，我认为好产品的核心在于解决真实痛点。很多产品经理容易陷入「功能堆砌」的误区，忽略了用户的真实需求。",
                "likes": 15600,
                "comments": 890,
                "shares": 2340,
            },
            {
                "post_id": "zhihu_002",
                "author_id": "zhihu_002",
                "author_name": "李开复",
                "content": "AI 确实会取代一部分重复性工作，但创造力、同理心、决策力等能力仍然是人类独有的优势。关键在于学会与AI协作。",
                "likes": 34500,
                "comments": 2340,
                "shares": 8900,
            },
            {
                "post_id": "zhihu_003",
                "author_id": "zhihu_003",
                "author_name": "如何看待",
                "content": "这个问题的本质其实是资源分配问题。当蛋糕不够大的时候，如何分蛋糕就成了关键。但更重要的是先把蛋糕做大。",
                "likes": 8900,
                "comments": 567,
                "shares": 1230,
            },
        ]

        for sample in sample_posts[:limit]:
            posts.append(
                SocialPost(
                    platform="zhihu",
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
        """获取回答详情"""
        posts = self.fetch_posts(limit=10)
        for post in posts:
            if post.post_id == post_id:
                return post
        return None

    def fetch_user_info(self, user_id: str) -> Optional[SocialUser]:
        """获取用户信息"""
        sample_users = {
            "zhihu_001": {
                "user_id": "zhihu_001",
                "username": "zhangliang",
                "display_name": "张亮",
                "followers": 890000,
                "following": 234,
                "bio": "产品经理 | 10年经验 | 关注产品思考",
                "verified": True,
            },
            "zhihu_002": {
                "user_id": "zhihu_002",
                "username": "kaifu",
                "display_name": "李开复",
                "followers": 15600000,
                "following": 89,
                "bio": "创新工场CEO | 人工智能研究员",
                "verified": True,
            },
        }

        user_data = sample_users.get(user_id)
        if not user_data:
            return None

        return SocialUser(platform="zhihu", **user_data, raw_data=user_data)

    def fetch_comments(
        self, post_id: str, limit: int = 50, **kwargs
    ) -> List[Dict[str, Any]]:
        """获取评论列表"""
        comments = [
            {"comment_id": "zhc001", "user": "用户A", "content": "说的很有道理！"},
            {"comment_id": "zhc002", "user": "用户B", "content": "受益匪浅"},
            {"comment_id": "zhc003", "user": "用户C", "content": "赞！"},
        ]
        return comments[:limit]
