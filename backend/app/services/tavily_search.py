"""
Tavily 搜索服务

功能：
- 调用 Tavily API 进行网络搜索
- 整合搜索结果生成完整事件描述
- 提供可视化数据和导出文本

参考文档：https://docs.tavily.com/
"""

import os
import json
from typing import Dict, Any, List, Optional
from datetime import datetime

from ..config import Config
from ..utils.llm_client import LLMClient


class TavilySearchService:
    """Tavily 搜索服务"""

    def __init__(self):
        self.api_key = os.environ.get("TAVILY_API_KEY", "")
        self.llm_client = LLMClient()

        if not self.api_key:
            raise ValueError("TAVILY_API_KEY 未配置，请检查 .env 文件")

    def search(
        self,
        query: str,
        search_depth: str = "basic",
        topic: str = "general",
        max_results: int = 10,
    ) -> Dict[str, Any]:
        """
        执行 Tavily 搜索

        Args:
            query: 搜索查询
            search_depth: 搜索深度，basic 或 advanced
            topic: 主题类型，general / news / finance
            max_results: 最大结果数

        Returns:
            搜索结果字典
        """
        try:
            from tavily import TavilyClient

            client = TavilyClient(api_key=self.api_key)

            response = client.search(
                query=query,
                search_depth=search_depth,
                topic=topic,
                max_results=max_results,
                include_answer=True,
                include_raw_content=True,
                include_images=False,
            )

            results = response.get("results", [])
            raw_answer = response.get("answer", "")

            results = self._clean_results(results)

            answer = self._generate_summary(query, raw_answer, results)

            visualization = self._generate_visualization(query, results, answer)

            return {
                "query": query,
                "answer": answer,
                "results": results,
                "visualization": visualization,
                "search_depth": search_depth,
                "topic": topic,
                "fetched_at": datetime.now().isoformat(),
            }

        except ImportError:
            raise ImportError("请安装 tavily-python: pip install tavily-python")
        except Exception as e:
            raise Exception(f"Tavily 搜索失败: {str(e)}")

    def _clean_results(self, results: List[Dict]) -> List[Dict]:
        """清理搜索结果，移除乱码和无效内容"""
        import re
        from urllib.parse import unquote

        cleaned = []
        for r in results:
            content = r.get("content", "")
            raw_content = r.get("raw_content", "")
            title = r.get("title", "")

            if content:
                is_garbled = False

                if content.startswith("<svg") or content.startswith("<?xml"):
                    is_garbled = True

                elif re.match(r"^[a-f0-9\s%]+$", content[:50]):
                    is_garbled = True

                elif re.search(r"3c[a-z0-9]+3e|user203e|svg|defs|style3e", content.lower()):
                    is_garbled = True

                elif re.search(r"%[0-9a-fA-F]{2}", content[:100]):
                    try:
                        decoded = unquote(content)
                        if "<svg" in decoded.lower() or "<?xml" in decoded.lower():
                            is_garbled = True
                        elif len(re.findall(r"[\u4e00-\u9fff]", decoded)) < len(decoded) * 0.05:
                            is_garbled = True
                        else:
                            content = decoded
                    except:
                        is_garbled = True

                elif re.search(r"[^\x00-\x7F\u4e00-\u9fff\u3000-\u303f\uff00-\uffef]", content[:100]):
                    if len(re.findall(r"[\u4e00-\u9fff]", content)) < len(content) * 0.1:
                        is_garbled = True

                if is_garbled and raw_content:
                    extracted = self._extract_text_from_html(raw_content)
                    if extracted and len(extracted) > 50:
                        content = extracted

                if is_garbled and (not raw_content or len(content) < 50):
                    if title:
                        content = f"来源: {title}"
                    else:
                        content = "[内容格式异常]"

            content = re.sub(r"<[^>]+>", "", content) if content else ""
            content = re.sub(r"\s+", " ", content).strip() if content else ""

            if content.startswith("[内容") and len(content) > 20:
                content = content.split("]")[0] + "]"

            if len(content) > 500:
                content = content[:500] + "..."

            r["content"] = content if content else "暂无内容摘要"
            cleaned.append(r)

        return cleaned

    def _extract_text_from_html(self, html: str) -> str:
        """从 HTML 中提取纯文本"""
        import re

        if not html:
            return ""

        text = re.sub(r"<script[^>]*>[\s\S]*?</script>", "", html, flags=re.IGNORECASE)
        text = re.sub(r"<style[^>]*>[\s\S]*?</style>", "", text, flags=re.IGNORECASE)
        text = re.sub(r"<svg[^>]*>[\s\S]*?</svg>", "", text, flags=re.IGNORECASE)
        text = re.sub(r"<!--[\s\S]*?-->", "", text)

        text = re.sub(r"<br\s*/?>", "\n", text, flags=re.IGNORECASE)
        text = re.sub(r"</p>", "\n", text, flags=re.IGNORECASE)
        text = re.sub(r"</div>", "\n", text, flags=re.IGNORECASE)

        text = re.sub(r"<[^>]+>", "", text)

        text = re.sub(r"&nbsp;", " ", text)
        text = re.sub(r"&amp;", "&", text)
        text = re.sub(r"&lt;", "<", text)
        text = re.sub(r"&gt;", ">", text)
        text = re.sub(r"&quot;", '"', text)
        text = re.sub(r"&#(\d+);", lambda m: chr(int(m.group(1))), text)

        lines = [line.strip() for line in text.split("\n") if line.strip()]
        text = " ".join(lines)

        text = re.sub(r"\s+", " ", text).strip()

        return text

    def _generate_visualization(
        self, query: str, results: List[Dict], answer: str
    ) -> Dict[str, Any]:
        """生成可视化数据"""

        sources = []
        for r in results[:10]:
            sources.append(
                {
                    "title": r.get("title", ""),
                    "url": r.get("url", ""),
                    "score": r.get("score", 0),
                    "published_date": r.get("published_date", ""),
                }
            )

        source_domains = {}
        for r in results:
            url = r.get("url", "")
            if url:
                domain = url.split("/")[2] if "://" in url else url
                source_domains[domain] = source_domains.get(domain, 0) + 1

        top_sources = sorted(source_domains.items(), key=lambda x: x[1], reverse=True)[
            :5
        ]

        return {
            "sources": sources,
            "top_sources": [{"domain": s[0], "count": s[1]} for s in top_sources],
            "total_results": len(results),
            "answer_length": len(answer) if answer else 0,
        }

    def extract_for_inference(
        self, query: str, include_raw_content: bool = True
    ) -> Dict[str, Any]:
        """
        提取文本用于推理

        Args:
            query: 搜索查询
            include_raw_content: 是否包含原始内容

        Returns:
            提取的文本数据
        """
        search_result = self.search(
            query=query,
            search_depth="advanced",
            topic="general",
            max_results=10,
        )

        results = search_result.get("results", [])

        extracted_parts = []
        extracted_parts.append(f"搜索主题：{query}")
        extracted_parts.append(
            f"\n=== Tavily 摘要 ===\n{search_result.get('answer', '无')}"
        )

        extracted_parts.append(f"\n=== 详细信息 ===")

        key_points = []
        for i, r in enumerate(results[:10], 1):
            title = r.get("title", "")
            content = r.get("content", "")
            url = r.get("url", "")

            extracted_parts.append(f"\n来源{i}：{title}")
            extracted_parts.append(f"内容：{content[:500]}...")

            key_points.append(
                {
                    "title": title,
                    "content": content[:200] if content else "",
                    "url": url,
                }
            )

        summary = self._generate_summary(
            query, search_result.get("answer", ""), results
        )

        sources = [
            {"title": r.get("title", ""), "url": r.get("url", "")} for r in results
        ]

        extracted_text = "\n".join(extracted_parts)

        return {
            "query": query,
            "extracted_text": extracted_text,
            "summary": summary,
            "key_points": key_points,
            "sources": sources,
            "fetched_at": search_result.get("fetched_at"),
        }

    def _generate_summary(self, query: str, answer: str, results: List[Dict]) -> str:
        """使用 LLM 生成更详细的摘要"""
        from ..utils.logger import get_logger

        logger = get_logger("mirofish.tavily_search")

        if not results:
            return "未找到相关信息"

        try:
            prompt = f"""请根据以下搜索结果，为用户的问题生成一个简洁的事件摘要。

用户问题：{query}

搜索到的摘要：
{answer}

请生成一个 200 字以内的事件摘要，包含：
1. 事件的主要经过
2. 相关参与方
3. 最新进展或结果

要求用中文回复。"""

            logger.info(f"[DEBUG] 正在调用 LLM 生成中文摘要...")

            response = self.llm_client.chat(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=500,
            )

            summary = response.strip()
            logger.info(f"[DEBUG] LLM 返回摘要: {summary[:100]}...")

            return summary if summary else answer

        except Exception as e:
            logger.error(f"[ERROR] LLM 生成摘要失败: {str(e)}")
            return answer if answer else "摘要生成失败"
