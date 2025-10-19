# Agent项目目录结构

## 项目概览

这是一个基于FastAPI和Next.js构建的智能Agent系统，支持实时对话、工具调用和流式响应。

## 目录结构

```
agent-project/
├── backend/                     # 后端应用
│   ├── app/                     # 主应用目录
│   │   ├── api/                 # API路由
│   │   │   ├── endpoints/       # API端点
│   │   │   │   ├── __init__.py
│   │   │   │   ├── admin.py     # 管理员API
│   │   │   │   ├── analytics.py # 分析统计API ⭐
│   │   │   │   ├── auth.py      # 认证API
│   │   │   │   ├── chat.py      # 聊天相关API
│   │   │   │   ├── chat_ws.py   # WebSocket聊天
│   │   │   │   ├── users.py     # 用户相关API
│   │   │   │   └── rag/         # RAG相关API ⭐
│   │   │   │       ├── __init__.py
│   │   │   │       ├── knowledge_bases.py # 知识库管理API
│   │   │   │       └── documents.py       # 文档管理API
│   │   │   ├── __init__.py
│   │   │   └── router.py        # API路由配置
│   │   ├── constants/           # 常量定义 ⭐
│   │   │   ├── __init__.py
│   │   │   ├── content_types.py # 内容类型常量
│   │   │   └── events.py        # 事件类型常量
│   │   ├── core/                # 核心配置
│   │   │   ├── __init__.py
│   │   │   ├── config.py        # 应用配置
│   │   │   ├── email.py         # 邮件服务
│   │   │   ├── prompts.py       # 系统提示词 ⭐
│   │   │   ├── redis_client.py  # Redis客户端
│   │   │   └── security.py      # 安全相关
│   │   ├── db/                  # 数据库
│   │   │   ├── __init__.py
│   │   │   ├── base.py          # 数据库模型抽象基类/接口
│   │   │   ├── mysql.py         # MySQL支持 ⭐
│   │   │   ├── postgresql.py    # PostgreSQL支持
│   │   │   └── session.py       # 数据库会话
│   │   ├── middleware/          # 中间件 ⭐
│   │   │   ├── __init__.py
│   │   │   ├── auth.py          # 认证中间件
│   │   │   └── rate_limit.py    # 速率限制
│   │   ├── models/              # 数据模型
│   │   │   ├── __init__.py
│   │   │   ├── ai_model.py      # AI模型配置
│   │   │   ├── base.py          # 模型基类
│   │   │   ├── chat.py          # 聊天相关模型
│   │   │   ├── invocation.py    # 调用记录模型 ⭐
│   │   │   ├── session.py       # 会话模型
│   │   │   ├── user.py          # 用户模型
│   │   │   └── rag/             # RAG数据模型 ⭐
│   │   │       ├── __init__.py
│   │   │       └── knowledge.py # 知识库模型（KnowledgeBase, Document, DocumentChunk）
│   │   ├── schemas/             # Pydantic模式
│   │   │   ├── __init__.py
│   │   │   ├── auth.py          # 认证schema
│   │   │   ├── chat.py          # 聊天相关模式
│   │   │   ├── invocation.py    # 调用记录schema ⭐
│   │   │   ├── session.py       # 会话模式
│   │   │   ├── user.py          # 用户模式
│   │   │   └── rag/             # RAG schemas ⭐
│   │   │       ├── __init__.py
│   │   │       └── knowledge.py # 知识库schemas
│   │   ├── services/            # 服务层
│   │   │   ├── __init__.py
│   │   │   ├── auth_service.py  # 认证服务
│   │   │   ├── chat_service.py  # 聊天服务
│   │   │   ├── history_service.py # 历史记录服务
│   │   │   ├── session_service.py # 会话服务
│   │   │   ├── user_service.py  # 用户服务
│   │   │   └── rag/             # RAG服务层 ⭐
│   │   │       ├── __init__.py
│   │   │       ├── knowledge_service.py    # 知识库管理服务
│   │   │       ├── pdf_parser_service.py   # PDF解析服务
│   │   │       ├── vector_store_service.py # 向量存储服务
│   │   │       ├── retrieval_service.py    # 检索服务
│   │   │       ├── reranker_service.py     # 重排序服务
│   │   │       ├── bge_embeddings.py       # BGE嵌入服务
│   │   │       └── model_manager.py        # 模型管理器
│   │   ├── ai/                  # AI服务层
│   │   │   ├── __init__.py
│   │   │   ├── factory.py       # AI客户端工厂
│   │   │   ├── adk_agent_adapter.py    # ADK Agent 主适配器（核心入口）
│   │   │   ├── adk_llm_adapter.py      # LLM 客户端适配器
│   │   │   ├── adk_session_service.py  # ADK 会话服务
│   │   │   ├── frontend_event_adapter.py # 前端事件格式转换
│   │   │   ├── mcp_tools_adapter.py    # MCP → ADK 工具适配
│   │   │   ├── clients/         # AI客户端
│   │   │   │   ├── __init__.py
│   │   │   │   ├── base.py      # AI客户端抽象基类/接口
│   │   │   │   └── qwen_client.py  # Ollama/Qwen 客户端
│   │   │   ├── mcp/             # 真正的 MCP 协议实现
│   │   │   │   ├── __init__.py
│   │   │   │   ├── protocol.py  # MCP 协议定义（JSON-RPC 2.0）
│   │   │   │   ├── server.py    # MCP Server 基类
│   │   │   │   ├── client.py    # MCP Client 实现
│   │   │   │   └── tools_server.py # 具体工具服务器
│   │   │   └── tools/           # 工具
│   │   │       ├── __init__.py
│   │   │       ├── base.py      # 工具抽象基类/接口
│   │   │       └── general/     # 通用工具目录
│   │   │           ├── __init__.py
│   │   │           ├── search.py       # 搜索工具
│   │   │           ├── calculator.py   # 计算器工具
│   │   │           └── weather.py      # 天气工具
│   │   ├── websocket/           # WebSocket
│   │   │   ├── __init__.py
│   │   │   ├── connection.py    # 连接管理
│   │   │   ├── handler.py       # WebSocket处理器接口
│   │   │   └── session.py       # WebSocket会话
│   │   ├── __init__.py
│   │   └── main.py              # 应用入口
│   ├── alembic/                 # 数据库迁移
│   │   ├── versions/
│   │   ├── env.py
│   │   └── script.py.mako
│   ├── tests/                   # 测试
│   │   ├── __init__.py
│   │   ├── conftest.py
│   │   ├── test_api/
│   │   ├── test_services/
│   │   └── test_tools/
│   ├── .env                     # 环境变量
│   ├── .env.example             # 环境变量示例
│   ├── alembic.ini              # Alembic配置
│   ├── pyproject.toml           # 项目配置
│   ├── Dockerfile               # Docker配置
│   └── requirements.txt         # 依赖
│
├── frontend/                    # 前端应用
│   ├── app/                     # Next.js应用（App Router）
│   │   ├── chat/                # 聊天页面
│   │   │   ├── [session_id]/    # 特定会话页面（动态路由）⭐
│   │   │   │   └── page.tsx     # 会话详情页
│   │   │   └── page.tsx         # 欢迎页面（/chat）⭐
│   │   ├── knowledge-bases/     # 知识库管理页面 ⭐
│   │   │   ├── [id]/            # 知识库详情页
│   │   │   │   └── page.tsx
│   │   │   └── page.tsx         # 知识库列表
│   │   ├── login/               # 登录页面
│   │   │   └── page.tsx
│   │   ├── register/            # 注册页面
│   │   │   └── page.tsx
│   │   ├── resend-verification/ # 重发验证邮件
│   │   │   └── page.tsx
│   │   ├── verify-email/        # 邮箱验证
│   │   │   └── page.tsx
│   │   ├── layout.tsx           # 布局组件
│   │   └── page.tsx             # 主页
│   ├── components/              # 组件
│   │   ├── chat/                # 聊天组件
│   │   │   ├── ContextProgress.tsx # 上下文进度（动画）⭐
│   │   │   ├── MessageInput.tsx # 消息输入（含知识库选择）
│   │   │   ├── MessageItem.tsx  # 消息项
│   │   │   ├── MessageList.tsx  # 消息列表
│   │   │   ├── ModelSelector.tsx # 模型选择器
│   │   │   ├── SessionSidebar.tsx # 会话侧边栏
│   │   │   ├── UserMenu.tsx     # 用户头像菜单 ⭐
│   │   │   ├── WelcomeScreen.tsx # 欢迎界面 ⭐
│   │   │   └── StreamingMessageItem.tsx # 流式消息项
│   │   ├── ui/                  # UI组件
│   │   │   ├── Button.tsx
│   │   │   ├── Input.tsx
│   │   │   └── Modal.tsx
│   │   └── layout/              # 布局组件
│   │       ├── Header.tsx
│   │       ├── Sidebar.tsx
│   │       └── Footer.tsx
│   ├── constants/               # 常量定义 ⭐
│   │   ├── contentTypes.ts      # 内容类型常量
│   │   └── events.ts            # 事件类型常量
│   ├── hooks/                   # 自定义Hooks
│   │   ├── useAnimatedNumber.ts # 数值动画Hook ⭐
│   │   ├── useChat.ts           # 聊天Hook
│   │   ├── useWebSocket.ts      # WebSocket Hook
│   │   └── useAuth.ts           # 认证Hook
│   ├── lib/                     # 工具库
│   │   ├── api/                 # API模块 ⭐
│   │   │   ├── rag.ts           # RAG API封装
│   │   │   └── rag/             # RAG子模块
│   │   ├── api.ts               # API客户端
│   │   ├── websocket.ts         # WebSocket客户端
│   │   └── utils.ts             # 工具函数
│   ├── store/                   # Zustand状态管理
│   │   ├── authStore.ts         # 认证状态
│   │   ├── chatStore.ts         # 聊天状态
│   │   ├── sessionStore.ts      # 会话状态
│   │   └── userStore.ts         # 用户状态
│   ├── types/                   # TypeScript类型
│   │   ├── chat.ts              # 聊天类型
│   │   ├── session.ts           # 会话类型
│   │   └── user.ts              # 用户类型
│   ├── public/                  # 静态资源
│   ├── styles/                  # 样式
│   │   └── globals.css          # 全局样式
│   ├── .env.local               # 环境变量
│   ├── .env.example             # 环境变量示例
│   ├── next.config.js           # Next.js配置
│   ├── tailwind.config.js       # Tailwind配置
│   ├── tsconfig.json            # TypeScript配置
│   ├── package.json             # 包配置
│   └── Dockerfile               # Docker配置
│
├── docker-compose.yml           # Docker Compose配置
├── .gitignore                   # Git忽略文件
├── README.md                    # 项目说明
├── tech-stack.md                # 技术栈文档
└── project-structure.md         # 项目结构文档
```

