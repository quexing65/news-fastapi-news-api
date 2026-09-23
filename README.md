# 新闻资讯平台（News Platform）

一个前后端分离的新闻资讯 App：后端基于 **FastAPI + SQLAlchemy 异步 + MySQL + Redis**，前端基于 **Vue 3 + Vant**。支持新闻分类浏览、详情阅读（浏览量统计）、用户注册登录、收藏、浏览历史，以及 AI 问答等能力。

## 技术栈

### 后端（toutiao_backend/）
| 分类 | 技术 |
|------|------|
| 语言/框架 | Python 3.13 / FastAPI / Uvicorn |
| ORM / 数据库 | SQLAlchemy 2.0（异步）+ aiomysql / MySQL |
| 缓存 | Redis 7（读写穿透缓存） |
| 消息队列 | Apache Kafka 3.9（KRaft 单节点，aiokafka 客户端） |
| 认证 | JWT + passlib(bcrypt) 密码加密 |
| 数据校验 | Pydantic v2 |
| 依赖管理 | uv（uv.lock 锁定版本） |
| 配置 | python-dotenv 读取环境变量 |

### 前端（xwzx-news/）
Vue 3 / Vite 7 / Vant 4 / Pinia（持久化）/ vue-router / vue-i18n（中英双语）/ axios / marked + DOMPurify

## 核心功能

- **新闻模块**：分类列表、分页新闻列表（`hasMore` 滚动加载）、详情（浏览量 +1）、相关新闻推荐
- **用户模块**：注册 / 登录（JWT）、个人信息查询与修改、修改密码
- **收藏模块**：收藏 / 取消收藏 / 收藏列表 / 清空
- **历史模块**：浏览历史记录 / 列表 / 单条删除 / 清空
- **AI 问答**：前端直连阿里云百炼（qwen3-max-preview），对话式新闻答疑

## 架构设计

```
Vue 3 前端  ──axios(REST /api/*)──▶  FastAPI 后端
                                        │
                      ┌─────────────────┼─────────────────┐
                      ▼                 ▼                 ▼
                  MySQL(业务数据)   Redis(缓存层)   Kafka(浏览量事件)
                                                      │
                                                      ▼
                                        view_consumer(攒批落库进程)
```

- **分层架构**：routers（路由）/ crud（数据操作）/ cache（缓存层）/ mq（消息队列）/ models（ORM）/ schemas（Pydantic 模型）六层职责分离
- **Redis 读写穿透**：对分类、列表、总数、详情、相关新闻等热点数据做缓存，浏览量落库后同步失效缓存，降低数据库压力
- **Kafka 异步浏览量**：详情接口只发浏览量事件立即返回（请求路径零数据库写入），独立消费者进程每 3 秒 / 500 条攒批落库（N 次浏览合并为一条 `views = views + N`），削平写入热点；at-least-once 语义，消息不丢
- **统一响应格式**：所有接口返回 `{code, message, data}`，注册全局异常处理器
- **鉴权依赖注入**：`get_current_user` 作为 FastAPI 依赖，保护私有接口

## 接口一览（共 18+ 个）

| 模块 | 方法 | 路径 | 说明 |
|------|------|------|------|
| News | GET | `/api/news/categories` | 新闻分类 |
| News | GET | `/api/news/list?categoryId=&page=&pageSize=` | 分页新闻列表 |
| News | GET | `/api/news/detail?id=` | 详情 + 浏览量 + 相关新闻 |
| User | POST | `/api/user/register` | 注册 |
| User | POST | `/api/user/login` | 登录（返回 Token） |
| User | GET | `/api/user/info` | 用户信息（需认证） |
| User | PUT | `/api/user/update` | 修改资料（需认证） |
| User | PUT | `/api/user/password` | 修改密码（需认证） |
| Favorite | GET/POST/DELETE | `/api/favorite/check|add|remove` | 收藏操作（需认证） |
| Favorite | GET/DELETE | `/api/favorite/list|clear` | 收藏列表 / 清空（需认证） |
| History | POST | `/api/history/add` | 新增浏览记录（需认证） |
| History | GET/DELETE | `/api/history/list|delete/{id}|clear` | 历史查询 / 删除（需认证） |

在线文档：启动后端后访问 `http://127.0.0.1:8000/docs`（Swagger）。

## 快速开始

### 环境要求
- Python 3.13+（推荐使用 [uv](https://docs.astral.sh/uv/) 管理）
- MySQL 8.x、Redis 7.x
- Kafka 3.x（Docker 一键启动，见下）

### 后端

```bash
cd toutiao_backend

# 1. 启动 Kafka（仓库根目录，单节点 KRaft）
cd .. && docker compose up -d && cd toutiao_backend

# 2. 安装依赖
uv sync

# 3. 配置数据库连接
cp .env.example .env
# 编辑 .env，填入你的 MySQL 账号密码

# 4. 初始化数据库表（models/ 下的 ORM 模型，按需执行建表）

# 5. 启动服务（默认 8000 端口）
uv run uvicorn main:app --reload --host 127.0.0.1 --port 8000

# 6. 另开终端，启动浏览量消费者（攒批落库进程）
uv run python -m mq.view_consumer
```

### 前端

```bash
cd xwzx-news
npm install
npm run dev   # 默认 5173 端口
```

## 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `ASYNC_DATABASE_URL` | MySQL 连接串 | `mysql+aiomysql://root@localhost:3306/news_app?charset=utf8mb4` |
| `KAFKA_BOOTSTRAP_SERVERS` | Kafka 连接地址 | `localhost:9092` |

前端 AI 问答需配置 `xwzx-news/.env.local` 中的 `VITE_AI_API_KEY`（阿里云百炼 Key）。

## 目录结构

```
toutiao-AI/
├── docker-compose.yml        # Kafka 单节点（KRaft）
├── toutiao_backend/          # FastAPI 后端
│   ├── main.py               # 应用入口（Kafka producer 生命周期）
│   ├── routers/              # API 路由（news/users/favorite/history）
│   ├── crud/                 # 数据操作层
│   ├── cache/                # Redis 缓存层
│   ├── mq/                   # Kafka 生产者 / 浏览量消费者
│   ├── models/               # SQLAlchemy ORM 模型
│   ├── schemas/              # Pydantic 请求/响应模型
│   ├── config/               # 数据库 / 缓存 / Kafka 配置
│   └── utils/                # JWT 认证、异常处理、统一响应
└── xwzx-news/                # Vue 3 前端
```

## License

仅供学习交流使用。
