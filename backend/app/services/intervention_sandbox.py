"""
干预推演服务 - 蝴蝶效应沙盒

功能模块：
1. 干预动作卡片生成 - 基于事件和情景动态生成干预策略卡片
2. 分叉时间线推演 - 基于SIR模型计算干预后的分叉时间线
3. 策略竞技场 - 多策略并排对比推演
4. 干预时机热力图 - 不同干预类型在不同时间点的效果矩阵
5. 链式反应可视化 - 干预的链式传播推演
6. 反事实推演 - 反事实推理对比
"""

import json
import random
from typing import Dict, Any, List, Optional

from ..utils.llm_client import LLMClient
from .algorithm_engine import AlgorithmEngine


INTERVENTION_TYPES = [
    {
        "id": "official_statement",
        "type": "official_statement",
        "name": "官方声明",
        "icon": "📢",
    },
    {
        "id": "kol_guidance",
        "type": "kol_guidance",
        "name": "KOL引导",
        "icon": "🤝",
    },
    {
        "id": "data_disclosure",
        "type": "data_disclosure",
        "name": "数据披露",
        "icon": "📊",
    },
    {
        "id": "precise_response",
        "type": "precise_response",
        "name": "精准回应",
        "icon": "🎯",
    },
    {
        "id": "cold_treatment",
        "type": "cold_treatment",
        "name": "冷处理",
        "icon": "⏰",
    },
    {
        "id": "topic_redirect",
        "type": "topic_redirect",
        "name": "话题转移",
        "icon": "🔄",
    },
]


