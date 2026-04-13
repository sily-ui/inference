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
from ..services.intervention_sandbox import InterventionSandboxService
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


@prediction_bp.route("/chat/stream", methods=["POST"])
def chat_about_prediction_stream():
    """
    AI对话 - 流式返回（SSE）

    请求（JSON）：
        {
            "question": "用户问题",
            "prediction_data": {...}  // 预测数据
        }

    返回（SSE流）：
        data: {"content": "文本片段"}
        ...
        data: {"done": true, "full_content": "完整回答"}
    """
    try:
        data = request.get_json() or {}

        question = data.get("question", "")
        prediction_data = data.get("prediction_data", {})

        if not question:
            return jsonify({"success": False, "error": "请提供问题"}), 400

        scenarios = prediction_data.get("scenarios", [])
        warnings = prediction_data.get("warnings", [])
        timeline = prediction_data.get("timeline", [])

        scenario_text = ""
        for i, s in enumerate(scenarios[:3], 1):
            scenario_text += f"\n{i}. {s.get('name', '')} (概率{s.get('probability', 0)}%, 风险等级:{s.get('risk_level', 'medium')})"
            scenario_text += f"\n   描述：{s.get('description', '')[:100]}"
            scenario_text += f"\n   关键因素：{', '.join(s.get('key_factors', [])[:2])}"

        warning_text = ""
        if warnings:
            for w in warnings[:3]:
                warning_text += f"\n- 第{w.get('day', 0)}天: {w.get('description', '')} (等级:{w.get('level', 'medium')})"
        else:
            warning_text = "\n暂无重大风险预警"

        timeline_highlights = ""
        if timeline:
            high_heat_days = [t for t in timeline if t.get('heat', 0) > 70][:3]
            for t in high_heat_days:
                timeline_highlights += f"\n- 第{t.get('day', 0)}天: 热度{t.get('heat', 0)}, {t.get('event', '')}"

        context = f"""你是MiroFish舆情预测系统的AI助手，一位资深的舆情分析专家。请基于以下详细的预测数据，为用户提供专业、实用、可操作的建议。

【事件背景】
{prediction_data.get("event_summary", "")}

【预测结论】
{prediction_data.get("conclusion", "")}

【情景分析】（按概率排序）
{scenario_text}

【关键预警】
{warning_text}

【热度高峰节点】
{timeline_highlights if timeline_highlights else '热度分布较为平稳'}

【用户问题】
{question}

【回答要求】
1. 回答要基于上述预测数据，给出具体、有针对性的建议
2. 如果涉及应对措施，请分点列出可执行的步骤
3. 如果涉及风险评估，说明概率和可能的影响
4. 语言专业但易懂，避免空洞的套话
5. 控制在200字以内，重点突出

请直接给出回答："""

        service = PublicOpinionPredictionService()

        def generate():
            import sys
            full_content = ""
            try:
                for chunk in service.llm_client.chat_stream(
                    messages=[{"role": "user", "content": context}],
                    temperature=0.7,
                    max_tokens=600,
                ):
                    full_content += chunk
                    data = json.dumps({'content': chunk}, ensure_ascii=False)
                    yield f"data: {data}\n\n"
                    sys.stdout.flush()
                data = json.dumps({'done': True, 'full_content': full_content}, ensure_ascii=False)
                yield f"data: {data}\n\n"
            except Exception as e:
                logger.error(f"流式对话失败: {str(e)}")
                data = json.dumps({'error': str(e), 'done': True}, ensure_ascii=False)
                yield f"data: {data}\n\n"

        from flask import make_response
        response = make_response(Response(
            stream_with_context(generate()),
            mimetype="text/event-stream"
        ))
        response.headers["Cache-Control"] = "no-cache"
        response.headers["X-Accel-Buffering"] = "no"
        response.headers["Transfer-Encoding"] = "chunked"
        response.headers["Connection"] = "keep-alive"
        response.headers["Content-Type"] = "text/event-stream; charset=utf-8"
        return response

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


# ============================================================
# 蝴蝶效应沙盒 - 干预推演API
# ============================================================


@prediction_bp.route("/intervention-cards", methods=["POST"])
def generate_intervention_cards():
    """
    生成干预动作卡片

    请求（JSON）：
        {
            "event_summary": "事件摘要",
            "scenarios": [...],
            "current_sentiment": "负面",
            "warnings": [...]
        }

    返回：
        {
            "success": true,
            "data": {
                "cards": [{id, type, name, icon, description, estimated_effect, best_timing, risks, prerequisite}]
            }
        }
    """
    try:
        data = request.get_json() or {}

        event_summary = data.get("event_summary", "")
        scenarios = data.get("scenarios", [])
        current_sentiment = data.get("current_sentiment", "中性")
        warnings = data.get("warnings", [])

        if not event_summary:
            return jsonify({"success": False, "error": "请提供事件摘要"}), 400

        service = InterventionSandboxService()

        result = service.generate_intervention_cards(
            event_summary=event_summary,
            scenarios=scenarios,
            current_sentiment=current_sentiment,
            warnings=warnings,
        )

        return jsonify({"success": True, "data": result})

    except Exception as e:
        logger.error(f"生成干预卡片失败: {str(e)}")
        return jsonify(
            {"success": False, "error": str(e), "traceback": traceback.format_exc()}
        ), 500


