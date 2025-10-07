# AI 模块架构文档

**目录**: `backend/app/ai/`  
**更新时间**: 2025-10-07

---

## 📂 目录结构

```
backend/app/ai/
├── adk_agent_adapter.py       # ADK Agent 主适配器（核心入口）
├── adk_llm_adapter.py          # LLM 客户端适配器
├── adk_session_service.py      # ADK 会话服务
├── frontend_event_adapter.py   # 前端事件格式转换（ADK → 前端展示）
├── mcp_tools_adapter.py        # MCP → ADK 工具适配
├── factory.py                  # AI 客户端工厂
│
├── mcp/                        # 真正的 MCP 协议实现
│   ├── protocol.py            # MCP 协议定义（JSON-RPC）
│   ├── server.py              # MCP Server 基类
│   ├── client.py              # MCP Client 实现
│   └── tools_server.py        # 具体工具服务器
│
├── clients/                    # LLM 客户端实现
│   ├── base.py                # 客户端基类
│   └── qwen_client.py         # Qwen/Ollama 客户端
│
└── tools/                      # 工具实现
    ├── base.py                # 工具基类
    └── general/               # 通用工具（计算器、天气、搜索）
```

---

## 🎯 核心文件说明

### 1. **`adk_agent_adapter.py`** - 主入口 ⭐⭐⭐⭐⭐

**角色**: 整个 AI 系统的核心适配器

**主要功能**:
- 作为 ChatService 和 ADK Agent 之间的桥梁
- 管理完整的对话流程（包括多轮工具调用）
- 通过 MCP 动态加载工具
- 转换事件格式供前端展示

**关键类**:
```python
class ADKAgentAdapter:
    async def run_streaming(
        messages,      # 对话历史
        system_prompt, # 系统提示
        user_id,       # 用户ID
        session_id     # 会话ID
    ) -> AsyncIterator[Dict]:
        # 返回流式事件
```

**调用者**: `ChatService`  
**依赖**:
- `ADKLlmAdapter` - LLM 通信
- `SimpleSessionService` - 会话管理
- `FrontendEventAdapter` - 前端格式转换
- `mcp_tools_adapter` - MCP 工具加载

---

### 2. **`adk_llm_adapter.py`** - LLM 适配器 ⭐⭐⭐⭐

**角色**: 将我们的 LLM 客户端适配到 ADK 的 `BaseLlm` 接口

**主要功能**:
- 实现 ADK 要求的 `generate_content_async()` 方法
- 转换消息格式：ADK ↔ Ollama/OpenAI
- 处理工具调用和结果
- 流式响应处理

**关键流程**:
```
ADK LlmRequest
    ↓
转换为 Ollama 格式
    ↓
调用 our_client.chat()
    ↓
流式接收响应
    ↓
转换为 ADK LlmResponse
```

**调用者**: `ADK Agent` (由 Google ADK 框架调用)  
**依赖**: `BaseAIClient` (Qwen/OpenAI 客户端)

---

### 3. **`adk_session_service.py`** - 会话服务 ⭐⭐⭐

**角色**: 为 ADK Runner 提供会话管理（SDK 层面自动管理）

**主要功能**:
- 创建、获取、删除会话
- **自动存储**会话事件（包括 thinking、tool_calls、tool_results）
- **自动传递**历史上下文给 LLM
- 内存存储（简化实现）

**关键类**:
```python
class SimpleSessionService(BaseSessionService):
    async def create_session(app_name, user_id, session_id)
    async def get_session(app_name, user_id, session_id)
    async def delete_session(app_name, user_id, session_id)
```

**为什么必需？**
虽然代码看起来简单，但这是 **ADK Runner 的必需参数**。ADK 在 SDK 内部会：
1. 自动调用 SessionService 存储每轮对话的事件
2. 在多轮对话中自动加载历史事件
3. 维护完整的对话上下文

**测试验证**（见 `tests/test_adk_session.py`）:
- ✅ 第一轮对话后，会话中自动存储了 592 个事件
- ✅ 第二轮对话时，LLM 能够正确记住之前的内容
- ✅ 工具调用历史正确传递给 LLM
- ✅ 多轮对话上下文完美保持

**调用者**: `ADK Runner` (ADK 框架内部自动调用)  
**依赖**: 无

---

### 4. **`frontend_event_adapter.py`** - 前端事件转换器 ⭐⭐⭐

