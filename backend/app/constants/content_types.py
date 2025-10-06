"""内容类型常量定义"""


class ContentType:
    """内容类型枚举"""

    TEXT = 10000          # 普通文本内容
    THINKING = 10040      # 思考内容
    TOOL_CALL = 10050     # 工具调用
    TOOL_RESULT = 10051   # 工具结果
    ERROR = 10099         # 错误信息


class MessageStatus:
    """消息状态枚举"""

    COMPLETED = 1         # 已完成
    PENDING = 4           # 进行中
    ERROR = 5             # 错误


def get_content_type_name(content_type: int) -> str:
    """获取内容类型名称"""
    content_type_map = {
        ContentType.TEXT: "文本",
        ContentType.THINKING: "思考",
        ContentType.TOOL_CALL: "工具调用",
        ContentType.TOOL_RESULT: "工具结果",
        ContentType.ERROR: "错误",
    }
    return content_type_map.get(content_type, f"未知类型({content_type})")


def get_message_status_name(status: int) -> str:
    """获取消息状态名称"""
    status_map = {
        MessageStatus.COMPLETED: "已完成",
        MessageStatus.PENDING: "进行中",
        MessageStatus.ERROR: "错误",
    }
    return status_map.get(status, f"未知状态({status})")

