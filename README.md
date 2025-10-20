# 🤖 智能 Agent 系统

基于 **FastAPI** + **Next.js** + **Google ADK** + **MCP** 构建的现代化智能对话系统。

## ✨ 核心特性

- 🚀 **实时流式响应**：支持 thinking（思考过程）、tool_call（工具调用）、content（回复内容）的流式输出
- 🧠 **多轮对话**：基于 Google ADK 的会话管理，自动维护上下文
- 🔧 **MCP 协议**：完整实现 Model Context Protocol（JSON-RPC 2.0）
- 🛠️ **动态工具加载**：计算器、天气查询、网络搜索等工具自动集成
- 📚 **RAG 知识库**：基于 LangChain 的文档检索增强，支持 PDF/Word/HTML 等多种格式
- ⚡ **异步文档处理**：上传立即返回（< 0.5秒），后台处理 + WebSocket 实时推送状态
- 💾 **双层会话管理**：业务层持久化 + SDK 层运行时缓存
- 🔐 **用户认证**：JWT 双 Token 机制 + Token 绑定 + 自动刷新
- 📊 **结构化存储**：完整记录 thinking 和 tool_call timeline
- 📈 **实时 Token 追踪**：每次 LLM 调用的 token 使用量实时推送和动画显示
- 🎨 **现代化 UI**：ChatGPT 风格界面 + 欢迎页面 + 流畅动画效果
- ⚡ **性能优化**：全局初始化避免重复请求，局部状态更新，智能缓存提升响应速度

## 🏗️ 技术架构

### 后端技术栈

| 技术 | 版本 | 说明 |
|------|------|------|
| **Python** | 3.11+ | 编程语言 |
| **FastAPI** | 0.109+ | Web 框架 |
| **Google ADK** | 0.1.0+ | Agent Development Kit |
| **SQLAlchemy** | 2.0+ | ORM 框架 |
| **PostgreSQL** | 14+ | 数据库（支持 pgvector） |
| **pgvector** | 0.5+ | 向量检索扩展 |
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
| **Google ADK** | Agent 开发工具包，管理对话和工具调用 |
| **Ollama** | 本地 LLM 运行（Qwen3:8b） |
| **OpenAI** | OpenAI API 支持（可选） |
| **MCP** | 工具协议标准化（JSON-RPC 2.0） |
| **LangChain** | RAG 文档处理和检索增强 |
| **FAISS** | 向量检索引擎（内存 + 磁盘持久化） |
| **pgvector** | PostgreSQL 向量扩展（向量备份） |
| **BGE-M3** | 多语言文本嵌入模型（GPU 加速） |
| **BGE-Reranker-V2-M3** | 结果重排序模型（GPU 加速） |

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
│   │   │       ├── general/   # 通用工具（计算器、天气等）
│   │   │       └── rag/       # RAG 检索工具 📚
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
- PostgreSQL 14+（需启用 pgvector 扩展）
- Redis 6+（用于 Token 和缓存管理）
- Ollama（用于本地 LLM）
- GPU（可选，用于 RAG 加速）

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
| **RAG Retriever** | 知识库检索（语义搜索）📚 | RAGMCPServer |

### 3. 会话管理

**业务层（永久存储）**：
- MySQL 数据库存储所有会话和消息
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

### 6. RAG 知识库管理 📚

基于 **pgvector** + **LangChain** 的文档检索增强系统（**已实现**）：

**数据模型**：
- `KnowledgeBase`：知识库管理（名称、描述、配置）
- `Document`：文档元数据（标题、格式、状态、token 数）
- `DocumentChunk`：统一父子块模型
  - 父块（Parent）：粗粒度上下文（2048 tokens）
  - 子块（Child）：细粒度检索（512 tokens）

**文档处理**（⚡ 异步优化）：
- 支持多种格式：PDF、Word、TXT、HTML、Markdown
- **异步处理架构**：上传立即返回（< 0.5秒），后台处理（ThreadPoolExecutor）
- **实时状态推送**：processing → completed，无需轮询
- 智能文本切分：父子分块策略（Parent-Child Chunking）
- 文本向量化：BGE-M3 多语言模型（**GPU 加速 7-10x**）
- 向量检索：FAISS 索引（内存检索 + 磁盘持久化）
- 向量备份：PostgreSQL + pgvector（支持 Vector 类型）
- 结果重排序：BGE-Reranker-V2-M3（**GPU 加速 12x**）

**知识库功能**：
- 完整的 CRUD API：`/api/v1/rag/knowledge-bases`
- **异步文档上传**：`/api/v1/rag/knowledge-bases/{id}/upload`（立即返回）
- **WebSocket 实时通知**：`DOCUMENT_STATUS_UPDATE` (7000)，推送完整文档信息
- **局部状态更新**：前端无刷新体验，流畅的 UI 更新
- 自动文本切分和向量化
- 语义相似度检索（支持跨语言：中文查询英文文档）
- 两阶段检索：召回（Vector Search）+ 重排（Cross-Encoder）
- 作为 MCP 工具供 Agent 调用（RAGMCPServer）