**角色**: 将 ADK 事件转换为前端展示格式

**主要功能**:
- 提取文本内容（content）
- 提取思考内容（thinking，从 `<think>` 标签）
- 提取工具调用（tool_call）
- 提取工具结果（tool_result）

**注意**: 这不是真正的 MCP 协议（工具调用），只是用于前端展示的格式转换

**关键流程**:
```
ADK Event (Google 格式)
    ↓
提取 content.parts
    ↓
检测 <think> 标签
    ↓
返回前端展示格式的事件字典
```

**调用者**: `ADKAgentAdapter`  
**依赖**: MCP 事件格式定义（复用数据结构）

---

### 5. **`mcp_tools_adapter.py`** - MCP 工具适配器 ⭐⭐⭐⭐

**角色**: 将 MCP 工具转换为 ADK FunctionTool

**主要功能**:
- 为会话设置 MCP 工具
- 从 MCP Client 获取所有工具
- 为每个 MCP 工具创建 ADK 包装
- 自动生成函数签名和文档

**关键函数**:
```python
async def setup_mcp_tools_for_session(session_id) -> MCPClient:
    # 创建 MCP 客户端
    # 注册所有工具服务器
    # 返回配置好的客户端

async def create_mcp_tools_for_adk(mcp_client) -> List[FunctionTool]:
    # 列出所有 MCP 工具
    # 为每个工具创建 ADK FunctionTool
    # 返回工具列表
```

**调用者**: `ADKAgentAdapter`  
**依赖**: `MCP Client`, `MCP Server`

---

### 6. **`factory.py`** - 客户端工厂 ⭐⭐⭐

**角色**: 创建和管理 LLM 客户端实例

**主要功能**:
- 根据 provider 创建对应客户端
- 单例模式（同一配置复用实例）
- 支持多种 LLM 提供商

**关键类**:
```python
class AIFactory:
    def create_client(
        provider: str,     # "ollama", "openai" 等
        model_name: str,   # 模型名称
        base_url: str      # API 地址
    ) -> BaseAIClient
```

**调用者**: `ChatService`, 测试代码  
**依赖**: `BaseAIClient`, 各个具体客户端

---

## 🏗️ MCP 模块（`mcp/`）

### 7. **`mcp/protocol.py`** - MCP 协议定义 ⭐⭐⭐⭐

**角色**: 定义 MCP 标准协议的所有数据结构

**主要内容**:
- JSON-RPC 2.0 基础类型
- 工具定义（ToolDefinition, ToolCallRequest, ToolCallResult）
- 资源定义（Resource, ResourceContent）
- 提示定义（Prompt）
- 初始化和能力声明

**用途**: 被所有 MCP 相关模块使用

---

### 8. **`mcp/server.py`** - MCP Server 基类 ⭐⭐⭐⭐

**角色**: 提供 MCP 服务器的抽象基类

**主要功能**:
- 处理 JSON-RPC 请求
- 路由到具体的处理器
- 初始化握手
- 工具列表和调用

**关键类**:
```python
class MCPServer(ABC):
    async def handle_request(request_data) -> response_data
    
    @abstractmethod
    async def get_tools() -> List[ToolDefinition]
    
    @abstractmethod
    async def call_tool(name, arguments) -> ToolCallResult

class InProcessMCPServer(MCPServer):
    # 进程内服务器（当前使用）

class StdioMCPServer(MCPServer):
    # 标准输入/输出服务器（用于子进程）
```

**子类**: `CalculatorMCPServer`, `WeatherMCPServer`, `SearchMCPServer`

---

### 9. **`mcp/client.py`** - MCP Client ⭐⭐⭐⭐

**角色**: MCP 客户端，负责与 MCP 服务器通信

**主要功能**:
- 注册和管理多个 MCP 服务器
- 自动发现工具
- 路由工具调用到正确的服务器
- 会话级客户端池

**关键类**:
```python
class MCPClient:
    async def register_server(name, server)
    async def list_all_tools() -> Dict[server_name, tools]
    async def call_tool(tool_name, arguments) -> ToolCallResult

class MCPClientPool:
    def get_or_create_client(session_id) -> MCPClient
```

**调用者**: `mcp_tools_adapter`  
**依赖**: `MCP Server` 实例

---

### 10. **`mcp/tools_server.py`** - 具体工具服务器 ⭐⭐⭐

**角色**: 将具体工具包装为 MCP 服务器

