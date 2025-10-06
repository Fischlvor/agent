/**
 * 内容类型常量定义
 * 与后端保持一致
 */

export const ContentType = {
  TEXT: 10000,              // 普通文本内容
  THINKING: 10040,          // 思考内容
  TOOL_CALL: 10050,         // 工具调用
  TOOL_RESULT: 10051,       // 工具结果
  ERROR: 10099,             // 错误信息
} as const;

export type ContentTypeValue = typeof ContentType[keyof typeof ContentType];

/**
 * 消息状态常量定义
 */
export const MessageStatus = {
  COMPLETED: 1,             // 已完成
  PENDING: 4,               // 进行中
  ERROR: 5,                 // 错误
} as const;

export type MessageStatusValue = typeof MessageStatus[keyof typeof MessageStatus];

/**
 * 获取内容类型名称
 */
export function getContentTypeName(contentType: number): string {
  const contentTypeMap: Record<number, string> = {
    [ContentType.TEXT]: '文本',
    [ContentType.THINKING]: '思考',
    [ContentType.TOOL_CALL]: '工具调用',
    [ContentType.TOOL_RESULT]: '工具结果',
    [ContentType.ERROR]: '错误',
  };
  return contentTypeMap[contentType] || `未知类型(${contentType})`;
}

/**
 * 获取消息状态名称
 */
export function getMessageStatusName(status: number): string {
  const statusMap: Record<number, string> = {
    [MessageStatus.COMPLETED]: '已完成',
    [MessageStatus.PENDING]: '进行中',
    [MessageStatus.ERROR]: '错误',
  };
  return statusMap[status] || `未知状态(${status})`;
}

