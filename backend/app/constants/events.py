"""WebSocket事件类型常量定义"""

class EventType:
    """WebSocket事件类型枚举"""

    # 系统事件 (1xxx)
    CONNECTED = 1000  # WebSocket连接成功
    DISCONNECTED = 1001  # WebSocket断开连接
    ERROR = 1999  # 错误事件

    # 消息事件 (2xxx)
    MESSAGE_START = 2000  # 消息生成开始
    MESSAGE_CONTENT = 2001  # 消息内容（流式增量）
    MESSAGE_DONE = 2002  # 消息生成完成

    # 思考事件 (3xxx)
    THINKING_START = 3000  # 思考开始
    THINKING_DELTA = 3001  # 思考内容增量
    THINKING_COMPLETE = 3002  # 思考完成

    # 工具调用事件 (4xxx)
    TOOL_CALL = 4000  # 工具调用
    TOOL_RESULT = 4001  # 工具执行结果

    # 调用追踪事件 (5xxx)
    LLM_INVOCATION_COMPLETE = 5000  # LLM调用完成
    TOOL_INVOCATION_COMPLETE = 5001  # 工具调用完成

    # 会话事件 (6xxx)
    SESSION_TITLE_UPDATED = 6000  # 会话标题已更新

    # 心跳事件 (9xxx)
    PING = 9000  # 心跳请求
    PONG = 9001  # 心跳响应


def get_event_type_name(event_type: int) -> str:
    """获取事件类型名称"""
    event_type_map = {
        EventType.CONNECTED: "连接成功",
        EventType.DISCONNECTED: "连接断开",
        EventType.ERROR: "错误",
        EventType.MESSAGE_START: "消息开始",
        EventType.MESSAGE_CONTENT: "消息内容",
        EventType.MESSAGE_DONE: "消息完成",
        EventType.THINKING_START: "思考开始",
        EventType.THINKING_DELTA: "思考增量",
        EventType.THINKING_COMPLETE: "思考完成",
        EventType.TOOL_CALL: "工具调用",
        EventType.TOOL_RESULT: "工具结果",
        EventType.LLM_INVOCATION_COMPLETE: "LLM调用完成",
        EventType.TOOL_INVOCATION_COMPLETE: "工具调用完成",
        EventType.SESSION_TITLE_UPDATED: "会话标题更新",
        EventType.PING: "心跳请求",
        EventType.PONG: "心跳响应",
    }
    return event_type_map.get(event_type, f"未知事件({event_type})")

