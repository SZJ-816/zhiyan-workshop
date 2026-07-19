# 智研工坊 (WorkNest)

科技创新研发效能平台 —— 集禅道项目管理、AI 智能分析、大数据处理于一体的全栈解决方案。

## 架构概览

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│   Frontend   │────▶│   Backend    │────▶│    MySQL     │
│  (Nginx)     │     │  (FastAPI)   │     │  (业务库)    │
└─────────────┘     └──────┬───────┘     └─────────────┘
                           │
              ┌────────────┼────────────┐
              ▼            ▼            ▼
       ┌──────────┐ ┌──────────┐ ┌──────────┐
       │  Redis   │ │ OpenAI   │ │  Kafka   │
       │  (缓存)  │ │  (AI对话) │ │ (消息队列)│
       └──────────┘ └──────────┘ └────┬─────┘
                                     │
                          ┌──────────┴──────────┐
                          ▼                     ▼
                   ┌────────────┐        ┌────────────┐
                   │   Spark    │        │   Flink    │
                   │ (批处理)    │        │ (实时流)    │
                   └─────┬──────┘        └─────┬──────┘
                         ▼                     ▼
                   ┌────────────────────────────────┐
                   │       PostgreSQL (数据仓库)     │
                   └────────────────────────────────┘
```

## 核心功能

| 模块 | 功能说明 |
|------|---------|
| 项目管理 | 禅道体系 —— 产品/项目/需求/任务/Bug 全生命周期管理 |
| AI 预测 | Bug 严重度自动分类、任务工时预估、项目风险等级预测 |
| AI 对话 | 集成 OpenAI API 的智能对话助手 |
| 批处理分析 | Spark 聚合 —— 项目健康度、人员效能排名、趋势统计 |
| 实时流处理 | Flink 窗口计算 —— 任务变更统计、Bug 发现/解决速率 |
| 创新管理 | 创新评分、转化评分、趋势分析仪表盘 |
| 数据资产 | 数据资产全生命周期管理 |
| 服务监控 | 一键面板监控所有微服务运行状态 |

## 技术栈

| 层次 | 技术 |
|------|------|
| 前端 | HTML5 + CSS3 + JavaScript（亮暗主题、响应式） |
| 后端 | Python 3.12 / FastAPI / Uvicorn / SQLAlchemy |
| 认证 | JWT (python-jose) / bcrypt |
| 数据库 | MySQL 8.0（业务库）、PostgreSQL 16（数据仓库） |
| 缓存 | Redis 7 |
| 消息队列 | Apache Kafka 3.7（KRaft 模式） |
| AI/ML | scikit-learn / OpenAI API / TF-IDF / RandomForest / GradientBoosting |
| 大数据 | Apache Spark 3.5（批处理）、Apache Flink 1.18（实时流） |
| 部署 | Docker Compose / Nginx 反向代理 |

## 项目结构

```
zhiyan-workshop/
├── frontend/                # 前端静态页面
│   ├── index.html           # 主工作台仪表盘
│   ├── launcher.html        # 服务管理启动面板
│   ├── innovation-lab.html  # 创新实验室
│   ├── ai-analytics.html    # AI 数据分析
│   ├── ai-chat.html         # AI 智能对话
│   ├── ai-prediction.html   # AI 预测分析
│   ├── ai-datamanage.html   # AI 数据管理
│   ├── ai-realtime.html     # AI 实时监控
│   ├── css/                 # 样式文件
│   └── js/                  # 脚本文件
├── backend/                 # FastAPI 后端
│   ├── requirements.txt     # Python 依赖
│   └── app/
│       ├── main.py          # 应用入口
│       ├── core/            # 配置与数据库
│       ├── models/          # SQLAlchemy ORM 模型
│       ├── schemas/         # Pydantic 请求/响应模型
│       ├── services/        # 业务服务层
│       └── api/routers/     # API 路由
├── ai_model/                # AI 模型
│   ├── training/            # 模型训练（Bug严重度/工时预估/风险预测）
│   └── inference/           # 模型推理服务
├── bigdata/                 # 大数据处理
│   ├── kafka/               # Kafka 生产者与消费管道
│   ├── spark/               # Spark 批处理分析
│   └── flink/               # Flink 实时流处理
└── deploy/                  # 部署配置
    ├── Dockerfile
    ├── docker-compose.yml
    └── nginx.conf
```

## 快速开始

### 环境要求

- Docker & Docker Compose
- Git

### 一键部署

```bash
git clone https://github.com/SZJ-816/zhiyan-workshop.git
cd zhiyan-workshop
cd deploy && docker-compose up -d
```

启动后 9 个容器将自动拉取并编排：

| 服务 | 容器名 | 端口 |
|------|--------|------|
| Nginx | zentao-nginx | 80 |
| FastAPI | zentao-fastapi | 8000 |
| MySQL | zentao-mysql | 3306 |
| PostgreSQL | ai_platform_postgres | 5432 |
| Redis | ai_platform_redis | 6379 |
| Kafka | ai_platform_kafka | 9092 |
| Spark Master | ai_platform_spark_master | 8080/7077 |
| Spark Worker | ai_platform_spark_worker | 8081 |
| Flink JM | ai_platform_flink_jobmanager | 8083 |

浏览器访问 `http://localhost` 即可使用。

### 数据初始化

```bash
# 后端启动后自动执行 seed
curl http://localhost/api/init/seed
```

### AI 模型训练

```bash
cd ai_model/training
pip install -r ../../backend/requirements.txt
python train_zentao_model.py
```

训练产物保存至 `/app/ai_models/`，推理服务自动加载。

### Spark 批处理

```bash
cd bigdata/spark
spark-submit --master spark://localhost:7077 zentao_batch.py
```

### Flink 实时流

```bash
cd bigdata/flink
flink run -py zentao_stream.py
```

## AI 预测模型

| 模型 | 算法 | 输入 | 输出 |
|------|------|------|------|
| Bug 严重度分类 | TF-IDF + RandomForest | Bug 标题文本 | fatal/serious/normal/minor/suggestion |
| 任务工时预估 | 多特征 + GradientBoosting | 预估工时/优先级/项目/负责人 | 预测耗时 + 置信区间 |
| 项目风险预测 | 聚合特征 + RandomForest | 任务完成率/Bug解决率/进度偏离 | 风险等级 + 健康评分 |

## License

MIT
