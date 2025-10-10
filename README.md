# 🤖 智能 Agent 系统

基于 **FastAPI** + **Next.js** + **Google ADK** + **MCP** 构建的现代化智能对话系统。

## ✨ 核心特性

- 🚀 **实时流式响应**：支持 thinking（思考过程）、tool_call（工具调用）、content（回复内容）的流式输出
- 🧠 **多轮对话**：基于 Google ADK 的会话管理，自动维护上下文
- 🔧 **MCP 协议**：完整实现 Model Context Protocol（JSON-RPC 2.0）
- 🛠️ **动态工具加载**：计算器、天气查询、网络搜索等工具自动集成
- 💾 **双层会话管理**：业务层持久化 + SDK 层运行时缓存
- 🔐 **用户认证**：JWT 令牌 + 数据库用户管理
- 📊 **结构化存储**：完整记录 thinking 和 tool_call timeline
- 📈 **实时 Token 追踪**：每次 LLM 调用的 token 使用量实时推送和 UI 显示

## 🏗️ 技术架构

### 后端技术栈

| 技术 | 版本 | 说明 |
|------|------|------|
| **Python** | 3.11+ | 编程语言 |
| **FastAPI** | 0.109+ | Web 框架 |
| **Google ADK** | 0.1.0+ | Agent Development Kit |
| **SQLAlchemy** | 2.0+ | ORM 框架 |
| **PostgreSQL** | 15+ | 数据库 |
| **Pydantic** | 2.0+ | 数据验证 |
| **WebSocket** | - | 实时通信 |

### 前端技术栈

| 技术 | 版本 | 说明 |
|------|------|------|
| **Next.js** | 14+ | React 框架 |
| **TypeScript** | 5+ | 类型系统 |
| **Tailwind CSS** | 3+ | CSS 框架 |
| **Zustand** | 4+ | 状态管理 |
| **React Markdown** | 9+ | Markdown 渲染 |

### AI 集成

| 组件 | 说明 |
|------|------|
| **Ollama** | 本地 LLM 运行（Qwen3:8b） |
| **OpenAI** | OpenAI API 支持（可选） |
| **MCP** | 工具协议标准化 |

## 📁 项目结构

```
agent-project/
├── backend/                    # 后端服务
│   ├── app/
│   │   ├── api/               # API 路由
│   │   ├── services/          # 业务服务层
│   │   ├── ai/                # AI 集成层 ⭐
│   │   │   ├── adk_agent_adapter.py      # ADK Agent 主适配器
│   │   │   ├── adk_llm_adapter.py        # LLM 客户端适配
│   │   │   ├── adk_session_service.py    # SDK 会话管理
│   │   │   ├── frontend_event_adapter.py # 事件格式转换
│   │   │   ├── mcp_tools_adapter.py      # MCP 工具适配
│   │   │   ├── mcp/                      # MCP 协议实现
│   │   │   │   ├── protocol.py           # JSON-RPC 2.0 协议
│   │   │   │   ├── server.py             # MCP Server 基类
│   │   │   │   ├── client.py             # MCP Client
│   │   │   │   └── tools_server.py       # 工具服务器
│   │   │   ├── clients/       # LLM 客户端
│   │   │   └── tools/         # 工具实现
│   │   ├── models/            # 数据库模型
│   │   └── websocket/         # WebSocket 处理
│   ├── tests/                 # 测试
│   └── alembic/               # 数据库迁移
│
├── frontend/                  # 前端应用
│   ├── app/                   # Next.js 页面
│   ├── components/            # React 组件
│   ├── hooks/                 # 自定义 Hooks
│   ├── lib/                   # 工具库
│   └── store/                 # Zustand 状态管理
│
├── project-structure.md       # 详细项目结构
├── tech-stack.md              # 技术栈详情
└── README.md                  # 本文件
```

详细目录说明请查看 [project-structure.md](./project-structure.md)

## 🚀 快速开始

### 环境要求

- Python 3.11+
- Node.js 18+
- PostgreSQL 15+
- Ollama（用于本地 LLM）

