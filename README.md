# 舆情态势感知与推演干预平台

<p align="center">
  <strong>基于 LLM-Agent 的智能舆情模拟与决策支持系统</strong>
</p>

<p align="center">
  <a href="#功能特性">功能特性</a> •
  <a href="#系统架构">系统架构</a> •
  <a href="#快速开始">快速开始</a> •
  <a href="#使用指南">使用指南</a> •
  <a href="#技术栈">技术栈</a>
</p>

---

## 📋 项目简介

本平台是一款面向舆情分析领域的智能推演系统，深度融合大语言模型（LLM）与多智能体（Multi-Agent）技术，构建从**知识图谱构建**、**智能体建模**、**舆情推演**到**干预决策**的全链路解决方案。

平台基于现实数据种子，通过 GraphRAG 技术构建领域知识图谱，利用 OASIS 框架模拟真实社交媒体环境中的多主体交互行为，并结合 LLM 的推理能力实现舆情态势的智能预测与干预策略生成。

---

## ✨ 功能特性

### 1️⃣ 知识图谱智能构建（Step1）
- **本体自动生成**：LLM 自动分析文档内容，提取现实种子，生成领域本体结构
- **GraphRAG 构建**：基于 Zep Cloud 构建时序知识图谱，支持社区摘要与实体关系抽取
- **实体关系可视化**：交互式图谱展示，支持节点详情查看与关系探索

### 2️⃣ 智能体建模与环境配置（Step2）
- **Agent 人设生成**：基于知识图谱自动初始化模拟个体，赋予独特行为模式与记忆系统
- **平台参数配置**：智能配置时间流速、内容分发机制、用户活跃时段等环境参数
- **事件编排设计**：基于叙事方向生成初始激活事件与热点话题

### 3️⃣ 多平台舆情模拟（Step3）
- **国内平台支持**：微博、B站、抖音、小红书、知乎等主流社交媒体环境模拟
- **实时交互推演**：基于 OASIS 框架的多 Agent 并发交互，模拟真实舆论演化
- **传播路径追踪**：可视化展示信息传播网络与关键节点影响

### 4️⃣ 智能报告生成（Step4）
- **舆情分析报告**：自动总结模拟过程中的关键事件、传播规律与风险预警
- **可视化图表**：热度趋势、情绪分布、传播网络等多维度数据展示
- **PDF 导出**：支持生成专业格式的分析报告文档

### 5️⃣ 态势预测与干预推演（Step5）
- **多策略推演**：官方声明、KOL引导、数据披露、精准回应、冷处理、话题转移等干预策略对比
- **干预时机热力图**：可视化展示不同策略在不同时机的效果评分
- **反事实推演引擎**：动态调整干预策略，观察舆情演变的"假设-验证"分析
- **AI 智能助手**：支持自然语言交互，解答舆情分析与策略选择问题

---

## 🏗️ 系统架构

```
┌─────────────────────────────────────────────────────────────────┐
│                        前端层 (Vue 3)                            │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌────────┐ │
│  │ Step1    │ │ Step2    │ │ Step3    │ │ Step4    │ │ Step5  │ │
│  │ 图谱构建 │ │ 环境配置 │ │ 模拟运行 │ │ 报告生成 │ │ 预测推演│ │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └────────┘ │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                        后端层 (Flask)                            │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐             │
│  │ Graph Builder│ │ Sim Manager  │ │ Intervention │             │
│  │ 知识图谱构建 │ │ 模拟管理     │ │ 干预策略引擎 │             │
│  └──────────────┘ └──────────────┘ └──────────────┘             │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐             │
│  │ Ontology Gen │ │ OASIS Runner │ │ Prediction   │             │
│  │ 本体生成     │ │ 模拟运行器   │ │ 预测服务     │             │
│  └──────────────┘ └──────────────┘ └──────────────┘             │
└─────────────────────────────────────────────────────────────────┘
                              │
              ┌───────────────┼───────────────┐
              ▼               ▼               ▼
        ┌──────────┐    ┌──────────┐    ┌──────────┐
        │ LLM 服务 │    │ Zep Cloud│    │ OASIS    │
        │ OpenAI   │    │ 知识图谱 │    │ 模拟框架 │
        └──────────┘    └──────────┘    └──────────┘
```

---

## 🚀 快速开始

### 环境要求

- **Python**: 3.11+
- **Node.js**: 18+
- **Docker & Docker Compose** (可选)

### 1. 克隆仓库

```bash
git clone https://github.com/your-username/inference.git
cd inference
```

### 2. 环境配置

复制环境变量示例文件并配置：

```bash
cp .env.example .env
```

编辑 `.env` 文件，配置以下关键参数：

```env
# LLM 配置
LLM_API_KEY=your_openai_api_key
LLM_BASE_URL=https://api.openai.com/v1
LLM_MODEL=gpt-4o

# Zep Cloud 配置
ZEP_API_KEY=your_zep_api_key

# Tavily 搜索配置
TAVILY_API_KEY=your_tavily_api_key

# Redis 配置（可选）
REDIS_URL=redis://localhost:6379/0
```

### 3. 本地开发模式

#### 后端启动

