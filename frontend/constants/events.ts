/**
 * WebSocket事件类型常量定义
 * 与后端保持一致
 */

export const EventType = {
  // 系统事件 (1xxx)
  CONNECTED: 1000,
  DISCONNECTED: 1001,
  ERROR: 1999,

  // 消息事件 (2xxx)
  MESSAGE_START: 2000,
  MESSAGE_CONTENT: 2001,
  MESSAGE_DONE: 2002,

  // 思考事件 (3xxx)
  THINKING_START: 3000,
  THINKING_DELTA: 3001,
  THINKING_COMPLETE: 3002,

  // 工具调用事件 (4xxx)
  TOOL_CALL: 4000,
  TOOL_RESULT: 4001,

  // 心跳事件 (9xxx)
  PING: 9000,
  PONG: 9001,
} as const;

export type EventTypeValue = typeof EventType[keyof typeof EventType];

/**
 * 获取事件类型名称
 */
export function getEventTypeName(eventType: number): string {
  const eventTypeMap: Record<number, string> = {
    [EventType.CONNECTED]: '连接成功',
    [EventType.DISCONNECTED]: '连接断开',
    [EventType.ERROR]: '错误',
    [EventType.MESSAGE_START]: '消息开始',
    [EventType.MESSAGE_CONTENT]: '消息内容',
    [EventType.MESSAGE_DONE]: '消息完成',
    [EventType.THINKING_START]: '思考开始',
    [EventType.THINKING_DELTA]: '思考增量',
    [EventType.THINKING_COMPLETE]: '思考完成',
    [EventType.TOOL_CALL]: '工具调用',
    [EventType.TOOL_RESULT]: '工具结果',
    [EventType.PING]: '心跳请求',
    [EventType.PONG]: '心跳响应',
  };
  return eventTypeMap[eventType] || `未知事件(${eventType})`;
}

