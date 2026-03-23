# MiroFish 前端开发接口文档

> 后端地址: `http://localhost:5001`
> 版本: v1.0.2

---

## 目录

1. [开发优先级建议](#开发优先级建议)
2. [通用响应格式](#通用响应格式)
3. [Graph 图谱模块](#graph-图谱模块)
4. [Simulation 模拟模块](#simulation-模拟模块)
5. [Report 报告模块](#report-报告模块)

---

## 开发优先级建议

### 第一阶段：核心流程（必须完成）

| 优先级 | 接口 | 用途 | 对应页面 |
|--------|------|------|----------|
| P0 | `POST /api/graph/ontology/generate` | 上传文档生成本体 | Step1 页面 |
| P0 | `POST /api/graph/build` | 启动图谱构建 | Step1 页面 |
| P0 | `GET /api/graph/task/{task_id}` | 查询图谱构建进度 | Step1 页面 |
| P0 | `POST /api/simulation/create` | 创建模拟 | Step2 页面 |
| P0 | `POST /api/simulation/prepare` | 准备模拟环境 | Step2 页面 |
| P0 | `POST /api/simulation/prepare/status` | 查询准备进度 | Step2 页面 |
| P0 | `POST /api/simulation/start` | 启动模拟 | Step3 页面 |
| P0 | `GET /api/simulation/{id}/run-status` | 获取运行状态 | Step3 页面 |
| P0 | `POST /api/simulation/stop` | 停止模拟 | Step3 页面 |

### 第二阶段：报告与交互

| 优先级 | 接口 | 用途 | 对应页面 |
|--------|------|------|----------|
| P1 | `POST /api/report/generate` | 生成报告 | Step4 页面 |
| P1 | `POST /api/report/generate/status` | 查询报告生成进度 | Step4 页面 |
| P1 | `GET /api/report/{id}` | 获取报告详情 | Step4 页面 |
| P1 | `GET /api/report/{id}/sections` | 获取报告章节（实时） | Step4 页面 |
| P1 | `POST /api/report/chat` | 与报告对话 | Interaction 页面 |

### 第三阶段：首页与历史

| 优先级 | 接口 | 用途 | 对应页面 |
|--------|------|------|----------|
| P2 | `GET /api/simulation/history` | 获取历史模拟列表 | 首页 |
| P2 | `GET /api/graph/project/list` | 获取项目列表 | 首页 |
| P2 | `GET /api/graph/project/{id}` | 获取项目详情 | 项目详情 |

### 第四阶段：高级功能

| 优先级 | 接口 | 用途 | 对应页面 |
|--------|------|------|----------|
| P3 | `POST /api/simulation/interview` | 采访Agent | Step3/报告页面 |
| P3 | `GET /api/simulation/{id}/posts` | 获取模拟帖子 | Step3 页面 |
| P3 | `GET /api/simulation/{id}/actions` | 获取Agent动作 | Step3 页面 |
| P3 | `GET /api/report/{id}/download` | 下载报告 | 报告页面 |

---

## 通用响应格式

### 成功响应
```json
{
  "success": true,
  "data": { ... }
}
```

### 错误响应
```json
{
  "success": false,
  "error": "错误描述",
  "traceback": "详细堆栈信息（仅DEBUG模式）"
}
```

---

## Graph 图谱模块

### 1. 上传文件并生成本体

```
POST /api/graph/ontology/generate
Content-Type: multipart/form-data
```

**请求参数:**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| files | File[] | ✅ | 上传的文件（PDF/MD/TXT），可多个 |
| simulation_requirement | string | ✅ | 模拟需求描述 |
| project_name | string | ❌ | 项目名称，默认 "Unnamed Project" |
| additional_context | string | ❌ | 额外说明信息 |

**响应:**
```json
{
  "success": true,
  "data": {
    "project_id": "proj_xxxx",
    "project_name": "武大学费舆情分析",
    "ontology": {
      "entity_types": [
        {"name": "Student", "description": "在校学生"},
        {"name": "Professor", "description": "教授"}
      ],
      "edge_types": [
        {"name": "STUDY_AT", "description": "就读于"},
        {"name": "WORK_AT", "description": "工作于"}
      ]
    },
    "analysis_summary": "文档分析摘要...",
    "files": [{"filename": "event.pdf", "size": 1024000}],
    "total_text_length": 15000
  }
}
```

**前端调用示例:**
```javascript
const formData = new FormData();
files.forEach(file => formData.append('files', file));
formData.append('simulation_requirement', '如果武汉大学发布学费调整通知...');
formData.append('project_name', '武大学费舆情分析');

const res = await fetch('/api/graph/ontology/generate', {
  method: 'POST',
  body: formData
});
```

---

### 2. 构建知识图谱

```
POST /api/graph/build
Content-Type: application/json
```

**请求参数:**

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| project_id | string | ✅ | - | 项目ID |
| graph_name | string | ❌ | 项目名称 | 图谱名称 |
| chunk_size | int | ❌ | 500 | 文本分块大小 |
| chunk_overlap | int | ❌ | 50 | 分块重叠大小 |
| force | boolean | ❌ | false | 强制重新构建 |

**请求示例:**
```json
{
  "project_id": "proj_abc123",
  "graph_name": "武大学费舆情图谱",
  "chunk_size": 500,
  "chunk_overlap": 50
}
```

**响应:**
```json
{
  "success": true,
  "data": {
    "project_id": "proj_abc123",
    "task_id": "task_xyz789",
    "message": "图谱构建任务已启动"
  }
}
```

---

### 3. 查询任务状态

```
GET /api/graph/task/{task_id}
```

**响应:**
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
    "result": null,
    "error": null
  }
}
```

**任务状态:**
- `pending` - 等待中
- `processing` - 处理中
- `completed` - 已完成
- `failed` - 失败

---

### 4. 获取图谱数据

```
GET /api/graph/data/{graph_id}
```

**响应:**
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

### 5. 项目管理

#### 获取项目列表
```
GET /api/graph/project/list?limit=50
```

#### 获取项目详情
```
GET /api/graph/project/{project_id}
```

#### 删除项目
```
DELETE /api/graph/project/{project_id}
```

#### 重置项目状态
```
POST /api/graph/project/{project_id}/reset
```

---

## Simulation 模拟模块

### 1. 获取图谱实体

```
GET /api/simulation/entities/{graph_id}?entity_types=Student,Professor&enrich=true
```

**Query参数:**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| entity_types | string | ❌ | 逗号分隔的实体类型列表 |
| enrich | boolean | ❌ | 是否获取相关边信息，默认true |

---

### 2. 创建模拟

```
POST /api/simulation/create
Content-Type: application/json
```

**请求参数:**

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| project_id | string | ✅ | - | 项目ID |
| graph_id | string | ❌ | 项目graph_id | 图谱ID |
| enable_twitter | boolean | ❌ | true | 启用Twitter模拟 |
| enable_reddit | boolean | ❌ | true | 启用Reddit模拟 |

**响应:**
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
    "created_at": "2024-12-10T11:00:00"
  }
}
```

---

### 3. 准备模拟环境（异步）

```
POST /api/simulation/prepare
Content-Type: application/json
```

**请求参数:**

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| simulation_id | string | ✅ | - | 模拟ID |
| entity_types | string[] | ❌ | 全部 | 指定实体类型过滤 |
| use_llm_for_profiles | boolean | ❌ | true | 使用LLM生成Agent人设 |
| parallel_profile_count | int | ❌ | 5 | 并行生成人设数量 |
| force_regenerate | boolean | ❌ | false | 强制重新生成 |

**响应（首次准备）:**
```json
{
  "success": true,
  "data": {
    "simulation_id": "sim_def456",
    "task_id": "task_prep001",
    "status": "preparing",
    "message": "准备任务已启动",
    "already_prepared": false,
    "expected_entities_count": 68,
    "entity_types": ["Student", "Professor"]
  }
}
```

**响应（已准备完成）:**
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
      "entity_types": ["Student", "Professor"]
    }
  }
}
```

---

### 4. 查询准备进度

```
POST /api/simulation/prepare/status
Content-Type: application/json
```

**请求参数:**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| task_id | string | ❌ | 任务ID |
| simulation_id | string | ❌ | 模拟ID |

> 至少提供其中一个参数

**响应:**
```json
{
  "success": true,
  "data": {
    "task_id": "task_prep001",
    "status": "processing",
    "progress": 35,
    "message": "[1/4] 生成Agent人设: 24/68 - 正在生成...",
    "progress_detail": {
      "current_stage": "generating_profiles",
      "current_stage_name": "生成Agent人设",
      "stage_index": 1,
      "total_stages": 4,
      "stage_progress": 35,
      "current_item": 24,
      "total_items": 68
    }
  }
}
```

---

### 5. 实时获取Agent配置

```
GET /api/simulation/{simulation_id}/profiles/realtime?platform=reddit
```

**响应:**
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
        "description": "武汉大学大三学生...",
        "traits": ["理性", "关注教育公平"],
        "memories": [...]
      }
    ]
  }
}
```