## 主要模块说明

### 后端模块

1. **API层**：处理HTTP请求和WebSocket连接
   - `endpoints/`: 包含各种API端点
     - `admin.py`: 管理员功能
     - `analytics.py`: 统计分析（Token使用、调用记录）⭐
     - `auth.py`: 用户认证
     - `chat.py`: 聊天接口
     - `chat_ws.py`: WebSocket实时聊天
     - `users.py`: 用户管理
   - `router.py`: API路由配置

2. **常量定义**：全局常量和枚举 ⭐
   - `content_types.py`: 内容类型常量（TEXT、THINKING、TOOL_CALL等）
   - `events.py`: WebSocket事件类型常量
     - `LLM_INVOCATION_COMPLETE` (5000): LLM调用完成
     - `TOOL_INVOCATION_COMPLETE` (5001): 工具调用完成
     - `DOCUMENT_STATUS_UPDATE` (7000): 文档状态更新 ⭐

3. **核心层**：核心配置和服务
   - `config.py`: 应用配置
   - `email.py`: 邮件服务
   - `prompts.py`: 系统提示词配置 ⭐
   - `redis_client.py`: Redis缓存客户端
   - `security.py`: 安全相关（JWT、密码加密）

4. **中间件**：请求处理中间件 ⭐
   - `auth.py`: 认证中间件
   - `rate_limit.py`: 速率限制（基于Redis）

