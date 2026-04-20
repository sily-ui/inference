#!/usr/bin/env python3
"""测试策略竞技场生成效果"""

import json
import sys
sys.path.insert(0, '.')

from app.services.intervention_sandbox import InterventionSandboxService

def test_strategy_generation():
    service = InterventionSandboxService()
    
    # 测试数据（iPhone18事件）
    event_summary = "iPhone18 Pro被曝灵动岛区域屏幕质量问题，用户吐槽屏幕易碎，事件正在微博等平台发酵，大量果粉表达不满"
    current_sentiment = "负面"
    
    # 模拟的原始时间线
    original_timeline = [
        {"day": 1, "heat": 70, "sentiment": 0.3, "risk": "medium"},
        {"day": 2, "heat": 85, "sentiment": 0.2, "risk": "high"},
        {"day": 3, "heat": 92, "sentiment": 0.15, "risk": "high"},
        {"day": 4, "heat": 95, "sentiment": 0.1, "risk": "high"},
    ]
    
    # 测试策略
    strategies = [
        {"type": "official_statement", "description": "发布官方声明回应屏幕质量问题", "timing": 2},
        {"type": "kol_guidance", "description": "邀请数码博主发声解释屏幕工艺", "timing": 3},
        {"type": "data_disclosure", "description": "公开屏幕质量检测数据", "timing": 2},
        {"type": "precise_response", "description": "针对用户质疑的点逐一回应", "timing": 3},
    ]
    
    print("="*80)
    print("测试事件：", event_summary)
    print("="*80)
    print("正在生成策略对比内容...")
    
    try:
        result = service.generate_strategy_comparison(event_summary, current_sentiment, strategies, original_timeline)
        
        print("\n✅ 生成成功！\n")
        
        # 打印每个策略的分析
        for idx, comp in enumerate(result['comparisons'], 1):
            print(f"📌 策略{idx}：{comp['strategy_name']}（得分：{comp['score']}）")
            print(f"   热度变化：{comp['heat_change']}%，情绪变化：{comp['sentiment_change']}，风险：{comp['risk_level']}")
            print(f"   分析：{comp['analysis']}")
            print(f"   优点：{comp['pros']}")
            print(f"   缺点：{comp['cons']}")
            print("-"*80)
        
        # 打印综合建议
        print("💡 综合建议：")
        print(result['recommendation'])
        print("\n" + "="*80)
        
    except Exception as e:
        print(f"❌ 生成失败：{str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_strategy_generation()
