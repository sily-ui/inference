"""
MiroFish Backend - Flask应用工厂
"""

import os
import warnings

# 抑制 multiprocessing resource_tracker 的警告（来自第三方库如 transformers）
# 需要在所有其他导入之前设置
warnings.filterwarnings("ignore", message=".*resource_tracker.*")

from flask import Flask, request
from flask_cors import CORS
from flasgger import Swagger

from .config import Config
from .utils.logger import setup_logger, get_logger
from .models.database import db


def create_app(config_class=Config):
    """Flask应用工厂函数"""
    app = Flask(__name__)
    app.config.from_object(config_class)

    # 初始化数据库
    db.init_app(app)

    # 设置JSON编码：确保中文直接显示（而不是 \uXXXX 格式）
    # Flask >= 2.3 使用 app.json.ensure_ascii，旧版本使用 JSON_AS_ASCII 配置
    if hasattr(app, "json") and hasattr(app.json, "ensure_ascii"):
        app.json.ensure_ascii = False

    # Swagger配置
    swagger_config = {
        "headers": [],
        "specs": [
            {
                "endpoint": "apispec",
                "route": "/apispec.json",
                "rule_filter": lambda rule: True,
                "model_filter": lambda tag: True,
            }
        ],
        "static_url_path": "/flasgger_static",
        "swagger_ui": True,
        "specs_route": "/api/docs/",
    }

    swagger_template = {
        "info": {
            "title": "MiroFish API",
            "description": "MiroFish - 简洁通用的群体智能引擎 API",
            "version": "1.0.0",
            "contact": {"name": "MiroFish Team", "email": "mirofish@shanda.com"},
        },
        "securityDefinitions": {
            "Bearer": {
                "type": "apiKey",
                "name": "Authorization",
                "in": "header",
                "description": "JWT Bearer token. Example: Bearer {token}",
            }
        },
    }

    Swagger(app, config=swagger_config, template=swagger_template)

    # 设置日志
    logger = setup_logger("mirofish")

    # 只在 reloader 子进程中打印启动信息（避免 debug 模式下打印两次）
    is_reloader_process = os.environ.get("WERKZEUG_RUN_MAIN") == "true"
    debug_mode = app.config.get("DEBUG", False)
    should_log_startup = not debug_mode or is_reloader_process

    if should_log_startup:
        logger.info("=" * 50)
        logger.info("MiroFish Backend 启动中...")
        logger.info("=" * 50)

    # 创建数据库表
    with app.app_context():
        db.create_all()
        if should_log_startup:
            logger.info("数据库表初始化完成")

    # 启用CORS
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    # 注册模拟进程清理函数（确保服务器关闭时终止所有模拟进程）
    from .services.simulation_runner import SimulationRunner

    SimulationRunner.register_cleanup()
    if should_log_startup:
        logger.info("已注册模拟进程清理函数")

    # 请求日志中间件
    @app.before_request
    def log_request():
        logger = get_logger("mirofish.request")
        logger.debug(f"请求: {request.method} {request.path}")
        if request.content_type and "json" in request.content_type:
            logger.debug(f"请求体: {request.get_json(silent=True)}")

    @app.after_request
    def log_response(response):
        logger = get_logger("mirofish.request")
        logger.debug(f"响应: {response.status_code}")
        return response

    # 注册蓝图
    from .api import graph_bp, simulation_bp, report_bp, social_bp, prediction_bp

    app.register_blueprint(graph_bp, url_prefix="/api/graph")
    app.register_blueprint(simulation_bp, url_prefix="/api/simulation")
    app.register_blueprint(report_bp, url_prefix="/api/report")
    app.register_blueprint(social_bp, url_prefix="/api/social")
    app.register_blueprint(prediction_bp, url_prefix="/api/prediction")

    # 健康检查
    @app.route("/health")
    def health():
        return {
            "status": "ok",
            "service": "MiroFish Backend",
            "version": "1.0.0",
            "api_docs": "/api/docs/",
        }

    if should_log_startup:
        logger.info("MiroFish Backend 启动完成")

    return app
