# 智能 Agent 开发技术栈（基于 Google ADK + MCP）

## 后端技术栈

| 类别 | 技术 | 版本 | 用途 |
|------|------|------|------|
| **编程语言** | Python | 3.11+ | 主要编程语言 |
| **Web框架** | FastAPI | 0.104+ | API开发 |
| **AI Agent框架** | Google ADK | 0.1.0+ | Agent 开发工具包 |
| **RAG框架** | LangChain | 0.1.0+ | 文档处理和检索增强 |
| **ORM** | SQLAlchemy | 2.0+ | 数据库交互 |
| **数据库** | PostgreSQL | 14+ | 元数据存储（支持 pgvector 扩展） |
| **向量检索** | FAISS | 1.7+ | 向量索引和检索（CPU/GPU）⭐ |
| **向量扩展** | pgvector | 0.5+ | PostgreSQL 向量类型（向量备份） |
| **HTTP客户端** | httpx | 0.25+ | API请求 |
| **数据验证** | Pydantic | 2.4+ | 数据模型 |
| **数据库迁移** | Alembic | 1.12+ | 数据库版本控制 |
| **文档解析** | PyMuPDF | 1.23+ | PDF 文档解析和文本提取 ⭐ |
| **文档加载** | python-docx | 最新 | Word 文档解析 |
| **嵌入模型** | BGE-M3 | - | 多语言文本嵌入（**GPU 加速**）⭐ |
| **重排序模型** | BGE-Reranker-V2-M3 | - | 结果重排序（**GPU 加速**）⭐ |
| **认证** | python-jose | 3.3.0+ | JWT认证 |
| **ASGI服务器** | Uvicorn | 0.24.0+ | 服务器 |
| **缓存** | Redis | 5.0+ | 速率限制和缓存 |

## 前端技术栈

| 类别 | 技术 | 版本 | 用途 |
|------|------|------|------|
| **框架** | Next.js | 14+ | React框架（App Router）|
| **编程语言** | TypeScript | 5.2+ | 类型系统 |
| **UI库** | shadcn/ui | 最新 | UI组件 |
| **样式** | TailwindCSS | 3.3+ | CSS框架 |
| **状态管理** | Zustand | 4.4+ | 全局状态管理 ⭐ |
| **API请求** | TanStack Query | 5.0+ | 数据获取 |
| **HTTP客户端** | Axios | 1.6.0+ | API通信 |
| **动画** | requestAnimationFrame | 原生 | 数值平滑动画 ⭐ |
| **表单处理** | React Hook Form | 7.45+ | 表单验证和处理 |
| **Markdown渲染** | React Markdown | 9+ | Markdown内容展示 |
| **图标库** | Heroicons | 2.0+ | UI图标 |

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

## RAG 技术栈（已实现）⭐

| 组件 | 技术 | 说明 |
|------|------|------|
| **文档解析** | PyMuPDF + python-docx | 支持 PDF、Word、TXT、HTML 等格式 |
| **文本分块** | Parent-Child Chunking | 父块（2048 tokens）+ 子块（512 tokens） |
| **文本向量化** | BGE-M3 | 多语言嵌入模型（GPU 加速） |
| **向量索引** | FAISS | 内存索引 + 磁盘持久化（CPU/GPU 可选） |
| **向量检索** | Inner Product / L2 Distance | FAISS 内置检索算法 |
| **元数据存储** | PostgreSQL + pgvector | 数据库存储（支持 Vector 类型） |
| **结果重排** | BGE-Reranker-V2-M3 | Cross-Encoder 重排序（GPU 加速） |
| **RAG Tool** | RAGMCPServer | 作为 MCP Tool 供 Agent 调用 |

### 数据模型设计

| 模型 | 字段 | 说明 |
|------|------|------|
| **KnowledgeBase** | id, name, description, config | 知识库管理 |
| **Document** | id, kb_id, title, format, status | 文档元数据 |
| **DocumentChunk** | id, doc_id, chunk_type, content, embedding | 统一父子块（支持 Vector 类型） |

### GPU 加速服务

| 服务 | GPU 加速 | 性能提升 |
|------|----------|----------|
| **BGE Embeddings（向量化）** | ✅ 强制 | 7-10倍（相比 CPU） |
| **BGE Reranker（重排序）** | ✅ 强制 | 12倍（相比 CPU） |
| **FAISS 检索** | 🔄 可选 | 支持 GPU 但当前使用 CPU |

**说明**：
- FAISS 索引存储在内存中，检索速度极快
- 索引会持久化到磁盘文件：`data/knowledge_base/faiss_indexes/kb_{kb_id}.faiss`
- PostgreSQL 存储元数据和向量备份（pgvector Vector 类型）
- 混合架构：快速检索（FAISS）+ 数据一致性（PostgreSQL）
