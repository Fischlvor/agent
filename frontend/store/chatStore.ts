/**
 * 聊天状态管理 Store (Zustand)
 */

import { create } from 'zustand';
import type {
  AIModel,
  ChatSession,
  ChatMessage,
  StreamingMessage,
  ToolCall,
  ChatStatus,
  WSMessage,
  WSMessageEnvelope,
  WSEventData
} from '@/types/chat';
import { ChatWebSocketManager } from '@/lib/websocket';
import { apiClient } from '@/lib/api';
import { EventType } from '@/constants/events';
import { ContentType, MessageStatus } from '@/constants/contentTypes';

interface ChatState {
  // 连接状态
  status: ChatStatus;
  wsManager: ChatWebSocketManager | null;
  error: string | null;
  messageTimeout: NodeJS.Timeout | null;  // ✅ 消息超时定时器

  // 模型
  models: AIModel[];
  currentModel: string | null;

  // 会话
  sessions: ChatSession[];
  currentSession: ChatSession | null;
  hasMoreSessions: boolean;

  // 消息
  messages: ChatMessage[];
  streamingMessage: StreamingMessage | null;

  // Actions
  // 连接管理
  connect: (token: string) => Promise<void>;
  disconnect: () => void;

  // 模型管理
  loadModels: () => Promise<void>;
  setCurrentModel: (modelId: string) => void;

  // 会话管理
  loadSessions: (cursor?: string) => Promise<void>;
  createSession: (title?: string) => Promise<void>;
  selectSession: (sessionId: string) => Promise<void>;
  updateSessionTitle: (sessionId: string, title: string) => Promise<void>;
  deleteSession: (sessionId: string) => Promise<void>;

  // 消息管理
  loadMessages: (sessionId: string) => Promise<void>;
  sendMessage: (content: string) => void;
  stopGeneration: () => void;
  editMessage: (messageId: string, newContent: string) => Promise<void>;
  editMessageAndRegenerate: (messageId: string, newContent: string) => Promise<void>;
  deleteMessage: (messageId: string) => Promise<void>;

  // WebSocket 消息处理
  parseWSMessageEnvelope: (envelope: WSMessageEnvelope) => WSMessage | null;
  handleWSMessage: (message: WSMessage) => void;

  // 清空状态
  reset: () => void;
}

const WS_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

