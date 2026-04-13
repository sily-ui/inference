# Step5 蝴蝶效应沙盒 — 改造设计文档

## 1. 改造目标

将 Step5 从"简单文本输入→数字输出"的干预模拟，升级为**交互式干预推演沙盒**，让用户像指挥官一样在时间线上部署干预动作，实时观察蝴蝶效应如何改变舆情走向。

## 2. 核心创新模块

### 2.1 干预动作卡片系统（Intervention Action Cards）

**功能**：基于前面的情景分析和风险评估，AI 自动生成一组干预动作卡片，每张卡片代表一种可执行的干预策略。

**前端组件**：`InterventionCardPool`
- 卡片类型：官方声明、KOL引导、数据披露、精准回应、冷处理、话题转移
- 每张卡片显示：图标、名称、预估效果方向、适用时机、风险提示
- 交互：点击卡片选中 → 自动填入干预输入区

**后端接口**：`POST /api/prediction/intervention-cards`
- 输入：`event_summary`, `scenarios`, `current_sentiment`, `warnings`
- 输出：6张干预卡片，每张包含 `id, type, name, icon, description, estimated_effect, best_timing, risks, prerequisite`
- 实现：LLM 根据事件特征和风险情景动态生成

### 2.2 分叉时间线（Branching Timeline）

**功能**：在趋势图上，用户选择干预类型和执行时间点后，时间线从该点分叉出新的预测曲线，与原始预测形成视觉对比。

**前端组件**：在现有趋势图区域增强
- 原始预测用实线，干预后预测用虚线+不同颜色
- 用户可选择干预插入的时间节点（Day1~DayN）
- 支持最多3条分叉线同时对比

**后端接口**：`POST /api/prediction/intervention-timeline`
- 输入：`event_summary`, `current_sentiment`, `time_range`, `intervention_type`, `intervention_day`, `original_timeline`
- 输出：干预后的完整时间线 `[{day, heat, sentiment, risk, event}]`
- 实现：基于 SIR 模型，在干预点修改 β/γ 参数重新计算后续时间轴，再用 LLM 生成事件描述

### 2.3 策略竞技场（Strategy Arena）

**功能**：用户可同时对比 2-3 个策略方案的效果，并排展示。

**前端组件**：`StrategyArena`
- 每个方案一张卡片，显示：热度变化、情绪变化、风险等级、综合评分
- 趋势曲线叠加对比（三条不同颜色曲线在同一图上）
- 综合评分由 LLM 生成

**后端接口**：`POST /api/prediction/strategy-compare`
- 输入：`event_summary`, `current_sentiment`, `strategies: [{type, description, timing}]`, `original_timeline`
- 输出：每个策略的 `timeline, heat_change, sentiment_change, risk_level, score, analysis`
- 实现：对每个策略分别调用 SIR+LLM 推演，再由 LLM 生成综合评分和分析

### 2.4 干预时机热力图（Intervention Timing Heatmap）

**功能**：展示不同干预类型在不同时间点的效果得分，告诉用户"什么时候做什么最有效"。

**前端组件**：`TimingHeatmap`
- X轴：干预执行时间（Day1~DayN）
- Y轴：干预类型
- 颜色：绿色=高效，黄色=中等，红色=低效/危险
- 鼠标悬停显示具体数值

**后端接口**：`POST /api/prediction/intervention-heatmap`
- 输入：`event_summary`, `current_sentiment`, `time_range`, `intervention_types`, `original_timeline`
- 输出：二维矩阵 `[{type, day, score, effectiveness, risk_note}]`
- 实现：LLM 根据事件特征和 SIR 模型传播曲线，评估每种干预在不同时间点的效果

### 2.5 链式反应可视化（Cascade Effect Visualization）

**功能**：展示干预动作如何通过社交网络逐层传播，直接利用 OASIS 模拟的 Agent 数据。

**前端组件**：`CascadeEffect`
- 涟漪动画展示干预信息在社交网络中的扩散
- 每层显示受影响的 Agent 数量和情绪变化
- 关键节点（高影响力 Agent）特殊标记

**后端接口**：`POST /api/prediction/cascade-effect`
- 输入：`event_summary`, `intervention_type`, `simulation_data`
- 输出：`{layers: [{level, affected_count, sentiment_shift, key_agents}], total_reach, cascade_speed}`
- 实现：LLM 基于 simulation_data 中的 Agent 数据，推演干预的链式传播路径

### 2.6 反事实推演（Counterfactual Reasoning）

**功能**：用户可以"移除"某个关键事件节点，观察没有该事件时舆情会如何发展。

**前端组件**：`CounterfactualPanel`
- 在时间线上标记可移除的关键事件节点
- 移除后重新生成对比时间线
- 显示差异量化（该事件的影响力）

