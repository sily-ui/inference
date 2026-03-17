"""
舆情预测相关API路由 - 完整版

功能模块：
1. 舆情时间轴推演 - 基于事件预测未来走势
2. 多情景概率预测 - 生成多种可能情景及概率
3. 干预策略模拟器 - 模拟不同干预策略的效果
4. 关键节点预警 - 识别潜在风险点
5. AI深度对话 - 基于预测结果进行问答
"""

import traceback
from flask import request, jsonify

from . import prediction_bp
from ..services.prediction_service import PublicOpinionPredictionService
from ..utils.logger import get_logger

logger = get_logger("mirofish.api.prediction")


@prediction_bp.route("/predict", methods=["POST"])
def predict_public_opinion():
    """
    完整舆情预测 - 包含5个功能模块

    请求（JSON）：
        {
            "simulation_id": "模拟ID",
            "report_id": "报告ID（可选）",
            "event_summary": "事件摘要",
            "current_sentiment": "当前情绪",
            "time_range": 7  // 预测天数
        }

    返回：
        {
            "success": true,
            "data": {
                "timeline": [...],  // 时间轴推演
                "scenarios": [...],  // 情景预测
                "warnings": [...],   // 关键预警
                "visualization": {...},  // 可视化数据
                "conclusion": "..."  // 预测结论
            }
        }
    """
    try:
        data = request.get_json() or {}

        simulation_id = data.get("simulation_id", "")
        report_id = data.get("report_id", "")
        event_summary = data.get("event_summary", "")
        current_sentiment = data.get("current_sentiment", "中性")
        time_range = data.get("time_range", 7)

        if not event_summary:
            return jsonify({"success": False, "error": "请提供事件摘要"}), 400

        service = PublicOpinionPredictionService()

        result = service.predict_full(
            simulation_id=simulation_id,
            report_id=report_id,
            event_summary=event_summary,
            current_sentiment=current_sentiment,
            time_range=time_range,
        )

        return jsonify({"success": True, "data": result})

    except Exception as e:
        logger.error(f"舆情预测失败: {str(e)}")
        return jsonify(
            {"success": False, "error": str(e), "traceback": traceback.format_exc()}
        ), 500


@prediction_bp.route("/intervention", methods=["POST"])
def simulate_intervention():
    """
    干预策略模拟

    请求（JSON）：
        {
            "event_summary": "事件摘要",
            "intervention": "干预措施",
            "current_sentiment": "当前情绪"
        }

    返回：
        {
            "success": true,
            "data": {
                "strategy": "...",
                "expected_effect": "...",
                "heat_change": 10,
                "sentiment_change": 0.1,
                "risk": "...",
                "recommendation": 4
            }
        }
    """
    try:
        data = request.get_json() or {}

        event_summary = data.get("event_summary", "")
        intervention = data.get("intervention", "")
        current_sentiment = data.get("current_sentiment", "中性")

        if not event_summary or not intervention:
            return jsonify({"success": False, "error": "请提供事件摘要和干预措施"}), 400

        service = PublicOpinionPredictionService()

        result = service.simulate_intervention(
            event_summary=event_summary,
            intervention=intervention,
            current_sentiment=current_sentiment,
        )

        return jsonify({"success": True, "data": result})

    except Exception as e:
        logger.error(f"干预模拟失败: {str(e)}")
        return jsonify(
            {"success": False, "error": str(e), "traceback": traceback.format_exc()}
        ), 500


@prediction_bp.route("/chat", methods=["POST"])
def chat_about_prediction():
    """
    AI对话 - 基于预测结果问答

    请求（JSON）：
        {
            "question": "用户问题",
            "prediction_data": {...}  // 预测数据
        }

    返回：
        {
            "success": true,
            "data": {
                "answer": "回答内容"
            }
        }
    """
    try:
        data = request.get_json() or {}

        question = data.get("question", "")
        prediction_data = data.get("prediction_data", {})

        if not question:
            return jsonify({"success": False, "error": "请提供问题"}), 400

        service = PublicOpinionPredictionService()

        answer = service.chat_about_prediction(
            question=question,
            prediction_data=prediction_data,
        )

        return jsonify({"success": True, "data": {"answer": answer}})

    except Exception as e:
        logger.error(f"对话失败: {str(e)}")
        return jsonify(
            {"success": False, "error": str(e), "traceback": traceback.format_exc()}
        ), 500


@prediction_bp.route("/demo", methods=["GET"])
def demo_prediction():
    """
    获取演示预测数据（用于测试）
    """
    try:
        service = PublicOpinionPredictionService()

        result = service.predict_full(
            simulation_id="demo",
            report_id="demo_report",
            event_summary="某科技公司发布新产品，引发网友热议，部分用户反馈产品存在问题",
            current_sentiment="复杂（正负面兼有）",
            time_range=7,
        )

        return jsonify({"success": True, "data": result})

    except Exception as e:
        logger.error(f"演示预测失败: {str(e)}")
        return jsonify(
            {"success": False, "error": str(e), "traceback": traceback.format_exc()}
        ), 500