```bash
cd backend
pip install -r requirements.txt
python run.py
```

后端服务将运行在 `http://localhost:5001`

#### 前端启动

```bash
cd frontend
npm install
npm run dev
```

前端开发服务器将运行在 `http://localhost:5173`

### 4. Docker 部署

```bash
docker-compose up -d
```

---

## 📖 使用指南

### 完整工作流程

#### Step 1: 知识图谱构建
1. 上传背景文档（支持 PDF、TXT、Word 等格式）
2. 输入模拟需求描述
3. 系统自动生成本体结构并构建知识图谱
4. 查看实体类型、关系类型与图谱统计

#### Step 2: 模拟环境配置
1. **Agent 人设生成**：基于知识图谱自动创建模拟个体
2. **平台参数配置**：配置内容分发机制、用户活跃模式等
3. **事件编排设计**：设置初始话题与激活序列

#### Step 3: 舆情模拟运行
1. 启动多 Agent 并发模拟
2. 实时观察舆情演化过程
3. 追踪传播路径与关键节点

#### Step 4: 报告生成
1. 自动生成舆情分析报告
2. 查看热度趋势、情绪分布等可视化图表
3. 导出 PDF 格式报告

#### Step 5: 预测与干预推演
1. 查看多策略对比分析
2. 使用干预时机热力图识别最佳窗口
3. 通过反事实推演验证策略效果
4. 咨询 AI 助手获取决策建议

---

## 🛠️ 技术栈

### 前端
- **Vue 3** + **Composition API**：现代化响应式框架
- **Vite**：极速构建工具
- **D3.js**：数据可视化与图谱绘制
- **Vue Router**：单页应用路由管理
- **Marked**：Markdown 渲染

### 后端
- **Flask**：轻量级 Web 框架
- **OpenAI SDK**：统一 LLM 调用接口
- **Zep Cloud**：GraphRAG 知识图谱服务
- **OASIS**：社交媒体多 Agent 模拟框架
- **CAMEL-AI**：智能体框架支持
- **Tavily**：智能搜索服务
- **ReportLab / python-docx**：报告生成

### 基础设施
- **Redis**：高速缓存与会话管理
- **Docker**：容器化部署
- **Nginx**：静态资源服务与反向代理

---

## 📁 项目结构

```
inference/
├── backend/                    # 后端服务
│   ├── app/
│   │   ├── api/               # RESTful API 路由
│   │   ├── models/            # 数据模型
│   │   ├── services/          # 业务逻辑服务
│   │   │   ├── social_plugins/    # 社交媒体平台插件
│   │   │   ├── intervention_sandbox.py  # 干预策略引擎
│   │   │   ├── prediction_agent.py      # 预测服务
│   │   │   └── simulation_runner.py     # 模拟运行器
│   │   └── utils/             # 工具函数
│   ├── scripts/               # 独立脚本
│   ├── requirements.txt       # Python 依赖
│   └── run.py                 # 启动入口
│
├── frontend/                   # 前端应用
│   ├── src/
│   │   ├── components/        # Vue 组件
│   │   │   ├── Step1GraphBuild.vue
│   │   │   ├── Step2EnvSetup.vue
│   │   │   ├── Step3Simulation.vue
│   │   │   ├── Step4Report.vue
│   │   │   └── Step5Prediction.vue
│   │   ├── views/             # 页面视图
│   │   ├── api/               # API 接口封装
│   │   └── router/            # 路由配置
│   ├── package.json
│   └── vite.config.js
│
├── docker-compose.yml         # Docker 编排配置
├── Dockerfile.backend         # 后端镜像
├── Dockerfile.frontend        # 前端镜像
└── README.md                  # 项目说明
```

---

## 🔧 配置说明

### 核心环境变量

| 变量名 | 说明 | 必需 |
|--------|------|------|
| `LLM_API_KEY` | LLM 服务 API 密钥 | ✅ |
| `LLM_BASE_URL` | LLM 服务基础 URL | ✅ |
| `LLM_MODEL` | 使用的大模型名称 | ✅ |
| `ZEP_API_KEY` | Zep Cloud API 密钥 | ✅ |
| `TAVILY_API_KEY` | Tavily 搜索 API 密钥 | ✅ |
| `REDIS_URL` | Redis 连接地址 | ❌ |

### 模拟参数配置

可通过后端服务的 API 接口动态配置模拟参数：

- **时间配置**：模拟总时长、每轮分钟数
- **内容分发机制**：时效权重、热度权重、相关性权重
- **Agent 参数**：活跃时段、发言频率、影响力权重

---

## 🤝 贡献指南

欢迎提交 Issue 和 Pull Request！

1. Fork 本仓库
2. 创建您的特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交您的更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开一个 Pull Request

---

## 📄 许可证

本项目基于 [MIT License](LICENSE) 开源协议。

---

## 🙏 致谢

- [OASIS](https://github.com/camel-ai/oasis) - 社交媒体模拟框架
- [Zep](https://www.getzep.com/) - GraphRAG 知识图谱服务
- [CAMEL](https://github.com/camel-ai/camel) - 智能体框架

---

<p align="center">
  Made with ❤️ for better public opinion analysis
</p>
