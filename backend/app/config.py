"""
配置管理
统一从项目根目录的 .env 文件加载配置
"""

import os
from dotenv import load_dotenv

# 加载项目根目录的 .env 文件
# 路径: MiroFish/.env (相对于 backend/app/config.py)
project_root_env = os.path.join(os.path.dirname(__file__), "../../.env")

if os.path.exists(project_root_env):
    load_dotenv(project_root_env, override=True)
    print(f"[DEBUG] 加载 .env 文件: {project_root_env}")
else:
    print(f"[DEBUG] .env 文件不存在: {project_root_env}")
    load_dotenv(override=True)

# 调试：打印实际加载的 ZEP_API_KEY
print(
    f"[DEBUG] ZEP_API_KEY: {os.environ.get('ZEP_API_KEY', 'NOT_SET')[:20] if os.environ.get('ZEP_API_KEY') else 'NOT_SET'}..."
)


class Config:
    """Flask配置类"""

    # Flask配置
    SECRET_KEY = os.environ.get("SECRET_KEY", "mirofish-secret-key")
    DEBUG = os.environ.get("FLASK_DEBUG", "True").lower() == "true"

    # JSON配置 - 禁用ASCII转义，让中文直接显示（而不是 \uXXXX 格式）
    JSON_AS_ASCII = False

    # LLM配置（统一使用OpenAI格式）
    LLM_API_KEY = os.environ.get("LLM_API_KEY")
    LLM_BASE_URL = os.environ.get("LLM_BASE_URL", "https://api.openai.com/v1")
    LLM_MODEL_NAME = os.environ.get("LLM_MODEL_NAME", "gpt-4o-mini")

    # Zep配置
    ZEP_API_KEY = os.environ.get("ZEP_API_KEY")

    # 文件上传配置
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50MB
    UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "../uploads")
    ALLOWED_EXTENSIONS = {"pdf", "md", "txt", "markdown"}

    # 文本处理配置
    DEFAULT_CHUNK_SIZE = 500  # 默认切块大小
    DEFAULT_CHUNK_OVERLAP = 50  # 默认重叠大小

    # OASIS模拟配置
    OASIS_DEFAULT_MAX_ROUNDS = int(os.environ.get("OASIS_DEFAULT_MAX_ROUNDS", "10"))
    OASIS_SIMULATION_DATA_DIR = os.path.join(
        os.path.dirname(__file__), "../uploads/simulations"
    )

    # OASIS平台可用动作配置
    OASIS_TWITTER_ACTIONS = [
        "CREATE_POST",
        "LIKE_POST",
        "REPOST",
        "FOLLOW",
        "DO_NOTHING",
        "QUOTE_POST",
    ]
    OASIS_REDDIT_ACTIONS = [
        "LIKE_POST",
        "DISLIKE_POST",
        "CREATE_POST",
        "CREATE_COMMENT",
        "LIKE_COMMENT",
        "DISLIKE_COMMENT",
        "SEARCH_POSTS",
        "SEARCH_USER",
        "TREND",
        "REFRESH",
        "DO_NOTHING",
        "FOLLOW",
        "MUTE",
    ]

    # Report Agent配置
    REPORT_AGENT_MAX_TOOL_CALLS = int(
        os.environ.get("REPORT_AGENT_MAX_TOOL_CALLS", "5")
    )
    REPORT_AGENT_MAX_REFLECTION_ROUNDS = int(
        os.environ.get("REPORT_AGENT_MAX_REFLECTION_ROUNDS", "2")
    )
    REPORT_AGENT_TEMPERATURE = float(os.environ.get("REPORT_AGENT_TEMPERATURE", "0.5"))

    # Redis缓存配置
    REDIS_URL = os.environ.get("REDIS_URL")
    LLM_CACHE_TTL = int(os.environ.get("LLM_CACHE_TTL", "3600"))

    # PostgreSQL 数据库配置
    DATABASE_URL = os.environ.get("DATABASE_URL")
    SQLALCHEMY_DATABASE_URI = DATABASE_URL
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_recycle": 300,
    }

    @classmethod
    def validate(cls):
        """验证必要配置"""
        errors = []
        if not cls.LLM_API_KEY:
            errors.append("LLM_API_KEY 未配置")
        if not cls.ZEP_API_KEY:
            errors.append("ZEP_API_KEY 未配置")
        if not cls.DATABASE_URL:
            errors.append("DATABASE_URL 未配置")
        return errors