export const useChatStore = create<ChatState>((set, get) => ({
  // 初始状态
  status: 'idle',
  wsManager: null,
  error: null,
  messageTimeout: null,  // ✅ 消息超时定时器
  models: [],
  currentModel: null,
  sessions: [],
  currentSession: null,
  hasMoreSessions: false,
  messages: [],
  streamingMessage: null,

  // ============ 连接管理 ============

  connect: async (token: string) => {
    const { wsManager } = get();

    // 如果已连接，直接返回
    if (wsManager?.isConnected) {
      return;
    }

    set({ status: 'connecting', error: null });

    try {
      const manager = new ChatWebSocketManager(WS_BASE_URL, token);

      // 注册消息处理器
      manager.on('message', (rawMessage: any) => {
        let message: WSMessage | null = null;

        // 检测是否为新格式（包含 event_data, event_id, event_type）
        if (rawMessage.event_data !== undefined && rawMessage.event_type !== undefined) {
          // 新格式：解析 envelope
          message = get().parseWSMessageEnvelope(rawMessage as WSMessageEnvelope);
        } else {
          // 旧格式：直接使用
          message = rawMessage as WSMessage;
        }

        if (message) {
          get().handleWSMessage(message);
        }
      });

      manager.on('close', () => {
        set({ status: 'idle' });
      });

      manager.on('error', (error) => {
        set({ status: 'error', error: error.message || 'WebSocket error' });
      });

      await manager.connect();

      set({ wsManager: manager, status: 'connected' });
    } catch (error: any) {
      set({ status: 'error', error: error.message || 'Failed to connect' });
      throw error;
    }
  },

  disconnect: () => {
    const { wsManager, messageTimeout } = get();

    // ✅ 清除超时定时器
    if (messageTimeout) {
      clearTimeout(messageTimeout);
    }

    if (wsManager) {
      wsManager.disconnect();
      set({ wsManager: null, status: 'idle', messageTimeout: null });
    }
  },

  // ============ 模型管理 ============

  loadModels: async () => {
    try {
      const models = await apiClient.getModels();
      set({ models, currentModel: models[0]?.model_id || null });
    } catch (error) {
      console.error('Failed to load models', error);
    }
  },

  setCurrentModel: (modelId: string) => {
    set({ currentModel: modelId });
  },

  // ============ 会话管理 ============

  loadSessions: async (cursor?: string) => {
    try {
      const response = await apiClient.getSessions(cursor);
      set((state) => ({
        sessions: cursor ? [...state.sessions, ...response.sessions] : response.sessions,
        hasMoreSessions: response.has_more
      }));
    } catch (error) {
      console.error('Failed to load sessions', error);
    }
  },

  createSession: async (title?: string) => {
    try {
      const session = await apiClient.createSession({
        title: title || '新对话',
        ai_model: get().currentModel || undefined
      });
      set((state) => ({
        sessions: [session, ...state.sessions],
        currentSession: session,
        messages: []
      }));
    } catch (error) {
      console.error('Failed to create session', error);
      throw error;
    }
  },

  selectSession: async (sessionId: string) => {
    try {
      const session = await apiClient.getSession(sessionId);
      set({ currentSession: session });
      await get().loadMessages(sessionId);
    } catch (error) {
      console.error('Failed to select session', error);
    }
  },

  updateSessionTitle: async (sessionId: string, title: string) => {
    try {
      const updatedSession = await apiClient.updateSession(sessionId, { title });
      set((state) => ({
        sessions: state.sessions.map((s) => (s.id === sessionId ? updatedSession : s)),
        currentSession: state.currentSession?.id === sessionId ? updatedSession : state.currentSession
      }));
    } catch (error) {
      console.error('Failed to update session', error);
    }
  },

  deleteSession: async (sessionId: string) => {
    try {
      await apiClient.deleteSession(sessionId);
      set((state) => ({
        sessions: state.sessions.filter((s) => s.id !== sessionId),
        currentSession: state.currentSession?.id === sessionId ? null : state.currentSession,
        messages: state.currentSession?.id === sessionId ? [] : state.messages
      }));
    } catch (error) {
      console.error('Failed to delete session', error);
    }
  },

  // ============ 消息管理 ============

  loadMessages: async (sessionId: string) => {
    try {
      const response = await apiClient.getMessages(sessionId);

      // ✅ 解析 structured_content，提取 timeline
      const messagesWithExtras = response.messages.map((msg) => {
        if (msg.role === 'assistant' && msg.structured_content?.timeline) {
          return {
            ...msg,
            timeline: msg.structured_content.timeline  // ✅ 直接使用时间线
          };
        }
        return msg;
      });

      set({ messages: messagesWithExtras });
    } catch (error) {
      console.error('Failed to load messages', error);
    }
  },

  sendMessage: (content: string) => {
    const { wsManager, currentSession, currentModel, messageTimeout } = get();

    if (!wsManager?.isConnected) {
      console.error('WebSocket not connected');
      return;
    }

    if (!currentSession) {
      console.error('No active session');
      return;
    }

    // ✅ 清除旧的超时定时器
    if (messageTimeout) {
      clearTimeout(messageTimeout);
    }

    // 发送 WebSocket 消息
    wsManager.send({
      type: 'send_message',
      session_id: currentSession.id,
      content,
      model_id: currentModel || undefined
    });

    // 添加用户消息到本地状态
    const userMessage: ChatMessage = {
      id: `temp-${Date.now()}`,
      session_id: currentSession.id,
      role: 'user',
      content,
      is_edited: false,
      is_deleted: false,
      is_pinned: false,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString()
    };

    // ✅ 启动 60 秒超时定时器
    const timeout = setTimeout(() => {
      const currentState = get();
      if (currentState.status === 'generating') {
        console.error('Message generation timeout');
        set({
          status: 'connected',
          error: '消息生成超时，请重试',
          streamingMessage: null,
          messageTimeout: null
        });

        // 3秒后清除错误
        setTimeout(() => {
          if (get().error === '消息生成超时，请重试') {
            set({ error: null });
          }
        }, 3000);
      }
    }, 60000);  // 60秒超时

    set((state) => ({
      messages: [...state.messages, userMessage],
      status: 'generating',
      messageTimeout: timeout
    }));
  },

  stopGeneration: () => {
    const { wsManager, currentSession } = get();

    if (wsManager?.isConnected && currentSession) {
      wsManager.send({
        type: 'stop_generation',
        session_id: currentSession.id
      });
    }
  },

  editMessage: async (messageId: string, newContent: string) => {
    try {
      await apiClient.updateMessage(messageId, { content: newContent });
      // 重新加载消息
      const { currentSession } = get();
      if (currentSession) {
        await get().loadMessages(currentSession.id);
      }
    } catch (error) {
      console.error('Failed to edit message', error);
    }
  },

  // ✅ 编辑消息并重新生成回复
  editMessageAndRegenerate: async (messageId: string, newContent: string) => {
    const { wsManager, currentSession, currentModel, messageTimeout } = get();

    if (!wsManager?.isConnected) {
      console.error('WebSocket not connected');
      return;
    }

    if (!currentSession) {
      console.error('No active session');
      return;
    }

    try {
      // 1. 编辑消息（后端会删除后续所有回复）
      await apiClient.updateMessage(messageId, { content: newContent });

      // 2. 重新加载消息列表
      await get().loadMessages(currentSession.id);

      // 3. 清除旧的超时定时器
      if (messageTimeout) {
        clearTimeout(messageTimeout);
      }

      // 4. 发送 WebSocket 消息重新生成回复（不创建新的用户消息）
      wsManager.send({
        type: 'send_message',
        session_id: currentSession.id,
        content: newContent,
        model_id: currentModel || undefined,
        skip_user_message: true,      // ✅ 告诉后端不要创建新的用户消息
        edited_message_id: messageId  // ✅ 标识正在编辑的消息ID
      });

      // 5. 设置生成状态和超时
      const timeout = setTimeout(() => {
        set({
          status: 'connected',
          error: '消息生成超时，请重试',
          messageTimeout: null,
          streamingMessage: null
        });
      }, 300000); // 5分钟超时

      set({ status: 'generating', messageTimeout: timeout });

    } catch (error) {
      console.error('Failed to edit message and regenerate', error);
      set({
        status: 'error',
        error: error instanceof Error ? error.message : '编辑消息失败'
      });
    }
  },

  deleteMessage: async (messageId: string) => {
    try {
      await apiClient.deleteMessage(messageId);
      set((state) => ({
        messages: state.messages.filter((m) => m.id !== messageId)
      }));
    } catch (error) {
      console.error('Failed to delete message', error);
    }
  },

  // ============ WebSocket 消息处理 ============

  /**
   * 解析新格式的 WebSocket 消息
   */
  parseWSMessageEnvelope: (envelope: WSMessageEnvelope): WSMessage | null => {
    try {
      const eventType = envelope.event_type;
      const eventData: WSEventData = JSON.parse(envelope.event_data);

      // 根据 event_type 转换为旧格式的 WSMessage
      switch (eventType) {
        case EventType.CONNECTED:
          return { type: 'connected', message: 'Connected' };

        case EventType.MESSAGE_START:
          return {
            type: 'start',
            message_id: eventData.message_id,
            event_id: Number(envelope.event_id),
            event_type: eventType
          };

        case EventType.MESSAGE_CONTENT:
          if (eventData.message) {
            const content = JSON.parse(eventData.message.content);
            return {
              type: 'content',
              delta: content.text || '',  // ✅ 统一使用 text 字段
              event_id: Number(envelope.event_id),
              event_type: eventType
            };
          }
          break;

        case EventType.MESSAGE_DONE:
          return {
            type: 'done',
            message_id: eventData.message_id,
            event_id: Number(envelope.event_id),
            event_type: eventType,
            generation_time: eventData.generation_time
          };

        case EventType.THINKING_START:
          if (eventData.message) {
            const content = JSON.parse(eventData.message.content);
            return {
              type: 'thinking_start',
              thinking_id: eventData.message.id,  // ✅ 从 message.id 获取
              title: content.finish_title || '',  // ✅ 对齐业界标准
              status: 'pending',
              event_id: Number(envelope.event_id),
              event_type: eventType
            };
          }
          break;

        case EventType.THINKING_DELTA:
          if (eventData.message) {
            const content = JSON.parse(eventData.message.content);
            return {
              type: 'thinking_delta',
              thinking_id: eventData.message.id,  // ✅ 从 message.id 获取
              delta: content.text || '',  // ✅ 统一使用 text 字段
              event_id: Number(envelope.event_id),
              event_type: eventType
            };
          }
          break;

        case EventType.THINKING_COMPLETE:
          if (eventData.message) {
            const content = JSON.parse(eventData.message.content);
            return {
              type: 'thinking_complete',
              thinking_id: eventData.message.id,  // ✅ 从 message.id 获取
              title: content.finish_title || '',  // ✅ 对齐业界标准
              status: 'success',
              event_id: Number(envelope.event_id),
              event_type: eventType
            };
          }
          break;

        case EventType.TOOL_CALL:
          if (eventData.message) {
            const content = JSON.parse(eventData.message.content);
            return {
              type: 'tool_call',
              tool_id: eventData.message.id,  // ✅ 获取 tool_id
              tool_name: content.name,  // ✅ 后端发送的是 name
              tool_args: content.args,  // ✅ 后端发送的是 args
              event_id: Number(envelope.event_id),
              event_type: eventType
            };
          }
          break;

        case EventType.TOOL_RESULT:
          if (eventData.message) {
            const content = JSON.parse(eventData.message.content);
            return {
              type: 'tool_result',
              tool_id: eventData.message.id,  // ✅ 获取 tool_id
              tool_name: content.name,  // ✅ 后端发送的是 name
              result: content.result,
              event_id: Number(envelope.event_id),
              event_type: eventType
            };
          }
          break;

        case EventType.ERROR:
          if (eventData.message) {
            const content = JSON.parse(eventData.message.content);
            return {
              type: 'error',
              error: content.error || '未知错误',
              event_id: Number(envelope.event_id),
              event_type: eventType
            };
          }
          break;

        case EventType.PONG:
          return { type: 'pong' };

        default:
          console.warn('Unknown event type:', eventType);
          return null;
      }

      return null;
    } catch (error) {
      console.error('Failed to parse message envelope:', error);
      return null;
    }
  },

  handleWSMessage: (message: WSMessage) => {
    // ✅ 清除超时定时器（除了 connected 和 pong）
    const { messageTimeout } = get();
    if (message.type !== 'connected' && message.type !== 'pong' && messageTimeout) {
      clearTimeout(messageTimeout);
      set({ messageTimeout: null });
    }

    switch (message.type) {
      case 'connected':
        console.log('WebSocket connected:', message.message);
        break;

      case 'pong':
        // 心跳响应，不需要处理
        break;

      case 'start':
        // 开始生成，创建流式消息
        set({
          streamingMessage: {
            id: message.message_id,
            role: 'assistant',
            content: '',
            isStreaming: true,
            toolCalls: [],
            timeline: [],  // ✅ 初始化 timeline
            thinkingBuffer: '',  // ✅ 用于累积当前正在进行的 thinking
            currentThinkingId: null  // ✅ 当前正在进行的 thinking 块 ID
          }
        });
        break;

      case 'thinking_start':
        // ✅ 思考开始（创建新的 thinking 块占位）
        set((state) => {
          if (!state.streamingMessage) return {};
          const newTimeline = [...(state.streamingMessage.timeline || [])];
          newTimeline.push({
            type: 'thinking',
            thinking_id: message.thinking_id,
            content: '',  // 开始时内容为空
            status: message.status,
            timestamp: new Date().toISOString()
          });
          return {
            streamingMessage: {
              ...state.streamingMessage,
              timeline: newTimeline,
              currentThinkingId: message.thinking_id,
              thinkingBuffer: ''
            }
          };
        });
        break;

      case 'thinking_delta':
        // ✅ 流式思考增量（累积到 buffer，更新 timeline 中的对应块）
        set((state) => {
          if (!state.streamingMessage) return {};
          const updatedTimeline = (state.streamingMessage.timeline || []).map((event) => {
            if (event.type === 'thinking' && event.thinking_id === message.thinking_id) {
              return {
                ...event,
                content: (event.content || '') + message.delta
              };
            }
            return event;
          });
          return {
            streamingMessage: {
              ...state.streamingMessage,
              timeline: updatedTimeline,
              thinkingBuffer: (state.streamingMessage.thinkingBuffer || '') + message.delta
            }
          };
        });
        break;

      case 'thinking_complete':
        // ✅ 思考完成（只标记状态，内容已通过 delta 累积完成）
        set((state) => {
          if (!state.streamingMessage) return {};
          const updatedTimeline = (state.streamingMessage.timeline || []).map((event) => {
            if (event.type === 'thinking' && event.thinking_id === message.thinking_id) {
              return {
                ...event,
                status: message.status  // 只更新状态
              };
            }
            return event;
          });
          return {
            streamingMessage: {
              ...state.streamingMessage,
              timeline: updatedTimeline,
              currentThinkingId: null,
              thinkingBuffer: ''
            }
          };
        });
        break;

      case 'thinking':
        // 兼容旧版本（已废弃）
        set((state) => {
          if (!state.streamingMessage) return {};
          return {
            streamingMessage: {
              ...state.streamingMessage,
              thinking: message.message
            }
          };
        });
        break;

      case 'tool_call':
        // ✅ 添加工具调用到 timeline
        set((state) => {
          if (!state.streamingMessage) return {};
          const newTimeline = [...(state.streamingMessage.timeline || [])];
          newTimeline.push({
            type: 'tool_call',
            tool_id: message.tool_id,  // ✅ 添加 tool_id
            tool_name: message.tool_name,
            tool_args: message.tool_args,
            status: 'pending',
            timestamp: new Date().toISOString()
          });

          // 同时保留旧的 toolCalls 数组（用于兼容）
          const toolCall: ToolCall = {
            tool_name: message.tool_name,
            tool_args: message.tool_args,
            status: 'pending'
          };

          return {
            streamingMessage: {
              ...state.streamingMessage,
              timeline: newTimeline,
              toolCalls: [...state.streamingMessage.toolCalls, toolCall]
            }
          };
        });
        break;

      case 'tool_result':
        // ✅ 更新工具调用结果（在 timeline 和 toolCalls 中都更新）
        set((state) => {
          if (!state.streamingMessage) return {};

          // ✅ 优先使用 tool_id 精确匹配，否则用 tool_name
          const updatedTimeline = [...(state.streamingMessage.timeline || [])];
          for (let i = updatedTimeline.length - 1; i >= 0; i--) {
            const event = updatedTimeline[i];
            if (event.type === 'tool_call' && event.status !== 'success') {
              // 优先用 tool_id 匹配，如果没有则用 tool_name
              const isMatch = message.tool_id
                ? event.tool_id === message.tool_id
                : event.tool_name === message.tool_name;

              if (isMatch) {
                updatedTimeline[i] = {
                  ...event,
                  result: message.result,
                  status: 'success' as const
                };
                break;  // ✅ 只更新最近的一个
              }
            }
          }

          // 更新 toolCalls 数组
          const updatedToolCalls = state.streamingMessage.toolCalls.map((tc) =>
            tc.tool_name === message.tool_name
              ? { ...tc, result: message.result, status: 'success' as const }
              : tc
          );

          return {
            streamingMessage: {
              ...state.streamingMessage,
              timeline: updatedTimeline,
              toolCalls: updatedToolCalls
            }
          };
        });
        break;

      case 'content':
        // ✅ 拼接增量内容
        set((state) => ({
          streamingMessage: state.streamingMessage
            ? {
                ...state.streamingMessage,
                content: state.streamingMessage.content + (message.delta || '')
              }
            : null
        }));
        break;

      case 'done':
        // 生成完成，保存消息
        const { streamingMessage, currentSession } = get();
        if (streamingMessage && currentSession) {
          // ✅ 直接使用 streamingMessage.timeline
          const finalMessage: ChatMessage = {
            id: message.message_id,
            session_id: currentSession.id,
            role: 'assistant',
            content: streamingMessage.content,
            is_edited: false,
            is_deleted: false,
            is_pinned: false,
            total_tokens: message.total_tokens,
            generation_time: message.generation_time,
            created_at: new Date().toISOString(),
            updated_at: new Date().toISOString(),
            timeline: streamingMessage.timeline  // ✅ 直接使用已构建的 timeline
          };

          set((state) => ({
            messages: [...state.messages, finalMessage],
            streamingMessage: null,
            status: 'connected'
          }));
        }
        break;

      case 'error':
        console.error('WebSocket error:', message.error);
        // ✅ 保存用户消息到历史（如果有）
        const { messages: errorMessages, currentSession: errorSession } = get();

        // 如果当前正在流式生成，保存到历史并清除
        const updatedMessages = get().streamingMessage
          ? [...errorMessages]  // 保留已有消息，放弃流式消息
          : errorMessages;

        set({
          status: 'connected',  // ✅ 恢复连接状态，允许重试
          error: message.error,
          streamingMessage: null,
          messages: updatedMessages
        });

        // ✅ 3秒后自动清除错误
        setTimeout(() => {
          if (get().error === message.error) {
            set({ error: null });
          }
        }, 3000);
        break;

      case 'info':
        console.log('WebSocket info:', message.message);
        break;
    }
  },

  // ============ 清空状态 ============

  reset: () => {
    const { wsManager } = get();
    if (wsManager) {
      wsManager.disconnect();
    }
    set({
      status: 'idle',
      wsManager: null,
      error: null,
      models: [],
      currentModel: null,
      sessions: [],
      currentSession: null,
      hasMoreSessions: false,
      messages: [],
      streamingMessage: null
    });
  }
}));

