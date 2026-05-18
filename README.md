# 智能任务拆解Agent系统

面向个人用户的智能目标拆解与任务自动化Agent系统。支持用户输入任意模糊大目标，通过AI Agent自动拆解为多级结构化子任务，生成优先级、时间规划、执行步骤，配套工具调用、进度管理、任务状态流转、定时提醒功能。

## 项目定位

轻量化企业级Agent任务编排落地项目，专注于：
- 🎯 **模糊目标结构化**：任意自然语言输入 → 三级任务拆解
- 🤖 **AI Agent驱动**：支持DeepSeek/通义千问/Claude自由切换
- 📊 **全生命周期管理**：创建→执行→复盘→统计
- 🔧 **内置工具库**：6种专业模板即调即用

## 技术栈

| 组件          | 技术选型                                        |
| ------------- | ----------------------------------------------- |
| 语言          | Python 3.10+                                    |
| Web框架       | FastAPI                                         |
| ORM           | SQLAlchemy 2.0                                  |
| 数据校验      | Pydantic v2                                     |
| 数据库        | MySQL 8.0                                       |
| 缓存          | Redis 7                                         |
| 定时任务      | APScheduler                                     |
| AI接口        | OpenAI兼容接口（DeepSeek/通义千问/Claude）       |
| 认证          | JWT + bcrypt                                    |

---

## 快速启动

### 方式一：Docker Compose（推荐）

```bash
# 1. 克隆项目并进入目录
cd task-agent-system

# 2. 修改环境变量配置
# 编辑 .env 文件，填入你的 LLM_API_KEY

# 3. 启动所有服务
docker-compose up -d

# 4. 初始化工具库
curl -X POST http://localhost:8000/api/v1/agent/tools/seed

# 5. 访问 API 文档
# http://localhost:8000/docs
```

### 方式二：手动部署

```bash
# 1. 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 2. 安装依赖
pip install -r requirements.txt

# 3. 确保 MySQL 和 Redis 已启动
# 4. 修改 .env 中的数据库连接信息

# 5. 启动服务
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# 6. 初始化工具库
curl -X POST http://localhost:8000/api/v1/agent/tools/seed
```

---

## 环境变量说明（.env）

```ini
# 应用配置
APP_NAME=TaskAgentSystem
APP_VERSION=1.0.0
DEBUG=false
HOST=0.0.0.0
PORT=8000

# MySQL 配置
MYSQL_HOST=127.0.0.1
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=your_password
MYSQL_DATABASE=task_agent_db

# Redis 配置
REDIS_HOST=127.0.0.1
REDIS_PORT=6379
REDIS_PASSWORD=
REDIS_DB=0

# JWT 配置（生产环境请更换密钥）
JWT_SECRET_KEY=your-secret-key
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=1440

# 大模型 API 配置
# DeepSeek:    base_url=https://api.deepseek.com/v1, model=deepseek-chat
# 通义千问:    base_url=https://dashscope.aliyuncs.com/compatible-mode/v1, model=qwen-plus
# Claude(代理): base_url=<代理地址>, model=claude-sonnet-4-20250514
LLM_API_KEY=sk-your-api-key
LLM_BASE_URL=https://api.deepseek.com/v1
LLM_MODEL_NAME=deepseek-chat
```

---

## API 接口文档

所有接口统一返回格式：
```json
{
  "code": 200,
  "msg": "操作成功",
  "data": { ... },
  "timestamp": 1702800000000
}
```

### 一、用户模块

#### 1.1 用户注册
- **POST** `/api/v1/user/register`
- **请求体：**
```json
{
  "username": "testuser",       // 必填，2-64字符
  "password": "123456",         // 必填，6-128字符
  "email": "user@example.com"  // 可选
}
```

#### 1.2 用户登录
- **POST** `/api/v1/user/login`
- **请求体：**
```json
{
  "username": "testuser",
  "password": "123456"
}
```
- **响应：** 返回 access_token，后续接口在 Header 中携带 `Authorization: Bearer <token>`

#### 1.3 获取用户信息
- **GET** `/api/v1/user/info`
- **Headers:** `Authorization: Bearer <token>`

#### 1.4 更新用户信息
- **PUT** `/api/v1/user/info`
- **Headers:** `Authorization: Bearer <token>`
- **请求体：** (`password`/`email` 可选)
```json
{
  "email": "new@example.com",
  "password": "newpassword123"
}
```

#### 1.5 校验登录态
- **POST** `/api/v1/user/check-login`
- **Headers:** `Authorization: Bearer <token>`

### 二、Agent 智能拆解（核心模块）

#### 2.1 AI拆解目标 ⭐
- **POST** `/api/v1/agent/decompose`
- **Headers:** `Authorization: Bearer <token>`
- **请求体：**
```json
{
  "goal_title": "2024年12月通过PMP考试",
  "goal_description": "我已经报名了PMP考试，目前的基础是项目管理入门水平，每天可以投入2小时学习",
  "goal_type": "备考",
  "deadline": "2024-12-31"
}
```
- **功能：** Agent自动拆解为三级任务树，含优先级、预估耗时、推荐工具

