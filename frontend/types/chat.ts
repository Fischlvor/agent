/**
 * 聊天相关的 TypeScript 类型定义
 */

// ============ AI 模型 ============

export interface AIModel {
  id: string;
  name: string;
  model_id: string;
  provider: string;
  base_url: string;
  description?: string;
  max_tokens: number;
  supports_streaming: boolean;
  supports_tools: boolean;
  is_active: boolean;
  icon_url?: string;
  display_order: number;
  config?: Record<string, any>;
  created_at: string;
  updated_at: string;
}

// ============ 会话 ============

export interface ChatSession {
  id: string;
  session_id?: string;
  user_id: string;
  title?: string;
  description?: string;
  status?: string;
  is_pinned: boolean;
  last_activity_at?: string;
  message_count: number;
  total_tokens: number;
  ai_model?: string;
  temperature: number;
  max_tokens: number;
  system_prompt?: string;
  created_at: string;
  updated_at: string;
  // 上下文管理
  current_context_tokens?: number;
  max_context_tokens?: number;
  context_usage_percent?: number;
  // 未读消息标记
  hasNewMessage?: boolean;
}

export interface CreateSessionRequest {
  title?: string;
  ai_model?: string;
  system_prompt?: string;
  temperature?: number;
  max_tokens?: number;
}

export interface UpdateSessionRequest {
  title?: string;
  is_pinned?: boolean;
  system_prompt?: string;
  temperature?: number;
  ai_model?: string;
}

export interface SessionListResponse {
  sessions: ChatSession[];
  next_cursor?: string;
  has_more: boolean;
}

// ============ 消息 ============

export interface TimelineEvent {
  type: 'thinking' | 'tool_call' | 'content';
  thinking_id?: string;  // ✅ for thinking (unique ID)
  content?: string;  // for thinking
  tool_id?: string;  // ✅ for tool_call (unique ID)
  tool_name?: string;  // for tool_call
  tool_args?: Record<string, any>;  // for tool_call
  result?: any;  // for tool_call
  status?: 'pending' | 'success' | 'error' | string;  // ✅ 支持自定义状态（如"深度思考中"）
  timestamp: string;
}

export interface ChatMessage {
  id: string;
  message_id?: string;
  session_id: string;
  parent_message_id?: string;
  role: 'user' | 'assistant' | 'system' | 'tool';
  content?: string;
  message_type?: string;
  status?: string;
  is_edited: boolean;
  is_deleted: boolean;
  is_pinned: boolean;
  sent_at?: string;
  model_name?: string;
  prompt_tokens?: number;
  completion_tokens?: number;
  total_tokens?: number;
  generation_time?: number;
  structured_content?: Record<string, any>;
  user_rating?: number;
  user_feedback?: string;
  created_at: string;
  updated_at: string;

  // OpenAI标准字段（用于工具调用）
  tool_calls?: Array<{
    id: string;
    type: 'function';
    function: {
      name: string;
      arguments: string | Record<string, any>;
    };
  }>;
  tool_call_id?: string;
  name?: string;

  // 消息分类字段（前端渲染依赖）
  message_subtype?: 'thinking' | 'tool_call' | 'tool_result' | 'final_response';
  is_internal?: boolean;
  display_order?: number;

  // 前端扩展字段（兼容旧格式）
  timeline?: TimelineEvent[];  // ✅ 事件时间线（逐步废弃）
}

export interface UpdateMessageRequest {
  content: string;
}

// ============ WebSocket 消息类型 ============

/**
 * WebSocket消息外层包装（新格式）
 */
export interface WSMessageEnvelope {
  event_data: string;        // JSON字符串（实际消息内容）
  event_id: string;          // 事件序列号
  event_type: number;        // 事件类型代码
}

/**
 * event_data内部的消息块结构
 */
export interface WSMessageBlock {
  id: string;                // 消息块ID
  content_type: number;      // 内容类型代码
  content: string;           // 内容（JSON字符串）
  pid?: string;              // 父块ID（可选）
}

/**
 * event_data 解析后的基础结构
 */
export interface WSEventData {
  // 消息标识
  message_id: string;
  conversation_id: string;
  local_message_id?: string;

  // 消息块
  message?: WSMessageBlock;

  // 状态
  status: number;
  is_delta?: boolean;
  is_finish?: boolean;

  // 增强
  message_index?: number;
  generation_time?: number;

  // 上下文信息（done事件专用）
  context_info?: {
    current_context_tokens: number;
    max_context_tokens: number;
  };
}

/**
 * 旧版本类型（保留兼容）
 */
export type WSMessageType =
  | 'ping'
  | 'pong'
  | 'connected'
  | 'send_message'
  | 'stop_generation'
  | 'start'
  | 'thinking_start'
  | 'thinking_delta'
  | 'thinking_complete'
  | 'thinking'
  | 'tool_call'
  | 'tool_result'
  | 'content'
  | 'done'
  | 'llm_invocation_complete'
  | 'session_title_updated'
  | 'error'
  | 'info';

export interface WSBaseMessage {
  type: WSMessageType;
  session_id?: string;  // 会话ID，用于验证消息归属
}

export interface WSConnectedMessage extends WSBaseMessage {
  type: 'connected';
  message: string;
}