**后端接口**：`POST /api/prediction/counterfactual`
- 输入：`event_summary`, `original_timeline`, `removed_event_day`, `removed_event_desc`
- 输出：`{counterfactual_timeline, impact_score, analysis}`
- 实现：LLM 重新推演不含该事件的舆情发展，对比差异

## 3. 前端页面布局

```
┌──────────────────────────────────────────────────────────────────┐
│  Step 5: 蝴蝶效应沙盒 — 交互式干预推演                            │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  🕐 分叉时间线（主视觉区域，复用现有趋势图增强）             │   │
│  │  ─── 原始预测    - - - 方案A    ··· 方案B                  │   │
│  │  [选择干预时间点] [选择干预类型] [生成分叉]                  │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
│  ┌─────────────────────────┐  ┌─────────────────────────────┐  │
│  │ 🃏 干预动作卡片池        │  │ 🗺️ 干预时机热力图            │  │
│  │                         │  │                             │  │
│  │ [📢官方声明] [🤝KOL引导] │  │  Day1  Day2  Day3  ...     │  │
│  │ [📊数据披露] [🎯精准回应] │  │  🟢🟢  🟢   🟡   ...      │  │
│  │ [⏰冷处理]  [🔄话题转移] │  │                             │  │
│  └─────────────────────────┘  └─────────────────────────────┘  │
│                                                                  │
│  ┌─────────────────────────┐  ┌─────────────────────────────┐  │
│  │ 🏟️ 策略竞技场            │  │ 🌊 链式反应可视化            │  │
│  │                         │  │                             │  │
│  │ 方案A vs 方案B vs 方案C  │  │  干预 → KOL → 媒体 → 公众   │  │
│  │ (并排对比+综合评分)       │  │  (涟漪动画+Agent影响)        │  │
│  └─────────────────────────┘  └─────────────────────────────┘  │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  🔮 反事实推演面板                                        │   │
│  │  "如果X事件没有发生..." → [选择事件] → [推演] → 对比结果    │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  💬 AI助手（保留原有功能）                                  │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

## 4. 后端接口设计

### 4.1 新增接口汇总

| 接口 | 方法 | 路径 | 说明 |
|------|------|------|------|
| 干预卡片生成 | POST | `/api/prediction/intervention-cards` | 根据事件和情景生成干预动作卡片 |
| 分叉时间线 | POST | `/api/prediction/intervention-timeline` | 计算干预后的分叉时间线 |
| 策略对比 | POST | `/api/prediction/strategy-compare` | 多策略并排对比推演 |
| 时机热力图 | POST | `/api/prediction/intervention-heatmap` | 干预时机效果矩阵 |
| 链式反应 | POST | `/api/prediction/cascade-effect` | 干预的链式传播推演 |
| 反事实推演 | POST | `/api/prediction/counterfactual` | 反事实推理对比 |

### 4.2 接口详细设计

#### 4.2.1 干预卡片生成

```
POST /api/prediction/intervention-cards

Request:
{
    "event_summary": "事件摘要",
    "scenarios": [...],          // 预测情景列表
    "current_sentiment": "负面", // 当前情绪
    "warnings": [...]            // 预警节点
}

Response:
{
    "success": true,
    "data": {
        "cards": [
            {
                "id": "official_statement",
                "type": "official_statement",
                "name": "官方声明",
                "icon": "📢",
                "description": "发布官方澄清公告或致歉声明，直接回应公众关切",
                "estimated_effect": "热度↓15-25%，情绪↑0.2-0.4",
                "best_timing": "事件爆发后24-48小时内",
                "risks": ["回应不当可能引发二次危机", "过度承诺难以兑现"],
                "prerequisite": "需要内部统一口径"
            },
            ...共6张卡片
        ]
    }
}
```

#### 4.2.2 分叉时间线

```
POST /api/prediction/intervention-timeline

Request:
{
    "event_summary": "事件摘要",
    "current_sentiment": "负面",
    "time_range": 7,
    "intervention_type": "official_statement",
    "intervention_description": "发布官方声明澄清事实",
    "intervention_day": 2,
    "original_timeline": [{day, heat, sentiment, risk, event}, ...]
}

Response:
{
    "success": true,
    "data": {
        "branch_timeline": [{day, heat, sentiment, risk, event}, ...],
        "comparison": {
            "peak_heat_change": -20,
            "avg_sentiment_change": 0.15,
            "risk_reduction": "high→medium",
            "recovery_speedup_days": 3
        },
        "analysis": "在第2天发布官方声明后..."
    }
}
```

#### 4.2.3 策略对比

```
POST /api/prediction/strategy-compare

Request:
{
    "event_summary": "事件摘要",
    "current_sentiment": "负面",
    "strategies": [
        {"type": "official_statement", "description": "发布官方声明", "timing": 2},
        {"type": "kol_guidance", "description": "邀请KOL发声", "timing": 3},
        {"type": "cold_treatment", "description": "冷处理等待自然衰减", "timing": 1}
    ],
    "original_timeline": [...]
}