5. **数据层**：数据模型和数据库交互
   - `models/`: ORM模型
     - `ai_model.py`: AI模型配置
     - `chat.py`: 消息模型
     - `invocation.py`: 调用记录模型（Token统计）⭐
     - `session.py`: 会话模型（含摘要、上下文管理）
     - `user.py`: 用户模型
     - `rag/knowledge.py`: RAG数据模型 ⭐
       - `KnowledgeBase`: 知识库（名称、描述、配置、统计信息）
       - `Document`: 文档（标题、格式、状态、token数、处理时间）
       - `DocumentChunk`: 文档块（统一父子块，支持 pgvector）
   - `schemas/`: Pydantic验证模式
     - 与models对应的请求/响应schema
     - `invocation.py`: 调用统计schema ⭐
     - `rag/knowledge.py`: RAG schemas（CRUD请求/响应）⭐
   - `db/`: 数据库支持
     - `base.py`: 数据库接口抽象
     - `mysql.py`: MySQL实现
     - `postgresql.py`: PostgreSQL实现（支持 pgvector）⭐
     - `session.py`: 数据库会话管理

6. **服务层**：业务逻辑处理
   - `auth_service.py`: 认证服务（登录、注册、邮箱验证）
   - `chat_service.py`: 聊天服务（含摘要生成、上下文管理）
   - `history_service.py`: 历史记录服务
   - `session_service.py`: 会话管理
   - `user_service.py`: 用户管理
   - `rag/`: RAG服务模块 ⭐
     - `knowledge_service.py`: 知识库CRUD、文档管理、统计
     - `pdf_parser_service.py`: 文档解析（PDF/Word/TXT）
     - `vector_store_service.py`: pgvector向量存储、检索
     - `retrieval_service.py`: 两阶段检索（召回+重排）
     - `reranker_service.py`: BGE-Reranker-V2-M3重排序
     - `bge_embeddings.py`: BGE-M3嵌入服务（GPU加速）
     - `model_manager.py`: 模型加载和缓存管理

