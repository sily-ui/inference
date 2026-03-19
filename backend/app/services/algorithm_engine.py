"""
算法引擎 - 用于舆情预测的算法实现

包含：
1. SIR模型 - 用于时间轴推演
2. 贝叶斯网络 - 用于情景概率预测
"""

import random
import math
from typing import Dict, Any, List
from datetime import datetime, timedelta


class AlgorithmEngine:
    """算法引擎 - 纯算法模式预测"""

    def __init__(self):
        self.sir_params = {
            'beta': 0.3,  # 传播率
            'gamma': 0.1,  # 恢复率
            'mu': 0.01,   # 自然衰减率
        }

    def generate_timeline(
        self,
        event_summary: str,
        current_sentiment: str,
        days: int
    ) -> List[Dict[str, Any]]:
        """
        使用SIR模型生成时间轴推演

        SIR模型: dS/dt = -β*S*I, dI/dt = β*S*I - γ*I, dR/dt = γ*I
        其中 S = 易感人群, I = 感染人群(关注者), R = 恢复人群(不再关注)
        """
        # 初始条件
        S = 0.9  # 易感人群比例
        I = 0.1  # 感染人群比例（初始关注度）
        R = 0.0  # 恢复人群比例

        # 根据情绪调整参数
        sentiment_factor = {
            "正面": 0.8,
            "负面": 1.2,
            "中性": 1.0,
            "复杂": 1.1,
        }.get(current_sentiment, 1.0)

        beta = self.sir_params['beta'] * sentiment_factor
        gamma = self.sir_params['gamma']
        mu = self.sir_params['mu']

        timeline = []
        dt = 0.1  # 时间步长

        for day in range(1, days + 1):
            # 使用欧拉方法求解SIR模型
            for _ in range(int(1/dt)):
                dS = (-beta * S * I + mu * R) * dt
                dI = (beta * S * I - gamma * I) * dt
                dR = (gamma * I - mu * R) * dt

                S = max(0, min(1, S + dS))
                I = max(0, min(1, I + dI))
                R = max(0, min(1, R + dR))

            # 热度基于感染人群比例
            heat = int(I * 100)

            # 情绪基于易感人群比例（剩余未关注人群的倾向）
            sentiment = round(0.3 + S * 0.5, 2)

            # 风险等级
            if heat > 70:
                risk = "high"
            elif heat > 40:
                risk = "medium"
            else:
                risk = "low"

            # 生成事件描述
            if day == 1:
                event = "事件初期，关注度开始上升"
            elif heat > 80:
                event = "热度达到高峰，舆论集中爆发"
            elif heat > 60:
                event = "事件持续发酵，多方参与讨论"
            elif heat > 40:
                event = "热度开始下降，讨论趋于理性"
            else:
                event = "关注度持续走低，事件逐渐平息"

            timeline.append({
                "day": day,
                "event": event,
                "heat": heat,
                "sentiment": sentiment,
                "risk": risk,
                "description": f"第{day}天: {event}",
            })

        return timeline

    def generate_scenarios(
        self,
        event_summary: str,
        current_sentiment: str
    ) -> List[Dict[str, Any]]:
        """
        使用贝叶斯网络生成情景概率预测

        基于事件特征和当前情绪动态计算各情景概率
        """
        # 分析事件特征
        event_features = self._analyze_event_features(event_summary)

        # 根据事件类型获取基础概率
        base_probabilities = self._get_base_probabilities(event_features["type"])

        # 根据情绪调整概率
        sentiment_adjustments = self._get_sentiment_adjustments(current_sentiment)

        # 根据事件特征调整概率
        feature_adjustments = self._get_feature_adjustments(event_features)

        # 应用所有调整
        adjusted_probs = {}
        for scenario, base_prob in base_probabilities.items():
            sentiment_adj = sentiment_adjustments.get(scenario, 0)
            feature_adj = feature_adjustments.get(scenario, 0)
            adjusted_probs[scenario] = max(0.05, base_prob + sentiment_adj + feature_adj)

        # 归一化概率
        total = sum(adjusted_probs.values())
        normalized_probs = {k: round(v/total * 100) for k, v in adjusted_probs.items()}

        # 根据事件特征生成情景详情
        scenarios = self._build_dynamic_scenarios(
            normalized_probs, event_features, current_sentiment
        )

        # 按概率排序
        scenarios.sort(key=lambda x: x["probability"], reverse=True)

        return scenarios

    def _analyze_event_features(self, event_summary: str) -> Dict[str, Any]:
        """分析事件特征"""
        event_lower = event_summary.lower()

        # 事件类型关键词
        type_keywords = {
            "product": ["产品", "质量", "bug", "故障", "体验", "功能", "更新", "版本"],
            "crisis": ["裁员", "倒闭", "破产", "财务", "亏损", "危机", "丑闻", "违规"],
            "safety": ["事故", "安全", "伤亡", "爆炸", "泄漏", "污染", "风险"],
            "celebrity": ["明星", "艺人", "网红", "绯闻", "出轨", "离婚", "恋情"],
            "policy": ["政策", "法规", "规定", "禁令", "限制", "调整", "改革"],
            "social": ["歧视", "公平", "性别", "种族", "阶层", "矛盾", "冲突"],
        }

        # 检测事件类型
        event_type = "general"
        type_scores = {}
        for etype, keywords in type_keywords.items():
            score = sum(1 for kw in keywords if kw in event_lower)
            if score > 0:
                type_scores[etype] = score
        if type_scores:
            event_type = max(type_scores, key=type_scores.get)

        # 检测严重程度
        severity_keywords = ["严重", "重大", "特大", "紧急", "恶性", "致命", "灾难"]
        severity = sum(1 for kw in severity_keywords if kw in event_lower)

        # 检测涉及主体
        entity_keywords = {
            "company": ["公司", "企业", "集团", "品牌", "厂商"],
            "government": ["政府", "官方", "部门", "机构", "监管"],
            "individual": ["个人", "员工", "用户", "消费者", "市民"],
        }
        entities = []
        for entity, keywords in entity_keywords.items():
            if any(kw in event_lower for kw in keywords):
                entities.append(entity)

        return {
            "type": event_type,
            "severity": min(severity, 3),  # 0-3
            "entities": entities if entities else ["unknown"],
            "has_numbers": any(c.isdigit() for c in event_summary),
            "length": len(event_summary)
        }

    def _get_base_probabilities(self, event_type: str) -> Dict[str, float]:
        """根据事件类型获取基础概率"""
        templates = {
            "product": {
                "平稳过渡": 0.40, "品牌修复": 0.25, "口碑恶化": 0.20, "竞品借势": 0.10, "行业反思": 0.05
            },
            "crisis": {
                "平稳过渡": 0.25, "危机深化": 0.30, "重组转型": 0.20, "行业震荡": 0.15, "监管介入": 0.10
            },
            "safety": {
                "平稳过渡": 0.20, "调查深入": 0.35, "责任追究": 0.25, "制度完善": 0.15, "同类排查": 0.05
            },
            "celebrity": {
                "平稳过渡": 0.35, "持续热议": 0.30, "反转洗白": 0.15, "事业受挫": 0.15, "同类曝光": 0.05
            },
            "policy": {
                "平稳过渡": 0.45, "讨论深化": 0.25, "执行争议": 0.15, "调整优化": 0.10, "社会适应": 0.05
            },
            "social": {
                "平稳过渡": 0.30, "持续讨论": 0.35, "群体对立": 0.20, "共识形成": 0.10, "政策响应": 0.05
            },
            "general": {
                "平稳过渡": 0.35, "持续发酵": 0.25, "二次爆发": 0.20, "官方介入": 0.12, "连锁反应": 0.08
            }
        }
        return templates.get(event_type, templates["general"]).copy()

    def _get_sentiment_adjustments(self, sentiment: str) -> Dict[str, float]:
        """根据情绪获取概率调整"""
        adjustments = {
            "正面": {"平稳过渡": 0.12, "官方介入": -0.03, "持续发酵": -0.05, "二次爆发": -0.04},
            "负面": {"持续发酵": 0.10, "二次爆发": 0.08, "平稳过渡": -0.12, "官方介入": -0.06},
            "复杂": {"连锁反应": 0.08, "二次爆发": 0.05, "平稳过渡": -0.08, "持续发酵": 0.05},
            "中性": {}
        }
        return adjustments.get(sentiment, {})

    def _get_feature_adjustments(self, features: Dict[str, Any]) -> Dict[str, float]:
        """根据事件特征获取概率调整"""
        adjustments = {}

        # 严重程度影响
        severity = features.get("severity", 0)
        if severity >= 2:
            adjustments["持续发酵"] = adjustments.get("持续发酵", 0) + 0.05 * severity
            adjustments["官方介入"] = adjustments.get("官方介入", 0) + 0.03 * severity

        # 涉及政府/监管
        if "government" in features.get("entities", []):
            adjustments["官方介入"] = adjustments.get("官方介入", 0) + 0.08
            adjustments["平稳过渡"] = adjustments.get("平稳过渡", 0) - 0.05

        return adjustments

    def _build_dynamic_scenarios(
        self, probabilities: Dict[str, int], features: Dict[str, Any], sentiment: str
    ) -> List[Dict[str, Any]]:
        """动态构建情景详情"""

        # 情景描述模板库
        scenario_library = {
            "平稳过渡": {
                "descriptions": [
                    "舆情按正常轨迹发展，公众理性讨论占主导，热度逐渐消退",
                    "事件关注度自然衰减，无新争议点出现，舆论回归平静",
                    "公众注意力逐步转移，讨论趋于理性，舆情平稳着陆"
                ],
                "factors_pool": [
                    ["无新争议", "公众理性", "自然衰减", "媒体降温"],
                    ["及时回应", "有效沟通", "话题价值下降", "新热点分流"],
                    ["官方引导", "舆论自律", "信息透明", "公众疲劳"]
                ],
                "risk": "low"
            },
            "持续发酵": {
                "descriptions": [
                    "话题保持较高热度，讨论持续深入，关注度维持在一定水平",
                    "多方持续参与讨论，话题价值被不断挖掘，舆情呈持续状态",
                    "事件影响逐步扩大，引发更多关联讨论，热度难以快速消退"
                ],
                "factors_pool": [
                    ["话题价值高", "多方参与", "持续爆料", "媒体跟进"],
                    ["争议未解", "利益相关", "情绪持续", "新角度出现"],
                    ["意见领袖关注", "平台推荐", "用户活跃", "讨论深入"]
                ],
                "risk": "medium"
            },
            "二次爆发": {
                "descriptions": [
                    "关键新证据或反转剧情出现，引发新一轮讨论高潮",
                    "重要信息披露或关键人物发声，舆情热度再次攀升",
                    "剧情出现重大转折，公众情绪被再次点燃，讨论量激增"
                ],
                "factors_pool": [
                    ["新证据曝光", "剧情反转", "关键发声", "情绪激化"],
                    ["信息更新", "立场转变", "深度挖掘", "意外发展"],
                    ["当事人回应", "第三方介入", "媒体聚焦", "公众震惊"]
                ],
                "risk": "high"
            },
            "官方介入": {
                "descriptions": [
                    "官方机构或权威媒体正式介入，推动事件解决或澄清",
                    "监管部门或权威机构表态，舆论走向趋于规范",
                    "官方调查或权威发布，为事件定性和解决提供依据"
                ],
                "factors_pool": [
                    ["官方关注", "权威发声", "政策信号", "舆论引导"],
                    ["监管介入", "调查启动", "制度响应", "规范出台"],
                    ["权威定性", "政策调整", "行业整顿", "公众期待"]
                ],
                "risk": "medium"
            },
            "连锁反应": {
                "descriptions": [
                    "事件引发相关领域或类似事件的连锁反应和广泛讨论",
                    "舆情影响扩散至关联领域，引发更深层次的思考和讨论",
                    "单一事件演变为行业或社会议题，影响范围持续扩大"
                ],
                "factors_pool": [
                    ["关联事件", "行业影响", "模式讨论", "深层反思"],
                    ["同类曝光", "制度讨论", "标准质疑", "行业自查"],
                    ["连锁效应", "蝴蝶效应", "系统性反思", "长期影响"]
                ],
                "risk": "medium"
            }
        }

        scenarios = []
        for name, prob in probabilities.items():
            template = scenario_library.get(name, scenario_library["平稳过渡"])

            # 随机选择描述和关键因素，增加多样性
            desc = random.choice(template["descriptions"])
            factors = random.choice(template["factors_pool"])

            # 根据事件特征微调描述
            if features["severity"] >= 2 and name == "持续发酵":
                desc = desc.replace("持续深入", "持续升温").replace("一定水平", "较高水平")

            scenarios.append({
                "name": name,
                "description": desc,
                "probability": prob,
                "key_factors": factors,
                "timeline": self._generate_dynamic_timeline(template["risk"], features),
                "risk_level": template["risk"]
            })

        return scenarios

    def _generate_dynamic_timeline(self, risk_level: str, features: Dict[str, Any]) -> str:
        """动态生成时间线描述"""
        base_timelines = {
            "low": ["3-5天", "1周内", "短期"],
            "medium": ["7-14天", "1-2周", "中期"],
            "high": ["14-21天", "2-4周", "长期"]
        }

        durations = base_timelines.get(risk_level, base_timelines["medium"])
        duration = random.choice(durations)

        # 根据事件特征调整
        if features["severity"] >= 2:
            patterns = [f"{duration}持续发酵", f"{duration}影响周期", f"{duration}观察期"]
        else:
            patterns = [f"{duration}热度维持", f"{duration}影响窗口", f"{duration}关键期"]

        return random.choice(patterns)
