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

        # 模块5: 初始结论 - 使用LLM润色
        conclusion = self._generate_conclusion(scenarios, warnings, event_summary)

        return {
            "simulation_id": simulation_id,
            "report_id": report_id,
            "event_summary": event_summary,
            "current_sentiment": current_sentiment,
            "time_range": time_range,
            "generated_at": datetime.now().isoformat(),
            "engine_mode": self.engine_mode,
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
                scenarios = self.algorithm_engine.generate_scenarios(
                    event_summary=event_summary,
                    current_sentiment=sentiment
                )
                # 使用LLM润色情景描述
                return self._polish_scenario_descriptions(scenarios, event_summary)
            except Exception as e:
                print(f"[AlgorithmEngine] 贝叶斯预测失败，回退到LLM: {e}")

        # LLM模式：直接生成并润色
        return self._generate_llm_scenarios(event_summary, sentiment)

    def _polish_scenario_descriptions(
        self, scenarios: List[Dict[str, Any]], event_summary: str
    ) -> List[Dict[str, Any]]:
        """使用LLM润色情景描述"""
        
        # 准备情景信息
        scenario_info = []
        for s in scenarios:
            scenario_info.append({
                "name": s.get("name", ""),
                "probability": s.get("probability", 0),
                "risk_level": s.get("risk_level", "medium"),
                "original_description": s.get("description", ""),
                "key_factors": s.get("key_factors", [])
            })

        prompt = f"""你是一位资深的舆情分析专家。请为以下舆情预测情景润色描述，使其更加自然、专业、有洞察力。

事件背景：{event_summary[:200]}

原始情景数据：
{json.dumps(scenario_info, ensure_ascii=False, indent=2)}

润色要求：
1. 每个情景的描述控制在60-80字
2. 语言要自然流畅，避免生硬的数据堆砌
3. 结合事件背景，给出有洞察力的分析
4. 突出该情景的核心特征和可能的影响
5. 保持客观专业的语气

请以JSON格式返回润色后的描述：
{{
    "descriptions": [
        {{
            "name": "情景名称",
            "polished_description": "润色后的自然描述...",
            "insight": "核心洞察（20字以内）"
        }}
    ]
}}

只返回JSON，不要其他解释。"""

        try:
            response = self.llm_client.chat(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=1500,
            )

            content = response if isinstance(response, str) else response.get("content", "")
            
            # 解析JSON
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]

            result = json.loads(content.strip())
            polished = result.get("descriptions", [])

            # 更新情景描述
            for i, scenario in enumerate(scenarios):
                if i < len(polished):
                    scenario["description"] = polished[i].get(
                        "polished_description", scenario.get("description", "")
                    )
                    scenario["insight"] = polished[i].get("insight", "")

            return scenarios

        except Exception as e:
            print(f"[LLM] 润色情景描述失败，使用原始描述: {e}")
            return scenarios

    def _generate_llm_scenarios(
        self, event_summary: str, sentiment: str
    ) -> List[Dict[str, Any]]:
        """使用LLM直接生成润色后的情景"""

        prompt = f"""你是一位资深的舆情分析师。请为以下舆情事件预测可能的发展情景。

事件：{event_summary}
当前情绪：{sentiment}

请生成4-5个发展情景，每个情景包含：
1. 简洁明了的名称
2. 结合事件背景的自然描述（60-80字），突出该情景的核心特征和可能的影响
3. 概率（总和约100）
4. 风险等级（high/medium/low）
5. 3-5个与该情景紧密相关的关键词
6. 时间线预测
7. 一句话核心洞察

请以JSON格式返回：
[{{
    "name": "场景名称",
    "description": "结合事件背景的自然描述...",
    "probability": 30,
    "risk_level": "medium",
    "keywords": ["关键词1", "关键词2", "关键词3"],
    "timeline": "时间线预测",
    "insight": "核心洞察"
}}]

只返回JSON数组，不要其他解释。"""

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

    def _generate_default_scenarios(
        self, event_summary: str = "", sentiment: str = "中性"
    ) -> List[Dict[str, Any]]:
        """生成基于事件特征的动态默认情景"""

        # 从事件摘要提取关键词特征
        event_lower = event_summary.lower()

        # 定义事件类型特征词
        event_types = {
            "product_issue": ["产品", "质量", "故障", "bug", "体验", "服务"],
            "company_crisis": ["裁员", "倒闭", "破产", "财务", "业绩", "亏损"],
            "public_safety": ["事故", "安全", "伤亡", "爆炸", "泄漏", "污染"],
            "celebrity": ["明星", "艺人", "网红", "绯闻", "出轨", "离婚"],
            "policy": ["政策", "法规", "规定", "禁令", "限制", "调整"],
            "social": ["歧视", "公平", "性别", "种族", "阶层", "矛盾"],
        }

        # 检测事件类型
        detected_type = "general"
        type_scores = {}
        for etype, keywords in event_types.items():
            score = sum(1 for kw in keywords if kw in event_lower)
            if score > 0:
                type_scores[etype] = score
        if type_scores:
            detected_type = max(type_scores, key=type_scores.get)

        # 基于事件类型和情绪调整概率分布
        base_probs = self._get_scenario_probabilities(detected_type, sentiment)

        # 生成情景描述
        scenarios = self._build_scenarios_by_type(detected_type, base_probs, sentiment)

        return scenarios

    def _get_scenario_probabilities(self, event_type: str, sentiment: str) -> Dict[str, int]:
        """根据事件类型和情绪获取情景概率分布"""

        # 基础概率模板
        templates = {
            "product_issue": {
                "平稳过渡": 40, "品牌修复": 25, "口碑恶化": 20, "竞品借势": 10, "行业反思": 5
            },
            "company_crisis": {
                "平稳过渡": 25, "危机深化": 30, "重组转型": 20, "行业震荡": 15, "监管介入": 10
            },
            "public_safety": {
                "平稳过渡": 20, "调查深入": 35, "责任追究": 25, "制度完善": 15, "同类排查": 5
            },
            "celebrity": {
                "平稳过渡": 35, "持续热议": 30, "反转洗白": 15, "事业受挫": 15, "同类曝光": 5
            },
            "policy": {
                "平稳过渡": 45, "讨论深化": 25, "执行争议": 15, "调整优化": 10, "社会适应": 5
            },
            "social": {
                "平稳过渡": 30, "持续讨论": 35, "群体对立": 20, "共识形成": 10, "政策响应": 5
            },
            "general": {
                "平稳过渡": 40, "持续发酵": 25, "二次爆发": 15, "官方介入": 12, "连锁反应": 8
            }
        }

        probs = templates.get(event_type, templates["general"]).copy()

        # 根据情绪调整概率
        sentiment_adjustments = {
            "正面": {"平稳过渡": 10, "持续发酵": -5, "二次爆发": -5},
            "负面": {"平稳过渡": -10, "持续发酵": 5, "二次爆发": 5},
            "复杂": {"平稳过渡": -5, "持续发酵": 5}
        }

        adjustments = sentiment_adjustments.get(sentiment, {})
        for key, adj in adjustments.items():
            if key in probs:
                probs[key] = max(5, min(60, probs[key] + adj))

        # 归一化到100
        total = sum(probs.values())
        return {k: round(v * 100 / total) for k, v in probs.items()}

    def _build_scenarios_by_type(
        self, event_type: str, probabilities: Dict[str, int], sentiment: str
    ) -> List[Dict[str, Any]]:
        """根据事件类型构建情景详情"""

        # 情景模板库
        scenario_templates = {
            "product_issue": {
                "平稳过渡": {
                    "description": "产品问题得到妥善解决，用户满意度逐步恢复，舆情自然消退",
                    "key_factors": ["快速响应", "有效修复", "用户沟通", "补偿到位"],
                    "risk_level": "low"
                },
                "品牌修复": {
                    "description": "通过积极公关和产品改进，品牌形象逐步修复，用户信心回升",
                    "key_factors": ["公关策略", "产品迭代", "用户运营", "口碑管理"],
                    "risk_level": "medium"
                },
                "口碑恶化": {
                    "description": "问题持续发酵，负面口碑扩散，用户流失加剧",
                    "key_factors": ["处理不当", "竞品攻击", "媒体跟进", "用户愤怒"],
                    "risk_level": "high"
                },
                "竞品借势": {
                    "description": "竞争对手借机营销，抢占市场份额，形成行业格局变化",
                    "key_factors": ["竞品动作", "市场反应", "用户迁移", "行业关注"],
                    "risk_level": "medium"
                },
                "行业反思": {
                    "description": "事件引发行业对产品标准和服务规范的反思和改进",
                    "key_factors": ["行业关注", "标准讨论", "监管关注", "标杆效应"],
                    "risk_level": "low"
                }
            },
            "company_crisis": {
                "平稳过渡": {
                    "description": "公司通过有效措施稳定局面，逐步恢复正常运营",
                    "key_factors": ["资金注入", "战略调整", "员工安抚", "市场信心"],
                    "risk_level": "low"
                },
                "危机深化": {
                    "description": "危机持续恶化，业务收缩，人才流失，市场地位下降",
                    "key_factors": ["资金链断裂", "核心人员离职", "客户流失", "信用危机"],
                    "risk_level": "high"
                },
                "重组转型": {
                    "description": "通过重组、并购或业务转型，公司获得新生",
                    "key_factors": ["战略重组", "业务调整", "新团队", "市场机会"],
                    "risk_level": "medium"
                },
                "行业震荡": {
                    "description": "公司危机引发行业连锁反应，影响上下游企业和市场信心",
                    "key_factors": ["供应链影响", "行业信心", "投资者担忧", "监管关注"],
                    "risk_level": "high"
                },
                "监管介入": {
                    "description": "监管部门介入调查，推动行业规范和制度完善",
                    "key_factors": ["监管调查", "合规要求", "行业整顿", "制度完善"],
                    "risk_level": "medium"
                }
            },
            "public_safety": {
                "平稳过渡": {
                    "description": "事故得到妥善处理，安全措施落实，公众担忧逐步消除",
                    "key_factors": ["事故控制", "救援到位", "信息公开", "善后处理"],
                    "risk_level": "low"
                },
                "调查深入": {
                    "description": "调查持续深入，更多细节曝光，责任追究逐步明确",
                    "key_factors": ["调查进展", "证据收集", "责任认定", "舆论关注"],
                    "risk_level": "medium"
                },
                "责任追究": {
                    "description": "相关责任人被追责，企业面临处罚和赔偿",
                    "key_factors": ["责任认定", "法律程序", "行政处罚", "民事赔偿"],
                    "risk_level": "high"
                },
                "制度完善": {
                    "description": "事件推动相关安全制度和监管机制的完善",
                    "key_factors": ["制度反思", "标准提升", "监管加强", "行业自律"],
                    "risk_level": "low"
                },
                "同类排查": {
                    "description": "引发同类场所或行业的全面安全排查和整改",
                    "key_factors": ["全面排查", "隐患整改", "行业整顿", "预防机制"],
                    "risk_level": "medium"
                }
            },
            "general": {
                "平稳过渡": {
                    "description": "热度逐渐下降，舆情平稳消退，公众注意力转移到其他事件",
                    "key_factors": ["新热点出现", "及时回应", "无新争议", "自然衰减"],
                    "risk_level": "low"
                },
                "持续发酵": {
                    "description": "话题保持热度，讨论持续进行，关注度维持在较高水平",
                    "key_factors": ["话题价值", "多方参与", "持续爆料", "媒体跟进"],
                    "risk_level": "medium"
                },
                "二次爆发": {
                    "description": "出现新证据或关键人物发声，引发新一轮讨论高潮",
                    "key_factors": ["新证据", "关键发声", "剧情反转", "情绪激化"],
                    "risk_level": "high"
                },
                "官方介入": {
                    "description": "官方机构或权威媒体介入，推动事件解决或澄清",
                    "key_factors": ["官方关注", "权威发声", "政策信号", "舆论引导"],
                    "risk_level": "medium"
                },
                "连锁反应": {
                    "description": "事件引发相关领域或类似事件的连锁反应和讨论",
                    "key_factors": ["关联事件", "行业影响", "模式讨论", "深层反思"],
                    "risk_level": "medium"
                }
            }
        }

        templates = scenario_templates.get(event_type, scenario_templates["general"])

        scenarios = []
        for name, prob in probabilities.items():
            template = templates.get(name, templates.get("平稳过渡"))
            scenarios.append({
                "name": name,
                "description": template["description"],
                "probability": prob,
                "key_factors": template["key_factors"],
                "timeline": self._generate_timeline_by_risk(template["risk_level"]),
                "risk_level": template["risk_level"]
            })

        # 按概率排序
        scenarios.sort(key=lambda x: x["probability"], reverse=True)
        return scenarios

    def _generate_timeline_by_risk(self, risk_level: str) -> str:
        """根据风险等级生成时间线描述"""
        timelines = {
            "low": ["3-5天内热度消退", "1周内基本平息", "短期影响有限"],
            "medium": ["持续1-2周", "7-10天热度维持", "中期影响需关注"],
            "high": ["持续2-4周", "14-21天发酵期", "长期影响深远"]
        }
        import random
        return random.choice(timelines.get(risk_level, timelines["medium"]))

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

    def _generate_conclusion(self, scenarios: List[Dict], warnings: List[Dict], event_summary: str = "") -> str:
        """生成预测结论 - 使用LLM润色"""

        # 准备情景数据
        sorted_scenarios = sorted(scenarios, key=lambda x: x.get("probability", 0), reverse=True)
        top = sorted_scenarios[0] if sorted_scenarios else {}
        second = sorted_scenarios[1] if len(sorted_scenarios) > 1 else None

        # 统计风险
        risk_count = {"high": 0, "medium": 0, "low": 0}
        for s in scenarios:
            r = s.get("risk_level", "medium")
            risk_count[r] = risk_count.get(r, 0) + 1

        # 准备预警信息
        warning_days = [w.get('day', 0) for w in warnings if w.get('day', 0) > 0]

        # 构建提示词
        prompt = f"""你是一位资深的舆情分析专家。请根据以下预测数据，撰写一段自然、专业、有洞察力的预测结论（100-150字）。

事件背景：{event_summary[:200] if event_summary else "某舆情事件"}

情景概率分布：
{json.dumps([{
    'name': s.get('name', ''),
    'probability': s.get('probability', 0),
    'risk_level': s.get('risk_level', 'medium'),
    'description': s.get('description', '')[:80]
} for s in sorted_scenarios[:3]], ensure_ascii=False, indent=2)}

主要风险情景数量：高风险{risk_count.get('high', 0)}个，中风险{risk_count.get('medium', 0)}个，低风险{risk_count.get('low', 0)}个

关键预警节点：{warning_days if warning_days else '暂无'}

撰写要求：
1. 语言自然流畅，避免生硬的数据堆砌
2. 突出最可能的情景及其概率
3. 提及风险分布和需要关注的要点
4. 给出简洁的行动建议
5. 控制在100-150字以内

请直接输出结论文字，不要有任何格式标记。"""

        try:
            response = self.llm_client.chat(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=300,
            )
            content = response if isinstance(response, str) else response.get("content", "")
            conclusion = content.strip()
            if conclusion:
                return conclusion
        except Exception as e:
            print(f"[LLM] 生成结论失败，使用模板生成: {e}")

        # LLM失败时的降级方案
        return self._generate_fallback_conclusion(scenarios, warnings)

    def _generate_fallback_conclusion(self, scenarios: List[Dict], warnings: List[Dict]) -> str:
        """生成结论的降级方案"""
        sorted_scenarios = sorted(scenarios, key=lambda x: x.get("probability", 0), reverse=True)
        top = sorted_scenarios[0] if sorted_scenarios else {}

        risk_count = {"high": 0, "medium": 0, "low": 0}
        for s in scenarios:
            r = s.get("risk_level", "medium")
            risk_count[r] = risk_count.get(r, 0) + 1

        high_risk = risk_count.get("high", 0)

        conclusion = f"基于预测分析，「{top.get('name', '未知')}」是最可能出现的情景，概率为{top.get('probability', 0)}%。"

        if high_risk >= 2:
            conclusion += "当前存在多个高风险情景，建议密切关注舆情动态，提前制定应对预案。"
        elif high_risk == 1:
            conclusion += "存在一定风险因素，建议持续关注发展趋势，适时采取引导措施。"
        else:
            conclusion += "整体风险可控，建议保持监测，及时掌握舆论走向。"

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

        # 构建详细的预测上下文
        scenarios = prediction_data.get("scenarios", [])
        warnings = prediction_data.get("warnings", [])
        timeline = prediction_data.get("timeline", [])

        # 格式化情景信息
        scenario_text = ""
        for i, s in enumerate(scenarios[:3], 1):
            scenario_text += f"\n{i}. {s.get('name', '')} (概率{s.get('probability', 0)}%, 风险等级:{s.get('risk_level', 'medium')})"
            scenario_text += f"\n   描述：{s.get('description', '')[:100]}"
            scenario_text += f"\n   关键因素：{', '.join(s.get('key_factors', [])[:2])}"

        # 格式化预警信息
        warning_text = ""
        if warnings:
            for w in warnings[:3]:
                warning_text += f"\n- 第{w.get('day', 0)}天: {w.get('description', '')} (等级:{w.get('level', 'medium')})"
        else:
            warning_text = "\n暂无重大风险预警"

        # 格式化时间线关键节点
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

        try:
            response = self.llm_client.chat(
                messages=[{"role": "user", "content": context}],
                temperature=0.7,
                max_tokens=600,
            )

            answer = response if isinstance(response, str) else response.get("content", "")
            return answer.strip() if answer else "抱歉，我暂时无法回答这个问题。"

        except Exception as e:
            return f"抱歉，处理您的问题时出现了错误。基于当前数据，建议您关注最可能的情景：{scenarios[0].get('name', '') if scenarios else '舆情发展'}。"

    def generate_recommended_questions(
        self,
        event_summary: str,
        scenarios: List[Dict[str, Any]],
        sentiment_distribution: List[Dict[str, Any]],
    ) -> List[str]:
        """
        基于预测情景生成推荐问题

        Args:
            event_summary: 事件摘要
            scenarios: 预测情景列表
            sentiment_distribution: 情绪分布

        Returns:
            推荐问题列表（3个）
        """
        # 提取情景信息
        scenario_info = []
        for i, s in enumerate(scenarios[:3]):
            scenario_info.append(
                f"{i+1}. {s.get('name', '')} (概率{s.get('probability', 0)}%, 风险{s.get('risk_level', 'medium')})"
            )

        # 提取情绪信息
        sentiment_info = []
        for s in sentiment_distribution:
            sentiment_info.append(f"{s.get('label', '')}: {s.get('percentage', 0)}%")

        prompt = f"""你是一个舆情分析专家。基于以下舆情预测数据，生成3个最有价值的推荐问题，帮助用户深入理解当前舆情态势。

事件摘要：{event_summary}

预测情景（按概率排序）：
{' '.join(scenario_info)}

情绪分布：
{' '.join(sentiment_info)}

请生成3个推荐问题，要求：
1. 问题要具体、有针对性，结合上述情景和情绪数据
2. 问题应该能帮助用户做出决策或采取行动
3. 问题类型可以包括：预防措施、应对策略、重点关注、风险评估等
4. 每个问题控制在30字以内
5. 返回JSON格式：{{"questions": ["问题1", "问题2", "问题3"]}}

请直接返回JSON，不要包含其他解释。"""

        try:
            response = self.llm_client.chat(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=300,
            )

            content = response if isinstance(response, str) else response.get("content", "")

            # 尝试解析JSON
            import re
            json_match = re.search(r'\{[^}]*"questions"[^}]*\}', content, re.DOTALL)
            if json_match:
                result = json.loads(json_match.group())
                questions = result.get("questions", [])
                if len(questions) >= 3:
                    return questions[:3]

            # 如果解析失败，使用备用方案
            return self._generate_default_questions(scenarios, sentiment_distribution)

        except Exception as e:
            return self._generate_default_questions(scenarios, sentiment_distribution)

    def _generate_default_questions(
        self, scenarios: List[Dict[str, Any]], sentiment_distribution: List[Dict[str, Any]]
    ) -> List[str]:
        """生成默认推荐问题"""
        questions = []

        if scenarios:
            top_scenario = scenarios[0]
            questions.append(
                f"针对\"{top_scenario.get('name', '最可能情景')}\"这一最可能发生的情景，应该采取哪些预防措施？"
            )

        high_risk = next((s for s in scenarios if s.get("risk_level") == "high"), None)
        if high_risk:
            questions.append(
                f"如果\"{high_risk.get('name', '高风险情景')}\"发生，最佳的应对策略是什么？"
            )

        negative = next((s for s in sentiment_distribution if s.get("type") == "negative"), None)
        if negative and negative.get("percentage", 0) > 30:
            questions.append(
                f"当前负面情绪占比{negative.get('percentage')}%如何有效引导舆论走向中性或正面？"
            )
        else:
            questions.append("基于当前舆情态势，未来需要重点关注哪些方面？")

        return questions[:3]

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