#### 2.2 与Agent对话
- **POST** `/api/v1/agent/chat`
- **Headers:** `Authorization: Bearer <token>`
- **请求体：**
```json
{
  "goal_id": 1,
  "user_message": "第一个主任务我觉得时间太紧了，能帮我重新规划一下吗？"
}
```

#### 2.3 获取工具列表
- **GET** `/api/v1/agent/tools`
- **Headers:** `Authorization: Bearer <token>`

#### 2.4 调用工具
- **POST** `/api/v1/agent/tool/call`
- **Headers:** `Authorization: Bearer <token>`
- **请求体：**
```json
{
  "tool_id": 1,
  "task_id": 1,
  "params": {
    "content": "项目管理知识体系"
  }
}
```

#### 2.5 初始化种子工具
- **POST** `/api/v1/agent/tools/seed`
- **Headers:** `Authorization: Bearer <token>`

### 三、任务管理

#### 3.1 创建总目标
- **POST** `/api/v1/task/goal`

#### 3.2 获取目标列表
- **GET** `/api/v1/task/goal/list?page=1&page_size=20`

#### 3.3 获取目标详情
- **GET** `/api/v1/task/goal/{goal_id}`

#### 3.4 更新目标
- **PUT** `/api/v1/task/goal/{goal_id}`

#### 3.5 删除目标
- **DELETE** `/api/v1/task/goal/{goal_id}`

#### 3.6 创建子任务
- **POST** `/api/v1/task/item`

#### 3.7 获取任务树
- **GET** `/api/v1/task/item/list/{goal_id}`

#### 3.8 更新子任务
- **PUT** `/api/v1/task/item/{task_id}`
- **支持状态变更：** 0待执行 → 1进行中 → 2已完成 / 3延期 / 4作废

#### 3.9 删除子任务
- **DELETE** `/api/v1/task/item/{task_id}`

#### 3.10 批量修改任务状态
- **PUT** `/api/v1/task/item/batch-status`
```json
{
  "task_ids": [1, 2, 3],
  "status": 2
}
```

#### 3.11 获取任务日志
- **GET** `/api/v1/task/log/{task_id}`

### 四、数据统计

#### 4.1 任务统计概览
- **GET** `/api/v1/stats/summary`

#### 4.2 月度统计
- **GET** `/api/v1/stats/monthly?months=6`

#### 4.3 目标类型分布
- **GET** `/api/v1/stats/goal-distribution`

#### 4.4 完整统计
- **GET** `/api/v1/stats/full`

### 五、系统

#### 5.1 健康检查
- **GET** `/health`

#### 5.2 根路径
- **GET** `/`

---

## 项目结构

```
project_root/
├── app/
│   ├── api/v1/          # 路由接口（user/task/agent/stats）
│   ├── core/            # 核心配置（JWT、异常处理、依赖）
│   ├── crud/            # 数据库增删改查
│   ├── db/              # 数据库连接、会话
│   ├── models/          # ORM模型（5张核心表）
│   ├── schemas/         # Pydantic请求/响应模型
│   ├── services/        # 业务逻辑（Agent拆解、LLM、工具、调度）
│   ├── utils/           # 工具函数（响应格式、日志、Redis、时间）
│   └── config.py        # 全局配置
├── main.py              # 项目入口
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── init.sql
└── .env
```

## 数据库表结构

| 表名         | 说明           | 关键字段                                             |
| ------------ | -------------- | ---------------------------------------------------- |
| user         | 用户表         | id, username, password_hash, email, status           |
| task_goal    | 总目标表       | id, user_id, title, description, goal_type, progress |
| task_item    | 子任务表       | id, goal_id, parent_id, title, priority, status      |
| agent_tool   | 工具表         | id, name, description, prompt_template, scenario      |
| task_log     | 操作日志表     | id, task_id, action_type, content                    |

## 大模型切换指南

系统使用OpenAI兼容接口，通过修改 `.env` 即可切换：

| 模型       | LLM_BASE_URL                                              | LLM_MODEL_NAME          |
| ---------- | --------------------------------------------------------- | ----------------------- |
| DeepSeek   | https://api.deepseek.com/v1                               | deepseek-chat           |
| 通义千问   | https://dashscope.aliyuncs.com/compatible-mode/v1         | qwen-plus / qwen-max    |
| Claude     | 需第三方代理或自行搭建中转                                   | claude-sonnet-4-20250514 |

## 任务状态机

```
待执行(0) ──→ 进行中(1) ──→ 已完成(2)
    │              │
    └──→ 作废(4)   └──→ 延期(3)
```

状态变更自动记录日志，支持批量操作。