**实现的服务器**:
- `CalculatorMCPServer` - 计算器
- `WeatherMCPServer` - 天气查询
- `SearchMCPServer` - 网络搜索

**每个服务器**:
```python
class CalculatorMCPServer(InProcessMCPServer):
    async def get_tools():
        # ✅ 从 BaseTool 自动提取参数描述
        params = CalculatorTool.get_parameters()
        
        # 构建 MCP 工具定义
        properties = {}
        for param_name, param_info in params.items():
            properties[param_name] = {
                "type": "string",
                "description": param_info.description  # 使用真实描述
            }
        
        return [ToolDefinition(
            name="calculate",
            description=CalculatorTool.get_description(),
            inputSchema={"type": "object", "properties": properties}
        )]
    
    async def call_tool(name, arguments):
        # 执行工具
        result = await self.calculator.execute(...)
        return ToolCallResult(content=[...])
```

**依赖**: `tools/general/` 下的具体工具实现

---

## 📦 支持模块

### 11. **`clients/base.py`** - 客户端基类

**角色**: 定义所有 LLM 客户端的统一接口

**关键方法**:
```python
class BaseAIClient(ABC):
    @abstractmethod
    async def chat(messages, tools, stream) -> AsyncIterator
```

---

### 12. **`clients/qwen_client.py`** - Qwen 客户端

**角色**: Ollama/Qwen 的具体实现

**主要功能**:
- 调用 Ollama API
- 处理流式响应
- 支持工具调用

---

### 13. **`tools/base.py`** - 工具基类

**角色**: 定义所有工具的统一接口

**关键方法**:
```python
class BaseTool(ABC):
    @abstractmethod
    async def execute(**kwargs) -> Any
    
    def get_name() -> str
    def get_description() -> str
```

---

### 14. **`tools/general/`** - 通用工具

包含具体的工具实现：
- `calculator.py` - 计算器工具
- `weather.py` - 天气查询工具
- `search.py` - 搜索工具

---

## 🔄 完整调用流程图

### 1️⃣ **用户发送消息的完整流程**