export interface WSPingMessage extends WSBaseMessage {
  type: 'ping';
}

export interface WSPongMessage extends WSBaseMessage {
  type: 'pong';
}

export interface WSSendMessageRequest extends WSBaseMessage {
  type: 'send_message';
  session_id: string;
  content: string;
  model_id?: string;
  skip_user_message?: boolean;  // ✅ 编辑后重新生成时不创建新的用户消息
  edited_message_id?: string;   // ✅ 编辑的消息ID（用于追踪和验证）
}

export interface WSStopGenerationRequest extends WSBaseMessage {
  type: 'stop_generation';
  session_id: string;
}

export interface WSStartMessage extends WSBaseMessage {
  type: 'start';
  message_id: string;
  event_id: number;
  event_type: number;
}

export interface WSThinkingStartMessage extends WSBaseMessage {
  type: 'thinking_start';
  thinking_id: string;
  title?: string;  // ✅ 思考标题（如"深度思考中"）
  status: string;
  event_id: number;
  event_type: number;
}

export interface WSThinkingDeltaMessage extends WSBaseMessage {
  type: 'thinking_delta';
  thinking_id: string;
  delta: string;
  event_id: number;
  event_type: number;
}

export interface WSThinkingCompleteMessage extends WSBaseMessage {
  type: 'thinking_complete';
  thinking_id: string;
  title?: string;  // ✅ 思考标题（如"已完成思考"）
  status: string;  // ✅ 只有状态标识，不含完整内容
  event_id: number;
  event_type: number;
}

export interface WSThinkingMessage extends WSBaseMessage {
  type: 'thinking';
  message: string;
}

export interface WSToolCallMessage extends WSBaseMessage {
  type: 'tool_call';
  tool_id?: string;  // ✅ 每轮唯一ID
  tool_name: string;
  tool_args: Record<string, any>;
  event_id: number;
  event_type: number;
}

export interface WSToolResultMessage extends WSBaseMessage {
  type: 'tool_result';
  tool_id?: string;  // ✅ 每轮唯一ID
  tool_name: string;
  result: any;
  event_id: number;
  event_type: number;
}

export interface WSContentMessage extends WSBaseMessage {
  type: 'content';
  delta: string;
  content?: string;  // ✅ 改为可选，后端只发送 delta
  event_id: number;
  event_type: number;
}

export interface WSDoneMessage extends WSBaseMessage {
  type: 'done';
  message_id: string;
  total_tokens?: number;
  prompt_tokens?: number;
  completion_tokens?: number;
  generation_time?: number;
  event_id: number;
  event_type: number;
  context_info?: {
    current_context_tokens: number;
    max_context_tokens: number;
  };
  session_info?: {
    session_id: string;
    message_count: number;
    total_prompt_tokens: number;
    total_completion_tokens: number;
    total_tokens: number;
  };
}

export interface WSErrorMessage extends WSBaseMessage {
  type: 'error';
  error: string;
  event_id: number;
  event_type: number;
}

export interface WSInfoMessage extends WSBaseMessage {
  type: 'info';
  message: string;
}

export interface WSSessionTitleUpdatedMessage extends WSBaseMessage {
  type: 'session_title_updated';
  session_id: string;
  title: string;
  event_id: number;
  event_type: number;
}

export interface WSLlmInvocationCompleteMessage extends WSBaseMessage {
  type: 'llm_invocation_complete';
  session_id: string;
  invocation: {
    sequence: number;
    tokens: {
      prompt: number;
      completion: number;
      total: number;
    };
    duration_ms: number;
    finish_reason: string;
  };
  session_cumulative_tokens: number;
  context_usage_percent: number;
  event_id: number;
  event_type: number;
}

export type WSMessage =
  | WSConnectedMessage
  | WSPingMessage
  | WSPongMessage
  | WSStartMessage
  | WSThinkingStartMessage        // ✅ 思考开始
  | WSThinkingDeltaMessage        // ✅ 思考增量
  | WSThinkingCompleteMessage     // ✅ 思考完成
  | WSThinkingMessage             // 兼容旧版本
  | WSToolCallMessage
  | WSToolResultMessage
  | WSContentMessage
  | WSDoneMessage
  | WSLlmInvocationCompleteMessage // ✅ LLM调用完成
  | WSSessionTitleUpdatedMessage  // ✅ 会话标题更新
  | WSErrorMessage
  | WSInfoMessage;

// ============ 聊天状态 ============

export interface ToolCall {
  tool_name: string;
  tool_args: Record<string, any>;
  result?: any;
  status: 'pending' | 'success' | 'error';
}

export interface StreamingMessage {
  id: string;
  session_id: string;  // ✅ 所属会话ID
  role: 'assistant';
  content: string;
  isStreaming: boolean;
  toolCalls: ToolCall[];
  thinking?: string;  // 保留用于兼容（已废弃）
  timeline?: TimelineEvent[];  // ✅ 事件时间线（多轮 thinking、tool_call）
  thinkingBuffer?: string;  // ✅ 当前正在进行的 thinking buffer
  currentThinkingId?: string | null;  // ✅ 当前正在进行的 thinking 块 ID
}

export type ChatStatus = 'idle' | 'connecting' | 'connected' | 'generating' | 'error';