7. **AI服务层**：基于 Google ADK 和 MCP 的 AI 集成
   - `adk_agent_adapter.py`: ADK Agent 主适配器（核心入口）
   - `adk_llm_adapter.py`: LLM 客户端适配器（适配到 ADK BaseLlm 接口）
   - `adk_session_service.py`: ADK 会话服务（SDK 层面会话管理）
   - `frontend_event_adapter.py`: 前端事件格式转换（ADK → 前端展示）
   - `mcp_tools_adapter.py`: MCP 工具适配器（MCP → ADK FunctionTool）
   - `factory.py`: AI客户端工厂
   - `clients/`: AI模型客户端
     - `base.py`: AI客户端抽象基类/接口
     - `qwen_client.py`: Ollama/Qwen 模型客户端
   - `mcp/`: 真正的 MCP 协议实现（JSON-RPC 2.0）
     - `protocol.py`: MCP 协议数据结构定义
     - `server.py`: MCP Server 基类（InProcessMCPServer, StdioMCPServer）
     - `client.py`: MCP Client 实现（管理多个 MCP 服务器）
     - `tools_server.py`: 具体工具服务器（Calculator, Weather, Search）
   - `tools/`: 工具实现
     - `base.py`: 工具抽象基类/接口
     - `general/`: 通用工具目录（Calculator, Weather, Search）

8. **WebSocket层**：实时通信
   - `connection.py`: 连接管理
   - `handler.py`: WebSocket处理器接口
   - `session.py`: WebSocket会话

### 前端模块

1. **页面**：Next.js App Router 页面
   - `chat/page.tsx`: 欢迎页面（ChatGPT 风格）⭐
   - `chat/[session_id]/page.tsx`: 会话详情页（动态路由）⭐
   - `knowledge-bases/`: 知识库管理页面 ⭐
   - `login/`, `register/`: 认证页面
   - `verify-email/`: 邮箱验证页面
   - `resend-verification/`: 重发验证邮件页面

2. **组件**：React组件
   - `chat/`: 聊天相关组件
     - `WelcomeScreen.tsx`: 欢迎界面（大输入框 + 快速提示词）⭐
     - `UserMenu.tsx`: 用户头像下拉菜单（个人信息 + 退出登录）⭐
     - `ContextProgress.tsx`: Token 使用进度条（圆形动画）⭐
     - `MessageList.tsx`: 消息列表
     - `MessageItem.tsx`: 单条消息展示
     - `MessageInput.tsx`: 消息输入框（含知识库选择）
     - `ModelSelector.tsx`: AI模型选择器
     - `SessionSidebar.tsx`: 会话列表侧边栏（含用户头像）
     - `StreamingMessageItem.tsx`: 流式消息展示
   - `ui/`: 通用UI组件
     - `Button.tsx`, `Input.tsx`, `Modal.tsx`
   - `layout/`: 布局组件
     - `Header.tsx`, `Sidebar.tsx`, `Footer.tsx`

3. **常量定义**：前端常量 ⭐
   - `contentTypes.ts`: 内容类型常量（与后端对应）
   - `events.ts`: WebSocket事件类型常量

4. **状态管理**：Zustand存储
   - `authStore.ts`: 认证状态（用户信息、登录状态）
   - `chatStore.ts`: 聊天状态（含流式处理、编辑、全局初始化）⭐
     - `isInitialized`: 全局初始化标记
     - `knowledgeBases`: 知识库缓存
     - `pendingMessage`: 待发送消息
     - `deletingSessionId`: 正在删除的会话ID
   - `sessionStore.ts`: 会话状态
   - `userStore.ts`: 用户状态

5. **Hooks**：自定义React Hooks
   - `useAnimatedNumber.ts`: 数值平滑动画（easeOutCubic）⭐
   - `useChat.ts`: 聊天相关功能
   - `useWebSocket.ts`: WebSocket连接管理
   - `useAuth.ts`: 认证相关功能

6. **工具库**：辅助功能
   - `api.ts`: API请求封装
   - `websocket.ts`: WebSocket客户端
   - `utils.ts`: 工具函数

7. **类型定义**：TypeScript类型
   - `chat.ts`: 聊天相关类型定义
   - `session.ts`: 会话类型
   - `user.ts`: 用户类型

## 路由与页面流程

### ChatGPT 风格界面流程 ⭐

1. **欢迎页面（`/chat`）**
   - 显示大输入框和快速提示词
   - 用户输入消息后自动创建会话
   - 保存待发送消息到 store (`pendingMessage`)
   - 跳转到会话详情页

