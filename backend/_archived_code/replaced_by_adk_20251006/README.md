# 已归档代码 - ADK 替换

**备份时间**: 2025-10-06  
**原因**: Google ADK Agent 集成完成，这些文件已被新的适配器替代

---

## 📂 目录结构

```
app/ai/
├── agent_service.py          # 原 Agent 服务 -> 现使用 adk_agent_adapter.py
├── function_calling.py        # 原函数调用逻辑 -> 现由 ADK 内置处理
└── tools/
    ├── executor.py            # 原工具执行器 -> 现由 ADK 内置处理
    ├── gateway.py             # 原工具网关 -> 现由 ADK 内置处理
    └── registry.py            # 原工具注册表 -> 现由 adk_tools_adapter.py 处理
```

---

## 🔄 替代方案

| 原文件 | 原路径 | 替代方案 | 新路径 |
|--------|--------|----------|--------|
| `agent_service.py` | `app/ai/` | ADK Agent 适配器 | `app/ai/adk_agent_adapter.py` |
| `function_calling.py` | `app/ai/` | ADK 内置功能 | - |
| `tools/executor.py` | `app/ai/tools/` | ADK 内置功能 | - |
| `tools/gateway.py` | `app/ai/tools/` | ADK 内置功能 | - |
| `tools/registry.py` | `app/ai/tools/` | ADK 工具适配器 | `app/ai/adk_tools_adapter.py` |

---

## 💡 为什么备份？

这些文件代表了之前自建的 Agent 系统实现，包含：
- Agent 服务逻辑
- 函数调用处理
- 工具管理系统

虽然已被 Google ADK 替代，但保留备份用于：
1. **参考**: 了解原有实现逻辑
2. **回滚**: 如果需要回退到原系统
3. **审计**: 代码演进历史追溯

---

## 🔍 代码特点

### agent_service.py
- 实现了完整的 Agent 执行流程
- 包含工具调用、流式响应等功能
- 与 ChatService 紧密集成

### function_calling.py
- 处理函数调用的格式转换
- 支持 OpenAI 格式的函数定义
- 参数验证和结果解析

### tools/executor.py
- 工具执行的核心逻辑
- 异步工具调用支持
- 错误处理和重试机制

### tools/gateway.py
- 工具注册和发现
- 权限控制
- 调用路由

### tools/registry.py
- 工具元数据管理
- Schema 生成
- 工具查询接口

---

## ✅ 迁移验证

ADK 集成已完成全面测试：
- ✅ 端到端测试通过
- ✅ 工具调用正常
- ✅ 流式响应正确
- ✅ 与 ChatService 兼容

详见: `../../ADK_MIGRATION_COMPLETE.md`

---

## 🔗 相关文档

- ADK 集成总结: `../../ADK_INTEGRATION_SUMMARY.md`
- 迁移完成报告: `../../ADK_MIGRATION_COMPLETE.md`
- 项目结构文档: `../../../project-structure.md`

---

**注意**: 这些文件仅供参考和备份，不应在生产环境中使用。