```
┌─────────────────────────────────────────────────────────────────┐
│                          用户发送消息                            │
│                    "北京天气怎么样？"                            │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│  1. ChatService (app/services/chat_service.py)                  │
│     - 接收 WebSocket 消息                                        │
│     - 获取历史对话                                               │
│     - 调用 Agent                                                 │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│  2. AIFactory.create_client()                                    │
│     ├─ 创建 QwenClient 实例                                     │
│     └─ 返回 BaseAIClient                                        │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│  3. ADKAgentAdapter.__init__()                                   │
│     ├─ 创建 ADKLlmAdapter(our_client)                           │
│     ├─ 创建 SimpleSessionService()                              │
│     └─ 创建 FrontendEventAdapter()                              │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│  4. ADKAgentAdapter.run_streaming()                              │
│                                                                   │
│     步骤 A: 加载工具（通过 MCP）                                │
│     ┌───────────────────────────────────────────────┐           │
│     │ setup_mcp_tools_for_session(session_id)      │           │
│     │   ├─ 获取/创建 MCP Client                     │           │
│     │   ├─ 创建 Calculator MCP Server              │           │
│     │   ├─ 创建 Weather MCP Server                 │           │
│     │   ├─ 创建 Search MCP Server                  │           │
│     │   └─ 注册所有服务器到客户端                  │           │
│     └───────────────────────────────────────────────┘           │
│                         │                                        │
│     ┌───────────────────────────────────────────────┐           │
│     │ create_mcp_tools_for_adk(mcp_client)         │           │
│     │   ├─ 调用 mcp_client.list_all_tools()        │           │
│     │   │   └─ 每个 Server 返回工具定义            │           │
│     │   └─ 为每个工具创建 ADK FunctionTool         │           │
│     └───────────────────────────────────────────────┘           │
│                         │                                        │
│     步骤 B: 创建 ADK Agent 和 Runner                            │
│     ┌───────────────────────────────────────────────┐           │
│     │ Agent(model=adk_llm, tools=adk_tools)        │           │
│     │ Runner(agent=agent, session_service=...)     │           │
│     └───────────────────────────────────────────────┘           │
│                         │                                        │
│     步骤 C: 运行 Runner（流式）                                 │
│     ┌───────────────────────────────────────────────┐           │
│     │ async for event in runner.run_async()        │           │
│     └───────────────────────────────────────────────┘           │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│  5. ADK Runner 自动循环                                          │
│                                                                   │
│     [轮次 1] LLM 决策                                            │
│     ┌───────────────────────────────────────────────┐           │
│     │ ADKLlmAdapter.generate_content_async()       │           │
│     │   ├─ 转换 ADK Request → Ollama 格式         │           │
│     │   ├─ 调用 our_client.chat(stream=True)      │           │
│     │   ├─ QwenClient → Ollama API                │           │
│     │   └─ 返回: tool_call(get_weather, "北京")   │           │
│     └───────────────────────────────────────────────┘           │
│                         │                                        │
│     [轮次 2] 执行工具                                            │
│     ┌───────────────────────────────────────────────┐           │
│     │ ADK 调用 FunctionTool.func()                 │           │
│     │   ├─ FunctionTool 调用 mcp_client.call_tool()│           │
│     │   ├─ MCP Client 路由到 Weather Server       │           │
│     │   ├─ Weather Server 调用 WeatherTool.execute()│          │
│     │   └─ 返回: {"temp": 25°C, "weather": "晴"}  │           │
│     └───────────────────────────────────────────────┘           │
│                         │                                        │
│     [轮次 3] LLM 生成最终回答                                    │
│     ┌───────────────────────────────────────────────┐           │
│     │ ADKLlmAdapter.generate_content_async()       │           │
│     │   ├─ 发送给 LLM（带上工具结果）              │           │
│     │   └─ 返回: "北京今天25°C，天气晴朗..."       │           │
│     └───────────────────────────────────────────────┘           │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│  6. FrontendEventAdapter.convert_adk_event_stream()              │
│     ├─ 提取文本内容                                             │
│     ├─ 提取 <think> 标签（如果有）                              │
│     ├─ 提取工具调用                                             │
│     ├─ 提取工具结果                                             │
│     └─ 转换为前端展示格式                                       │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│  7. ADKAgentAdapter._frontend_to_chat_format()                   │
│     └─ 最后一层格式转换（前端格式 → ChatService 格式）          │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│  8. ChatService 接收流式事件                                     │
│     ├─ {type: "content", content: "北京今天..."}                │
│     ├─ {type: "tool_call", tool_name: "get_weather", ...}       │
│     ├─ {type: "tool_result", result: {...}}                     │
│     └─ 通过 WebSocket 发送给前端                                │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🎨 模块关系图

```
┌─────────────────────────────────────────────────────────────────┐
│                        AI 模块架构                               │
│                                                                   │
│  ┌────────────────────────────────────────────────────────┐     │
│  │              ADKAgentAdapter (核心)                     │     │
│  │          ┌──────────┬──────────┬──────────┐            │     │
│  │          │          │          │          │            │     │
│  │          ▼          ▼          ▼          ▼            │     │
│  │   ┌──────────┐ ┌────────┐ ┌────────┐ ┌──────────┐    │     │
│  │   │   LLM    │ │Session │ │  MCP   │ │   MCP    │    │     │
│  │   │ Adapter  │ │Service │ │Frontend│ │  Tools   │    │     │
│  │   │          │ │        │ │ Event  │ │  Adapter │    │     │
│  │   └─────┬────┘ └────────┘ └────────┘ └────┬─────┘    │     │
│  └─────────┼─────────────────────────────────┼──────────┘     │
│            │                                   │                │
│            ▼                                   ▼                │
│  ┌──────────────────┐              ┌──────────────────┐        │
│  │   LLM Clients    │              │   MCP System     │        │
│  │                  │              │                  │        │
│  │  ┌────────────┐  │              │  ┌────────────┐ │        │
│  │  │  Factory   │  │              │  │   Client   │ │        │
│  │  └─────┬──────┘  │              │  └─────┬──────┘ │        │
│  │        │         │              │        │        │        │
│  │        ▼         │              │        ▼        │        │
│  │  ┌────────────┐  │              │  ┌────────────┐ │        │
│  │  │QwenClient  │  │              │  │  Servers   │ │        │
│  │  │(Ollama)    │  │              │  │            │ │        │
│  │  └────────────┘  │              │  │Calculator  │ │        │
│  │                  │              │  │Weather     │ │        │
│  │  BaseAIClient    │              │  │Search      │ │        │
│  └──────────────────┘              │  └─────┬──────┘ │        │
│                                    │        │        │        │
│                                    │        ▼        │        │
│                                    │  ┌────────────┐ │        │
│                                    │  │   Tools    │ │        │
│                                    │  │(实际实现)   │ │        │
│                                    │  └────────────┘ │        │
│                                    └──────────────────┘        │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📝 关键数据流

