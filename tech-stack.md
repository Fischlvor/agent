# 智能 Agent 开发技术栈（基于 Google ADK + MCP）

## 后端技术栈

| 类别 | 技术 | 版本 | 用途 |
|------|------|------|------|
| **编程语言** | Python | 3.11+ | 主要编程语言 |
| **Web框架** | FastAPI | 0.104+ | API开发 |
| **AI Agent框架** | Google ADK | 0.1.0+ | Agent 开发工具包 |
| **RAG框架** | LangChain | 0.1.0+ | 文档处理和检索增强 |
| **ORM** | SQLAlchemy | 2.0+ | 数据库交互 |
| **数据库** | MySQL | 8.0+ | 数据存储 |
| **HTTP客户端** | httpx | 0.25+ | API请求 |
| **数据验证** | Pydantic | 2.4+ | 数据模型 |
| **数据库迁移** | Alembic | 1.12+ | 数据库版本控制 |
| **向量存储** | FAISS | 1.7+ | 向量检索（RAG） |
| **文档加载** | PyPDF, python-docx | 最新 | 文档解析（RAG） |
| **认证** | python-jose | 3.3.0+ | JWT认证 |
| **ASGI服务器** | Uvicorn | 0.24.0+ | 服务器 |
| **缓存** | Redis | 5.0+ | 速率限制和缓存 |

## 前端技术栈

| 类别 | 技术 | 版本 | 用途 |
|------|------|------|------|
| **框架** | Next.js | 14+ | React框架 |
| **编程语言** | TypeScript | 5.2+ | 类型系统 |
| **UI库** | shadcn/ui | 最新 | UI组件 |
| **样式** | TailwindCSS | 3.3+ | CSS框架 |
| **状态管理** | Zustand | 4.4+ | 前端状态 |
| **API请求** | TanStack Query | 5.0+ | 数据获取 |
| **HTTP客户端** | Axios | 1.6.0+ | API通信 |
| **动画** | Framer Motion | 10.16+ | UI动画效果 |
| **表单处理** | React Hook Form | 7.45+ | 表单验证和处理 |

## 开发与部署工具

| 类别 | 技术 | 版本 | 用途 |
|------|------|------|------|
| **容器化** | Docker | 最新 | 环境隔离 |
| **版本控制** | Git | 最新 | 代码版本管理 |
| **CI/CD** | GitHub Actions | 最新 | 自动化部署 |
| **API测试** | Postman | 最新 | API测试和文档 |

## Google ADK 核心组件

| 组件 | 用途 | 说明 |
|------|------|------|
| **Agent** | 智能代理 | 自主决策和工具调用的 AI 代理 |
| **Runner** | 运行时管理 | 管理 Agent 的执行流程和多轮对话 |
| **BaseLlm** | LLM 接口 | 统一的语言模型接口抽象 |
| **FunctionTool** | 工具定义 | 将 Python 函数包装为 Agent 可调用工具 |
| **SessionService** | 会话管理 | 管理用户会话和对话历史 |
| **Content/Part** | 消息结构 | 标准化的消息格式定义 |

## MCP 协议组件

| 组件 | 用途 | 说明 |
|------|------|------|
| **MCP Server** | 工具服务器 | 提供工具能力的独立服务 |
| **MCP Client** | 工具客户端 | 连接和管理多个 MCP 服务器 |
| **JSON-RPC 2.0** | 通信协议 | 标准化的远程过程调用协议 |
| **Tool Discovery** | 工具发现 | 自动发现和注册可用工具 |

## RAG 组件（基于 LangChain）

| 组件 | 用途 | 说明 |
|------|------|------|
| **Document Loaders** | 文档加载 | 支持 PDF、Word、HTML 等多种格式 |
| **Text Splitters** | 文本分块 | 智能切分长文档为可检索片段 |
| **Embeddings** | 文本向量化 | 调用自有 embeddings 接口生成向量 |
| **Vector Stores** | 向量数据库 | FAISS 或 MySQL 向量字段存储 |
| **Retrievers** | 信息检索 | 基于语义相似度检索相关文档 |
| **RAG Tool** | 检索工具 | 作为 MCP Tool 供 Agent 调用 | 