"""
舆情预测服务 - 混合引擎版

功能模块：
1. 舆情时间轴推演 - SIR模型(算法) / LLM
2. 多情景概率预测 - 贝叶斯网络(算法) / LLM
3. 干预策略模拟器 - LLM
4. 关键节点预警 - 规则引擎
5. AI深度对话 - LLM

引擎模式:
- algorithm: 纯算法模式（时间轴+情景使用算法）
- llm: 纯LLM模式（全部使用LLM）
- hybrid: 混合模式（时间轴+情景使用算法，其他使用LLM）
"""

import os
import json
import random
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict

from ..config import Config
from ..utils.llm_client import LLMClient
from .algorithm_engine import AlgorithmEngine


@dataclass
class PredictionScenario:
    """预测场景"""

    name: str
    description: str
    probability: float
    key_factors: List[str]
    timeline: str
    risk_level: str


@dataclass
class TimelineNode:
    """时间轴节点"""

    day: int
    event: str
    sentiment: float
    heat: float
    risk: str
    description: str


@dataclass
class WarningNode:
    """预警节点"""

    day: int
    type: str
    level: str
    description: str
    suggestion: str


@dataclass
class InterventionResult:
    """干预结果"""

    strategy: str
    expected_effect: str
    risk: str
    recommendation: int
    heat_change: float
    sentiment_change: float