**前端界面**：
- 知识库列表：`/knowledge-bases`
- 知识库详情：`/knowledge-bases/[id]`
- 文档上传和管理
- 实时处理状态显示

**GPU 性能优势**：
- ⚡ 文本向量化速度提升 **7-10倍**（BGE-M3，相比 CPU）
- ⚡ 重排序速度提升 **12倍**（Reranker，相比 CPU）
- ⚡ 端到端检索延迟降低到 **30-50ms**（原 300-500ms）
- 📊 支持更大的知识库（100K+ 向量）
- 🔥 支持 NVIDIA TITAN / RTX 系列 GPU

**使用流程**：
```
1. 用户上传文档（PDF/Word/TXT 等）
2. PyMuPDF 解析文档，提取文本和元数据
3. 按章节智能切分为父块（2048 tokens）和子块（512 tokens）
4. BGE-M3 模型生成向量（GPU 加速）
5. 向量存入 FAISS 索引（内存）并持久化到磁盘
6. 元数据和向量备份存入 PostgreSQL（pgvector）
7. Agent 对话时自动调用 RAG 工具检索
   - 第一阶段：向量召回 Top-20 子块（FAISS 内存检索）
   - 第二阶段：重排序选出 Top-5 父块（Reranker GPU）
8. LLM 基于检索结果生成回答
```