2. **会话详情页（`/chat/[sessionId]`）**
   - 动态路由，显示特定会话的消息
   - 自动检测 `pendingMessage` 并发送
   - 实时显示 thinking、tool_call、content
   - Token 使用进度圆形动画

3. **会话切换优化**
   - 全局初始化一次（`chatStore.initialize()`）
   - 切换会话不重复请求 models/sessions/knowledge-bases
   - 从 ~15 个请求降至 0 个重复请求

4. **错误处理**
   - 删除当前会话 → 自动跳转欢迎页
   - 访问不存在会话 → 自动跳转欢迎页
   - 避免 404 请求（使用 `deletingSessionId` 标记）

## 数据流

### 用户对话流程

1. **前端** → 用户在前端输入消息
2. **WebSocket** → 消息通过 WebSocket 发送到后端
3. **ChatService（业务层）** → 保存用户消息到数据库，加载历史消息
4. **ADK Agent（AI层）** → 调用 ADK Agent 适配器处理对话
5. **MCP Client** → 通过 MCP 协议动态加载工具（Calculator, Weather, Search）
6. **ADK Runner** → 自动管理多轮思考和工具调用
   - LLM 生成 thinking（思考过程）
   - LLM 决定调用工具
   - MCP Server 执行工具
   - 工具结果返回给 LLM
   - LLM 生成最终回复
7. **Frontend Event Adapter** → 将 ADK 事件转换为前端展示格式
8. **ChatService** → 保存助手消息到数据库（包含 timeline）
9. **WebSocket** → 流式返回事件给前端（thinking, tool_call, content）
10. **前端** → 实时显示 AI 响应

### 会话管理（双层架构）

**业务层（ChatService + 数据库）**：
- 永久存储会话和消息
- 用户管理、权限控制
- 消息编辑、删除、统计

**SDK层（SimpleSessionService + 内存）**：
- ADK 内部运行时状态
- 临时缓存当前对话的 592 个内部事件
- 自动管理多轮上下文传递

---

## WebSocket 消息格式规范

### 消息外层结构（Envelope）

所有后端发送的 WebSocket 消息都遵循统一的 Envelope 格式：

```typescript
{
  event_data: string,      // JSON字符串，包含实际的事件数据
  event_id: string,        // 事件序号（每种事件类型单独计数，从0开始）
  event_type: number       // 事件类型代码（见下方事件类型表）
}
```

### 事件类型（EventType）

| 代码 | 名称 | 说明 |
|------|------|------|
| `1000` | CONNECTED | WebSocket 连接成功 |
| `1999` | ERROR | 错误消息 |
| `2000` | MESSAGE_START | 消息生成开始 |
| `2001` | MESSAGE_CONTENT | 消息内容增量 |
| `2002` | MESSAGE_DONE | 消息生成完成 |
| `3000` | THINKING_START | 思考开始 |
| `3001` | THINKING_DELTA | 思考内容增量 |
| `3002` | THINKING_COMPLETE | 思考完成 |
| `4000` | TOOL_CALL | 工具调用 |
| `4001` | TOOL_RESULT | 工具结果 |
| `9000` | PING | 心跳请求 |
| `9001` | PONG | 心跳响应 |

### event_data 结构

`event_data` 字段是一个 JSON 字符串，解析后包含以下字段：

#### 通用字段

| 字段 | 类型 | 说明 |
|------|------|------|
| `message_id` | string | 消息ID（整条对话的唯一标识） |
| `conversation_id` | string | 会话ID |
| `message_index` | number | 消息序号（递增） |
| `status` | number | 消息状态（1=完成, 4=处理中, 5=错误） |
| `is_delta` | boolean | 是否为增量更新 |
| `is_finish` | boolean | 是否结束 |

#### message 对象（嵌套字段）

`event_data.message` 包含具体的消息内容：

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | string | **当前事件块的唯一ID**（用于匹配 start/delta/complete） |
| `content_type` | number | 内容类型（10000=文本, 10040=思考, 10050=工具调用, 10051=工具结果） |
| `content` | string | **JSON字符串**，包含具体内容（见下方各类型详情） |

---

### 各事件类型详解

#### 1. CONNECTED (1000)

连接建立成功。

**event_data 示例**：
```json
{}
```

---

#### 2. MESSAGE_START (2000)

开始生成新消息。

**event_data 示例**：
```json
{
  "message_id": "abc-123",
  "conversation_id": "session-456",
  "message_index": 0
}
```

---

#### 3. THINKING_START (3000)

开始一轮思考。