Response:
{
    "success": true,
    "data": {
        "comparisons": [
            {
                "strategy_name": "发布官方声明",
                "timeline": [...],
                "heat_change": -20,
                "sentiment_change": 0.3,
                "risk_level": "low",
                "score": 85,
                "analysis": "快速回应有效降低热度...",
                "pros": ["见效快", "直接回应关切"],
                "cons": ["需要统一口径", "可能被挑刺"]
            },
            ...每个策略一份
        ],
        "recommendation": "综合评估，建议采用「发布官方声明」策略..."
    }
}
```

#### 4.2.4 时机热力图

```
POST /api/prediction/intervention-heatmap

Request:
{
    "event_summary": "事件摘要",
    "current_sentiment": "负面",
    "time_range": 7,
    "intervention_types": ["official_statement", "kol_guidance", "cold_treatment", "data_disclosure"],
    "original_timeline": [...]
}

Response:
{
    "success": true,
    "data": {
        "heatmap": [
            {
                "type": "official_statement",
                "type_name": "官方声明",
                "scores": [
                    {"day": 1, "score": 95, "effectiveness": "极高", "risk_note": "越早回应越有效"},
                    {"day": 2, "score": 85, "effectiveness": "高", "risk_note": "仍在黄金窗口期"},
                    ...
                ]
            },
            ...每个干预类型一份
        ]
    }
}
```

#### 4.2.5 链式反应

```
POST /api/prediction/cascade-effect

Request:
{
    "event_summary": "事件摘要",
    "intervention_type": "official_statement",
    "intervention_description": "发布官方声明",
    "simulation_data": {...}    // OASIS模拟数据
}

Response:
{
    "success": true,
    "data": {
        "layers": [
            {
                "level": 1,
                "description": "官方声明发布",
                "affected_count": 1,
                "sentiment_shift": 0,
                "key_agents": [{"name": "官方账号", "influence": "high"}]
            },
            {
                "level": 2,
                "description": "KOL和媒体转发扩散",
                "affected_count": 15,
                "sentiment_shift": 0.1,
                "key_agents": [{"name": "某知名博主", "influence": "high"}, ...]
            },
            {
                "level": 3,
                "description": "普通用户讨论和情绪转变",
                "affected_count": 200,
                "sentiment_shift": 0.2,
                "key_agents": []
            }
        ],
        "total_reach": 216,
        "cascade_speed": "中等（约6-12小时覆盖核心群体）",
        "analysis": "官方声明通过KOL和媒体..."
    }
}
```

#### 4.2.6 反事实推演

```
POST /api/prediction/counterfactual

Request:
{
    "event_summary": "事件摘要",
    "current_sentiment": "负面",
    "original_timeline": [...],
    "removed_event_day": 3,
    "removed_event_desc": "某KOL发布负面评论引爆舆论"
}

Response:
{
    "success": true,
    "data": {
        "counterfactual_timeline": [{day, heat, sentiment, risk, event}, ...],
        "impact_score": 35,
        "impact_description": "该事件贡献了约35%的舆情热度",
        "analysis": "如果没有该KOL的负面评论，舆情热度将显著降低...",
        "key_difference": "峰值热度从85降至55，风险等级从high降至medium"
    }
}
```

## 5. 前端组件拆分

保留原有 Step5Prediction.vue 作为容器，内部拆分为子组件：

```
Step5Prediction.vue (容器组件，保留加载状态、Agent分析状态)
├── BranchingTimeline.vue      — 分叉时间线（增强现有趋势图）
├── InterventionCardPool.vue   — 干预动作卡片池
├── TimingHeatmap.vue          — 干预时机热力图
├── StrategyArena.vue          — 策略竞技场
├── CascadeEffect.vue          — 链式反应可视化
├── CounterfactualPanel.vue    — 反事实推演面板
└── AIAssistant.vue            — AI助手（保留原有功能）
```

## 6. 数据流

```
用户操作 → 前端组件 → API调用 → 后端路由 → LLM/算法引擎 → 返回结果 → 前端渲染

具体流程：
1. Step5 加载完成 → 调用 intervention-cards 生成卡片
2. 用户选择卡片+时间点 → 调用 intervention-timeline 生成分叉线
3. 用户选择多个策略 → 调用 strategy-compare 并排对比
4. 页面加载时 → 调用 intervention-heatmap 生成热力图
5. 用户选择干预 → 调用 cascade-effect 展示链式反应
6. 用户选择关键事件 → 调用 counterfactual 反事实推演
```

## 7. 实现优先级

1. **P0（核心）**：干预卡片 + 分叉时间线 — 这是最核心的交互
2. **P1（重要）**：策略竞技场 + 时机热力图 — 增强决策支持
3. **P2（亮点）**：链式反应 + 反事实推演 — 最具创新性