@prediction_bp.route("/intervention-timeline", methods=["POST"])
def generate_intervention_timeline():
    """
    生成分叉时间线

    请求（JSON）：
        {
            "event_summary": "事件摘要",
            "current_sentiment": "负面",
            "time_range": 7,
            "intervention_type": "official_statement",
            "intervention_description": "发布官方声明",
            "intervention_day": 2,
            "original_timeline": [...]
        }

    返回：
        {
            "success": true,
            "data": {
                "branch_timeline": [...],
                "comparison": {peak_heat_change, avg_sentiment_change, risk_reduction, recovery_speedup_days},
                "analysis": "..."
            }
        }
    """
    try:
        data = request.get_json() or {}

        event_summary = data.get("event_summary", "")
        current_sentiment = data.get("current_sentiment", "中性")
        time_range = data.get("time_range", 7)
        intervention_type = data.get("intervention_type", "official_statement")
        intervention_description = data.get("intervention_description", "")
        intervention_day = data.get("intervention_day", 2)
        original_timeline = data.get("original_timeline", [])

        if not event_summary:
            return jsonify({"success": False, "error": "请提供事件摘要"}), 400

        if not original_timeline:
            return jsonify({"success": False, "error": "请提供原始预测时间线"}), 400

        service = InterventionSandboxService()

        result = service.generate_intervention_timeline(
            event_summary=event_summary,
            current_sentiment=current_sentiment,
            time_range=time_range,
            intervention_type=intervention_type,
            intervention_description=intervention_description,
            intervention_day=intervention_day,
            original_timeline=original_timeline,
        )

        return jsonify({"success": True, "data": result})

    except Exception as e:
        logger.error(f"生成分叉时间线失败: {str(e)}")
        return jsonify(
            {"success": False, "error": str(e), "traceback": traceback.format_exc()}
        ), 500


@prediction_bp.route("/strategy-compare", methods=["POST"])
def strategy_compare():
    """
    多策略并排对比推演

    请求（JSON）：
        {
            "event_summary": "事件摘要",
            "current_sentiment": "负面",
            "strategies": [
                {"type": "official_statement", "description": "发布官方声明", "timing": 2},
                {"type": "kol_guidance", "description": "邀请KOL发声", "timing": 3}
            ],
            "original_timeline": [...]
        }

    返回：
        {
            "success": true,
            "data": {
                "comparisons": [{strategy_name, timeline, heat_change, sentiment_change, risk_level, score, analysis, pros, cons}],
                "recommendation": "..."
            }
        }
    """
    try:
        data = request.get_json() or {}

        event_summary = data.get("event_summary", "")
        current_sentiment = data.get("current_sentiment", "中性")
        strategies = data.get("strategies", [])
        original_timeline = data.get("original_timeline", [])

        if not event_summary or not strategies:
            return jsonify({"success": False, "error": "请提供事件摘要和策略列表"}), 400

        if not original_timeline:
            return jsonify({"success": False, "error": "请提供原始预测时间线"}), 400

        service = InterventionSandboxService()

        result = service.generate_strategy_comparison(
            event_summary=event_summary,
            current_sentiment=current_sentiment,
            strategies=strategies,
            original_timeline=original_timeline,
        )

        return jsonify({"success": True, "data": result})

    except Exception as e:
        logger.error(f"策略对比失败: {str(e)}")
        return jsonify(
            {"success": False, "error": str(e), "traceback": traceback.format_exc()}
        ), 500


@prediction_bp.route("/intervention-heatmap", methods=["POST"])
def generate_intervention_heatmap():
    """
    生成干预时机热力图

    请求（JSON）：
        {
            "event_summary": "事件摘要",
            "current_sentiment": "负面",
            "time_range": 7,
            "intervention_types": ["official_statement", "kol_guidance", ...],
            "original_timeline": [...]
        }

    返回：
        {
            "success": true,
            "data": {
                "heatmap": [{type, type_name, scores: [{day, score, effectiveness, risk_note}]}]
            }
        }
    """
    try:
        data = request.get_json() or {}

        event_summary = data.get("event_summary", "")
        current_sentiment = data.get("current_sentiment", "中性")
        time_range = data.get("time_range", 7)
        intervention_types = data.get("intervention_types", [
            "official_statement", "kol_guidance", "cold_treatment", "data_disclosure"
        ])
        original_timeline = data.get("original_timeline", [])

        if not event_summary:
            return jsonify({"success": False, "error": "请提供事件摘要"}), 400

        if not original_timeline:
            return jsonify({"success": False, "error": "请提供原始预测时间线"}), 400

        service = InterventionSandboxService()

        result = service.generate_intervention_heatmap(
            event_summary=event_summary,
            current_sentiment=current_sentiment,
            time_range=time_range,
            intervention_types=intervention_types,
            original_timeline=original_timeline,
        )

        return jsonify({"success": True, "data": result})

    except Exception as e:
        logger.error(f"生成热力图失败: {str(e)}")
        return jsonify(
            {"success": False, "error": str(e), "traceback": traceback.format_exc()}
        ), 500