**event_data 示例**：
```json
{
  "message_id": "abc-123",
  "conversation_id": "session-456",
  "message": {
    "id": "thinking-001",           // 本轮思考的唯一ID
    "content_type": 10040,
    "content": "{\"finish_title\": \"深度思考中\"}"
  },
  "status": 4,
  "is_delta": true,
  "message_index": 1
}
```

**content 字段解析**：
```json
{
  "finish_title": "深度思考中"     // 思考状态文本
}
```

---

#### 4. THINKING_DELTA (3001)

思考内容增量（流式输出）。

**event_data 示例**：
```json
{
  "message_id": "abc-123",
  "conversation_id": "session-456",
  "message": {
    "id": "thinking-001",           // 与 THINKING_START 的 id 相同
    "content_type": 10040,
    "content": "{\"text\": \"用户想了解天气\"}"
  },
  "status": 4,
  "is_delta": true,
  "message_index": 2
}
```

**content 字段解析**：
```json
{
  "text": "用户想了解天气"          // 增量文本（需前端累积）
}
```

---

#### 5. THINKING_COMPLETE (3002)

思考完成。

**event_data 示例**：
```json
{
  "message_id": "abc-123",
  "conversation_id": "session-456",
  "message": {
    "id": "thinking-001",           // 与 THINKING_START 的 id 相同
    "content_type": 10040,
    "content": "{\"finish_title\": \"已完成思考\"}"
  },
  "status": 1,
  "is_finish": true,
  "message_index": 3
}
```

**content 字段解析**：
```json
{
  "finish_title": "已完成思考"     // 完成状态文本
}
```

---

#### 6. TOOL_CALL (4000)

调用工具。

**event_data 示例**：
```json
{
  "message_id": "abc-123",
  "conversation_id": "session-456",
  "message": {
    "id": "tool-001",               // 本次工具调用的唯一ID
    "content_type": 10050,
    "content": "{\"name\": \"weathertool\", \"args\": {\"location\": \"Beijing\"}}"
  },
  "status": 4,
  "message_index": 4
}
```

**content 字段解析**：
```json
{
  "name": "weathertool",            // 工具名称
  "args": {                         // 工具参数
    "location": "Beijing",
    "unit": "celsius"
  }
}
```

---

#### 7. TOOL_RESULT (4001)

工具执行结果。

**event_data 示例**：
```json
{
  "message_id": "abc-123",
  "conversation_id": "session-456",
  "message": {
    "id": "tool-001",               // 与 TOOL_CALL 的 id 相同
    "content_type": 10051,
    "content": "{\"name\": \"weathertool\", \"result\": {\"temperature\": 25}}"
  },
  "status": 1,
  "message_index": 5
}
```

**content 字段解析**：
```json
{
  "name": "weathertool",            // 工具名称
  "result": {                       // 工具返回结果
    "temperature": 25,
    "description": "晴天"
  }
}
```

---

#### 8. MESSAGE_CONTENT (2001)

消息正文内容增量。

**event_data 示例**：
```json
{
  "message_id": "abc-123",
  "conversation_id": "session-456",
  "message": {
    "id": "content-001",
    "content_type": 10000,
    "content": "{\"text\": \"今天天气不错\"}"
  },
  "status": 4,
  "is_delta": true,
  "message_index": 6
}
```

**content 字段解析**：
```json
{
  "text": "今天天气不错"            // 增量文本（需前端累积）
}
```

---

#### 9. MESSAGE_DONE (2002)

消息生成完成。

**event_data 示例**：
```json
{
  "message_id": "abc-123",
  "conversation_id": "session-456",
  "status": 1,
  "is_finish": true,
  "message_index": 7,
  "generation_time": 2.5            // 生成耗时（秒）
}
```

---

#### 10. ERROR (1999)

错误消息。

**event_data 示例**：
```json
{
  "message_id": "abc-123",
  "conversation_id": "session-456",
  "message": {
    "id": "error-001",
    "content_type": 10099,
    "content": "{\"error\": \"模型调用失败\"}"
  },
  "status": 5,
  "message_index": 8
}
```

**content 字段解析**：
```json
{
  "error": "模型调用失败"           // 错误信息
}
```

---

### 关键设计说明

#### 1. 事件ID（event_id）重置机制

`event_id` 在**每种事件类型切换时重置为 0**，用于追踪同类型事件的顺序。

**示例**：
```
THINKING_START:  event_id=0
THINKING_DELTA:  event_id=0, 1, 2, ...
THINKING_COMPLETE: event_id=0
MESSAGE_CONTENT: event_id=0, 1, 2, ...  (重置)
MESSAGE_DONE:    event_id=0
```

#### 2. 多轮匹配（message.id）

**问题**：多轮思考或工具调用时，如何区分不同轮次？