---

### 6. 实时获取模拟配置

```
GET /api/simulation/{simulation_id}/config/realtime
```

**响应:**
```json
{
  "success": true,
  "data": {
    "simulation_id": "sim_def456",
    "file_exists": true,
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

### 7. 启动模拟运行

```
POST /api/simulation/start
Content-Type: application/json
```

**请求参数:**

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| simulation_id | string | ✅ | - | 模拟ID |
| platform | string | ❌ | "parallel" | 平台: twitter/reddit/parallel |
| max_rounds | int | ❌ | 自动计算 | 最大模拟轮数 |
| enable_graph_memory_update | boolean | ❌ | false | 启用图谱记忆更新 |
| force | boolean | ❌ | false | 强制重新开始 |

**响应:**
```json
{
  "success": true,
  "data": {
    "simulation_id": "sim_def456",
    "runner_status": "running",
    "process_pid": 12345,
    "twitter_running": true,
    "reddit_running": true,
    "started_at": "2025-12-01T10:00:00"
  }
}
```

---

### 8. 获取运行状态

```
GET /api/simulation/{simulation_id}/run-status
```

**响应:**
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

### 9. 获取详细运行状态

```
GET /api/simulation/{simulation_id}/run-status/detail?platform=twitter
```

**响应:**
```json
{
  "success": true,
  "data": {
    "simulation_id": "sim_def456",
    "runner_status": "running",
    "current_round": 45,
    "all_actions": [
      {
        "round_num": 45,
        "timestamp": "2024-12-10T14:30:00",
        "platform": "twitter",
        "agent_id": 3,
        "agent_name": "张同学",
        "action_type": "CREATE_POST",
        "action_args": {"content": "关于学费调整..."},
        "success": true
      }
    ],
    "twitter_actions": [...],
    "reddit_actions": [...],
    "recent_actions": [...]
  }
}
```

---

### 10. 停止模拟

```
POST /api/simulation/stop
Content-Type: application/json
```

**请求:**
```json
{"simulation_id": "sim_def456"}
```

---

### 11. 获取模拟帖子

```
GET /api/simulation/{simulation_id}/posts?platform=reddit&limit=50&offset=0
```

**响应:**
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

### 12. 采访Agent

```
POST /api/simulation/interview
Content-Type: application/json
```

**请求参数:**

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| simulation_id | string | ✅ | - | 模拟ID |
| agent_id | int | ✅ | - | Agent ID |
| prompt | string | ✅ | - | 采访问题 |
| platform | string | ❌ | 双平台 | 指定平台 |
| timeout | int | ❌ | 60 | 超时时间（秒） |

**响应（指定平台）:**
```json
{
  "success": true,
  "data": {
    "agent_id": 0,
    "prompt": "你对这次学费调整有什么看法？",
    "result": {
      "agent_id": 0,
      "response": "作为一名学生...",
      "platform": "twitter",
      "timestamp": "2024-12-10T15:00:00"
    }
  }
}
```

**响应（双平台模式）:**
```json
{
  "success": true,
  "data": {
    "agent_id": 0,
    "result": {
      "platforms": {
        "twitter": {"response": "在Twitter上我会..."},
        "reddit": {"response": "在Reddit上我会详细分析..."}
      }
    }
  }
}
```

---

### 13. 批量采访Agent

```
POST /api/simulation/interview/batch
Content-Type: application/json
```

**请求:**
```json
{
  "simulation_id": "sim_def456",
  "interviews": [
    {"agent_id": 0, "prompt": "你的看法？", "platform": "twitter"},
    {"agent_id": 1, "prompt": "你的建议？"}
  ],
  "platform": "reddit",
  "timeout": 120
}
```

---

### 14. 获取历史模拟列表

```
GET /api/simulation/history?limit=20
```

**响应:**
```json
{
  "success": true,
  "data": [
    {
      "simulation_id": "sim_abc123",
      "project_id": "proj_xyz789",
      "project_name": "武大舆情分析",
      "simulation_requirement": "如果武汉大学发布...",
      "status": "completed",
      "entities_count": 68,
      "profiles_count": 68,
      "entity_types": ["Student", "Professor"],
      "created_at": "2024-12-10T14:30:00",
      "total_rounds": 120,
      "current_round": 120,
      "runner_status": "completed",
      "report_id": "report_def456",
      "files": [{"filename": "event_description.pdf"}]
    }
  ],
  "count": 1
}
```

---

## Report 报告模块

### 1. 生成报告（异步）

```
POST /api/report/generate
Content-Type: application/json
```

**请求:**
```json
{
  "simulation_id": "sim_def456",
  "force_regenerate": false
}
```

**响应:**
```json
{
  "success": true,
  "data": {
    "simulation_id": "sim_def456",
    "report_id": "report_abc123",
    "task_id": "task_report001",
    "status": "generating",
    "message": "报告生成任务已启动",
    "already_generated": false
  }
}
```

---

### 2. 查询报告生成进度

```
POST /api/report/generate/status
Content-Type: application/json
```

**请求:**
```json
{
  "task_id": "task_report001",
  "simulation_id": "sim_def456"
}
```

**响应:**
```json
{
  "success": true,
  "data": {
    "task_id": "task_report001",
    "status": "processing",
    "progress": 35,
    "message": "[关键发现] 正在分析数据..."
  }
}
```

---

### 3. 获取报告详情

```
GET /api/report/{report_id}
```

**响应:**
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
        {"title": "关键发现", "status": "completed"}
      ]
    },
    "markdown_content": "# 舆情模拟分析报告\n\n## 执行摘要\n\n...",
    "created_at": "2024-12-10T15:00:00",
    "completed_at": "2024-12-10T15:30:00"
  }
}
```

