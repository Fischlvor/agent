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
│   │   │   │   ├── chat.py      # 聊天相关API
│   │   │   │   ├── session.py   # 会话管理API
│   │   │   │   └── user.py      # 用户相关API
│   │   │   ├── __init__.py
│   │   │   └── router.py        # API路由配置
│   │   ├── core/                # 核心配置
│   │   │   ├── __init__.py
│   │   │   ├── config.py        # 应用配置
│   │   │   └── security.py      # 安全相关
│   │   ├── db/                  # 数据库
│   │   │   ├── __init__.py
│   │   │   ├── base.py          # 数据库模型抽象基类/接口
│   │   │   └── session.py       # 数据库会话
│   │   ├── models/              # 数据模型
│   │   │   ├── __init__.py
│   │   │   ├── chat.py          # 聊天相关模型
│   │   │   ├── session.py       # 会话模型
│   │   │   └── user.py          # 用户模型
│   │   ├── schemas/             # Pydantic模式
│   │   │   ├── __init__.py
│   │   │   ├── chat.py          # 聊天相关模式
│   │   │   ├── session.py       # 会话模式
│   │   │   └── user.py          # 用户模式
│   │   ├── services/            # 服务层
│   │   │   ├── __init__.py
│   │   │   ├── chat_service.py  # 聊天服务
│   │   │   ├── history_service.py # 历史记录服务
│   │   │   └── session_service.py # 会话服务
│   │   ├── ai/                  # AI服务层
│   │   │   ├── __init__.py
│   │   │   ├── factory.py       # AI客户端工厂
│   │   │   ├── function_calling.py # 函数调用处理
│   │   │   ├── clients/         # AI客户端
│   │   │   │   ├── __init__.py
│   │   │   │   ├── base.py      # AI客户端抽象基类/接口
│   │   │   │   └── qwen_client.py  # 阿里云千问客户端
│   │   │   └── tools/           # 工具
│   │   │       ├── __init__.py
│   │   │       ├── registry.py  # 工具注册表
│   │   │       ├── executor.py  # 工具执行器
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
│   ├── app/                     # Next.js应用
│   │   ├── chat/                # 聊天页面
│   │   │   ├── [session_id]/    # 特定会话页面
│   │   │   │   └── page.tsx
│   │   │   └── page.tsx         # 聊天主页
│   │   ├── login/               # 登录页面
│   │   │   └── page.tsx
│   │   ├── register/            # 注册页面
│   │   │   └── page.tsx
│   │   ├── layout.tsx           # 布局组件
│   │   └── page.tsx             # 主页
│   ├── components/              # 组件
│   │   ├── chat/                # 聊天组件
│   │   │   ├── ChatWindow.tsx   # 聊天窗口
│   │   │   ├── ChatInput.tsx    # 聊天输入
│   │   │   ├── MessageList.tsx  # 消息列表
│   │   │   └── Message.tsx      # 消息组件
│   │   ├── ui/                  # UI组件
│   │   │   ├── Button.tsx
│   │   │   ├── Input.tsx
│   │   │   └── Modal.tsx
│   │   └── layout/              # 布局组件
│   │       ├── Header.tsx
│   │       ├── Sidebar.tsx
│   │       └── Footer.tsx
│   ├── hooks/                   # 自定义Hooks
│   │   ├── useChat.ts           # 聊天Hook
│   │   ├── useWebSocket.ts      # WebSocket Hook
│   │   └── useAuth.ts           # 认证Hook
│   ├── lib/                     # 工具库
│   │   ├── api.ts               # API客户端
│   │   ├── websocket.ts         # WebSocket客户端
│   │   └── utils.ts             # 工具函数
│   ├── store/                   # Zustand状态管理
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
   - `router.py`: API路由配置

2. **服务层**：业务逻辑处理
   - `chat_service.py`: 处理聊天相关业务逻辑
   - `history_service.py`: 管理聊天历史
   - `session_service.py`: 管理用户会话

3. **AI服务层**：AI模型集成和工具管理
   - `factory.py`: AI客户端工厂
   - `function_calling.py`: 模拟函数调用处理
   - `clients/`: 各种AI模型的客户端
     - `base.py`: AI客户端抽象基类/接口
     - `qwen_client.py`: 阿里云千问模型客户端
   - `tools/`: 工具系统
     - `registry.py`: 工具注册表
     - `executor.py`: 工具执行器
     - `base.py`: 工具抽象基类/接口
     - `general/`: 通用工具目录

4. **WebSocket层**：实时通信
   - `connection.py`: 连接管理
   - `handler.py`: WebSocket处理器接口
   - `session.py`: WebSocket会话

5. **数据层**：数据模型和数据库交互
   - `models/`: ORM模型
   - `schemas/`: Pydantic验证模式
   - `db/`: 数据库配置和会话

### 前端模块

1. **页面**：Next.js页面
   - `chat/`: 聊天相关页面
   - `login/`, `register/`: 认证页面

2. **组件**：React组件
   - `chat/`: 聊天相关组件
   - `ui/`: 通用UI组件
   - `layout/`: 布局组件

3. **状态管理**：Zustand存储
   - `chatStore.ts`: 聊天状态
   - `sessionStore.ts`: 会话状态
   - `userStore.ts`: 用户状态

4. **Hooks**：自定义React Hooks
   - `useChat.ts`: 聊天相关功能
   - `useWebSocket.ts`: WebSocket连接管理
   - `useAuth.ts`: 认证相关功能

5. **工具库**：辅助功能
   - `api.ts`: API请求
   - `websocket.ts`: WebSocket客户端
   - `utils.ts`: 工具函数

## 数据流

1. 用户在前端输入消息
2. 消息通过WebSocket发送到后端
3. 后端处理消息并传递给AI服务
4. AI服务决定是否调用工具
5. 工具执行结果返回给AI服务
6. AI服务生成响应
7. 响应通过WebSocket流式返回给前端
8. 前端实时显示响应

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