**解决**：使用 `message.id` 作为每轮的唯一标识：
- `THINKING_START` → `THINKING_DELTA` → `THINKING_COMPLETE` 使用**相同的 `message.id`**
- `TOOL_CALL` → `TOOL_RESULT` 使用**相同的 `message.id`**

**示例流程**：
```
1. THINKING_START   (message.id="think-1")
2. THINKING_DELTA   (message.id="think-1") ← 匹配
3. THINKING_COMPLETE(message.id="think-1") ← 匹配
4. TOOL_CALL        (message.id="tool-1")
5. TOOL_RESULT      (message.id="tool-1")  ← 匹配
6. THINKING_START   (message.id="think-2")  ← 新一轮
7. THINKING_DELTA   (message.id="think-2")
8. THINKING_COMPLETE(message.id="think-2")
```

#### 3. 增量更新（is_delta）

当 `is_delta=true` 时，`content.text` 字段包含**增量内容**，前端需累积显示。

#### 4. 内容类型代码（content_type）

| 代码 | 名称 | 说明 |
|------|------|------|
| `10000` | TEXT | 普通文本 |
| `10040` | THINKING | 思考内容 |
| `10050` | TOOL_CALL | 工具调用 |
| `10051` | TOOL_RESULT | 工具结果 |
| `10099` | ERROR | 错误信息 |

#### 5. 消息状态代码（status）

| 代码 | 名称 | 说明 |
|------|------|------|
| `1` | COMPLETED | 已完成 |
| `4` | PENDING | 处理中 |
| `5` | ERROR | 错误 |

---

### 完整示例（单次对话）

```
→ 用户: "北京天气如何？"

← [1] MESSAGE_START
← [2] THINKING_START     (id="think-1")
← [3] THINKING_DELTA     (id="think-1", text="用户询问北京天气...")
← [4] THINKING_DELTA     (id="think-1", text="需要调用天气工具")
← [5] THINKING_COMPLETE  (id="think-1")
← [6] TOOL_CALL          (id="tool-1", name="weathertool", args={...})
← [7] TOOL_RESULT        (id="tool-1", result={temperature: 25})
← [8] MESSAGE_CONTENT    (text="北京今天")
← [9] MESSAGE_CONTENT    (text="天气晴朗")
← [10] MESSAGE_CONTENT   (text="，温度25°C")
← [11] MESSAGE_DONE
```

---

### 前端处理流程

1. **接收 Envelope**：解析 `event_type` 和 `event_data`
2. **解析 event_data**：JSON.parse(`event_data`)
3. **解析 message.content**：JSON.parse(`event_data.message.content`)
4. **匹配事件**：
   - `THINKING_START` → 创建新的 thinking 块（使用 `message.id`）
   - `THINKING_DELTA` → 根据 `message.id` 找到对应块，累积 `content.text`
   - `THINKING_COMPLETE` → 根据 `message.id` 标记完成
   - `TOOL_CALL` → 创建新的 tool 块（使用 `message.id`）
   - `TOOL_RESULT` → 根据 `message.id` 更新结果
   - `MESSAGE_CONTENT` → 累积正文内容
5. **状态更新**：根据 `status` 字段更新 UI（pending/completed/error）

---

## 📝 项目演进历史

### 2025-10-09

#### 🔧 数据库架构优化
- **数据库优化**：统一使用 MySQL 数据库
- **主键重构**：所有模型主键从 UUID 改为自增整型，提升性能
- **数据库抽象**：完善数据库接口抽象层

#### ✨ 功能增强
- **分析统计**：新增 `/api/analytics` 接口，提供 Token 使用统计
- **调用追踪**：`InvocationLog` 模型记录每次 AI 调用的详细信息
- **前端优化**：改进消息展示逻辑，优化事件处理

### 2025-10-08

#### 🧠 智能摘要系统
- **自动摘要**：会话达到一定消息数自动生成摘要
- **上下文管理**：
  - 新增 `context_window_size` 字段记录上下文窗口大小
  - 新增 `context_usage_percentage` 字段追踪上下文使用率
  - 前端新增 `ContextProgress` 组件可视化展示
- **智能压缩**：上下文超限时自动触发摘要压缩

### 2025-10-07

#### 📊 Token 统计与限流
- **Token 记录**：完整记录每次调用的 Token 使用情况
- **速率限制**：基于 Redis 的智能限流中间件
- **Redis 增强**：扩展 Redis 客户端功能，支持更多数据结构
- **系统提示词**：提取系统提示词到配置文件（`core/prompts.py`）

#### 📚 文档体系
- 完善 README.md（技术栈、快速开始、核心功能）
- 创建项目结构文档（本文档）
- 编写技术栈说明（`tech-stack.md`）