---

### 4. 根据模拟ID获取报告

```
GET /api/report/by-simulation/{simulation_id}
```

---

### 5. 获取报告章节列表（实时）

```
GET /api/report/{report_id}/sections
```

**响应:**
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
      }
    ],
    "total_sections": 2,
    "is_complete": false
  }
}
```

---

### 6. 下载报告

```
GET /api/report/{report_id}/download
```

返回 Markdown 文件下载。

---

### 7. 与报告Agent对话

```
POST /api/report/chat
Content-Type: application/json
```

**请求:**
```json
{
  "simulation_id": "sim_def456",
  "message": "请解释一下舆情走向的主要影响因素",
  "chat_history": [
    {"role": "user", "content": "..."},
    {"role": "assistant", "content": "..."}
  ]
}
```

**响应:**
```json
{
  "success": true,
  "data": {
    "response": "根据模拟数据分析...",
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

### 8. Token统计

#### 获取统计
```
GET /api/report/token-stats
```

#### 重置统计
```
POST /api/report/token-stats/reset
```

---

## 状态说明

### 项目状态流转
```
created → ontology_generated → graph_building → graph_completed → failed
```

### 模拟状态流转
```
created → preparing → ready → running → completed/stopped/failed
```

### Runner状态
- `idle` - 空闲
- `running` - 运行中
- `paused` - 已暂停
- `completed` - 已完成
- `stopped` - 已停止

### 报告状态
- `generating` - 生成中
- `completed` - 已完成
- `failed` - 失败

---

## 前端轮询建议

| 场景 | 接口 | 建议轮询间隔 |
|------|------|--------------|
| 图谱构建进度 | `GET /api/graph/task/{task_id}` | 2秒 |
| 模拟准备进度 | `POST /api/simulation/prepare/status` | 2秒 |
| 模拟运行状态 | `GET /api/simulation/{id}/run-status` | 1秒 |
| 报告生成进度 | `POST /api/report/generate/status` | 3秒 |
| 报告章节实时更新 | `GET /api/report/{id}/sections` | 2秒 |
| Agent配置实时查看 | `GET /api/simulation/{id}/profiles/realtime` | 3秒 |

---

## 错误码

| 状态码 | 说明 |
|--------|------|
| 200 | 成功 |
| 400 | 请求参数错误 |
| 404 | 资源不存在 |
| 500 | 服务器内部错误 |
| 504 | 网关超时（Interview超时） |