### 工具调用的两条路径

```
┌─────────────────────────────────────────────────────────────────┐
│                      工具结果的两条路径                          │
│                                                                   │
│  ADK 执行工具 → 得到结果                                         │
│        │                                                          │
│        ├──────────────────┬──────────────────┐                   │
│        │                  │                  │                   │
│        ▼                  ▼                  ▼                   │
│   路径 1: 传给 LLM    路径 2: 传给前端                           │
│   (内部循环)          (事件流)                                   │
│        │                  │                                      │
│        ▼                  ▼                                      │
│  ADKLlmAdapter      FrontendEventAdapter                         │
│  (不经过 MCP)       (转换为展示格式)                             │
│        │                  │                                      │
│        ▼                  ▼                                      │
│  {"role": "tool",   {"type": "tool_result",                     │
│   "content": ...}    "result": ...}                             │
│        │                  │                                      │
│        ▼                  ▼                                      │
│  发送给 Ollama      发送给前端                                   │
│  (下一轮对话)       (实时展示)                                   │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🔑 关键设计模式

### 1. **适配器模式** (Adapter Pattern)

```
外部接口 → 适配器 → 内部实现

例如：
ChatService → ADKAgentAdapter → ADK Agent
BaseAIClient → ADKLlmAdapter → ADK BaseLlm
BaseTool → CalculatorMCPServer → MCP Server
```

### 2. **工厂模式** (Factory Pattern)

```
AIFactory.create_client(provider, model_name)
  ├─ "ollama" → QwenClient
  ├─ "openai" → OpenAIClient
  └─ "anthropic" → AnthropicClient (未来)
```

### 3. **策略模式** (Strategy Pattern)

```
不同的 LLM 客户端实现相同接口
  ├─ BaseAIClient (抽象基类)
  ├─ QwenClient (Ollama 实现)
  └─ OpenAIClient (OpenAI 实现)
```

### 4. **观察者模式** (Observer Pattern)

```
流式响应（AsyncIterator）
  └─ 每个事件通知订阅者（ChatService）
```

---

## 💡 设计亮点

### 1. **解耦与标准化**
- 通过 MCP 协议解耦工具实现
- 通过适配器解耦外部框架（ADK）
- 符合行业标准（MCP, JSON-RPC）

### 2. **可扩展性**
- 新增 LLM 只需实现 `BaseAIClient`
- 新增工具只需创建 `MCPServer`
- 支持外部 MCP 服务器

### 3. **流式处理**
- 所有核心流程支持流式
- 实时响应，用户体验好
- 资源利用率高

### 4. **会话隔离**
- 每个会话独立的 MCP Client
- 会话级工具状态管理
- 避免跨会话干扰

---

## 📖 使用示例

### 基本用法

```python
# 1. 创建客户端
from app.ai.factory import FACTORY
client = FACTORY.create_client("ollama", "qwen3:8b")

# 2. 创建 Agent
from app.ai.adk_agent_adapter import ADKAgentAdapter
agent = ADKAgentAdapter(client)

# 3. 运行（工具自动通过 MCP 加载）
async for event in agent.run_streaming(
    messages=[{"role": "user", "content": "计算 2+2"}],
    session_id="session_123"
):
    print(event)
    # {"type": "tool_call", "tool_name": "calculate", ...}
    # {"type": "tool_result", "result": {"result": 4}}
    # {"type": "content", "content": "2+2等于4"}
```

---

## 🚀 未来扩展

1. **外部 MCP Server 支持**
   - Stdio 通信
   - WebSocket 远程连接

2. **更多 LLM 支持**
   - Anthropic Claude
   - Google Gemini
   - 本地模型

3. **MCP 功能扩展**
   - Resources（资源访问）
   - Prompts（提示模板）

4. **性能优化**
   - 工具结果缓存
   - 并行工具调用
   - 连接池管理

---

## 📚 相关文档

- `mcp/README.md` - MCP 详细文档
- `MCP_IMPLEMENTATION_COMPLETE.md` - MCP 实现报告
- `CLEANUP_SUMMARY.md` - 代码清理总结

---

**这份文档展示了 AI 模块的完整架构和协作关系！** 🎉

