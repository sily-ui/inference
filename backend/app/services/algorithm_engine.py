"""
舆情预测算法引擎

包含:
1. SIR舆情传播模型 - 基于传染病模型预测舆情热度演变
2. 贝叶斯情景预测器 - 基于贝叶斯推理预测多情景概率

特点: 纯CPU计算，无需GPU，响应速度快
"""

import math
import random
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class SIRParameters:
    beta: float = 0.4
    gamma: float = 0.15
    mu: float = 1.0
    initial_I: float = 0.1
    initial_R: float = 0.0


class SIROpinionModel:
    """
    SIR舆情传播模型
    
    基于传染病模型改进的舆情传播预测:
    - S (Susceptible): 易感人群 - 潜在关注者
    - I (Infected): 感染人群 - 活跃讨论者
    - R (Recovered): 康复人群 - 失去兴趣者
    
    核心方程:
    dS/dt = -β * μ * S * I
    dI/dt = β * μ * S * I - γ * I
    dR/dt = γ * I
    """
    
    EVENT_TEMPLATES = {
        'rising': [
            "事件持续发酵，关注度快速上升",
            "舆论热度攀升，多平台讨论增加",
            "话题传播加速，引发广泛关注",
            "舆情进入爆发期，讨论量激增",
        ],
        'peak': [
            "舆情达到峰值，各方高度关注",
            "讨论热度达到最高点",
            "舆论关注度达到顶峰",
            "事件影响力最大化",
        ],
        'declining': [
            "热度开始回落，讨论逐渐减少",
            "舆论进入衰退期",
            "公众注意力开始转移",
            "话题热度逐步下降",
        ],
        'stable': [
            "舆情趋于平稳，进入常态化",
            "讨论热度保持稳定",
            "舆论态势相对平稳",
            "关注度维持在中等水平",
        ],
        'rebound': [
            "出现新的讨论热点，舆情反弹",
            "新因素介入，热度回升",
            "事件出现新进展，关注度上升",
        ],
        'low': [
            "热度持续走低，接近尾声",
            "公众关注度明显下降",
            "舆情影响逐渐消退",
        ]
    }
    
    def __init__(self, params: Optional[SIRParameters] = None):
        self.params = params or SIRParameters()
    
    def predict_timeline(
        self, 
        event_summary: str,
        current_sentiment: str = "中性",
        days: int = 7,
        event_features: Optional[Dict[str, float]] = None
    ) -> List[Dict[str, Any]]:
        """
        预测舆情时间轴
        
        Args:
            event_summary: 事件摘要（用于事件描述生成）
            current_sentiment: 当前情绪状态
            days: 预测天数
            event_features: 事件特征（影响模型参数）
        
        Returns:
            时间轴预测结果列表
        """
        params = self._adjust_parameters(event_features, current_sentiment)
        
        S = 1.0 - params.initial_I - params.initial_R
        I = params.initial_I
        R = params.initial_R
        
        timeline = []
        prev_heat = 0
        trend = 'rising'
        
        sentiment_base = self._get_sentiment_base(current_sentiment)
        
        for day in range(1, days + 1):
            dS = -params.beta * params.mu * S * I
            dI = params.beta * params.mu * S * I - params.gamma * I
            dR = params.gamma * I
            
            S = max(0, S + dS)
            I = max(0, min(1, I + dI))
            R = max(0, min(1, R + dR))
            
            total = S + I + R
            if total > 0:
                S, I, R = S/total, I/total, R/total
            
            heat = min(100, I * 150)
            heat = self._add_noise(heat, 5)
            
            trend = self._determine_trend(heat, prev_heat, day, days)
            prev_heat = heat
            
            sentiment = self._calculate_sentiment(I, R, sentiment_base, day)
            risk = self._calculate_risk(heat, I, trend)
            
            event = self._generate_event(day, heat, trend, event_summary)
            
            timeline.append({
                'day': day,
                'event': event,
                'heat': round(heat, 1),
                'sentiment': round(sentiment, 2),
                'risk': risk,
                'description': f"第{day}天预测 - {trend}阶段"
            })
        
        return timeline
    
    def _adjust_parameters(
        self, 
        event_features: Optional[Dict[str, float]], 
        sentiment: str
    ) -> SIRParameters:
        """根据事件特征调整模型参数"""
        params = SIRParameters(
            beta=self.params.beta,
            gamma=self.params.gamma,
            mu=self.params.mu,
            initial_I=self.params.initial_I,
            initial_R=self.params.initial_R
        )
        
        if event_features:
            if event_features.get('sensitivity', 0) > 0.7:
                params.beta *= 1.3
                params.mu *= 1.2
            
            if event_features.get('media_coverage', 0) > 0.6:
                params.mu *= 1.3
            
            if event_features.get('official_response', 0) > 0.5:
                params.gamma *= 1.5
        
        sentiment_impact = {
            '负面': (1.2, 0.8, 0.15),
            '正面': (0.8, 1.2, 0.08),
            '中性': (1.0, 1.0, 0.1),
            '复杂': (1.1, 0.9, 0.12),
        }
        
        beta_adj, gamma_adj, i_adj = sentiment_impact.get(sentiment, (1.0, 1.0, 0.1))
        params.beta *= beta_adj
        params.gamma *= gamma_adj
        params.initial_I = i_adj
        
        params.beta = min(0.8, max(0.1, params.beta))
        params.gamma = min(0.5, max(0.05, params.gamma))
        
        return params
    
    def _get_sentiment_base(self, sentiment: str) -> float:
        """获取情绪基准值"""
        mapping = {
            '正面': 0.7,
            '负面': 0.3,
            '中性': 0.5,
            '复杂': 0.4,
        }
        return mapping.get(sentiment, 0.5)
    
    def _determine_trend(self, heat: float, prev_heat: float, day: int, total_days: int) -> str:
        """判断当前趋势阶段"""
        if day <= 2:
            return 'rising' if heat > 40 else 'stable'
        
        if day >= total_days - 1:
            return 'low' if heat < 30 else 'declining'
        
        heat_change = heat - prev_heat
        
        if heat_change > 10:
            return 'rebound'
        elif heat_change > 3:
            return 'rising'
        elif heat_change < -10:
            return 'declining'
        elif heat_change < -3:
            return 'declining'
        elif heat > 70:
            return 'peak'
        else:
            return 'stable'
    
    def _calculate_sentiment(self, I: float, R: float, base: float, day: int) -> float:
        """计算情绪值"""
        recovery_effect = R * 0.2
        infection_effect = I * 0.1
        
        sentiment = base + recovery_effect - infection_effect
        
        day_factor = math.sin(day * 0.5) * 0.05
        sentiment += day_factor
        
        return max(0.1, min(0.9, sentiment))
    
    def _calculate_risk(self, heat: float, I: float, trend: str) -> str:
        """计算风险等级"""
        if heat > 75 or (trend == 'rising' and heat > 60):
            return 'high'
        elif heat > 45 or trend in ['peak', 'rebound']:
            return 'medium'
        else:
            return 'low'
    
    def _generate_event(self, day: int, heat: float, trend: str, event_summary: str) -> str:
        """生成事件描述"""
        templates = self.EVENT_TEMPLATES.get(trend, self.EVENT_TEMPLATES['stable'])
        template = random.choice(templates)
        
        if day == 1:
            return f"事件初期发展：{template}"
        elif trend == 'peak':
            return template
        elif trend == 'rebound':
            return f"舆情出现转折：{template}"
        else:
            return template
    
    def _add_noise(self, value: float, noise_level: float) -> float:
        """添加随机噪声"""
        noise = random.uniform(-noise_level, noise_level)
        return max(0, min(100, value + noise))


