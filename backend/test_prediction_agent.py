"""
测试 Prediction Agent 的智能体思考-规划-执行能力
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.prediction_agent import PredictionAgent, PredictionLogger
import json

def test_prediction_agent():
    """测试预测Agent的完整流程"""
    
    print("=" * 60)
    print("Prediction Agent 测试")
    print("=" * 60)
    
    # 测试数据
    event_summary = """
    某科技公司发布新款智能手机，上市首日销量突破100万台。
    但随后有用户反馈产品存在发热问题和电池续航不足的情况，
    部分用户在社交媒体上表达不满，引发广泛关注和讨论。
    """
    
    current_sentiment = "复杂"
    time_range = 7
    
    simulation_data = {
        "all_actions": [
            {"round_num": 1, "action_type": "post", "sentiment": "negative"},
            {"round_num": 2, "action_type": "comment", "sentiment": "negative"},
            {"round_num": 3, "action_type": "share", "sentiment": "neutral"},
        ],
        "agent_count": 24
    }
    
    print(f"\n📝 事件摘要: {event_summary[:100]}...")
    print(f"🌡️ 当前情绪: {current_sentiment}")
    print(f"📅 预测天数: {time_range}")
    print(f"📊 模拟数据: {len(simulation_data['all_actions'])} 条动作, {simulation_data['agent_count']} 个Agent")
    
    # 创建Agent
    print("\n" + "-" * 60)
    print("🤖 创建 Prediction Agent...")
    print("-" * 60)
    
    agent = PredictionAgent(
        simulation_id="test_sim_001",
        event_summary=event_summary,
        current_sentiment=current_sentiment,
        time_range=time_range,
        simulation_data=simulation_data
    )
    
    # 定义进度回调
    def progress_callback(stage, progress, message):
        print(f"\r[{stage.upper():12}] {progress:3d}% - {message}", end="", flush=True)
    
    # 执行预测
    print("\n" + "-" * 60)
    print("🚀 开始执行预测...")
    print("-" * 60 + "\n")
    
    try:
        result = agent.predict(progress_callback=progress_callback)
        
        print("\n\n" + "=" * 60)
        print("✅ 预测完成!")
        print("=" * 60)
        
        # 输出结果摘要
        print(f"\n📋 预测ID: {result.get('prediction_id')}")
        print(f"🎯 置信度: {result.get('confidence', 0) * 100:.0f}%")
        
        # 规划结果
        plan = result.get('plan', {})
        if plan:
            print(f"\n📊 预测策略:")
            print(f"   - 事件类型: {plan.get('event_type', 'unknown')}")
            print(f"   - 分析工具: {[p.get('tool') for p in plan.get('analysis_plan', [])]}")
        
        # 情景预测
        scenarios = result.get('scenarios', [])
        if scenarios:
            print(f"\n📈 情景概率分布:")
            for i, s in enumerate(scenarios[:3], 1):
                print(f"   {i}. {s.get('name')}: {s.get('probability')}% ({s.get('risk_level')}风险)")
        
        # 时间轴
        timeline = result.get('timeline', [])
        if timeline:
            print(f"\n📅 时间轴预测 (共{len(timeline)}天):")
            for t in timeline[:3]:
                print(f"   第{t.get('day')}天: 热度{t.get('heat')}, 风险{t.get('risk')}")
            if len(timeline) > 3:
                print(f"   ...")
        
        # 预警
        warnings = result.get('warnings', [])
        if warnings:
            print(f"\n⚠️ 关键预警 ({len(warnings)}个):")
            for w in warnings[:2]:
                print(f"   - {w.get('description')}")
        
        # 核心洞察
        insights = result.get('key_insights', [])
        if insights:
            print(f"\n💡 核心洞察:")
            for insight in insights:
                print(f"   • {insight}")
        
        # 行动建议
        suggestions = result.get('action_suggestions', [])
        if suggestions:
            print(f"\n📌 行动建议:")
            for s in suggestions:
                print(f"   • {s}")
        
        # 最终结论
        conclusion = result.get('conclusion', '')
        if conclusion:
            print(f"\n📝 最终结论:")
            print(f"   {conclusion}")
        
        # 检查日志文件
        log_path = os.path.join(
            os.path.dirname(__file__), 
            "uploads", "predictions", 
            result.get('prediction_id', ''), 
            "agent_log.jsonl"
        )
        if os.path.exists(log_path):
            print(f"\n📄 日志文件: {log_path}")
            with open(log_path, 'r', encoding='utf-8') as f:
                logs = [json.loads(line) for line in f if line.strip()]
            print(f"   共 {len(logs)} 条日志记录")
            
            # 显示关键日志
            print("\n📝 关键思考过程:")
            for log in logs[:5]:
                action = log.get('action', '')
                message = log.get('details', {}).get('message', '')
                print(f"   [{action}] {message}")
        
        return result
        
    except Exception as e:
        print(f"\n\n❌ 预测失败: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_tool_execution():
    """测试工具执行能力"""
    print("\n" + "=" * 60)
    print("🔧 工具执行测试")
    print("=" * 60)
    
    agent = PredictionAgent(
        event_summary="测试事件",
        current_sentiment="中性",
        time_range=5
    )
    
    # 测试SIR模型
    print("\n1️⃣ 测试 SIR 模型分析...")
    sir_result = agent._tool_sir_model({
        "event_summary": "某产品发布引发热议",
        "current_sentiment": "中性",
        "days": 5
    })
    print(f"   峰值热度: {sir_result.get('peak_heat')}")
    print(f"   峰值日期: 第{sir_result.get('peak_day')}天")
    print(f"   趋势: {sir_result.get('trend')}")
    
    # 测试贝叶斯预测
    print("\n2️⃣ 测试贝叶斯情景预测...")
    bayes_result = agent._tool_bayesian_predictor({
        "event_summary": "某产品发布引发热议",
        "current_sentiment": "中性"
    })
    print(f"   情景数量: {len(bayes_result.get('scenarios', []))}")
    print(f"   最可能情景: {bayes_result.get('top_scenario')}")
    print(f"   概率: {bayes_result.get('top_probability')}%")
    
    # 测试风险评估
    print("\n3️⃣ 测试风险评估...")
    risk_result = agent._tool_risk_assessor({
        "timeline": sir_result.get('timeline', []),
        "scenarios": bayes_result.get('scenarios', [])
    })
    print(f"   预警数量: {len(risk_result.get('warnings', []))}")
    print(f"   风险分布: {risk_result.get('risk_distribution')}")
    
    print("\n✅ 工具测试完成!")


if __name__ == "__main__":
    print("\n" + "🤖" * 30)
    print("Prediction Agent 智能体能力测试")
    print("🤖" * 30 + "\n")
    
    # 先测试工具
    test_tool_execution()
    
    # 再测试完整流程
    print("\n")
    result = test_prediction_agent()
    
    if result:
        print("\n" + "=" * 60)
        print("🎉 所有测试通过!")
        print("=" * 60)