class InterventionSandboxService:
    """干预推演沙盒服务"""

    def __init__(self):
        self.llm_client = LLMClient()
        self.algorithm_engine = AlgorithmEngine()

    def generate_intervention_cards(
        self,
        event_summary: str,
        scenarios: List[Dict[str, Any]],
        current_sentiment: str,
        warnings: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """生成干预动作卡片"""

        scenario_text = ""
        for i, s in enumerate(scenarios[:4], 1):
            scenario_text += f"\n{i}. {s.get('name', '')} (概率{s.get('probability', 0)}%, 风险:{s.get('risk_level', 'medium')})"

        warning_text = ""
        if warnings:
            for w in warnings[:3]:
                warning_text += f"\n- {w.get('description', '')} (等级:{w.get('level', 'medium')})"

        prompt = f"""你是一位资深的舆情危机公关专家，擅长用通俗易懂、接地气的语言描述应对策略。请为以下舆情事件生成6种干预策略卡片。

事件背景：{event_summary}
当前情绪：{current_sentiment}

预测情景：
{scenario_text}

关键预警：
{warning_text if warning_text else '暂无重大预警'}

请生成以下6种干预策略的详细卡片信息：
1. 官方声明 - 发布官方澄清公告或致歉声明
2. KOL引导 - 邀请意见领袖/权威人士发声
3. 数据披露 - 公开调查数据、证据或事实
4. 精准回应 - 针对核心质疑点逐一回应
5. 冷处理 - 不主动回应，等待自然衰减
6. 话题转移 - 引导公众关注其他话题

【语言风格要求 - 必须严格遵守】
1. 绝对禁止使用以下词汇和表达：
   - 禁止："降温效果"、"显著"、"有效遏制"、"明显改善"、"情绪改善"、"压制热度"
   - 禁止："舆情发酵"、"舆论引导"、"公信力"、"态势"、"格局"
   - 禁止："综上所述"、"建议综合评估"、"形成组合拳"
   - 禁止：任何四字成语或官方套话

2. 必须使用口语化、接地气的表达：
   - 用"热度降下来"代替"降温效果显著"
   - 用"大家情绪会好一些"代替"情绪改善明显"
   - 用"能快速稳住局面"代替"有效遏制舆情扩散"
   - 用"这招"、"这个办法"代替"该策略"

3. 每个字段的具体要求：
   - description字段（30-50字）：像跟朋友聊天一样说这个策略要干啥。❌错误示例："发布官方声明以正视听，有效引导舆论走向" ✅正确示例："发个正式声明，把情况说清楚，让大家别瞎猜了"
   - estimated_effect：用大白话描述预期效果。❌错误示例："降温效果最强，能快速压制热度" ✅正确示例："这招挺管用，能让热度降个15-20%，大家情绪能稳一稳"
   - best_timing：说清楚什么时候出手最合适。❌错误示例："黄金窗口期" ✅正确示例："事发当天4小时内，越早越好，别拖"
   - risks：说人话的风险提示。❌错误示例："可能引发次生舆情风险" ✅正确示例："说错话可能火上浇油，越描越黑"
   - prerequisite：简单明了的前置条件。❌错误示例："需确保信息准确性和口径一致性" ✅正确示例："先把内部口径统一好，别自己人打自己人脸"

每种策略请输出JSON格式：
{{
    "cards": [
        {{
            "id": "official_statement",
            "type": "official_statement",
            "name": "官方声明",
            "icon": "📢",
            "description": "用大白话描述这个策略要做什么（30-50字）",
            "estimated_effect": "热度↓X-Y%，情绪↑A.B",
            "best_timing": "最佳时机",
            "risks": ["风险1", "风险2"],
            "prerequisite": "前置条件"
        }}
    ]
}}

只返回JSON，不要其他解释。"""

        try:
            response = self.llm_client.chat(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=2000,
            )
            content = response if isinstance(response, str) else response.get("content", "")

            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]

            result = json.loads(content.strip())
            cards = result.get("cards", [])

            for card in cards:
                if not card.get("icon"):
                    for t in INTERVENTION_TYPES:
                        if t["id"] == card.get("id") or t["type"] == card.get("type"):
                            card["icon"] = t["icon"]
                            break

            return {"cards": cards}
        except Exception as e:
            return {"cards": self._generate_default_cards(event_summary, current_sentiment)}

    def _generate_default_cards(
        self, event_summary: str, current_sentiment: str
    ) -> List[Dict[str, Any]]:
        """生成默认干预卡片"""
        cards = []
        defaults = [
            {
                "id": "official_statement",
                "type": "official_statement",
                "name": "官方声明",
                "icon": "📢",
                "description": "发布官方声明回应公众关切，表明态度和立场",
                "estimated_effect": "热度能降15-25%，大家情绪会好一些",
                "best_timing": "事发当天黄金4小时内，越快越好",
                "risks": ["说错话可能火上浇油", "承诺太多后面兑现不了"],
                "prerequisite": "内部先统一口径，别自己人打自己人脸",
            },
            {
                "id": "kol_guidance",
                "type": "kol_guidance",
                "name": "KOL引导",
                "icon": "🤝",
                "description": "找几个有影响力的博主或专家帮你说说话，让他们带带节奏",
                "estimated_effect": "热度降10-20%，情绪好转一些",
                "best_timing": "事情发酵2-4天后，等大家情绪稍微平复点",
                "risks": ["找的人不靠谱可能反水", "被网友看出来是买的水军就尴尬了"],
                "prerequisite": "先跟KOL沟通好，确保他们愿意站台",
            },
            {
                "id": "data_disclosure",
                "type": "data_disclosure",
                "name": "数据披露",
                "icon": "📊",
                "description": "把调查数据、证据啥的亮出来，用事实说话",
                "estimated_effect": "热度降10-15%，情绪会理性一些",
                "best_timing": "调查有个初步结果后，别空口无凭",
                "risks": ["数据可能被断章取义", "有些数据可能对自己不利"],
                "prerequisite": "数据要整理清楚，别出纰漏",
            },
            {
                "id": "precise_response",
                "type": "precise_response",
                "name": "精准回应",
                "icon": "🎯",
                "description": "针对大家质疑的点一个个回应，别打太极",
                "estimated_effect": "热度降12-22%，情绪改善明显",
                "best_timing": "质疑点都明确了之后1-2天内",
                "risks": ["漏了关键问题会被追着打", "回应不够说服力"],
                "prerequisite": "先把质疑点都梳理清楚",
            },
            {
                "id": "cold_treatment",
                "type": "cold_treatment",
                "name": "冷处理",
                "icon": "⏰",
                "description": "先不吭声，等热度自己降下来",
                "estimated_effect": "热度慢慢降5-10%，情绪变化不大",
                "best_timing": "热度已经过了最高峰，没啥新料的时候",
                "risks": ["可能被认为装死", "万一有新爆料就炸了"],
                "prerequisite": "确认不会有新的实锤爆出来",
            },
            {
                "id": "topic_redirect",
                "type": "topic_redirect",
                "name": "话题转移",
                "icon": "🔄",
                "description": "搞个新话题或者活动，把大家注意力引开",
                "estimated_effect": "热度降8-15%，情绪看运气",
                "best_timing": "热度开始往下走的时候",
                "risks": ["转移太明显会被识破", "新话题可能也翻车"],
                "prerequisite": "准备好能吸引人的替代话题",
            },
        ]
        return defaults

    def generate_intervention_timeline(
        self,
        event_summary: str,
        current_sentiment: str,
        time_range: int,
        intervention_type: str,
        intervention_description: str,
        intervention_day: int,
        original_timeline: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """生成分叉时间线"""

        type_name_map = {t["id"]: t["name"] for t in INTERVENTION_TYPES}
        intervention_name = type_name_map.get(intervention_type, intervention_type)

        original_text = ""
        for node in original_timeline:
            original_text += f"\nDay{node.get('day', 0)}: 热度={node.get('heat', 0)}, 情绪={node.get('sentiment', 0)}, 风险={node.get('risk', 'medium')}, 事件={node.get('event', '')}"

        sir_timeline = self._compute_sir_intervention_timeline(
            event_summary, current_sentiment, time_range,
            intervention_type, intervention_day, original_timeline
        )

        timeline_text = ""
        for node in sir_timeline:
            timeline_text += f"\nDay{node.get('day', 0)}: 热度={node.get('heat', 0)}, 情绪={node.get('sentiment', 0)}, 风险={node.get('risk', 'medium')}"

        prompt = f"""你是一位舆情危机公关顾问，擅长用通俗易懂的语言描述干预效果。请基于以下信息，生成干预后的舆情发展时间线。

事件背景：{event_summary}
当前情绪：{current_sentiment}
干预类型：{intervention_name}
干预描述：{intervention_description}
干预执行时间：第{intervention_day}天

原始预测时间线：
{original_text}

SIR模型计算的干预后数值趋势：
{timeline_text}

【语言风格要求 - 必须严格遵守】
1. 绝对禁止使用以下词汇和表达：
   - 禁止："降温效果"、"显著"、"有效遏制"、"明显改善"、"压制热度"
   - 禁止："舆情发酵"、"舆论引导"、"公信力"、"态势"、"格局"
   - 禁止："综上所述"、"情绪改善"、"良性讨论"
   - 禁止：任何四字成语或官方套话

2. 必须使用口语化、接地气的表达：
   - 用"热度降下来"代替"降温效果显著"
   - 用"大家情绪会好一些"代替"情绪改善明显"
   - 用"这招"代替"该干预措施"

3. 每个字段的具体要求：
   - event字段（15字以内）：描述当天发生了什么，像讲故事一样。❌错误示例："干预效果显著，热度快速下降" ✅正确示例："发了声明后，大家讨论少了"
   - analysis字段（80-120字）：像跟朋友总结这次干预怎么样。❌错误示例："官方声明干预效果显著。通过提前释放稳定信号，有效遏制了市场焦虑的扩散与升级，使舆情热度峰值大幅降低。" ✅正确示例："这次官方声明挺及时的，热度从100降到了13，风险也控制住了。虽然整体情绪因为理性讨论而有所下降，但避免了剧烈波动。"

请基于SIR模型的数值趋势，为干预后的每一天生成自然的事件描述。
从干预执行日（第{intervention_day}天）开始，之后每天的事件描述需要体现干预的影响。

请以JSON格式返回完整的时间线（{time_range}天）：
{{
    "branch_timeline": [
        {{
            "day": 1,
            "heat": 80,
            "sentiment": 0.5,
            "risk": "medium",
            "event": "事件发展描述（15字以内，说人话）"
        }}
    ],
    "comparison": {{
        "peak_heat_change": -20,
        "avg_sentiment_change": 0.15,
        "risk_reduction": "high→medium",
        "recovery_speedup_days": 3
    }},
    "analysis": "干预效果分析（80-120字，像跟朋友聊天一样）"
}}

只返回JSON，不要其他解释。"""

        try:
            response = self.llm_client.chat(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=2000,
            )
            content = response if isinstance(response, str) else response.get("content", "")

            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]

            result = json.loads(content.strip())

            if "branch_timeline" in result:
                for i, node in enumerate(result["branch_timeline"]):
                    if i < intervention_day - 1:
                        if i < len(original_timeline):
                            node["heat"] = original_timeline[i].get("heat", node.get("heat", 50))
                            node["sentiment"] = original_timeline[i].get("sentiment", node.get("sentiment", 0.5))
                            node["risk"] = original_timeline[i].get("risk", node.get("risk", "medium"))

            return result
        except Exception as e:
            return {
                "branch_timeline": sir_timeline,
                "comparison": {
                    "peak_heat_change": -15,
                    "avg_sentiment_change": 0.1,
                    "risk_reduction": "medium→low",
                    "recovery_speedup_days": 2,
                },
                "analysis": f"在第{intervention_day}天执行「{intervention_name}」后，舆情热度预计下降，情绪有所改善。建议配合其他措施综合使用。",
            }

    def _compute_sir_intervention_timeline(
        self,
        event_summary: str,
        current_sentiment: str,
        time_range: int,
        intervention_type: str,
        intervention_day: int,
        original_timeline: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """基于SIR模型计算干预后的时间线"""

        intervention_beta_factor = {
            "official_statement": 0.6,
            "kol_guidance": 0.7,
            "data_disclosure": 0.75,
            "precise_response": 0.65,
            "cold_treatment": 0.9,
            "topic_redirect": 0.8,
        }.get(intervention_type, 0.8)

        intervention_gamma_factor = {
            "official_statement": 1.5,
            "kol_guidance": 1.3,
            "data_disclosure": 1.2,
            "precise_response": 1.4,
            "cold_treatment": 1.0,
            "topic_redirect": 1.1,
        }.get(intervention_type, 1.2)

        sentiment_factor = {
            "正面": 0.8, "负面": 1.2, "中性": 1.0, "复杂": 1.1,
        }.get(current_sentiment, 1.0)

        base_beta = 0.3 * sentiment_factor
        base_gamma = 0.1

        S = 0.9
        I = 0.1
        R = 0.0
        dt = 0.1

        timeline = []
        for day in range(1, time_range + 1):
            beta = base_beta
            gamma = base_gamma

            if day >= intervention_day:
                beta *= intervention_beta_factor
                gamma *= intervention_gamma_factor

            for _ in range(int(1 / dt)):
                dS = (-beta * S * I + 0.01 * R) * dt
                dI = (beta * S * I - gamma * I) * dt
                dR = (gamma * I - 0.01 * R) * dt
                S = max(0, min(1, S + dS))
                I = max(0, min(1, I + dI))
                R = max(0, min(1, R + dR))

            heat = int(I * 100)
            sentiment = round(0.3 + S * 0.5, 2)
            risk = "high" if heat > 70 else ("medium" if heat > 40 else "low")

            event = "关注度持续走低，事件逐渐平息"
            if day < intervention_day:
                if day < len(original_timeline):
                    event = original_timeline[day - 1].get("event", event)
            else:
                if heat > 80:
                    event = "干预效果尚未显现，热度仍高"
                elif heat > 60:
                    event = "干预开始发挥作用，热度逐步下降"
                elif heat > 40:
                    event = "干预效果明显，讨论趋于理性"
                else:
                    event = "干预成功，关注度显著降低"

            timeline.append({
                "day": day,
                "heat": heat,
                "sentiment": sentiment,
                "risk": risk,
                "event": event,
            })

        return timeline

    def generate_counterfactual_dag(
        self,
        event_summary: str,
        current_sentiment: str,
        time_range: int,
        strategy: str,
        simulation_data: Dict[str, Any],
        original_timeline: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """反事实推演引擎 - 生成DAG传播网络和态势趋势"""

        all_actions = simulation_data.get("all_actions", [])
        agent_count = simulation_data.get("agent_count", 0)

        dag = self._build_dag_from_data(
            event_summary, current_sentiment, time_range,
            strategy, all_actions, original_timeline
        )

        trend = self._build_trend_from_data(
            event_summary, current_sentiment, time_range,
            strategy, original_timeline
        )

        return {
            "dag": dag,
            "trend": trend,
        }

    def _build_dag_from_data(
        self,
        event_summary: str,
        current_sentiment: str,
        time_range: int,
        strategy: str,
        all_actions: List[Dict],
        original_timeline: List[Dict],
    ) -> Dict[str, Any]:
        """基于模拟数据构建DAG传播网络"""

        node_templates = [
            {"name": "事件起源", "depth": 0, "sentiment": "负面", "influence": 90},
            {"name": "社交媒体传播", "depth": 1, "sentiment": "负面", "influence": 75},
            {"name": "KOL转发扩散", "depth": 1, "sentiment": "负面", "influence": 80},
            {"name": "主流媒体报道", "depth": 2, "sentiment": "中性", "influence": 70},
            {"name": "公众情绪发酵", "depth": 2, "sentiment": "负面", "influence": 65},
            {"name": "官方首次回应", "depth": 3, "sentiment": "正面", "influence": 85},
            {"name": "意见分化", "depth": 3, "sentiment": "复杂", "influence": 55},
            {"name": "深度讨论", "depth": 4, "sentiment": "中性", "influence": 45},
            {"name": "二次传播", "depth": 4, "sentiment": "负面", "influence": 50},
            {"name": "话题降温", "depth": 5, "sentiment": "中性", "influence": 30},
            {"name": "长尾效应", "depth": 5, "sentiment": "中性", "influence": 20},
        ]

        if strategy == "cutnode":
            node_templates = [n for n in node_templates if n["name"] != "KOL转发扩散"]
            for n in node_templates:
                if n["depth"] >= 2:
                    n["influence"] = max(10, n["influence"] - 15)
        elif strategy == "official":
            official_node = {"name": "权威通报", "depth": 2, "sentiment": "正面", "influence": 88}
            node_templates.insert(4, official_node)
            for n in node_templates:
                if n["sentiment"] == "负面" and n["depth"] >= 3:
                    n["influence"] = max(10, n["influence"] - 10)
        elif strategy == "amplify":
            amplify_node = {"name": "正面声音放大", "depth": 2, "sentiment": "正面", "influence": 72}
            node_templates.insert(4, amplify_node)
            for n in node_templates:
                if n["sentiment"] == "负面" and n["depth"] >= 3:
                    n["influence"] = max(10, n["influence"] - 8)

        if all_actions and len(all_actions) > 0:
            action_agents = set()
            for action in all_actions[:50]:
                agent_name = action.get("agent_name", "")
                if agent_name and agent_name not in action_agents:
                    action_agents.add(agent_name)
                    if len(node_templates) < 20:
                        content = action.get("content", "")
                        sentiment = "负面"
                        if any(w in content for w in ["支持", "赞同", "好", "棒"]):
                            sentiment = "正面"
                        elif any(w in content for w in ["但是", "不过", "虽然"]):
                            sentiment = "复杂"

                        node_templates.append({
                            "name": agent_name[:6] if len(agent_name) > 6 else agent_name,
                            "depth": min(5, 1 + len(action_agents) // 3),
                            "sentiment": sentiment,
                            "influence": 30 + random.randint(0, 30),
                        })

        nodes = []
        for i, tmpl in enumerate(node_templates):
            sentiment_type = "neutral"
            if tmpl["sentiment"] in ["负面"]:
                sentiment_type = "negative"
            elif tmpl["sentiment"] in ["正面"]:
                sentiment_type = "positive"
            elif tmpl["sentiment"] in ["复杂"]:
                sentiment_type = "complex"

            risk_level = "low"
            if tmpl["influence"] > 70 and tmpl["sentiment"] == "负面":
                risk_level = "high"
            elif tmpl["influence"] > 50:
                risk_level = "medium"

            influence_label = "高" if tmpl["influence"] > 65 else "中" if tmpl["influence"] > 35 else "低"

            nodes.append({
                "id": f"n{i}",
                "name": tmpl["name"],
                "depth": tmpl["depth"],
                "influence": tmpl["influence"],
                "influenceLabel": influence_label,
                "sentiment": tmpl["sentiment"],
                "sentimentType": sentiment_type,
                "riskLevel": risk_level,
                "timeStep": i * max(1, (time_range * 24) // max(len(node_templates), 1)),
                "features": {
                    "spread": min(100, tmpl["influence"] + random.randint(-10, 15)),
                    "influence": min(100, tmpl["influence"] + random.randint(-5, 10)),
                    "sentiment": min(100, (80 if tmpl["sentiment"] == "负面" else 30 if tmpl["sentiment"] == "正面" else 50) + random.randint(-15, 15)),
                    "credibility": min(100, 40 + random.randint(0, 40)),
                    "persistence": min(100, 20 + random.randint(0, 50)),
                },
                "agentLog": [
                    {"type": "thought", "prefix": "Thought:", "content": f"识别到「{tmpl['name']}」节点的传播特征，评估其在{tmpl['sentiment']}情绪链中的影响力..."},
                    {"type": "action", "prefix": "Action:", "content": f"调用传播分析工具，计算节点影响力指数为{tmpl['influence']}，情绪极性为{tmpl['sentiment']}"},
                    {"type": "observation", "prefix": "Observation:", "content": f"节点位于L{tmpl['depth']}层，影响力{influence_label}，风险等级{risk_level}，传播深度{tmpl['depth']}级"},
                ],
            })

        edges = []
        for i in range(1, len(nodes)):
            source_idx = max(0, i - 1 - random.randint(0, 1))
            edges.append({"source": nodes[source_idx]["id"], "target": nodes[i]["id"]})
            if i > 2 and random.random() > 0.5:
                alt_source = random.randint(0, i - 2)
                edges.append({"source": nodes[alt_source]["id"], "target": nodes[i]["id"]})

        return {"nodes": nodes, "edges": edges}

    def _build_trend_from_data(
        self,
        event_summary: str,
        current_sentiment: str,
        time_range: int,
        strategy: str,
        original_timeline: List[Dict],
    ) -> Dict[str, Any]:
        """构建态势趋势数据"""

        total_hours = time_range * 24
        sentiment_factor = {"正面": 0.8, "负面": 1.2, "中性": 1.0, "复杂": 1.1}.get(current_sentiment, 1.0)

        base_beta = 0.3 * sentiment_factor
        base_gamma = 0.1

        strategy_factor = {
            "natural": (1.0, 1.0),
            "official": (0.75, 1.3),
            "cutnode": (0.6, 1.5),
            "amplify": (0.8, 1.2),
        }.get(strategy, (1.0, 1.0))

        S, I, R = 0.9, 0.1, 0.0
        dt = 0.1

        S2, I2, R2 = 0.9, 0.1, 0.0

        original = []
        intervened = []

        for h in range(0, total_hours + 1, 4):
            for _ in range(int(4 / dt)):
                dS = (-base_beta * S * I + 0.01 * R) * dt
                dI = (base_beta * S * I - base_gamma * I) * dt
                dR = (base_gamma * I - 0.01 * R) * dt
                S = max(0, min(1, S + dS))
                I = max(0, min(1, I + dI))
                R = max(0, min(1, R + dR))

                beta2 = base_beta * strategy_factor[0]
                gamma2 = base_gamma * strategy_factor[1]
                dS2 = (-beta2 * S2 * I2 + 0.01 * R2) * dt
                dI2 = (beta2 * S2 * I2 - gamma2 * I2) * dt
                dR2 = (gamma2 * I2 - 0.01 * R2) * dt
                S2 = max(0, min(1, S2 + dS2))
                I2 = max(0, min(1, I2 + dI2))
                R2 = max(0, min(1, R2 + dR2))

            original.append({"time": h, "value": round(I * 100)})
            intervened.append({"time": h, "value": round(I2 * 100)})

        return {"original": original, "intervened": intervened}

    def generate_timeline_events(
        self,
        event_summary: str,
        current_sentiment: str,
        time_range: int,
        scenarios: List[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """基于LLM生成舆情时间线事件描述"""

        scenario_text = ""
        if scenarios:
            for i, s in enumerate(scenarios[:3], 1):
                scenario_text += f"\n{i}. {s.get('name', '')} (概率{s.get('probability', 0)}%)"

        prompt = f"""你是一位资深的舆情分析专家。请为以下舆情事件预测未来{time_range}天可能发生的关键节点事件。

事件背景：{event_summary}
当前情绪：{current_sentiment}

预测情景：
{scenario_text if scenario_text else '暂无具体情景预测'}

请生成{time_range}天的舆情发展关键事件，每个事件应该：
1. 符合舆情传播的自然规律（发酵期、爆发期、高潮期、衰减期）
2. 与事件背景紧密相关，具有针对性
3. 体现可能的风险等级变化

输出JSON格式：
{{
    "events": [
        {{
            "day": 1,
            "event": "事件描述（15-25字，具体描述当天可能发生的关键事件）",
            "risk_hint": "风险提示（10字内，如'需关注'、'高风险'等）"
        }}
    ],
    "overall_trend": "整体趋势描述（20字内）",
    "key_turning_point": "关键转折点（第几天，15字内说明）"
}}

只返回JSON，不要其他解释。"""

        try:
            response = self.llm_client.chat(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.8,
                max_tokens=2000,
            )
            content = response if isinstance(response, str) else response.get("content", "")

            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]

            result = json.loads(content.strip())
            return result
        except Exception as e:
            default_events = []
            default_templates = [
                "事件开始发酵，社交媒体出现相关讨论",
                "话题热度上升，KOL开始关注并参与讨论",
                "主流媒体介入报道，舆论范围扩大",
                "官方首次回应，公众情绪出现分化",
                "讨论进入深水区，多方观点激烈碰撞",
                "舆情达到峰值，社会关注度最高",
                "话题开始降温，讨论趋于理性",
                "舆论逐渐平息，进入长尾阶段",
            ]
            for day in range(1, time_range + 1):
                idx = min(day - 1, len(default_templates) - 1)
                default_events.append({
                    "day": day,
                    "event": default_templates[idx],
                    "risk_hint": "正常" if day < 3 else ("需关注" if day < 6 else "高风险")
                })
            return {
                "events": default_events,
                "overall_trend": "舆情先升后降，中期风险较高",
                "key_turning_point": "第3-4天，舆情进入关键期"
            }

    def generate_strategy_comparison(
        self,
        event_summary: str,
        current_sentiment: str,
        strategies: List[Dict[str, Any]],
        original_timeline: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """多策略并排对比推演"""

        type_name_map = {t["id"]: t["name"] for t in INTERVENTION_TYPES}

        strategies_text = ""
        sir_results = []
        for i, s in enumerate(strategies, 1):
            s_type = s.get("type", "official_statement")
            s_name = type_name_map.get(s_type, s.get("description", s_type))
            s_desc = s.get("description", s_name)
            s_timing = s.get("timing", 2)

            sir_tl = self._compute_sir_intervention_timeline(
                event_summary, current_sentiment, len(original_timeline),
                s_type, s_timing, original_timeline
            )

            post_intervention = [n for n in sir_tl if n["day"] >= s_timing]
            avg_heat = sum(n["heat"] for n in post_intervention) / max(len(post_intervention), 1)
            avg_sent = sum(n["sentiment"] for n in post_intervention) / max(len(post_intervention), 1)

            orig_avg_heat = sum(n.get("heat", 50) for n in original_timeline) / max(len(original_timeline), 1)
            heat_change = round(avg_heat - orig_avg_heat, 1)

            orig_avg_sent = sum(n.get("sentiment", 0.5) for n in original_timeline) / max(len(original_timeline), 1)
            sent_change = round(avg_sent - orig_avg_sent, 2)

            sir_results.append({
                "index": i,
                "type": s_type,
                "name": s_name,
                "description": s_desc,
                "timing": s_timing,
                "timeline": sir_tl,
                "heat_change": heat_change,
                "sentiment_change": sent_change,
            })

            tl_summary = ", ".join([f"Day{n['day']}:{n['heat']}" for n in sir_tl[:7]])
            strategies_text += f"\n策略{i}: {s_name}（第{s_timing}天执行）- 热度变化:{heat_change}%, 情绪变化:{sent_change} - 趋势: {tl_summary}"

        original_summary = ", ".join([f"Day{n.get('day', i+1)}:{n.get('heat', 50)}" for i, n in enumerate(original_timeline[:7])])

        prompt = f"""你是一位资深的舆情危机公关顾问，擅长用通俗易懂的语言分析不同应对策略的优劣。请对比以下干预策略的效果。

事件背景：{event_summary}
当前情绪：{current_sentiment}

原始预测趋势：{original_summary}

各策略SIR模型推演结果：
{strategies_text}

【语言风格要求 - 必须严格遵守】
1. 绝对禁止使用以下词汇和表达：
   - 禁止："降温效果"、"显著"、"有效遏制"、"明显改善"、"情绪改善"、"压制热度"
   - 禁止："舆情发酵"、"舆论引导"、"公信力"、"态势"、"格局"、"窗口期"
   - 禁止："综上所述"、"建议综合评估"、"形成组合拳"、"综合施策"
   - 禁止：任何四字成语或官方套话

2. 必须使用口语化、接地气的表达：
   - 用"热度降下来"代替"降温效果显著"
   - 用"大家情绪会好一些"代替"情绪改善明显"
   - 用"这招"、"这个办法"代替"该策略"
   - 用"挺管用"、"还不错"代替"效果显著"

3. 每个字段的具体要求（必须严格执行）：
   - analysis字段（50-80字）：像跟朋友聊天一样分析这个策略怎么样，必须结合{event_summary}的具体背景，不能泛泛而谈。❌错误示例："降温效果最强，能快速压制热度，避免舆情发酵。但情绪改善有限，且长期热度被过度抑制，可能错失良性讨论机会，显得应对生硬。" ✅正确示例："这招对这个舆论事件挺管用的，能快速把热度压下去，但显得有点生硬，大家会觉得你在敷衍，不是真心想解决问题"
   - pros：说人话的优点列表，每个优点要具体可落地。❌错误示例：["降温效果显著", "有效遏制舆情扩散"] ✅正确示例：["见效快，当天就能看到热度下降", "能快速堵住不实谣言的传播"]
   - cons：说人话的缺点列表，每个缺点要具体实际。❌错误示例：["情绪改善有限", "长期热度被过度抑制"] ✅正确示例：["显得有点生硬，容易被骂做贼心虚", "会错过跟用户解释清楚的机会"]
   - recommendation（60-100字）：直接说结论，别绕弯子，要给出具体的执行建议。❌错误示例："综上所述，建议综合评估各策略的优缺点，选择最适合当前情况的方案，可考虑多策略组合使用。" ✅正确示例："建议主要用策略4，一个一个回应网友的质疑，前期可以先发个官方声明稳住局面，双管齐下效果最好。"

输出JSON格式：
{{
    "comparisons": [
        {{
            "strategy_name": "策略名称",
            "heat_change": -20,
            "sentiment_change": 0.3,
            "risk_level": "low",
            "score": 85,
            "analysis": "用大白话分析效果（50-80字）",
            "pros": ["优点1", "优点2"],
            "cons": ["缺点1", "缺点2"]
        }}
    ],
    "recommendation": "综合推荐建议（60-100字，直接说结论）"
}}

只返回JSON，不要其他解释。"""

        try:
            response = self.llm_client.chat(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=2500,
            )
            content = response if isinstance(response, str) else response.get("content", "")

            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]

            result = json.loads(content.strip())

            for i, comp in enumerate(result.get("comparisons", [])):
                if i < len(sir_results):
                    sr = sir_results[i]
                    comp["timeline"] = sr["timeline"]
                    comp["type"] = sr["type"]

            return result
        except Exception as e:
            comparisons = []
            for sr in sir_results:
                # 根据策略类型生成不同的默认内容
                base_pros = {
                    "official_statement": ["见效快，当天就能看到效果", "能快速堵住不实谣言"],
                    "kol_guidance": ["传播速度快，年轻人容易接受", "比官方说的话大家更信"],
                    "data_disclosure": ["用事实说话，大家更容易信服", "透明不容易被骂"],
                    "precise_response": ["针对性强，能解决大家真正关心的问题", "容易拉好感"],
                    "cold_treatment": ["不用做什么，省成本", "不会说错话搞出新问题"],
                    "topic_redirect": ["能把大家注意力引到正面内容上", "不用直面负面问题"]
                }
                base_cons = {
                    "official_statement": ["显得有点生硬，容易被骂敷衍", "说不好反而会火上浇油"],
                    "kol_guidance": ["KOL可能翻车，反而搞出新问题", "大家会觉得你在花钱控评"],
                    "data_disclosure": ["数据容易被大家断章取义", "整理数据要花不少时间"],
                    "precise_response": ["需要花不少人力去回应", "有一个回应不好就会被骂"],
                    "cold_treatment": ["容易被骂装死，大家情绪会更差", "可能会有新的谣言冒出来"],
                    "topic_redirect": ["转移太明显会被大家骂心虚", "新话题可能也会翻车"]
                }
                pros = base_pros.get(sr["type"], ["有一定效果", "可执行"])
                cons = base_cons.get(sr["type"], ["效果不确定", "有一定风险"])

                comparisons.append({
                    "strategy_name": sr["name"],
                    "type": sr["type"],
                    "timeline": sr["timeline"],
                    "heat_change": sr["heat_change"],
                    "sentiment_change": sr["sentiment_change"],
                    "risk_level": "low" if sr["heat_change"] < -15 else ("medium" if sr["heat_change"] < -5 else "high"),
                    "score": max(30, min(95, 70 + int(sr["heat_change"]))),
                    "analysis": f"这个{sr['name']}的办法大概能让热度降{abs(sr['heat_change'])}%左右，整体还可以。",
                    "pros": pros,
                    "cons": cons,
                })
            return {
                "comparisons": comparisons,
                "recommendation": "建议主要用精准回应的办法，针对大家关心的问题一个个回答，前期可以先出个官方声明稳住局面。",
            }

    def generate_intervention_heatmap(
        self,
        event_summary: str,
        current_sentiment: str,
        time_range: int,
        intervention_types: List[str],
        original_timeline: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """生成干预时机热力图"""

        type_name_map = {t["id"]: t["name"] for t in INTERVENTION_TYPES}

        heatmap_data = []
        for itype in intervention_types:
            scores = []
            for day in range(1, time_range + 1):
                sir_tl = self._compute_sir_intervention_timeline(
                    event_summary, current_sentiment, time_range,
                    itype, day, original_timeline
                )

                post = [n for n in sir_tl if n["day"] >= day]
                orig_post = [n for n in original_timeline if n.get("day", 0) >= day]

                if post and orig_post:
                    avg_heat_post = sum(n["heat"] for n in post) / len(post)
                    avg_heat_orig = sum(n.get("heat", 50) for n in orig_post) / len(orig_post)
                    heat_reduction = avg_heat_orig - avg_heat_post

                    avg_sent_post = sum(n["sentiment"] for n in post) / len(post)
                    avg_sent_orig = sum(n.get("sentiment", 0.5) for n in orig_post) / len(orig_post)
                    sent_improvement = avg_sent_post - avg_sent_orig

                    score = max(0, min(100, int(50 + heat_reduction * 1.5 + sent_improvement * 50)))
                else:
                    score = 50

                if score >= 80:
                    effectiveness = "极高"
                elif score >= 60:
                    effectiveness = "高"
                elif score >= 40:
                    effectiveness = "中等"
                elif score >= 20:
                    effectiveness = "较低"
                else:
                    effectiveness = "低效"

                risk_note = ""
                if itype == "official_statement" and day > 3:
                    risk_note = "回应过晚，公信力受损"
                elif itype == "cold_treatment" and day <= 2:
                    risk_note = "过早冷处理可能激化情绪"
                elif itype == "kol_guidance" and day <= 1:
                    risk_note = "事件初期KOL介入可能引质疑"
                elif itype == "data_disclosure" and day <= 1:
                    risk_note = "数据尚未整理完毕"
                elif score >= 80:
                    risk_note = "黄金时机"
                elif score >= 60:
                    risk_note = "仍在有效窗口"
                elif score < 30:
                    risk_note = "时机不佳"

                scores.append({
                    "day": day,
                    "score": score,
                    "effectiveness": effectiveness,
                    "risk_note": risk_note,
                })

            heatmap_data.append({
                "type": itype,
                "type_name": type_name_map.get(itype, itype),
                "scores": scores,
            })

        return {"heatmap": heatmap_data}

    def generate_cascade_effect(
        self,
        event_summary: str,
        intervention_type: str,
        intervention_description: str,
        simulation_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """生成链式反应推演"""

        type_name_map = {t["id"]: t["name"] for t in INTERVENTION_TYPES}
        intervention_name = type_name_map.get(intervention_type, intervention_type)

        agent_summary = ""
        all_actions = simulation_data.get("all_actions", [])
        if all_actions:
            action_types = {}
            for action in all_actions:
                at = action.get("action_type", "unknown")
                action_types[at] = action_types.get(at, 0) + 1
            agent_summary = f"模拟数据包含{len(all_actions)}条Agent活动记录，类型分布：{json.dumps(action_types, ensure_ascii=False)}"

        prompt = f"""你是一位社交网络传播分析专家。请推演以下干预措施在社交网络中的链式传播过程。

事件背景：{event_summary}
干预类型：{intervention_name}
干预描述：{intervention_description}

OASIS模拟数据概况：
{agent_summary if agent_summary else '暂无模拟数据，请基于一般社交网络规律推演'}

请推演干预信息如何通过社交网络逐层传播，生成3-4层传播链。

输出JSON格式：
{{
    "layers": [
        {{
            "level": 1,
            "description": "干预信息发布（15字内）",
            "affected_count": 1,
            "sentiment_shift": 0,
            "key_agents": [{{"name": "发布者名称", "influence": "high", "role": "官方账号"}}]
        }},
        {{
            "level": 2,
            "description": "意见领袖和媒体转发扩散（15字内）",
            "affected_count": 15,
            "sentiment_shift": 0.1,
            "key_agents": [{{"name": "某知名博主", "influence": "high", "role": "KOL"}}, {{"name": "某主流媒体", "influence": "high", "role": "媒体"}}]
        }},
        {{
            "level": 3,
            "description": "普通用户讨论和情绪转变（15字内）",
            "affected_count": 200,
            "sentiment_shift": 0.2,
            "key_agents": []
        }}
    ],
    "total_reach": 216,
    "cascade_speed": "传播速度描述（如：中等，约6-12小时覆盖核心群体）",
    "analysis": "链式反应分析（80-120字）"
}}

只返回JSON，不要其他解释。"""

        try:
            response = self.llm_client.chat(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=1500,
            )
            content = response if isinstance(response, str) else response.get("content", "")

            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]

            return json.loads(content.strip())
        except Exception as e:
            return {
                "layers": [
                    {"level": 1, "description": "干预信息发布", "affected_count": 1, "sentiment_shift": 0, "key_agents": [{"name": "官方账号", "influence": "high", "role": "发布者"}]},
                    {"level": 2, "description": "KOL和媒体转发", "affected_count": 20, "sentiment_shift": 0.1, "key_agents": [{"name": "意见领袖", "influence": "high", "role": "KOL"}]},
                    {"level": 3, "description": "普通用户讨论", "affected_count": 300, "sentiment_shift": 0.2, "key_agents": []},
                ],
                "total_reach": 321,
                "cascade_speed": "中等，约6-12小时覆盖核心群体",
                "analysis": f"「{intervention_name}」通过KOL和媒体的二次传播，逐步影响普通用户的认知和情绪。",
            }

    def generate_counterfactual(
        self,
        event_summary: str,
        current_sentiment: str,
        original_timeline: List[Dict[str, Any]],
        removed_event_day: int,
        removed_event_desc: str,
    ) -> Dict[str, Any]:
        """反事实推演"""

        original_text = ""
        for node in original_timeline:
            original_text += f"\nDay{node.get('day', 0)}: 热度={node.get('heat', 0)}, 情绪={node.get('sentiment', 0)}, 风险={node.get('risk', 'medium')}, 事件={node.get('event', '')}"

        sir_timeline = self._compute_counterfactual_sir(
            event_summary, current_sentiment, len(original_timeline),
            removed_event_day, original_timeline
        )

        cf_text = ""
        for node in sir_timeline:
            cf_text += f"\nDay{node.get('day', 0)}: 热度={node.get('heat', 0)}, 情绪={node.get('sentiment', 0)}, 风险={node.get('risk', 'medium')}"

        prompt = f"""你是一位舆情因果推断专家。请进行反事实推演：如果某个关键事件没有发生，舆情会如何发展？

事件背景：{event_summary}
当前情绪：{current_sentiment}

原始预测时间线：
{original_text}

假设移除的事件：第{removed_event_day}天的「{removed_event_desc}」

SIR模型计算的反事实趋势（移除该事件后的传播率降低）：
{cf_text}

请基于SIR模型趋势，生成反事实时间线和分析。

输出JSON格式：
{{
    "counterfactual_timeline": [
        {{
            "day": 1,
            "heat": 75,
            "sentiment": 0.5,
            "risk": "medium",
            "event": "事件描述（15字内）"
        }}
    ],
    "impact_score": 35,
    "impact_description": "该事件贡献了约X%的舆情热度（20字内）",
    "analysis": "反事实分析（80-120字，说明移除该事件后舆情的差异）",
    "key_difference": "核心差异描述（30字内）"
}}

只返回JSON，不要其他解释。"""

        try:
            response = self.llm_client.chat(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=2000,
            )
            content = response if isinstance(response, str) else response.get("content", "")

            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]

            return json.loads(content.strip())
        except Exception as e:
            orig_peak = max((n.get("heat", 0) for n in original_timeline), default=50)
            cf_peak = max((n["heat"] for n in sir_timeline), default=50)
            impact = round((orig_peak - cf_peak) / max(orig_peak, 1) * 100)

            return {
                "counterfactual_timeline": sir_timeline,
                "impact_score": impact,
                "impact_description": f"该事件贡献了约{impact}%的舆情热度",
                "analysis": f"如果没有「{removed_event_desc}」，舆情热度峰值将从{orig_peak}降至{cf_peak}，整体风险等级降低。该事件是推动舆情升级的关键因素。",
                "key_difference": f"峰值热度从{orig_peak}降至{cf_peak}",
            }

    def _compute_counterfactual_sir(
        self,
        event_summary: str,
        current_sentiment: str,
        time_range: int,
        removed_event_day: int,
        original_timeline: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """计算反事实SIR时间线（移除某事件后传播率降低）"""

        sentiment_factor = {
            "正面": 0.8, "负面": 1.2, "中性": 1.0, "复杂": 1.1,
        }.get(current_sentiment, 1.0)

        base_beta = 0.3 * sentiment_factor
        base_gamma = 0.1

        S = 0.9
        I = 0.1
        R = 0.0
        dt = 0.1

        timeline = []
        for day in range(1, time_range + 1):
            beta = base_beta
            gamma = base_gamma

            if day >= removed_event_day:
                beta *= 0.7
                gamma *= 1.2

            for _ in range(int(1 / dt)):
                dS = (-beta * S * I + 0.01 * R) * dt
                dI = (beta * S * I - gamma * I) * dt
                dR = (gamma * I - 0.01 * R) * dt
                S = max(0, min(1, S + dS))
                I = max(0, min(1, I + dI))
                R = max(0, min(1, R + dR))

            heat = int(I * 100)
            sentiment = round(0.3 + S * 0.5, 2)
            risk = "high" if heat > 70 else ("medium" if heat > 40 else "low")

            event = "舆情热度较低，讨论趋于平静"
            if day < removed_event_day:
                if day - 1 < len(original_timeline):
                    event = original_timeline[day - 1].get("event", event)
            else:
                if heat > 60:
                    event = "舆情有所讨论但未大规模扩散"
                elif heat > 40:
                    event = "讨论保持理性，未出现激化"
                else:
                    event = "关注度低，舆情平稳"

            timeline.append({
                "day": day,
                "heat": heat,
                "sentiment": sentiment,
                "risk": risk,
                "event": event,
            })

        return timeline