#### 🚀 核心架构实现
- **Google ADK 集成**：
  - `adk_agent_adapter.py`: 主适配器
  - `adk_llm_adapter.py`: LLM 适配
  - `adk_session_service.py`: 会话管理
- **MCP 协议实现**：
  - 完整的 JSON-RPC 2.0 协议支持
  - MCP Server/Client 架构
  - 工具服务器（Calculator、Weather、Search）
- **事件转换**：`frontend_event_adapter.py` 将 ADK 事件转换为前端格式
- **架构文档**：编写详细的 AI 架构说明（`ai/ARCHITECTURE.md`）

### 2025-10-06

#### 🎉 项目初始化
- **后端架构**：
  - FastAPI 框架搭建
  - SQLAlchemy ORM + Alembic 迁移
  - JWT 认证系统
  - WebSocket 实时通信
- **前端架构**：
  - Next.js 14 + TypeScript
  - Tailwind CSS 样式系统
  - Zustand 状态管理
  - React Markdown 渲染
- **AI 工具系统**：
  - 基础工具实现（Calculator、Weather、Search）
  - 工具注册和调用框架
  - Qwen/Ollama 客户端
- **数据模型**：
  - User（用户）
  - Session（会话）
  - Message（消息）
  - AIModel（AI 模型配置）

---

## 🎯 前端架构与性能优化

### 路由架构（Next.js App Router）

| 路由 | 类型 | 说明 |
|------|------|------|
| `/chat` | 静态路由 | 欢迎页面（ChatGPT 风格）|
| `/chat/[sessionId]` | 动态路由 | 会话详情页（支持 RSC） |
| `/knowledge-bases` | 静态路由 | 知识库列表 |
| `/knowledge-bases/[id]` | 动态路由 | 知识库详情 |

**RSC（React Server Components）**：
- Next.js 自动优化客户端导航
- URL 带 `_rsc` 参数的请求用于获取 RSC 载荷
- 提供更快的导航体验和更小的传输体积

### 状态管理架构

| Store | 用途 | 缓存策略 |
|------|------|----------|
| `authStore` | 认证状态 | 持久化到 localStorage |
| `chatStore` | 聊天状态 | 全局单例，跨页面共享 |

**chatStore 关键字段**：
- `isInitialized`：全局初始化标记，避免重复请求
- `knowledgeBases`：知识库列表缓存
- `pendingMessage`：待发送消息（用于页面跳转）
- `deletingSessionId`：删除标记（避免 404 请求）

### 性能优化策略

| 优化项 | 方法 | 效果 |
|--------|------|------|
| **全局初始化** | `initialize()` 方法只执行一次 | 减少 90% API 请求 |
| **知识库缓存** | store 全局缓存 | 避免每次页面重载 |
| **智能删除** | 先跳转再删除 + 标记防止加载 | 无 404 请求 |
| **动画优化** | `requestAnimationFrame` | 60fps 流畅动画 |
| **RSC 优化** | Next.js 自动管理 | 更快的页面切换 |

### 动画系统

**useAnimatedNumber Hook**：
```typescript
- 监听目标值变化
- 使用 requestAnimationFrame 逐帧更新
- 应用缓动函数（easeOutCubic）
- 在指定时间内完成过渡（默认 800ms）
```

**应用场景**：
- Token 使用量圆形进度条平滑变化
- 配合 CSS `animate-pulse` 和 `drop-shadow` 实现脉冲效果
- 提供自然的视觉反馈

### 错误处理

| 场景 | 处理方式 | 用户体验 |
|------|----------|----------|
| 会话不存在 | 自动跳转欢迎页 | 无感知恢复 |
| 删除当前会话 | 先跳转再删除 | 无 404 错误 |
| WebSocket 断开 | 自动重连 | 实时状态提示 |
| API 请求失败 | 错误提示 + 重试 | 友好错误提示 |

---

## 🔑 关键设计决策

### 双层会话管理
- **业务层（持久化）**：ChatService + MySQL，永久存储
- **SDK层（运行时）**：ADK SessionService，内存缓存，进程重启清空

### 数据库选型
- **当前**：MySQL（性能优化、广泛支持）
- **特点**：自增主键、高效索引、成熟生态

### 事件流设计
```
用户输入 → WebSocket → ChatService（保存）
         → ADK Agent → ┌─────────────┐
                       │  MCP Tools  │
                       │      ↕      │  (循环调用)
                       │     LLM     │
        ┌──────────────└─────────────┘
        └→ Frontend Adapter（格式转换）
         → WebSocket → 前端（流式渲染）
```

### 上下文管理策略
1. **初期**：直接传递所有历史消息
2. **优化**：达到阈值触发自动摘要
3. **未来**：向量检索 + 相关性过滤

---