@prediction_bp.route("/cascade-effect", methods=["POST"])
def generate_cascade_effect():
    """
    生成链式反应推演

    请求（JSON）：
        {
            "event_summary": "事件摘要",
            "intervention_type": "official_statement",
            "intervention_description": "发布官方声明",
            "simulation_data": {...}
        }

    返回：
        {
            "success": true,
            "data": {
                "layers": [{level, description, affected_count, sentiment_shift, key_agents}],
                "total_reach": 216,
                "cascade_speed": "...",
                "analysis": "..."
            }
        }
    """
    try:
        data = request.get_json() or {}

        event_summary = data.get("event_summary", "")
        intervention_type = data.get("intervention_type", "official_statement")
        intervention_description = data.get("intervention_description", "")
        simulation_data = data.get("simulation_data", {})

        if not event_summary:
            return jsonify({"success": False, "error": "请提供事件摘要"}), 400

        service = InterventionSandboxService()

        result = service.generate_cascade_effect(
            event_summary=event_summary,
            intervention_type=intervention_type,
            intervention_description=intervention_description,
            simulation_data=simulation_data,
        )

        return jsonify({"success": True, "data": result})

    except Exception as e:
        logger.error(f"生成链式反应失败: {str(e)}")
        return jsonify(
            {"success": False, "error": str(e), "traceback": traceback.format_exc()}
        ), 500


@prediction_bp.route("/counterfactual", methods=["POST"])
def generate_counterfactual():
    """
    反事实推演

    请求（JSON）：
        {
            "event_summary": "事件摘要",
            "current_sentiment": "负面",
            "original_timeline": [...],
            "removed_event_day": 3,
            "removed_event_desc": "某KOL发布负面评论引爆舆论"
        }

    返回：
        {
            "success": true,
            "data": {
                "counterfactual_timeline": [...],
                "impact_score": 35,
                "impact_description": "...",
                "analysis": "...",
                "key_difference": "..."
            }
        }
    """
    try:
        data = request.get_json() or {}

        event_summary = data.get("event_summary", "")
        current_sentiment = data.get("current_sentiment", "中性")
        original_timeline = data.get("original_timeline", [])
        removed_event_day = data.get("removed_event_day", 3)
        removed_event_desc = data.get("removed_event_desc", "")

        if not event_summary:
            return jsonify({"success": False, "error": "请提供事件摘要"}), 400

        if not original_timeline:
            return jsonify({"success": False, "error": "请提供原始预测时间线"}), 400

        if not removed_event_desc:
            return jsonify({"success": False, "error": "请提供移除事件的描述"}), 400

        service = InterventionSandboxService()

        result = service.generate_counterfactual(
            event_summary=event_summary,
            current_sentiment=current_sentiment,
            original_timeline=original_timeline,
            removed_event_day=removed_event_day,
            removed_event_desc=removed_event_desc,
        )

        return jsonify({"success": True, "data": result})

    except Exception as e:
        logger.error(f"反事实推演失败: {str(e)}")
        return jsonify(
            {"success": False, "error": str(e), "traceback": traceback.format_exc()}
        ), 500


@prediction_bp.route("/timeline-events", methods=["POST"])
def generate_timeline_events():
    """
    基于LLM生成舆情时间线事件描述

    请求（JSON）：
        {
            "event_summary": "事件摘要",
            "current_sentiment": "负面",
            "time_range": 7,
            "scenarios": [...]
        }

    返回：
        {
            "success": true,
            "data": {
                "events": [{day, event, risk_hint}],
                "overall_trend": "...",
                "key_turning_point": "..."
            }
        }
    """
    try:
        data = request.get_json() or {}

        event_summary = data.get("event_summary", "")
        current_sentiment = data.get("current_sentiment", "中性")
        time_range = data.get("time_range", 7)
        scenarios = data.get("scenarios", [])

        if not event_summary:
            return jsonify({"success": False, "error": "请提供事件摘要"}), 400

        service = InterventionSandboxService()

        result = service.generate_timeline_events(
            event_summary=event_summary,
            current_sentiment=current_sentiment,
            time_range=time_range,
            scenarios=scenarios,
        )

        return jsonify({"success": True, "data": result})

    except Exception as e:
        logger.error(f"生成时间线事件失败: {str(e)}")
        return jsonify(
            {"success": False, "error": str(e), "traceback": traceback.format_exc()}
        ), 500