class BayesianScenarioPredictor:
    """
    贝叶斯情景预测器
    
    基于贝叶斯推理预测多种舆情发展情景的概率分布
    
    P(Scenario|Evidence) = P(Evidence|Scenario) * P(Scenario) / P(Evidence)
    """
    
    SCENARIO_TEMPLATES = {
        '平稳过渡': {
            'base_prob': 0.35,
            'description': '热度逐渐下降，舆情平稳消退，公众注意力转移到其他事件',
            'factors': ['新热点出现', '官方及时回应', '无新争议点', '舆论疲劳'],
            'risk_level': 'low',
            'timeline': '3-5天内热度明显下降',
            'likelihood_weights': {
                'low_sensitivity': 1.5,
                'has_official_response': 1.3,
                'low_media_coverage': 1.2,
                'short_duration': 1.2,
            }
        },
        '二次爆发': {
            'base_prob': 0.25,
            'description': '出现新证据或意见领袖发声，引发第二轮讨论高潮',
            'factors': ['新证据曝光', 'KOL发声', '官方回应不当', '关联事件'],
            'risk_level': 'high',
            'timeline': '第4-7天可能出现',
            'likelihood_weights': {
                'high_sensitivity': 1.6,
                'no_official_response': 1.4,
                'high_media_coverage': 1.3,
                'has_controversy': 1.5,
            }
        },
        '持续发酵': {
            'base_prob': 0.20,
            'description': '保持在热搜榜单，舆情进入常态化讨论',
            'factors': ['话题持续争议', '多方持续发声', '事件复杂度高', '社会关注度高'],
            'risk_level': 'medium',
            'timeline': '持续1-2周',
            'likelihood_weights': {
                'high_complexity': 1.4,
                'multiple_parties': 1.3,
                'social_impact': 1.4,
            }
        },
        '官方介入': {
            'base_prob': 0.15,
            'description': '监管机构或官方媒体正式回应，舆论走向可控',
            'factors': ['官方声明', '政策出台', '舆论管控', '权威解读'],
            'risk_level': 'low',
            'timeline': '1周内',
            'likelihood_weights': {
                'government_related': 1.6,
                'policy_impact': 1.4,
                'mainstream_attention': 1.3,
            }
        },
        '温和争议': {
            'base_prob': 0.05,
            'description': '争议保持在温和范围内，不会出现剧烈波动',
            'factors': ['理性讨论为主', '信息透明度高', '各方态度温和'],
            'risk_level': 'low',
            'timeline': '持续平稳',
            'likelihood_weights': {
                'transparent_info': 1.5,
                'rational_discussion': 1.4,
            }
        }
    }
    
    FEATURE_MAPPING = {
        'sensitivity': {
            'high': 'high_sensitivity',
            'medium': None,
            'low': 'low_sensitivity',
        },
        'media_coverage': {
            'high': 'high_media_coverage',
            'medium': None,
            'low': 'low_media_coverage',
        },
        'official_response': {
            'yes': 'has_official_response',
            'no': 'no_official_response',
        },
        'controversy': {
            'high': 'has_controversy',
            'low': None,
        },
        'complexity': {
            'high': 'high_complexity',
            'low': None,
        },
        'duration': {
            'short': 'short_duration',
            'long': None,
        }
    }
    
    def __init__(self):
        self.scenarios = self.SCENARIO_TEMPLATES.copy()
    
    def predict_scenarios(
        self,
        event_summary: str,
        current_sentiment: str = "中性",
        event_features: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        预测多情景概率分布
        
        Args:
            event_summary: 事件摘要
            current_sentiment: 当前情绪
            event_features: 事件特征字典
        
        Returns:
            情景概率列表
        """
        features = event_features or self._extract_features(event_summary, current_sentiment)
        
        likelihoods = {}
        for scenario_name, scenario_data in self.scenarios.items():
            likelihood = self._calculate_likelihood(scenario_data, features)
            likelihoods[scenario_name] = likelihood
        
        posterior = self._bayesian_update(likelihoods)
        
        results = []
        for scenario_name, prob in posterior.items():
            scenario_data = self.scenarios[scenario_name]
            results.append({
                'name': scenario_name,
                'description': scenario_data['description'],
                'probability': round(prob * 100, 1),
                'key_factors': scenario_data['factors'][:3],
                'timeline': scenario_data['timeline'],
                'risk_level': scenario_data['risk_level']
            })
        
        results.sort(key=lambda x: x['probability'], reverse=True)
        
        return results
    
    def _extract_features(self, event_summary: str, sentiment: str) -> Dict[str, Any]:
        """从事件摘要中提取特征"""
        features = {
            'sensitivity': 'medium',
            'media_coverage': 'medium',
            'official_response': 'no',
            'controversy': 'low',
            'complexity': 'medium',
        }
        
        high_sensitivity_keywords = ['争议', '冲突', '抗议', '丑闻', '腐败', '违法', '死亡', '事故']
        media_keywords = ['热搜', '头条', '爆', '刷屏', '热议']
        official_keywords = ['官方', '政府', '声明', '回应', '通报']
        controversy_keywords = ['对立', '分歧', '质疑', '批评', '不满']
        
        summary_lower = event_summary.lower()
        
        if any(kw in event_summary for kw in high_sensitivity_keywords):
            features['sensitivity'] = 'high'
        elif sentiment == '负面':
            features['sensitivity'] = 'high'
        
        if any(kw in event_summary for kw in media_keywords):
            features['media_coverage'] = 'high'
        
        if any(kw in event_summary for kw in official_keywords):
            features['official_response'] = 'yes'
        
        if any(kw in event_summary for kw in controversy_keywords):
            features['controversy'] = 'high'
        
        if len(event_summary) > 200 or '复杂' in event_summary:
            features['complexity'] = 'high'
        
        return features
    
    def _calculate_likelihood(
        self, 
        scenario_data: Dict, 
        features: Dict[str, Any]
    ) -> float:
        """计算似然概率 P(Evidence|Scenario)"""
        weights = scenario_data.get('likelihood_weights', {})
        
        likelihood = 1.0
        
        for feature_key, feature_value in features.items():
            if feature_key in self.FEATURE_MAPPING:
                mapping = self.FEATURE_MAPPING[feature_key]
                weight_key = mapping.get(feature_value)
                
                if weight_key and weight_key in weights:
                    likelihood *= weights[weight_key]
        
        return likelihood
    
    def _bayesian_update(self, likelihoods: Dict[str, float]) -> Dict[str, float]:
        """贝叶斯更新计算后验概率"""
        priors = {name: data['base_prob'] for name, data in self.scenarios.items()}
        
        unnormalized = {}
        for name in self.scenarios:
            unnormalized[name] = likelihoods[name] * priors[name]
        
        total = sum(unnormalized.values())
        
        if total == 0:
            return priors
        
        posterior = {name: prob / total for name, prob in unnormalized.items()}
        
        return posterior


class AlgorithmEngine:
    """
    算法引擎 - 统一接口
    
    整合SIR模型和贝叶斯预测器，提供统一的预测接口
    """
    
    def __init__(self):
        self.sir_model = SIROpinionModel()
        self.scenario_predictor = BayesianScenarioPredictor()
    
    def generate_timeline(
        self,
        event_summary: str,
        current_sentiment: str = "中性",
        days: int = 7,
        event_features: Optional[Dict[str, float]] = None
    ) -> List[Dict[str, Any]]:
        """
        生成时间轴预测
        
        使用SIR舆情传播模型
        """
        return self.sir_model.predict_timeline(
            event_summary=event_summary,
            current_sentiment=current_sentiment,
            days=days,
            event_features=event_features
        )
    
    def generate_scenarios(
        self,
        event_summary: str,
        current_sentiment: str = "中性",
        event_features: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        生成情景概率预测
        
        使用贝叶斯情景预测器
        """
        return self.scenario_predictor.predict_scenarios(
            event_summary=event_summary,
            current_sentiment=current_sentiment,
            event_features=event_features
        )
    
    def predict(
        self,
        event_summary: str,
        current_sentiment: str = "中性",
        days: int = 7
    ) -> Dict[str, Any]:
        """
        完整预测 - 返回时间轴和情景预测
        """
        timeline = self.generate_timeline(event_summary, current_sentiment, days)
        scenarios = self.generate_scenarios(event_summary, current_sentiment)
        
        return {
            'timeline': timeline,
            'scenarios': scenarios,
            'engine': 'algorithm',
            'generated_at': datetime.now().isoformat()
        }
