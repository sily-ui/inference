"""
舆情预测相关API路由 - 完整版

功能模块：
1. 舆情时间轴推演 - 基于事件预测未来走势
2. 多情景概率预测 - 生成多种可能情景及概率
3. 干预策略模拟器 - 模拟不同干预策略的效果
4. 关键节点预警 - 识别潜在风险点
5. AI深度对话 - 基于预测结果进行问答

Agent模式：
- 使用ReACT架构实现思考-规划-执行的智能体行为
- 支持实时日志流式返回
"""

import os
import json
import traceback
import time
from flask import request, jsonify, Response, stream_with_context

from . import prediction_bp
from ..services.prediction_service import PublicOpinionPredictionService
from ..services.prediction_agent import PredictionAgent, PredictionLogger
from ..config import Config
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


@prediction_bp.route("/recommend-questions", methods=["POST"])
def recommend_questions():
    """
    基于预测情景生成推荐问题

    请求（JSON）：
        {
            "event_summary": "事件摘要",
            "scenarios": [...],  // 预测情景列表
            "sentiment_distribution": [...]  // 情绪分布
        }

    返回：
        {
            "success": true,
            "data": {
                "questions": ["问题1", "问题2", "问题3"]
            }
        }
    """
    try:
        data = request.get_json() or {}

        event_summary = data.get("event_summary", "")
        scenarios = data.get("scenarios", [])
        sentiment_distribution = data.get("sentiment_distribution", [])

        if not event_summary or not scenarios:
            return jsonify({"success": False, "error": "请提供事件摘要和预测情景"}), 400

        service = PublicOpinionPredictionService()

        questions = service.generate_recommended_questions(
            event_summary=event_summary,
            scenarios=scenarios,
            sentiment_distribution=sentiment_distribution,
        )

        return jsonify({"success": True, "data": {"questions": questions}})

    except Exception as e:
        logger.error(f"生成推荐问题失败: {str(e)}")
        return jsonify(
            {"success": False, "error": str(e), "traceback": traceback.format_exc()}
        ), 500


@prediction_bp.route("/agent/predict", methods=["POST"])
def agent_predict():
    """
    Agent模式舆情预测 - ReACT架构

    使用智能体思考-规划-执行模式进行预测：
    1. 规划阶段：分析事件特征，制定预测策略
    2. 分析阶段：通过ReACT循环调用工具
    3. 反思阶段：检查预测合理性，生成结论

    请求（JSON）：
        {
            "simulation_id": "模拟ID",
            "event_summary": "事件摘要",
            "current_sentiment": "当前情绪",
            "time_range": 7,
            "simulation_data": {...}  // 模拟运行数据
        }

    返回：
        {
            "success": true,
            "data": {
                "prediction_id": "...",
                "plan": {...},
                "timeline": [...],
                "scenarios": [...],
                "warnings": [...],
                "conclusion": "...",
                "confidence": 0.85,
                "key_insights": [...],
                "action_suggestions": [...]
            }
        }
    """
    try:
        data = request.get_json() or {}

        simulation_id = data.get("simulation_id", "")
        event_summary = data.get("event_summary", "")
        current_sentiment = data.get("current_sentiment", "中性")
        time_range = data.get("time_range", 7)
        simulation_data = data.get("simulation_data", {})

        if not event_summary:
            return jsonify({"success": False, "error": "请提供事件摘要"}), 400

        agent = PredictionAgent(
            simulation_id=simulation_id,
            event_summary=event_summary,
            current_sentiment=current_sentiment,
            time_range=time_range,
            simulation_data=simulation_data,
        )

        result = agent.predict()

        return jsonify({"success": True, "data": result})

    except Exception as e:
        logger.error(f"Agent预测失败: {str(e)}")
        return jsonify(
            {"success": False, "error": str(e), "traceback": traceback.format_exc()}
        ), 500


@prediction_bp.route("/agent/stream", methods=["POST"])
def agent_predict_stream():
    """
    Agent模式舆情预测 - 流式返回（SSE）

    实时返回Agent的思考过程和执行状态

    请求（JSON）：
        {
            "simulation_id": "模拟ID",
            "event_summary": "事件摘要",
            "current_sentiment": "当前情绪",
            "time_range": 7,
            "simulation_data": {...}
        }

    返回（SSE流）：
        event: log
        data: {"action": "planning_start", "stage": "planning", ...}

        event: progress
        data: {"stage": "planning", "progress": 10, "message": "..."}

        event: result
        data: {"success": true, "data": {...}}
    """

    def generate():
        data = request.get_json() or {}

        simulation_id = data.get("simulation_id", "")
        event_summary = data.get("event_summary", "")
        current_sentiment = data.get("current_sentiment", "中性")
        time_range = data.get("time_range", 7)
        simulation_data = data.get("simulation_data", {})

        if not event_summary:
            yield f"event: error\ndata: {json.dumps({'error': '请提供事件摘要'})}\n\n"
            return

        prediction_id = f"pred_{int(time.time() * 1000)}"
        log_file_path = os.path.join(
            Config.UPLOAD_FOLDER, "predictions", prediction_id, "agent_log.jsonl"
        )
        os.makedirs(os.path.dirname(log_file_path), exist_ok=True)

        last_log_position = 0

        def progress_callback(stage, progress, message):
            nonlocal last_log_position
            yield f"event: progress\ndata: {json.dumps({'stage': stage, 'progress': progress, 'message': message})}\n\n"

        agent = PredictionAgent(
            simulation_id=simulation_id,
            event_summary=event_summary,
            current_sentiment=current_sentiment,
            time_range=time_range,
            simulation_data=simulation_data,
        )

        def run_prediction():
            return agent.predict()

        import threading
        result_container = {"result": None, "error": None}

        def prediction_thread():
            try:
                result_container["result"] = agent.predict()
            except Exception as e:
                result_container["error"] = str(e)

        thread = threading.Thread(target=prediction_thread)
        thread.start()

        while thread.is_alive():
            if os.path.exists(log_file_path):
                with open(log_file_path, "r", encoding="utf-8") as f:
                    f.seek(last_log_position)
                    new_content = f.read()
                    last_log_position = f.tell()

                    for line in new_content.strip().split("\n"):
                        if line:
                            try:
                                log_entry = json.loads(line)
                                yield f"event: log\ndata: {json.dumps(log_entry, ensure_ascii=False)}\n\n"
                            except json.JSONDecodeError:
                                pass

            time.sleep(0.2)

        thread.join()

        if result_container["error"]:
            yield f"event: error\ndata: {json.dumps({'error': result_container['error']})}\n\n"
        else:
            yield f"event: result\ndata: {json.dumps({'success': True, 'data': result_container['result']}, ensure_ascii=False)}\n\n"

    return Response(
        stream_with_context(generate()),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        }
    )


@prediction_bp.route("/agent/logs/<prediction_id>", methods=["GET"])
def get_agent_logs(prediction_id):
    """
    获取Agent预测日志

    返回指定预测任务的所有日志记录
    """
    try:
        log_file_path = os.path.join(
            Config.UPLOAD_FOLDER, "predictions", prediction_id, "agent_log.jsonl"
        )

        if not os.path.exists(log_file_path):
            return jsonify({"success": False, "error": "日志文件不存在"}), 404

        logs = []
        with open(log_file_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    logs.append(json.loads(line))

        return jsonify({"success": True, "data": {"logs": logs}})

    except Exception as e:
        logger.error(f"获取日志失败: {str(e)}")
        return jsonify(
            {"success": False, "error": str(e), "traceback": traceback.format_exc()}
        ), 500