### 1. 后端启动

```bash
# 进入后端目录
cd backend

# 创建 conda 环境（推荐）
conda create -n ai_chat_env python=3.11
conda activate ai_chat_env

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env 文件，设置数据库连接等

# 运行数据库迁移
alembic upgrade head

# 启动开发服务器
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 2. 前端启动

```bash
# 进入前端目录
cd frontend

# 安装依赖
npm install

# 配置环境变量
cp .env.example .env.local
# 编辑 .env.local，设置后端 API 地址

# 启动开发服务器
npm run dev
```

### 3. Ollama 启动（必需）

```bash
# 启动 Ollama
ollama serve

# 拉取模型（在另一个终端）
ollama pull qwen3:8b
```

### 4. 访问应用

- 前端：http://localhost:3000
- 后端 API：http://localhost:8000
- API 文档：http://localhost:8000/docs

## 🔧 核心功能

### 1. 实时对话

支持流式输出，包含：
- **Thinking**：AI 的思考过程（可选显示）
- **Tool Call**：工具调用及参数
- **Tool Result**：工具执行结果
- **Content**：AI 的最终回复

### 2. 工具系统

基于 MCP 协议的工具系统：

| 工具 | 功能 | MCP Server |
|------|------|------------|
| **Calculator** | 数学计算（支持四则运算、幂运算、括号） | CalculatorMCPServer |
| **Weather** | 天气查询（OpenWeatherMap API） | WeatherMCPServer |
| **Search** | 网络搜索（模拟） | SearchMCPServer |

### 3. 会话管理

**业务层（永久存储）**：
- PostgreSQL 数据库存储所有会话和消息
- 支持会话列表、搜索、编辑、删除
- 记录完整的 timeline（thinking + tool_call + content）

**SDK 层（运行时缓存）**：
- ADK SessionService 管理当前对话状态
- 自动累积和传递多轮上下文
- 内存存储，进程重启后清空

### 4. 消息编辑

支持编辑历史消息并重新生成 AI 回复：
- 软删除原消息及后续所有回复
- 保留编辑历史（parent_message_id）
- 自动重新生成助手回复

### 5. Token 实时追踪

每次 LLM 调用完成时实时推送和显示：
- **推送信息**：
  - 输入/输出/总计 token 数量
  - 调用序号和耗时（毫秒）
  - 会话累计 token 数
  - 上下文使用率百分比
- **UI 显示**：
  - 顶部 ContextProgress 组件实时更新
  - 显示本次调用的 token 使用量
  - 圆形进度条动态显示（如：`2.3K / 32K context used`）
  - 颜色根据使用率自动调整（< 70% 灰色，70-90% 橙色，> 90% 红色）
- **控制台日志**：
  ```
  [LLM调用 #3] Tokens: 1498(输入) + 819(输出) = 2317(总计), 
  耗时: 12974ms, 会话累计: 4143 tokens, 上下文使用率: 12.95%
  ```

## 📚 详细文档

- [项目结构文档](./project-structure.md) - 完整的目录结构说明
- [技术栈文档](./tech-stack.md) - 技术选型和版本说明
- [AI 架构文档](./backend/app/ai/ARCHITECTURE.md) - AI 模块详细设计
- [MCP 协议文档](./backend/app/ai/mcp/README.md) - MCP 实现说明

## 🧪 测试

### 后端测试

```bash
cd backend

# 运行所有测试
pytest

# 运行特定测试
pytest tests/test_adk_session.py

# 运行 MCP 工具测试
python tests/test_real_mcp.py
```

### 前端测试

```bash
cd frontend

# 运行测试
npm test
```

## 📊 性能指标

- **响应延迟**：< 100ms（首字响应）
- **流式输出**：实时（< 10ms 每个 chunk）
- **并发支持**：100+ WebSocket 连接
- **数据库查询**：< 50ms（索引优化）

## 🔐 安全特性

- JWT 令牌认证
- 密码 bcrypt 加密
- SQL 注入防护（ORM）
- XSS 防护（前端）
- CORS 配置
- WebSocket 鉴权

## 🛠️ 开发工具

### 后端调试

```bash
# 查看日志
tail -f backend/uvicorn.log

# 数据库迁移
alembic revision --autogenerate -m "description"
alembic upgrade head
```

### 前端调试

```bash
# 类型检查
npm run type-check

# Lint
npm run lint
```

## 📝 更新日志

### 2025-10-10

#### 📊 LLM Token 实时追踪与显示
- **实时推送**：每次 LLM 调用完成时推送详细的 token 统计信息
  - 输入/输出/总计 token 数量
  - 调用序号和耗时
  - 会话累计 token 数
  - 上下文使用率百分比
- **UI 实时更新**：ContextProgress 组件实时显示本次调用的 token 使用量
  - 圆形进度条动态更新（`2.3K / 32K context used`）
  - 颜色根据使用率自动调整（灰色→橙色→红色）
  - 平滑动画过渡效果
- **新增事件类型**：`LLM_INVOCATION_COMPLETE` (5000) 

### 2025-10-09

#### ✨ 对话功能增强 (6a19824)
- 新增调用统计分析接口（`/api/analytics`）
- 实现 Token 使用追踪（InvocationLog 模型）
- 重构主键类型为整型，提升性能
- 优化 AI 模型调用记录
- 前端新增事件常量管理
- 改进错误处理和日志记录

### 2025-10-08

#### 🧠 智能摘要功能 (ab8fa75)
- 新增会话自动摘要生成
- 实现上下文进度追踪
- 添加上下文管理字段（`context_window_size`、`context_usage_percentage`）
- 前端新增上下文进度组件（ContextProgress）
- 优化聊天服务的上下文处理

### 2025-10-07

#### 📊 Token 统计 (bcce693)
- 实现 Token 使用记录和统计
- 新增速率限制中间件
- 增强 Redis 客户端功能
- 优化 ADK Agent 和 LLM 适配器
- 改进 WebSocket 连接管理
- 新增系统提示词配置

#### 📚 文档完善 (a0c389f)
- 创建完整的 README 文档
- 更新项目结构说明（project-structure.md）
- 添加技术栈详细说明

#### 🚀 核心架构实现 (8779dcb)
- 实现 Google ADK 集成
- 完整的 MCP 协议实现（JSON-RPC 2.0）
- 创建 ADK Agent 适配器
- 实现 ADK LLM 适配器（支持 Ollama/OpenAI）
- 新增 MCP 工具服务器和客户端
- 实现前端事件适配器

### 2025-10-06

#### 🎉 项目初始化 (f911252)
- 搭建 FastAPI + Next.js 基础架构
- 实现用户认证系统（JWT + bcrypt）
- 创建数据库模型（User、Session、Message、AIModel）
- 实现基础 AI 工具（Calculator、Weather、Search）
- 搭建 WebSocket 实时通信
- 配置 Docker 和 Alembic 数据库迁移
- 创建前端聊天界面和状态管理
- 编写项目结构和技术栈文档

## 🤝 贡献指南

欢迎贡献代码！请遵循以下步骤：

1. Fork 项目
2. 创建特性分支（`git checkout -b feature/AmazingFeature`）
3. 提交更改（`git commit -m 'Add some AmazingFeature'`）
4. 推送到分支（`git push origin feature/AmazingFeature`）
5. 开启 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

## 🙏 致谢

- [Google ADK](https://github.com/google/generative-ai-python) - Agent Development Kit
- [FastAPI](https://fastapi.tiangolo.com/) - 现代化 Web 框架
- [Next.js](https://nextjs.org/) - React 框架
- [Ollama](https://ollama.ai/) - 本地 LLM 运行
- [Model Context Protocol](https://spec.modelcontextprotocol.io/) - 工具协议标准

## 📞 联系方式

- 项目主页：[GitHub](https://github.com/Fischlvor/agent/)
- 问题反馈：[Issues](https://github.com/Fischlvor/agent/issues)

---

**Built with ❤️ using Google ADK and MCP**