**快速开始**：
```bash
cd backend
./setup_gpu.sh  # 自动配置 GPU 环境
# 详见 backend/GPU_OPTIMIZATION.md 和 backend/RAG_TESTING.md
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
- **文档上传**：< 0.5s（上传接口响应，异步处理）
- **文档处理**：2-3s（后台解析、切分、向量化，10 页 PDF）
- **向量检索**：30-50ms（FAISS 内存检索 + GPU 重排序）

## 🔐 安全特性

### 认证与授权
- **JWT 双 Token 机制**：
  - Access Token（JWT，60分钟有效）：用于 API 请求认证
  - Refresh Token（UUID，7天有效）：用于刷新 Access Token
  - Token 绑定机制：Access Token 与 Refresh Token 关联，删除 Refresh Token 后 Access Token 立即失效
- **会话管理**：
  - Refresh Token 存储在 Redis（支持多设备登录）
  - 登出时删除 Refresh Token，Access Token 立即失效
  - Token 刷新时删除旧 Token，防止重放攻击
- **中间件保护**：
  - JWT 中间件自动验证 Token 有效性
  - Token 失效时直接返回 401（不继续执行请求）
  - 支持黑名单机制（强制登出）

### 数据安全
- 密码 bcrypt 加密（自动加盐）
- SQL 注入防护（SQLAlchemy ORM）
- XSS 防护（前端输入过滤）
- CORS 配置（限制跨域访问）

### 通信安全
- WebSocket 鉴权（Token 验证）
- HTTPS 支持（生产环境推荐）
- Cookie HttpOnly + SameSite（防 CSRF）

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

### 2025-10-20 (最新)

#### ⚡ RAG 文档处理异步化与前端局部更新优化 ⭐

**核心改进**：将文档处理改为真正的异步任务，上传接口立即返回（< 0.5秒），通过 WebSocket 实时推送状态和完整文档信息，前端采用局部更新策略提升用户体验。

**后端优化**：
- **异步任务架构** (`documents.py`)：
  - 新增 ThreadPoolExecutor（4线程）+ 独立事件循环执行文档处理
  - 上传接口立即返回 PROCESSING 状态，后台任务处理解析、分块、向量化
  - 修复 BackgroundTasks 参数顺序问题，避免 FastAPI 验证错误
- **WebSocket 推送增强** (`chat_ws.py`)：
  - notify_document_status 新增 filesize、page_count、chunk_count、parent_chunk_count 参数
  - 完成时推送完整文档信息，前端无需额外 API 调用
- **数据库会话管理** (`documents.py`)：
  - 后台任务使用独立数据库 session（SESSION_LOCAL），避免与主请求 session 冲突
  - 自动关闭 session，防止资源泄漏
- **JWT 中间件优化** (`jwt_middleware.py`)：
  - PUBLIC_PATHS 改用 set 数据结构（O(1) 查找效率）
  - 新增 /api/v1/sso/auth/refresh 到公开路径，修复 token 刷新被拦截问题
  - 新增调试日志记录 upload 请求
- **文档列表排序** (`knowledge_service.py`)：
  - list_documents 查询添加 ORDER BY created_at DESC
  - 新上传文档始终显示在列表最前面

**前端优化**：
- **局部状态更新** (`page.tsx`)：
  - WebSocket 收到状态更新时，使用 setDocuments + map 局部修改对应文档
  - 避免整个列表重新加载，消除闪烁
  - 接收并更新文档详细信息（filesize、page_count、chunk_count）
- **乐观更新策略** (`page.tsx`)：
  - 上传成功后立即在列表顶部添加新文档（状态 PROCESSING）
  - 删除文档时直接从列表中过滤，无需重新加载
- **最小化 API 调用** (`page.tsx`)：
  - 移除上传进度条状态（uploadProgress）
  - 仅在 completed/failed 时刷新知识库统计信息
  - processing 状态无需任何 API 调用
- **修复 Authorization header** (`rag.ts`)：
  - 移除 multipart/form-data 上传时手动设置的 Content-Type
  - 让 axios 自动处理，避免覆盖 Authorization header

**性能提升**：
- 上传接口响应时间：4.6s → < 0.5s（提升 90%+）
- 列表刷新方式：整页重载 → 局部更新（0 次闪烁）
- API 调用次数：每次 2 个请求 → 仅完成时 1 个请求（减少 50%）
- 并发上传支持：串行阻塞 → 并发处理（线程池）

---

#### 🔐 安全修复：Token 绑定机制 ⭐
- **问题**：用户登出后，Access Token 在过期前（60分钟）仍可使用
- **修复方案**：实现 Access Token 与 Refresh Token 绑定机制
  - Token 生成：在 Access Token（JWT）中存储 `refresh_token_id`
  - Token 验证：每次请求时检查绑定的 Refresh Token 是否存在
  - 立即失效：删除 Refresh Token 后，Access Token 立即失效
- **中间件拦截**：
  - 验证失败时直接返回 401（不继续执行请求）
  - Token 格式错误 → 401：无效的Token格式
  - Token 缺少绑定 → 401：Token格式不支持（请重新登录）
  - Refresh Token 失效 → 401：Token已失效（会话已结束）
  - 系统错误 → 503：认证服务暂时不可用
- **前端优化**：
  - 修复 refresh token 失败时的死循环问题
  - 失败时同步清除 localStorage 和 authStore
  - 添加防重复跳转机制
- **影响**：所有旧版本 Token（无 `refresh_token_id`）不再兼容，需重新登录
- **参考文档**：详见本次修复的 commit 记录

### 2025-10-20

#### 📚 RAG 知识库系统（已完整实现）⭐
- **核心框架**：
  - 基于 **LangChain** 构建完整 RAG 管道
  - 文档加载器（Document Loaders）、文本分块器（Text Splitters）
  - 向量存储（Vector Stores）、检索器（Retrievers）
- **数据模型**：
  - `KnowledgeBase`：知识库管理（名称、描述、配置、统计）
  - `Document`：文档元数据（标题、格式、状态、token数）
  - `DocumentChunk`：统一父子块模型（支持 pgvector）
- **后端服务**：
  - `KnowledgeService`：知识库 CRUD 和文档管理
  - `PDFParser`：多格式文档解析（PyMuPDF/python-docx）
  - `VectorStore`：FAISS 向量索引（内存 + 磁盘持久化）
  - `RetrievalService`：两阶段检索链（召回+重排）
  - `BGEEmbeddings`：BGE-M3 嵌入模型（GPU 加速）
  - `RerankerService`：BGE-Reranker-V2-M3 重排序（GPU 加速）
- **前端界面**：
  - 知识库列表页（`/knowledge-bases`）
  - 知识库详情页（`/knowledge-bases/[id]`）
  - 文档上传和管理
  - 实时处理状态显示（DOCUMENT_STATUS_UPDATE 事件）
- **API端点**：
  - `/api/v1/rag/knowledge-bases`：知识库 CRUD
  - `/api/v1/rag/documents`：文档上传和管理
- **向量检索架构**：
  - FAISS 向量索引：内存检索 + 磁盘持久化
  - PostgreSQL：元数据存储 + 向量备份（pgvector）
  - 混合架构：快速检索 + 数据一致性
- **工具集成**：
  - RAGMCPServer 作为 MCP Tool 供 Agent 调用
  - 支持语义搜索和多语言检索

### 2025-10-19

#### 🎨 UI/UX 重大优化
- **ChatGPT 风格界面**：
  - 新增欢迎页面（`WelcomeScreen`）：大输入框 + 快速提示词
  - 动态路由：`/chat`（欢迎页）+ `/chat/[sessionId]`（会话详情页）
  - 会话创建流程优化：输入后自动创建会话并跳转
- **用户体验提升**：
  - 新增用户头像菜单（`UserMenu`）：头像、用户名、邮箱、退出登录
  - 删除当前会话自动跳转欢迎页
  - 访问不存在会话自动跳转欢迎页
  - 平滑的页面过渡和路由切换
- **动画效果**：
  - Token 使用圆形进度条平滑动画（`useAnimatedNumber` Hook）
  - 数值变化采用 `easeOutCubic` 缓动函数
  - 进度条更新时脉冲发光效果
- **性能优化**：
  - ✅ 全局初始化优化：避免重复请求 models/sessions/knowledge-bases
  - ✅ 知识库缓存到 store：只加载一次
  - ✅ 切换会话不再重复初始化：从 ~15 个请求降至 0 个
  - 页面切换速度提升 90%

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