class PublicOpinionPredictionService:
    """舆情预测服务 - 混合引擎版"""

    def __init__(self):
        self.llm_client = LLMClient()
        self.algorithm_engine = AlgorithmEngine()
        self.engine_mode = getattr(Config, 'PREDICTION_ENGINE', 'hybrid')

    def predict_full(
        self,
        simulation_id: str,
        report_id: str,
        event_summary: str,
        current_sentiment: str = "中性",
        time_range: int = 7,
    ) -> Dict[str, Any]:
        """
        完整预测：包含5个功能模块

        Args:
            simulation_id: 模拟ID
            report_id: 报告ID（用于获取历史数据）
            event_summary: 事件摘要
            current_sentiment: 当前情绪
            time_range: 预测天数

        Returns:
            完整预测结果
        """

        # 模块1: 时间轴推演 - 根据引擎模式选择
        timeline = self._generate_timeline(event_summary, current_sentiment, time_range)

        # 模块2: 多情景预测 - 根据引擎模式选择
        scenarios = self._generate_scenarios(event_summary, current_sentiment)
        
        # 模块2.5: 情景描述说明 - LLM生成
        scenario_summary = self._generate_scenario_summary(scenarios, event_summary)

        # 模块3: 关键节点预警 - 规则引擎（无需LLM）
        warnings = self._generate_warnings(timeline, scenarios)

        # 模块4: 可视化数据 - 纯计算（无需LLM）
        visualization = self._generate_visualization(timeline, scenarios, warnings)

        # 模块5: 初始结论 - 模板化（无需LLM）
        conclusion = self._generate_conclusion(scenarios, warnings)

        return {
            "simulation_id": simulation_id,
            "report_id": report_id,
            "event_summary": event_summary,
            "current_sentiment": current_sentiment,
            "time_range": time_range,
            "generated_at": datetime.now().isoformat(),
            "engine_mode": self.engine_mode,
            # 5个功能模块
            "timeline": timeline,
            "scenarios": scenarios,
            "scenario_summary": scenario_summary,
            "warnings": warnings,
            "visualization": visualization,
            "conclusion": conclusion,
        }

    def _generate_timeline(
        self, event_summary: str, sentiment: str, days: int
    ) -> List[Dict[str, Any]]:
        """模块1: 生成时间轴推演 - 混合引擎"""
        
        # 算法模式或混合模式：使用SIR模型
        if self.engine_mode in ['algorithm', 'hybrid']:
            try:
                return self.algorithm_engine.generate_timeline(
                    event_summary=event_summary,
                    current_sentiment=sentiment,
                    days=days
                )
            except Exception as e:
                print(f"[AlgorithmEngine] SIR模型预测失败，回退到LLM: {e}")
        
        # LLM模式或算法失败时的回退
        sentiment_map = {
            "正面": 0.7,
            "负面": 0.3,
            "中性": 0.5,
            "复杂": 0.4,
        }
        base_sentiment = sentiment_map.get(sentiment, 0.5)

        prompt = f"""你是一个舆情预测专家。请预测以下事件在接下来{days}天的发展轨迹。

事件：{event_summary}
当前情绪：{sentiment}

请生成一个{days}天的时间线，每天包含：
1. 可能发生的标志性事件
2. 预测的热度指数（0-100）
3. 预测的情绪指数（0-1，0为完全负面，1为完全正面）
4. 风险等级（low/medium/high）

请以JSON格式返回：
[{{
    "day": 1,
    "event": "第1天可能的事件",
    "heat": 80,
    "sentiment": 0.6,
    "risk": "medium",
    "description": "描述"
}}]
"""

        try:
            response = self.llm_client.chat(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=2000,
            )

            content = (
                response if isinstance(response, str) else response.get("content", "")
            )

            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]

            timeline = json.loads(content.strip())
            return timeline[:days]

        except Exception as e:
            # 生成默认时间线
            return self._generate_default_timeline(days, base_sentiment)

    def _generate_default_timeline(
        self, days: int, base_sentiment: float
    ) -> List[Dict[str, Any]]:
        """生成默认时间线"""
        timeline = []
        for i in range(1, days + 1):
            heat = max(20, min(100, 80 - i * 5 + random.randint(-10, 10)))
            sent = max(0.1, min(0.9, base_sentiment + random.uniform(-0.1, 0.1)))

            if i <= 2:
                risk = "high" if heat > 70 else "medium"
                event = f"事件持续发酵，{'关注度上升' if heat > 70 else '开始平稳'}"
            elif i <= 5:
                risk = "medium"
                event = "舆论走向关键期，可能出现转折点"
            else:
                risk = "low"
                event = "热度逐渐消退，进入常态化"

            timeline.append(
                {
                    "day": i,
                    "event": event,
                    "heat": heat,
                    "sentiment": round(sent, 2),
                    "risk": risk,
                    "description": f"第{i}天预测",
                }
            )
        return timeline

    def _generate_scenarios(
        self, event_summary: str, sentiment: str
    ) -> List[Dict[str, Any]]:
        """模块2: 生成多情景概率预测 - 混合引擎"""
        
        # 算法模式或混合模式：使用贝叶斯网络
        if self.engine_mode in ['algorithm', 'hybrid']:
            try:
                return self.algorithm_engine.generate_scenarios(
                    event_summary=event_summary,
                    current_sentiment=sentiment
                )
            except Exception as e:
                print(f"[AlgorithmEngine] 贝叶斯预测失败，回退到LLM: {e}")

        prompt = f"""你是一个专业的舆情分析师。请预测这个舆情事件可能的发展方向和概率。

事件：{event_summary}
当前情绪：{sentiment}

请生成4-5个可能的发展场景，要求：
1. 场景名称要简洁明了
2. 概率总和约为100
3. 包含风险等级和关键因素

请以JSON格式返回：
[{{
    "name": "场景名称",
    "description": "详细描述",
    "probability": 30,
    "key_factors": ["因素1", "因素2"],
    "timeline": "时间线预测",
    "risk_level": "high/medium/low"
}}]
"""

        try:
            response = self.llm_client.chat(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=3000,
            )

            content = (
                response if isinstance(response, str) else response.get("content", "")
            )

            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]

            scenarios = json.loads(content.strip())
            return scenarios

        except Exception as e:
            return self._generate_default_scenarios()

    def _generate_default_scenarios(self) -> List[Dict[str, Any]]:
        """生成默认情景"""
        return [
            {
                "name": "平稳过渡",
                "description": "热度逐渐下降，舆情平稳消退，公众注意力转移到其他事件",
                "probability": 35,
                "key_factors": ["新热点出现", "官方及时回应", "无新争议点"],
                "timeline": "3-5天内热度明显下降",
                "risk_level": "low",
            },
            {
                "name": "二次爆发",
                "description": "出现新证据或意见领袖发声，引发第二轮讨论高潮",
                "probability": 25,
                "key_factors": ["新证据曝光", "KOL发声", "官方回应不当"],
                "timeline": "第4-7天可能出现",
                "risk_level": "high",
            },
            {
                "name": "持续发酵",
                "description": "保持在热搜榜单，舆情进入常态化讨论",
                "probability": 20,
                "key_factors": ["话题具有持续争议性", "多方持续发声"],
                "timeline": "持续1-2周",
                "risk_level": "medium",
            },
            {
                "name": "官方介入",
                "description": "监管机构或官方媒体正式回应，舆论走向可控",
                "probability": 15,
                "key_factors": ["官方声明", "政策出台", "舆论管控"],
                "timeline": "1周内",
                "risk_level": "low",
            },
        ]

    def _generate_scenario_summary(
        self, scenarios: List[Dict[str, Any]], event_summary: str
    ) -> str:
        """生成情景概率分布的描述说明"""
        
        # 提取关键信息
        top_scenario = max(scenarios, key=lambda x: x.get('probability', 0))
        high_risk_count = sum(1 for s in scenarios if s.get('risk_level') == 'high')
        
        prompt = f"""请为以下舆情情景概率分布写一段简短的描述说明（2-3句话，不超过80字）。

事件背景：{event_summary[:200]}

情景分布：
{json.dumps([{'name': s['name'], 'probability': s['probability'], 'risk_level': s['risk_level']} for s in scenarios], ensure_ascii=False)}

最可能情景：{top_scenario['name']}（{top_scenario['probability']}%）
高风险情景数量：{high_risk_count}

要求：
1. 说明最可能的发展方向
2. 提及风险分布情况
3. 语言简洁专业，适合在界面上展示

请直接返回描述文字，不要包含任何格式标记。"""

        try:
            response = self.llm_client.chat(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.5,
                max_tokens=200,
            )
            content = response if isinstance(response, str) else response.get("content", "")
            return content.strip()
        except Exception as e:
            # 降级：生成默认描述
            risk_text = f"其中{high_risk_count}个为高风险情景" if high_risk_count > 0 else "整体风险可控"
            return f"当前舆情最可能朝「{top_scenario['name']}」方向发展，概率为{top_scenario['probability']}%。{risk_text}，建议持续关注舆情动态。"

    def _generate_warnings(
        self, timeline: List[Dict], scenarios: List[Dict]
    ) -> List[Dict[str, Any]]:
        """模块3: 生成关键节点预警"""

        warnings = []

        # 从时间线中识别高风险节点
        for node in timeline:
            if node.get("risk") == "high":
                warnings.append(
                    {
                        "day": node.get("day"),
                        "type": "风险节点",
                        "level": "high",
                        "description": node.get("event", ""),
                        "suggestion": "建议提前准备应对方案，密切关注舆情动态",
                    }
                )

        # 从情景中识别风险
        high_risk_scenarios = [s for s in scenarios if s.get("risk_level") == "high"]
        if high_risk_scenarios and len(warnings) < 3:
            for scenario in high_risk_scenarios[:2]:
                warnings.append(
                    {
                        "day": 0,
                        "type": "高风险情景",
                        "level": scenario.get("risk_level"),
                        "description": f"可能出现情景：{scenario.get('name')}",
                        "suggestion": f"关键因素：{', '.join(scenario.get('key_factors', [])[:2])}",
                    }
                )

        # 添加通用预警
        if len(warnings) == 0:
            warnings.append(
                {
                    "day": 3,
                    "type": "常规关注",
                    "level": "medium",
                    "description": "第3天为舆论走向关键节点",
                    "suggestion": "建议持续关注，准备应急预案",
                }
            )

        return warnings[:5]

    def _generate_visualization(
        self, timeline: List[Dict], scenarios: List[Dict], warnings: List[Dict]
    ) -> Dict[str, Any]:
        """模块4: 生成可视化数据"""

        # 热度/情绪曲线
        heat_curve = [{"day": n["day"], "value": n["heat"]} for n in timeline]
        sentiment_curve = [{"day": n["day"], "value": n["sentiment"]} for n in timeline]

        # 情景概率
        probability_data = [
            {"name": s["name"], "value": s["probability"], "risk": s["risk_level"]}
            for s in scenarios
        ]

        # 风险分布
        risk_count = {"high": 0, "medium": 0, "low": 0}
        for s in scenarios:
            risk = s.get("risk_level", "medium")
            risk_count[risk] = risk_count.get(risk, 0) + 1

        # 预警分布
        warning_by_level = {"high": 0, "medium": 0, "low": 0}
        for w in warnings:
            level = w.get("level", "medium")
            warning_by_level[level] = warning_by_level.get(level, 0) + 1

        return {
            "heat_curve": heat_curve,
            "sentiment_curve": sentiment_curve,
            "probability_chart": probability_data,
            "risk_distribution": risk_count,
            "warning_distribution": warning_by_level,
            "timeline_markers": [
                {"day": w["day"], "type": w["type"], "level": w["level"]}
                for w in warnings
            ],
        }

    def _generate_conclusion(self, scenarios: List[Dict], warnings: List[Dict]) -> str:
        """生成预测结论"""

        # 找出最高概率情景
        top = max(scenarios, key=lambda x: x.get("probability", 0))
        top_name = top.get("name", "")
        top_prob = top.get("probability", 0)
        top_desc = top.get("description", "")

        # 找出第二高概率情景
        sorted_scenarios = sorted(scenarios, key=lambda x: x.get("probability", 0), reverse=True)
        second = sorted_scenarios[1] if len(sorted_scenarios) > 1 else None

        # 统计风险
        risk_count = {"high": 0, "medium": 0, "low": 0}
        for s in scenarios:
            r = s.get("risk_level", "medium")
            risk_count[r] = risk_count.get(r, 0) + 1

        high_risk_count = risk_count.get("high", 0)
        medium_risk_count = risk_count.get("medium", 0)

        # 根据概率区间选择不同的表达方式
        if top_prob >= 50:
            confidence = "极大概率"
        elif top_prob >= 35:
            confidence = "较大概率"
        elif top_prob >= 25:
            confidence = "可能"
        else:
            confidence = "有一定可能"

        # 根据风险等级构建描述
        if high_risk_count >= 2:
            risk_desc = "整体风险偏高，需高度警惕"
        elif high_risk_count == 1:
            risk_desc = "存在一定风险，建议密切关注"
        elif medium_risk_count > 0:
            risk_desc = "风险可控，但仍需防范"
        else:
            risk_desc = "整体风险较低，态势平稳"

        # 构建情景描述
        scenario_templates = {
            "平稳过渡": f"舆情将逐渐降温，公众注意力转移，{top_desc[:30] if top_desc else '事件影响逐步消退'}",
            "二次爆发": f"需警惕舆情反弹，{top_desc[:30] if top_desc else '可能出现新一轮讨论高潮'}",
            "持续发酵": f"话题将持续引发关注，{top_desc[:30] if top_desc else '进入常态化讨论阶段'}",
            "官方介入": f"官方回应将成为关键，{top_desc[:30] if top_desc else '监管态度影响舆情走向'}",
            "温和争议": f"争议将保持温和态势，{top_desc[:30] if top_desc else '不会出现剧烈波动'}",
            "制度调整": f"可能引发制度层面反思，{top_desc[:30] if top_desc else '推动相关政策完善'}",
        }

        # 找到匹配的情景描述
        scenario_desc = None
        for key, desc in scenario_templates.items():
            if key in top_name:
                scenario_desc = desc
                break

        if not scenario_desc:
            scenario_desc = top_desc[:50] if top_desc else f"预计出现'{top_name}'的发展态势"

        # 构建预警提示
        if len(warnings) == 0:
            warning_text = "暂无重大风险预警"
        elif len(warnings) == 1:
            warning_text = f"需关注{warnings[0].get('day', 0)}天后的关键节点"
        else:
            days = [w.get('day', 0) for w in warnings if w.get('day', 0) > 0]
            if days:
                warning_text = f"需重点关注第{min(days)}天和第{max(days)}天等关键节点"
            else:
                warning_text = f"需关注{len(warnings)}个关键风险节点"

        # 组合结论
        conclusion = f"{confidence}出现「{top_name}」的情景（{top_prob}%）。{scenario_desc}。{risk_desc}，{warning_text}。"

        # 如果有次高概率情景且概率接近，添加补充说明
        if second and second.get("probability", 0) > top_prob - 15 and second.get("probability", 0) >= 20:
            conclusion += f"同时需防范「{second.get('name')}」的可能性（{second.get('probability')}%）。"

        return conclusion

    def simulate_intervention(
        self, event_summary: str, intervention: str, current_sentiment: str = "中性"
    ) -> Dict[str, Any]:
        """
        干预策略模拟

        Args:
            event_summary: 事件摘要
            intervention: 干预措施描述
            current_sentiment: 当前情绪

        Returns:
            干预效果预测
        """

        prompt = f"""你是一个舆情干预专家。请模拟以下干预策略的效果。

事件：{event_summary}
干预措施：{intervention}
当前情绪：{current_sentiment}

请分析这个干预策略的效果，包括：
1. 预期热度变化（百分比，正数表示上升，负数表示下降）
2. 预期情绪变化（正数表示变正面，负数表示变负面）
3. 可能的风险
4. 推荐度（1-5星）

请以JSON格式返回：
{{
    "strategy": "{intervention}",
    "expected_effect": "效果描述",
    "heat_change": 10,
    "sentiment_change": 0.1,
    "risk": "可能的风险",
    "recommendation": 4
}}
"""

        try:
            response = self.llm_client.chat(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=1000,
            )

            content = (
                response if isinstance(response, str) else response.get("content", "")
            )

            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]

            result = json.loads(content.strip())
            return result

        except Exception as e:
            return {
                "strategy": intervention,
                "expected_effect": "模拟失败，使用默认效果",
                "heat_change": random.randint(-30, 20),
                "sentiment_change": round(random.uniform(-0.1, 0.2), 2),
                "risk": "存在不确定性",
                "recommendation": 3,
            }

    def chat_about_prediction(
        self, question: str, prediction_data: Dict[str, Any]
    ) -> str:
        """
        AI对话：基于预测结果回答问题

        Args:
            question: 用户问题
            prediction_data: 预测数据

        Returns:
            回答内容
        """

        context = f"""你是一个舆情预测专家。请基于以下预测数据回答用户的问题。

预测摘要：
- 事件：{prediction_data.get("event_summary", "")}
- 预测天数：{prediction_data.get("time_range", 7)}天
- 结论：{prediction_data.get("conclusion", "")}

用户问题：{question}

请用简洁专业的语言回答。如果用户问的是预测相关的问题，给出你的专业建议。
"""

        try:
            response = self.llm_client.chat(
                messages=[{"role": "user", "content": context}],
                temperature=0.7,
                max_tokens=500,
            )

            return (
                response if isinstance(response, str) else response.get("content", "")
            )

        except Exception as e:
            return "抱歉，我现在无法回答这个问题。请稍后再试。"

    # 以下为保留的原有方法
    def predict(
        self,
        simulation_id: str,
        current_time: str,
        event_summary: str,
        public_sentiment: str,
        key_actors: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """兼容旧版API"""

        result = self.predict_full(
            simulation_id=simulation_id,
            report_id="",
            event_summary=event_summary,
            current_sentiment=public_sentiment,
        )

        # 转换为旧版格式
        return {
            "simulation_id": simulation_id,
            "current_time": current_time,
            "event_summary": event_summary,
            "public_sentiment": public_sentiment,
            "thinking_process": [
                {
                    "step": "分析",
                    "thinking": "基于事件分析",
                    "conclusion": result["conclusion"],
                }
            ],
            "scenarios": result["scenarios"],
            "conclusion": result["conclusion"],
            "visualization": result["visualization"],
        }
