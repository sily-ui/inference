# MiroFish API 接口文档

> 版本: v1.0.3  
> 基础URL: `http://localhost:5001/api`  
> 编码: UTF-8  
> 响应格式: JSON

---

## 目录

- [概述](#概述)
- [通用说明](#通用说明)
- [首页接口](#首页接口)
- [Step 1: 本体生成](#step-1-本体生成)
- [Step 2: 图谱构建](#step-2-图谱构建)
- [Step 3: 模拟准备与运行](#step-3-模拟准备与运行)
- [Step 4: 报告生成](#step-4-报告生成)
- [Step 5: 舆情预测](#step-5-舆情预测)
- [辅助接口](#辅助接口)
- [错误码说明](#错误码说明)

---

## 概述

MiroFish 是一个基于知识图谱的舆情模拟分析系统，提供完整的舆情事件分析流程：

```
上传文档 → 生成本体 → 构建图谱 → 模拟运行 → 生成报告 → 舆情预测
```

### 核心功能模块

| 模块 | 说明 |
|------|------|
| 本体生成 | 分析文档，提取实体类型和关系类型 |
| 图谱构建 | 基于Zep构建知识图谱 |
| OASIS模拟 | 多Agent社交媒体模拟 |
| 报告生成 | AI自动生成分析报告 |
| 舆情预测 | 时间轴推演、情景预测、干预模拟 |

---

## 通用说明

### 响应格式

所有接口统一返回以下格式：

```json
{
    "success": true,
    "data": { ... }
}
```

错误响应：

```json
{
    "success": false,
    "error": "错误描述",
    "traceback": "详细堆栈信息（仅调试模式）"
}
```

### 认证方式

当前版本无需认证，后续可扩展JWT认证。

### 内容类型

- 文件上传: `multipart/form-data`
- JSON请求: `application/json`

---

## 首页接口

### 1. 获取历史模拟列表

获取所有历史模拟项目，用于首页展示。

**请求**

```
GET /api/simulation/history
```

**Query参数**

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| limit | int | 否 | 20 | 返回数量限制 |

**响应示例**

```json
{
    "success": true,
    "data": [
        {
            "simulation_id": "sim_abc123",
            "project_id": "proj_xyz789",
            "project_name": "武大舆情分析",
            "simulation_requirement": "如果武汉大学发布一则关于学费调整的通知...",
            "status": "completed",
            "entities_count": 68,
            "profiles_count": 68,
            "entity_types": ["Student", "Professor", "Administrator", "PublicFigure"],
            "created_at": "2024-12-10T14:30:00",
            "updated_at": "2024-12-10T18:45:00",
            "created_date": "2024-12-10",
            "total_rounds": 120,
            "current_round": 120,
            "total_simulation_hours": 72,
            "runner_status": "completed",
            "report_id": "report_def456",
            "version": "v1.0.2",
            "files": [
                {"filename": "event_description.pdf"},
                {"filename": "background.md"}
            ]
        }
    ],
    "count": 1
}
```

**字段说明**

| 字段 | 类型 | 说明 |
|------|------|------|
| simulation_id | string | 模拟唯一标识 |
| project_id | string | 关联项目ID |
| project_name | string | 项目名称 |
| simulation_requirement | string | 模拟需求描述 |
| status | string | 模拟状态: `preparing`/`ready`/`running`/`completed`/`stopped`/`failed` |
| entities_count | int | 实体数量 |
| profiles_count | int | Agent配置数量 |
| entity_types | array | 实体类型列表 |
| total_rounds | int | 总轮数 |
| current_round | int | 当前轮数 |
| runner_status | string | 运行器状态: `idle`/`running`/`paused`/`completed`/`stopped` |
| report_id | string | 关联报告ID |

---

### 2. 获取项目列表

**请求**

```
GET /api/graph/project/list
```

**Query参数**

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| limit | int | 否 | 50 | 返回数量限制 |

**响应示例**

```json
{
    "success": true,
    "data": [
        {
            "project_id": "proj_abc123",
            "name": "舆情分析项目",
            "status": "graph_completed",
            "created_at": "2024-12-10T10:00:00",
            "updated_at": "2024-12-10T12:00:00",
            "files": [
                {"filename": "document.pdf", "size": 1024000}
            ],
            "total_text_length": 50000,
            "ontology": {
                "entity_types": [...],
                "edge_types": [...]
            },
            "graph_id": "graph_xyz",
            "simulation_requirement": "..."
        }
    ],
    "count": 1
}
```

---

### 3. 获取项目详情

**请求**

```
GET /api/graph/project/{project_id}
```

**路径参数**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| project_id | string | 是 | 项目ID |

**响应示例**

```json
{
    "success": true,
    "data": {
        "project_id": "proj_abc123",
        "name": "舆情分析项目",
        "status": "graph_completed",
        "created_at": "2024-12-10T10:00:00",
        "updated_at": "2024-12-10T12:00:00",
        "files": [
            {"filename": "document.pdf", "size": 1024000}
        ],
        "total_text_length": 50000,
        "ontology": {
            "entity_types": [
                {
                    "name": "Student",
                    "description": "在校学生"
                },
                {
                    "name": "Professor",
                    "description": "教授或教师"
                }
            ],
            "edge_types": [
                {
                    "name": "STUDY_AT",
                    "description": "就读于"
                }
            ]
        },
        "analysis_summary": "文档分析摘要...",
        "graph_id": "graph_xyz",
        "simulation_requirement": "模拟需求描述...",
        "chunk_size": 500,
        "chunk_overlap": 50
    }
}
```

---

## Step 1: 本体生成

### 1.1 上传文件并生成本体

上传文档文件，AI自动分析生成本体定义（实体类型和关系类型）。

**请求**

```
POST /api/graph/ontology/generate
Content-Type: multipart/form-data
```

**Form参数**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| files | file[] | 是 | 上传的文件（支持 PDF/MD/TXT），可多个 |
| simulation_requirement | string | 是 | 模拟需求描述，描述要模拟的舆情场景 |
| project_name | string | 否 | 项目名称，默认 "Unnamed Project" |
| additional_context | string | 否 | 额外说明信息 |

**请求示例（JavaScript）**

```javascript
const formData = new FormData();
formData.append('files', file1);
formData.append('files', file2);
formData.append('simulation_requirement', '如果武汉大学发布一则关于学费调整的通知，学生和公众会有什么反应？');
formData.append('project_name', '武大学费舆情分析');

const response = await fetch('/api/graph/ontology/generate', {
    method: 'POST',
    body: formData
});
```

**响应示例**

```json
{
    "success": true,
    "data": {
        "project_id": "proj_abc123",
        "project_name": "武大学费舆情分析",
        "ontology": {
            "entity_types": [
                {
                    "name": "Student",
                    "description": "在校学生，可能对学费调整有直接反应"
                },
                {
                    "name": "Professor",
                    "description": "教授或教师，可能发表专业意见"
                },
                {
                    "name": "Administrator",
                    "description": "学校管理人员，决策者"
                },
                {
                    "name": "PublicFigure",
                    "description": "公众人物，可能影响舆论走向"
                },
                {
                    "name": "MediaOutlet",
                    "description": "媒体机构"
                }
            ],
            "edge_types": [
                {
                    "name": "STUDY_AT",
                    "description": "就读于某学校"
                },
                {
                    "name": "WORK_AT",
                    "description": "工作于某机构"
                },
                {
                    "name": "AFFILIATED_WITH",
                    "description": "关联于某组织"
                }
            ]
        },
        "analysis_summary": "文档描述了一个关于高校学费调整的舆情事件...",
        "files": [
            {"filename": "event.pdf", "size": 1024000}
        ],
        "total_text_length": 15000
    }
}
```

**字段说明**

| 字段 | 类型 | 说明 |
|------|------|------|
| project_id | string | 项目唯一标识，后续步骤需使用 |
| ontology.entity_types | array | 实体类型定义 |
| ontology.edge_types | array | 关系类型定义 |
| analysis_summary | string | AI生成的文档分析摘要 |
| total_text_length | int | 提取的文本总长度 |

---

## Step 2: 图谱构建

### 2.1 构建知识图谱

根据项目ID构建知识图谱（异步任务）。

**请求**

```
POST /api/graph/build
Content-Type: application/json
```

**请求参数**

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| project_id | string | 是 | - | 项目ID（Step1返回的project_id） |
| graph_name | string | 否 | 项目名称 | 图谱名称 |
| chunk_size | int | 否 | 500 | 文本分块大小 |
| chunk_overlap | int | 否 | 50 | 分块重叠大小 |
| force | boolean | 否 | false | 强制重新构建 |

**请求示例**

```json
{
    "project_id": "proj_abc123",
    "graph_name": "武大学费舆情图谱",
    "chunk_size": 500,
    "chunk_overlap": 50
}
```

**响应示例**

```json
{
    "success": true,
    "data": {
        "project_id": "proj_abc123",
        "task_id": "task_xyz789",
        "message": "图谱构建任务已启动，请通过 /task/{task_id} 查询进度"
    }
}
```

---

### 2.2 查询任务状态

查询图谱构建任务进度。

**请求**

```
GET /api/graph/task/{task_id}
```

**路径参数**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| task_id | string | 是 | 任务ID |

**响应示例**

```json
{
    "success": true,
    "data": {
        "task_id": "task_xyz789",
        "task_type": "graph_build",
        "status": "processing",
        "progress": 45,
        "message": "正在添加文本块 15/30...",
        "progress_detail": {
            "stage": "adding_text",
            "current": 15,
            "total": 30
        },
        "created_at": "2024-12-10T10:00:00",
        "updated_at": "2024-12-10T10:05:00",
        "result": null,
        "error": null
    }
}
```

**任务状态说明**

| 状态 | 说明 |
|------|------|
| pending | 等待中 |
| processing | 处理中 |
| completed | 已完成 |
| failed | 失败 |

**完成时的响应**

```json
{
    "success": true,
    "data": {
        "task_id": "task_xyz789",
        "status": "completed",
        "progress": 100,
        "message": "图谱构建完成",
        "result": {
            "project_id": "proj_abc123",
            "graph_id": "graph_abc123",
            "node_count": 150,
            "edge_count": 280,
            "chunk_count": 30
        }
    }
}
```

---

### 2.3 获取图谱数据

获取构建完成的图谱数据。

**请求**

```
GET /api/graph/data/{graph_id}
```

**响应示例**

```json
{
    "success": true,
    "data": {
        "graph_id": "graph_abc123",
        "node_count": 150,
        "edge_count": 280,
        "nodes": [
            {
                "id": "node_1",
                "label": "Student",
                "name": "张三",
                "properties": {...}
            }
        ],
        "edges": [
            {
                "source": "node_1",
                "target": "node_2",
                "type": "STUDY_AT",
                "properties": {...}
            }
        ]
    }
}
```

---

## Step 3: 模拟准备与运行

### 3.1 创建模拟

基于项目创建新的模拟实例。

**请求**

```
POST /api/simulation/create
Content-Type: application/json
```

**请求参数**

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| project_id | string | 是 | - | 项目ID |
| graph_id | string | 否 | 项目graph_id | 图谱ID |
| enable_twitter | boolean | 否 | true | 启用Twitter模拟 |
| enable_reddit | boolean | 否 | true | 启用Reddit模拟 |

**请求示例**

```json
{
    "project_id": "proj_abc123",
    "enable_twitter": true,
    "enable_reddit": true
}
```

**响应示例**

```json
{
    "success": true,
    "data": {
        "simulation_id": "sim_def456",
        "project_id": "proj_abc123",
        "graph_id": "graph_abc123",
        "status": "created",
        "enable_twitter": true,
        "enable_reddit": true,
        "created_at": "2024-12-10T11:00:00",
        "updated_at": "2024-12-10T11:00:00"
    }
}
```

---

### 3.2 准备模拟环境（异步）

为模拟生成Agent配置和模拟参数（异步任务，耗时操作）。

**请求**

```
POST /api/simulation/prepare
Content-Type: application/json
```

**请求参数**

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| simulation_id | string | 是 | - | 模拟ID |
| entity_types | array | 否 | 全部 | 指定实体类型过滤 |
| use_llm_for_profiles | boolean | 否 | true | 使用LLM生成Agent人设 |
| parallel_profile_count | int | 否 | 5 | 并行生成人设数量 |
| force_regenerate | boolean | 否 | false | 强制重新生成 |

**请求示例**

```json
{
    "simulation_id": "sim_def456",
    "use_llm_for_profiles": true,
    "parallel_profile_count": 5
}
```

**响应示例（首次准备）**

```json
{
    "success": true,
    "data": {
        "simulation_id": "sim_def456",
        "task_id": "task_prep001",
        "status": "preparing",
        "message": "准备任务已启动",
        "already_prepared": false
    }
}
```

**响应示例（已准备完成）**

```json
{
    "success": true,
    "data": {
        "simulation_id": "sim_def456",
        "status": "ready",
        "message": "已有完成的准备工作，无需重复生成",
        "already_prepared": true,
        "prepare_info": {
            "status": "ready",
            "entities_count": 68,
            "profiles_count": 68,
            "entity_types": ["Student", "Professor", "Administrator"]
        }
    }
}
```

---

### 3.3 查询准备进度

**请求**

```
POST /api/simulation/prepare/status
Content-Type: application/json
```

**请求参数**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| task_id | string | 否 | 任务ID |
| simulation_id | string | 否 | 模拟ID |

> 至少提供其中一个参数

**响应示例**

```json
{
    "success": true,
    "data": {
        "task_id": "task_prep001",
        "status": "processing",
        "progress": 35,
        "message": "[generating_profiles] 正在生成Agent人设 (24/68)",
        "progress_detail": {
            "stage": "generating_profiles",
            "current": 24,
            "total": 68
        }
    }
}
```

---

### 3.4 实时获取Agent配置

在生成过程中实时查看已生成的Agent配置。

**请求**

```
GET /api/simulation/{simulation_id}/profiles/realtime
```

**Query参数**

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| platform | string | 否 | reddit | 平台类型: `reddit`/`twitter` |

**响应示例**

```json
{
    "success": true,
    "data": {
        "simulation_id": "sim_def456",
        "platform": "reddit",
        "count": 24,
        "total_expected": 68,
        "is_generating": true,
        "file_exists": true,
        "file_modified_at": "2024-12-10T11:30:00",
        "profiles": [
            {
                "agent_id": 0,
                "user_id": "student_zhang",
                "user_name": "张同学",
                "description": "武汉大学大三学生，关注学费问题...",
                "traits": ["理性", "关注教育公平"],
                "memories": [...]
            }
        ]
    }
}
```

---

### 3.5 实时获取模拟配置

**请求**

```
GET /api/simulation/{simulation_id}/config/realtime
```

**响应示例**

```json
{
    "success": true,
    "data": {
        "simulation_id": "sim_def456",
        "file_exists": true,
        "file_modified_at": "2024-12-10T11:45:00",
        "is_generating": false,
        "generation_stage": "completed",
        "config_generated": true,
        "config": {
            "simulation_requirement": "...",
            "time_config": {
                "total_simulation_hours": 72,
                "minutes_per_round": 30
            },
            "agent_configs": [...]
        },
        "summary": {
            "total_agents": 68,
            "simulation_hours": 72,
            "initial_posts_count": 5
        }
    }
}
```

---

### 3.6 运行模拟

启动模拟运行。

**请求**

```
POST /api/simulation/run
Content-Type: application/json
```

**请求参数**

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| simulation_id | string | 是 | - | 模拟ID |
| total_rounds | int | 否 | 自动计算 | 总轮数 |
| parallel_count | int | 否 | 5 | 并行Agent数量 |
| round_interval | float | 否 | 1.0 | 轮次间隔（秒） |

**请求示例**

```json
{
    "simulation_id": "sim_def456",
    "total_rounds": 144,
    "parallel_count": 5,
    "round_interval": 1.0
}
```

**响应示例**

```json
{
    "success": true,
    "data": {
        "simulation_id": "sim_def456",
        "status": "running",
        "message": "模拟已启动",
        "total_rounds": 144,
        "parallel_count": 5
    }
}
```

---

### 3.7 获取运行状态

**请求**

```
GET /api/simulation/{simulation_id}/run-status
```

**响应示例**

```json
{
    "success": true,
    "data": {
        "simulation_id": "sim_def456",
        "runner_status": "running",
        "current_round": 45,
        "total_rounds": 144,
        "progress_percent": 31.25,
        "simulated_hours": 22.5,
        "total_simulation_hours": 72,
        "twitter_running": true,
        "reddit_running": true,
        "twitter_actions_count": 1250,
        "reddit_actions_count": 1890,
        "total_actions_count": 3140,
        "started_at": "2024-12-10T12:00:00",
        "updated_at": "2024-12-10T14:30:00"
    }
}
```

---

### 3.8 获取详细运行状态

包含所有Agent动作详情。

**请求**

```
GET /api/simulation/{simulation_id}/run-status/detail
```

**Query参数**

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| platform | string | 否 | 全部 | 过滤平台: `twitter`/`reddit` |

**响应示例**

```json
{
    "success": true,
    "data": {
        "simulation_id": "sim_def456",
        "runner_status": "running",
        "current_round": 45,
        "total_rounds": 144,
        "all_actions": [
            {
                "round_num": 45,
                "timestamp": "2024-12-10T14:30:00",
                "platform": "twitter",
                "agent_id": 3,
                "agent_name": "张同学",
                "action_type": "CREATE_POST",
                "action_args": {
                    "content": "关于学费调整，我认为..."
                },
                "result": null,
                "success": true
            }
        ],
        "twitter_actions": [...],
        "reddit_actions": [...],
        "recent_actions": [...],
        "rounds_count": 45
    }
}
```

---

### 3.9 暂停/继续模拟

**请求**

```
POST /api/simulation/pause
Content-Type: application/json
```

**请求参数**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| simulation_id | string | 是 | 模拟ID |

**继续模拟**

```
POST /api/simulation/resume
Content-Type: application/json
```

---

### 3.10 停止模拟

**请求**

```
POST /api/simulation/stop
Content-Type: application/json
```

**请求参数**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| simulation_id | string | 是 | 模拟ID |

---

### 3.11 采访Agent

在模拟运行中或完成后，采访单个Agent获取其观点。

**请求**

```
POST /api/simulation/interview
Content-Type: application/json
```

**请求参数**

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| simulation_id | string | 是 | - | 模拟ID |
| agent_id | int | 是 | - | Agent ID |
| prompt | string | 是 | - | 采访问题 |
| platform | string | 否 | 双平台 | 指定平台: `twitter`/`reddit` |
| timeout | int | 否 | 60 | 超时时间（秒） |

**请求示例**

```json
{
    "simulation_id": "sim_def456",
    "agent_id": 0,
    "prompt": "你对这次学费调整有什么看法？",
    "platform": "twitter"
}
```

**响应示例（指定平台）**

```json
{
    "success": true,
    "data": {
        "agent_id": 0,
        "prompt": "你对这次学费调整有什么看法？",
        "result": {
            "agent_id": 0,
            "response": "作为一名学生，我认为这次学费调整需要更加透明...",
            "platform": "twitter",
            "timestamp": "2024-12-10T15:00:00"
        }
    }
}
```

**响应示例（双平台模式，不指定platform）**

```json
{
    "success": true,
    "data": {
        "agent_id": 0,
        "prompt": "你对这次学费调整有什么看法？",
        "result": {
            "agent_id": 0,
            "platforms": {
                "twitter": {
                    "agent_id": 0,
                    "response": "在Twitter上我会这样表达...",
                    "platform": "twitter"
                },
                "reddit": {
                    "agent_id": 0,
                    "response": "在Reddit上我会详细分析...",
                    "platform": "reddit"
                }
            }
        }
    }
}
```

---

### 3.12 批量采访Agent

**请求**

```
POST /api/simulation/interview/batch
Content-Type: application/json
```

**请求参数**

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| simulation_id | string | 是 | - | 模拟ID |
| interviews | array | 是 | - | 采访列表 |
| platform | string | 否 | 双平台 | 默认平台 |
| timeout | int | 否 | 120 | 超时时间（秒） |

**请求示例**

```json
{
    "simulation_id": "sim_def456",
    "interviews": [
        {"agent_id": 0, "prompt": "你的看法？", "platform": "twitter"},
        {"agent_id": 1, "prompt": "你的建议？"}
    ]
}
```

---

### 3.13 获取模拟帖子

**请求**

```
GET /api/simulation/{simulation_id}/posts
```

**Query参数**

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| platform | string | 否 | reddit | 平台类型 |
| limit | int | 否 | 50 | 返回数量 |
| offset | int | 否 | 0 | 偏移量 |

**响应示例**

```json
{
    "success": true,
    "data": {
        "platform": "reddit",
        "total": 150,
        "count": 50,
        "posts": [
            {
                "post_id": 1,
                "agent_id": 0,
                "title": "关于学费调整的讨论",
                "content": "...",
                "created_at": "2024-12-10T12:30:00",
                "num_likes": 15,
                "num_dislikes": 2,
                "num_comments": 8
            }
        ]
    }
}
```

---

### 3.14 获取模拟评论

**请求**

```
GET /api/simulation/{simulation_id}/comments
```

**Query参数**

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| post_id | int | 否 | - | 过滤帖子ID |
| limit | int | 否 | 50 | 返回数量 |
| offset | int | 否 | 0 | 偏移量 |

---

### 3.15 获取时间线

按轮次汇总的模拟时间线。

**请求**

```
GET /api/simulation/{simulation_id}/timeline
```

**Query参数**

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| start_round | int | 否 | 0 | 起始轮次 |
| end_round | int | 否 | 全部 | 结束轮次 |

**响应示例**

```json
{
    "success": true,
    "data": {
        "rounds_count": 144,
        "timeline": [
            {
                "round": 1,
                "actions_count": 68,
                "twitter_actions": 34,
                "reddit_actions": 34,
                "timestamp": "2024-12-10T12:00:00"
            }
        ]
    }
}
```

---

### 3.16 获取Agent统计

**请求**

```
GET /api/simulation/{simulation_id}/agent-stats
```

**响应示例**

```json
{
    "success": true,
    "data": {
        "agents_count": 68,
        "stats": [
            {
                "agent_id": 0,
                "agent_name": "张同学",
                "total_actions": 45,
                "posts_count": 12,
                "comments_count": 20,
                "likes_count": 13
            }
        ]
    }
}
```

---

## Step 4: 报告生成

### 4.1 生成报告（异步）

基于模拟结果生成分析报告。

**请求**

```
POST /api/report/generate
Content-Type: application/json
```

**请求参数**

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| simulation_id | string | 是 | - | 模拟ID |
| force_regenerate | boolean | 否 | false | 强制重新生成 |

**请求示例**

```json
{
    "simulation_id": "sim_def456"
}
```

**响应示例**

```json
{
    "success": true,
    "data": {
        "simulation_id": "sim_def456",
        "report_id": "report_abc123",
        "task_id": "task_report001",
        "status": "generating",
        "message": "报告生成任务已启动，请通过 /api/report/generate/status 查询进度",
        "already_generated": false
    }
}
```

---

### 4.2 查询报告生成进度

**请求**

```
POST /api/report/generate/status
Content-Type: application/json
```

**请求参数**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| task_id | string | 否 | 任务ID |
| simulation_id | string | 否 | 模拟ID |

**响应示例**

```json
{
    "success": true,
    "data": {
        "task_id": "task_report001",
        "status": "processing",
        "progress": 35,
        "message": "[关键发现] 正在分析数据...",
        "result": null
    }
}
```

---

### 4.3 获取报告详情

**请求**

```
GET /api/report/{report_id}
```

**响应示例**

```json
{
    "success": true,
    "data": {
        "report_id": "report_abc123",
        "simulation_id": "sim_def456",
        "status": "completed",
        "outline": {
            "sections": [
                {"title": "执行摘要", "status": "completed"},
                {"title": "模拟背景", "status": "completed"},
                {"title": "关键发现", "status": "completed"},
                {"title": "舆情分析", "status": "completed"},
                {"title": "结论与建议", "status": "completed"}
            ]
        },
        "markdown_content": "# 舆情模拟分析报告\n\n## 执行摘要\n\n...",
        "created_at": "2024-12-10T15:00:00",
        "completed_at": "2024-12-10T15:30:00"
    }
}
```

---

### 4.4 根据模拟ID获取报告

**请求**

```
GET /api/report/by-simulation/{simulation_id}
```

---

### 4.5 获取报告章节列表

用于分章节实时展示报告生成进度。

**请求**

```
GET /api/report/{report_id}/sections
```

**响应示例**

```json
{
    "success": true,
    "data": {
        "report_id": "report_abc123",
        "sections": [
            {
                "filename": "section_01.md",
                "section_index": 1,
                "content": "## 执行摘要\n\n本次模拟分析了..."
            },
            {
                "filename": "section_02.md",
                "section_index": 2,
                "content": "## 模拟背景\n\n..."
            }
        ],
        "total_sections": 2,
        "is_complete": false
    }
}
```

---

### 4.6 获取单个章节

**请求**

```
GET /api/report/{report_id}/section/{section_index}
```

---

### 4.7 下载报告

支持三种格式的报告下载：Markdown、PDF、Word。

#### 4.7.1 下载 Markdown 格式

**请求**

```
GET /api/report/{report_id}/download
```

**响应**

返回 Markdown 文件下载（`.md` 格式）。

---

#### 4.7.2 下载 PDF 格式（美化版）

使用 ReportLab 生成的美观 PDF 报告，支持中文字体和格式化排版。

**请求**

```
GET /api/report/{report_id}/download/pdf
```

**响应**

返回 PDF 文件下载（`.pdf` 格式）。

**特性**
- 自动注册系统中文字体（SimHei、SimSun、Microsoft YaHei）
- 支持标题层级（H1-H3）
- 支持列表、引用、代码块等 Markdown 元素
- 包含页眉页脚和页码
- 自动生成报告元数据（报告ID、生成时间）

---

#### 4.7.3 下载 Word 格式

使用 python-docx 生成的 Word 文档，支持中文字体。

**请求**

```
GET /api/report/{report_id}/download/word
```

**响应**

返回 Word 文件下载（`.docx` 格式）。

**特性**
- 支持中文字体（SimHei、SimSun）
- 支持标题层级（H1-H3）
- 支持有序列表、无序列表
- 支持引用块
- 自动生成报告元数据

---

### 4.8 与报告Agent对话

基于报告内容进行问答。

**请求**

```
POST /api/report/chat
Content-Type: application/json
```

**请求参数**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| simulation_id | string | 是 | 模拟ID |
| message | string | 是 | 用户消息 |
| chat_history | array | 否 | 对话历史 |

**请求示例**

```json
{
    "simulation_id": "sim_def456",
    "message": "请解释一下舆情走向的主要影响因素",
    "chat_history": [
        {"role": "user", "content": "之前的对话..."},
        {"role": "assistant", "content": "之前的回复..."}
    ]
}
```

**响应示例**

```json
{
    "success": true,
    "data": {
        "response": "根据模拟数据分析，舆情走向主要受以下因素影响...",
        "tool_calls": [
            {"tool": "search_nodes", "query": "舆情走向"}
        ],
        "sources": [
            {"type": "node", "id": "node_123", "content": "..."}
        ]
    }
}
```

---

## Step 5: 舆情预测

### 5.1 完整舆情预测

包含时间轴推演、情景预测、关键预警等功能。

**请求**

```
POST /api/prediction/predict
Content-Type: application/json
```

**请求参数**

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| simulation_id | string | 否 | - | 模拟ID |
| report_id | string | 否 | - | 报告ID |
| event_summary | string | 是 | - | 事件摘要 |
| current_sentiment | string | 否 | 中性 | 当前情绪状态 |
| time_range | int | 否 | 7 | 预测天数 |

**请求示例**

```json
{
    "simulation_id": "sim_def456",
    "event_summary": "某高校发布学费调整通知，引发学生和公众热议",
    "current_sentiment": "复杂（正负面兼有）",
    "time_range": 7
}
```

**响应示例**

```json
{
    "success": true,
    "data": {
        "timeline": [
            {
                "day": 1,
                "date": "2024-12-11",
                "predicted_heat": 85,
                "predicted_sentiment": "负面主导",
                "key_events": ["官方回应发布"],
                "confidence": 0.85
            },
            {
                "day": 2,
                "date": "2024-12-12",
                "predicted_heat": 92,
                "predicted_sentiment": "负面高峰",
                "key_events": ["媒体跟进报道", "学生组织发声"],
                "confidence": 0.78
            }
        ],
        "scenarios": [
            {
                "name": "乐观情景",
                "probability": 0.25,
                "description": "学校及时回应，调整方案合理...",
                "outcome": "舆情逐渐平息"
            },
            {
                "name": "中性情景",
                "probability": 0.50,
                "description": "学校回应不够充分...",
                "outcome": "舆情持续发酵"
            },
            {
                "name": "悲观情景",
                "probability": 0.25,
                "description": "学校回应不当或延迟...",
                "outcome": "舆情失控"
            }
        ],
        "warnings": [
            {
                "level": "high",
                "type": "情绪拐点",
                "description": "第2-3天可能出现负面情绪高峰",
                "recommendation": "建议在此之前发布官方回应"
            },
            {
                "level": "medium",
                "type": "关键人物",
                "description": "公众人物的表态可能放大舆情",
                "recommendation": "关注意见领袖动态"
            }
        ],
        "visualization": {
            "heat_trend": [...],
            "sentiment_distribution": {...}
        },
        "conclusion": "综合预测分析，该事件在未来7天内..."
    }
}
```

---

### 5.2 干预策略模拟

模拟不同干预措施的效果。

**请求**

```
POST /api/prediction/intervention
Content-Type: application/json
```

**请求参数**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| event_summary | string | 是 | 事件摘要 |
| intervention | string | 是 | 干预措施描述 |
| current_sentiment | string | 否 | 当前情绪状态 |

**请求示例**

```json
{
    "event_summary": "高校学费调整引发争议",
    "intervention": "学校召开新闻发布会，详细解释调整原因，并承诺设立专项奖学金",
    "current_sentiment": "负面主导"
}
```

**响应示例**

```json
{
    "success": true,
    "data": {
        "strategy": "透明沟通+利益补偿",
        "expected_effect": "预计可有效缓解负面情绪",
        "heat_change": -25,
        "sentiment_change": 0.3,
        "risk": "低风险，建议执行",
        "recommendation": 4,
        "analysis": "该干预策略通过透明化决策过程和提供补偿措施..."
    }
}
```

---

### 5.3 AI对话问答

基于预测结果进行问答。

**请求**

```
POST /api/prediction/chat
Content-Type: application/json
```

**请求参数**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| question | string | 是 | 用户问题 |
| prediction_data | object | 否 | 预测数据上下文 |

**请求示例**

```json
{
    "question": "如果学校在第3天才回应，会有什么后果？",
    "prediction_data": {...}
}
```

**响应示例**

```json
{
    "success": true,
    "data": {
        "answer": "如果学校延迟到第3天才回应，根据预测模型分析..."
    }
}
```

---

### 5.4 获取演示数据

用于测试预测功能。

**请求**

```
GET /api/prediction/demo
```

---

## 辅助接口

### 社交搜索

#### Tavily搜索

使用Tavily搜索完整事件信息。

**请求**

```
POST /api/social/search
Content-Type: application/json
```

**请求参数**

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| query | string | 是 | - | 搜索描述 |
| search_depth | string | 否 | basic | 搜索深度: `basic`/`advanced` |
| topic | string | 否 | general | 主题: `general`/`news`/`finance` |
| max_results | int | 否 | 10 | 最大结果数 |

**响应示例**

```json
{
    "success": true,
    "data": {
        "query": "武汉大学学费调整",
        "answer": "Tavily生成的摘要答案...",
        "results": [
            {
                "title": "相关新闻标题",
                "url": "https://...",
                "content": "内容摘要...",
                "score": 0.95
            }
        ]
    }
}
```

---

#### 提取文本用于推理

**请求**

```
POST /api/social/extract
Content-Type: application/json
```

**请求参数**

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| query | string | 是 | - | 搜索描述 |
| include_raw_content | boolean | 否 | true | 是否包含原始内容 |

---

#### 情感分析

**请求**

```
POST /api/social/sentiment/analyze
Content-Type: application/json
```

**请求参数**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| text | string | 是 | 待分析文本 |

**响应示例**

```json
{
    "success": true,
    "data": {
        "label": "negative",
        "score": 0.75,
        "emotions": ["愤怒", "失望"],
        "summary": "文本整体呈现负面情绪...",
        "aspects": {
            "学费": "negative",
            "学校管理": "negative"
        }
    }
}
```

---

### Token统计

#### 获取Token使用统计

**请求**

```
GET /api/report/token-stats
```

**响应示例**

```json
{
    "success": true,
    "data": {
        "model_name": "qwen-plus",
        "total_tokens": 150000,
        "prompt_tokens": 90000,
        "completion_tokens": 60000,
        "total_calls": 150,
        "cached_tokens": 10000,
        "estimated_cost": 0.525
    }
}
```

---

#### 重置Token统计

**请求**

```
POST /api/report/token-stats/reset
```

---

### 任务管理

#### 列出所有任务

**请求**

```
GET /api/graph/tasks
```

---

### 项目管理

#### 删除项目

**请求**

```
DELETE /api/graph/project/{project_id}
```

---

#### 重置项目状态

**请求**

```
POST /api/graph/project/{project_id}/reset
```

---

### 图谱管理

#### 删除图谱

**请求**

```
DELETE /api/graph/delete/{graph_id}
```

---

## 错误码说明

### HTTP状态码

| 状态码 | 说明 |
|--------|------|
| 200 | 成功 |
| 400 | 请求参数错误 |
| 404 | 资源不存在 |
| 500 | 服务器内部错误 |
| 504 | 网关超时 |

### 错误响应格式

```json
{
    "success": false,
    "error": "错误描述信息",
    "traceback": "详细堆栈信息（仅DEBUG模式）"
}
```

### 常见错误

| 错误信息 | 原因 | 解决方案 |
|----------|------|----------|
| 请提供 simulation_requirement | 未填写模拟需求 | 在请求中添加 simulation_requirement 参数 |
| 项目不存在: xxx | project_id 无效 | 检查 project_id 是否正确 |
| 图谱正在构建中 | 重复提交构建请求 | 等待当前任务完成或使用 force: true |
| ZEP_API_KEY未配置 | 环境变量缺失 | 检查 .env 文件配置 |
| 模拟环境未运行 | Interview 时模拟已停止 | 确保模拟处于运行状态 |

---

## 附录

### 项目状态流转

```
created → ontology_generated → graph_building → graph_completed → failed
```

### 模拟状态流转

```
created → preparing → ready → running → completed/stopped/failed
```

### 实体类型示例

```json
{
    "name": "Student",
    "description": "在校学生，可能对学费调整有直接反应"
}
```

### Agent Profile示例

```json
{
    "agent_id": 0,
    "user_id": "student_zhang",
    "user_name": "张同学",
    "description": "武汉大学大三学生，计算机专业，关注教育公平问题",
    "traits": ["理性", "关注教育公平", "善于表达"],
    "memories": [
        "之前参与过学生会的学费讨论",
        "家庭经济条件一般"
    ]
}
```

### 动作类型

**Twitter平台**

| 动作 | 说明 |
|------|------|
| CREATE_POST | 发推文 |
| LIKE_POST | 点赞 |
| REPOST | 转发 |
| QUOTE_POST | 引用转发 |
| FOLLOW | 关注 |
| DO_NOTHING | 无操作 |

**Reddit平台**

| 动作 | 说明 |
|------|------|
| CREATE_POST | 发帖 |
| CREATE_COMMENT | 评论 |
| LIKE_POST | 点赞帖子 |
| DISLIKE_POST | 踩帖子 |
| LIKE_COMMENT | 点赞评论 |
| DISLIKE_COMMENT | 踩评论 |
| SEARCH_POSTS | 搜索帖子 |
| SEARCH_USER | 搜索用户 |
| TREND | 查看趋势 |
| REFRESH | 刷新 |
| FOLLOW | 关注 |
| MUTE | 屏蔽 |
| DO_NOTHING | 无操作 |

---

## 更新日志

### v1.0.2
- 新增实时状态监控接口
- 优化Interview采访功能，支持双平台模式
- 新增批量采访接口

### v1.0.1
- 新增分章节报告输出
- 优化Token统计

### v1.0.0
- 初始版本发布
