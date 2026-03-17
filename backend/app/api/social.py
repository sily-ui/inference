"""
Tavily 搜索相关API路由

功能：
- 用户输入简短描述，通过 Tavily 搜索完整事件信息
- 可视化搜索结果
- 导出文本用于后续推理

工作流程：
用户输入简短描述 -> Tavily API 搜索 -> 整合完整事件 -> 展示结果 -> 导出推理
"""

import traceback
from flask import request, jsonify, Response, stream_with_context
from . import social_bp
from ..services.tavily_search import TavilySearchService
from ..utils.logger import get_logger

logger = get_logger("mirofish.api.tavily")


@social_bp.route("/search", methods=["POST"])
def search_with_tavily():
    """
    使用 Tavily 搜索完整事件信息

    请求（JSON）：
        {
            "query": "用户输入的简短描述",
            "search_depth": "basic" | "advanced",  // 可选，默认 basic
            "topic": "general" | "news" | "finance", // 可选，默认 general
            "max_results": 10  // 可选，默认 10
        }

    返回：
        {
            "success": true,
            "data": {
                "query": "原始查询",
                "answer": "Tavily 生成的摘要答案",
                "results": [...],  // 搜索结果列表
                "visualization": {...}  // 可视化数据
            }
        }
    """
    try:
        data = request.get_json() or {}

        query = data.get("query", "")
        if not query:
            return jsonify({"success": False, "error": "请提供搜索描述"}), 400

        search_depth = data.get("search_depth", "basic")
        topic = data.get("topic", "general")
        max_results = data.get("max_results", 10)

        tavily_service = TavilySearchService()

        result = tavily_service.search(
            query=query, search_depth=search_depth, topic=topic, max_results=max_results
        )

        return jsonify({"success": True, "data": result})

    except Exception as e:
        logger.error(f"Tavily 搜索失败: {str(e)}")
        return jsonify(
            {"success": False, "error": str(e), "traceback": traceback.format_exc()}
        ), 500


@social_bp.route("/extract", methods=["POST"])
def extract_for_inference():
    """
    提取文本用于推理（整合搜索结果）

    请求（JSON）：
        {
            "query": "用户输入的简短描述",
            "include_raw_content": true  // 可选，是否包含原始内容
        }

    返回：
        {
            "success": true,
            "data": {
                "extracted_text": "整合后的完整文本",
                "summary": "事件摘要",
                "key_points": [...],  // 关键点列表
                "sources": [...]  // 来源列表
            }
        }
    """
    try:
        data = request.get_json() or {}

        query = data.get("query", "")
        if not query:
            return jsonify({"success": False, "error": "请提供搜索描述"}), 400

        include_raw_content = data.get("include_raw_content", True)

        tavily_service = TavilySearchService()

        result = tavily_service.extract_for_inference(
            query=query, include_raw_content=include_raw_content
        )

        return jsonify({"success": True, "data": result})

    except Exception as e:
        logger.error(f"提取失败: {str(e)}")
        return jsonify(
            {"success": False, "error": str(e), "traceback": traceback.format_exc()}
        ), 500


@social_bp.route("/sentiment/analyze", methods=["POST"])
def analyze_text_sentiment():
    """
    分析文本情感

    请求（JSON）：
        {
            "text": "待分析文本"
        }

    返回：
        {
            "success": true,
            "data": {
                "label": "positive/negative/neutral",
                "score": 0.85,
                "emotions": [...],
                "summary": "..."
            }
        }
    """
    try:
        from ..services.social_plugins import get_mcp_client

        data = request.get_json() or {}

        text = data.get("text", "")
        if not text:
            return jsonify({"success": False, "error": "请提供待分析文本"}), 400

        mcp_client = get_mcp_client()
        result = mcp_client.analyze_sentiment(text)

        return jsonify(
            {
                "success": True,
                "data": {
                    "label": result.label,
                    "score": result.score,
                    "emotions": result.emotions,
                    "summary": result.summary,
                    "aspects": result.aspects,
                },
            }
        )

    except Exception as e:
        logger.error(f"情感分析失败: {str(e)}")
        return jsonify(
            {"success": False, "error": str(e), "traceback": traceback.format_exc()}
        ), 500


@social_bp.route("/search/stream", methods=["POST"])
def search_with_tavily_stream():
    """
    流式搜索 - SSE 实时返回 LLM 生成的中文摘要

    请求（JSON）：
        {
            "query": "用户输入的简短描述",
            "search_depth": "basic" | "advanced",
            "topic": "general" | "news" | "finance",
            "max_results": 10
        }

    返回：SSE 流式输出
        data: {"type": "chunk", "content": "..."}
        data: {"type": "done", "content": "..."}
    """
    try:
        data = request.get_json() or {}

        query = data.get("query", "")
        if not query:
            return jsonify({"success": False, "error": "请提供搜索描述"}), 400

        search_depth = data.get("search_depth", "basic")
        topic = data.get("topic", "general")
        max_results = data.get("max_results", 10)

        def generate():
            try:
                tavily_service = TavilySearchService()

                # 先返回搜索结果
                result = tavily_service.search(
                    query=query,
                    search_depth=search_depth,
                    topic=topic,
                    max_results=max_results,
                )

                yield f"data: {json.dumps({'type': 'results', 'data': result})}\n\n"

                # 流式输出 LLM 生成的中文摘要
                from ..utils.llm_client import LLMClient

                llm = LLMClient()

                prompt = f"""请根据以下搜索结果，为用户的问题生成一个简洁的事件摘要。

用户问题：{query}

搜索到的摘要：
{result.get("answer", "")}

请生成一个 200 字以内的事件摘要，包含：
1. 事件的主要经过
2. 相关参与方
3. 最新进展或结果

要求用中文回复。"""

                full_content = ""
                for chunk in llm.chat_stream(
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.7,
                    max_tokens=500,
                ):
                    full_content += chunk
                    yield f"data: {json.dumps({'type': 'chunk', 'content': chunk})}\n\n"

                # 完成后返回完整摘要
                yield f"data: {json.dumps({'type': 'done', 'summary': full_content})}\n\n"

            except Exception as e:
                yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"

        return Response(
            stream_with_context(generate()),
            mimetype="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )

    except Exception as e:
        logger.error(f"流式搜索失败: {str(e)}")
        return jsonify(
            {"success": False, "error": str(e), "traceback": traceback.format_exc()}
        ), 500
