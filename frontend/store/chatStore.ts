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
  sendMessage: (content: string, parentMessageId?: string) => void;
  stopGeneration: () => void;
  editMessage: (messageId: string, newContent: string) => Promise<void>;
  editMessageAndRegenerate: (messageId: string, newContent: string) => Promise<void>;

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
      // ✅ 先保存流式消息状态（不清空，保留在后台）
      const { streamingMessage: currentStreaming, status: currentStatus } = get();

      if (currentStreaming) {
        console.log(`[切换会话] 流式消息会话ID: ${currentStreaming.session_id}, 目标会话ID: ${sessionId}`);
      }

      const session = await apiClient.getSession(sessionId);
      set({ currentSession: session });
      await get().loadMessages(sessionId);

      // ✅ 检查流式消息是否属于目标会话
      const streamingBelongsToTargetSession = currentStreaming &&
        currentStreaming.session_id === sessionId;

      if (streamingBelongsToTargetSession) {
        // 流式消息属于当前会话，恢复显示（状态已存在，无需重新设置）
        console.log('[WebSocket] ✅ 恢复流式显示:', currentStreaming.id);
      } else {
        // 流式消息属于其他会话，不清空，只是更新状态为connected
        // 这样切回原会话时仍能看到流式传输
        set({ status: 'connected' });
        console.log('[WebSocket] ⏸️ 暂时隐藏其他会话的流式消息（保留在后台）');
      }

      // ✅ 清除该会话的未读标记
      set((state) => ({
        sessions: state.sessions.map((s) =>
          (s.id === sessionId || s.session_id === sessionId)
            ? { ...s, hasNewMessage: false }
            : s
        )
      }));
    } catch (error) {
      console.error('Failed to select session', error);
    }
  },

  updateSessionTitle: async (sessionId: string, title: string) => {
    try {
      const updatedSession = await apiClient.updateSession(sessionId, { title });
      set((state) => ({
        sessions: state.sessions.map((s) =>
          (s.id === sessionId || s.session_id === sessionId) ? updatedSession : s
        ),
        currentSession: (state.currentSession?.id === sessionId || state.currentSession?.session_id === sessionId)
          ? updatedSession : state.currentSession
      }));
    } catch (error) {
      console.error('Failed to update session', error);
    }
  },

  deleteSession: async (sessionId: string) => {
    try {
      await apiClient.deleteSession(sessionId);
      set((state) => ({
        sessions: state.sessions.filter((s) => s.id !== sessionId && s.session_id !== sessionId),
        currentSession: (state.currentSession?.id === sessionId || state.currentSession?.session_id === sessionId) ? null : state.currentSession,
        messages: (state.currentSession?.id === sessionId || state.currentSession?.session_id === sessionId) ? [] : state.messages
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

  sendMessage: async (content: string, parentMessageId?: string) => {
    const { wsManager, currentSession, currentModel, messageTimeout } = get();

    if (!wsManager?.isConnected) {
      console.error('WebSocket not connected');
      set({ error: 'WebSocket 未连接' });
      return;
    }

    if (!currentSession) {
      console.error('No active session');
      set({ error: '没有活动会话' });
      return;
    }

    // ✅ 清除旧的超时定时器
    if (messageTimeout) {
      clearTimeout(messageTimeout);
    }

    try {
      // ✅ 通过 HTTP POST 发送消息
      const userMessage = await apiClient.sendMessage(
        currentSession.session_id || currentSession.id,  // 优先使用session_id
        content,
        currentModel || undefined,
        parentMessageId  // 传递父消息ID（用于编辑关联）
      );

      // ✅ 添加用户消息到本地状态
      set((state) => ({
        messages: [...state.messages, userMessage],
        status: 'generating'
      }));

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

      set({ messageTimeout: timeout });

    } catch (error: any) {
      console.error('Failed to send message:', error);
      set({
        status: 'connected',
        error: error.response?.data?.detail || '发送消息失败'
      });

      // 3秒后清除错误
      setTimeout(() => {
        set({ error: null });
      }, 3000);
    }
  },

  stopGeneration: () => {
    const { wsManager, currentSession } = get();

    if (wsManager?.isConnected && currentSession) {
      wsManager.send({
        type: 'stop_generation',
        session_id: currentSession.session_id || currentSession.id
      });
    }
  },

  editMessage: async (messageId: string, newContent: string) => {
    try {
      await apiClient.updateMessage(messageId, { content: newContent });
      // 重新加载消息
      const { currentSession } = get();
      if (currentSession) {
        await get().loadMessages(currentSession.session_id || currentSession.id);
      }
    } catch (error) {
      console.error('Failed to edit message', error);
    }
  },

  // ✅ 编辑消息并重新生成回复（ChatGPT模式）
  // 流程：删除原消息和后续回复 → 发送新消息（带parent_message_id） → AI自动生成回复
  editMessageAndRegenerate: async (messageId: string, newContent: string) => {
    const { currentSession } = get();

    if (!currentSession) {
      console.error('No active session');
      set({ error: '没有活动会话' });
      return;
    }

    try {
      // 1. 删除原消息和后续所有回复
      await apiClient.updateMessage(messageId, { content: newContent });

      // 2. 重新加载消息列表（原消息已被删除）
      await get().loadMessages(currentSession.session_id || currentSession.id);

      // 3. 发送新消息（创建新的用户消息，带parent_message_id关联，并触发AI生成）
      await get().sendMessage(newContent, messageId);

    } catch (error: any) {
      console.error('Failed to edit message and regenerate', error);
      set({
        status: 'connected',
        error: error.response?.data?.detail || '编辑消息失败'
      });

      // 3秒后清除错误
      setTimeout(() => {
        set({ error: null });
      }, 3000);
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
            session_id: eventData.conversation_id,  // ✅ 提取会话ID
            event_id: Number(envelope.event_id),
            event_type: eventType
          };

        case EventType.MESSAGE_CONTENT:
          if (eventData.message) {
            const content = JSON.parse(eventData.message.content);
            return {
              type: 'content',
              delta: content.text || '',  // ✅ 统一使用 text 字段
              session_id: eventData.conversation_id,  // ✅ 提取会话ID
              event_id: Number(envelope.event_id),
              event_type: eventType
            };
          }
          break;

        case EventType.MESSAGE_DONE:
          return {
            type: 'done',
            message_id: eventData.message_id,
            session_id: eventData.conversation_id,  // ✅ 提取会话ID
            event_id: Number(envelope.event_id),
            event_type: eventType,
            generation_time: eventData.generation_time,
            context_info: (eventData as any).context_info,  // ✅ 提取上下文信息
            session_info: (eventData as any).session_info   // ✅ 提取会话信息
          };

        case EventType.THINKING_START:
          if (eventData.message) {
            const content = JSON.parse(eventData.message.content);
            return {
              type: 'thinking_start',
              thinking_id: eventData.message.id,  // ✅ 从 message.id 获取
              title: content.finish_title || '',  // ✅ 对齐业界标准
              status: 'pending',
              session_id: eventData.conversation_id,  // ✅ 提取会话ID
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
              session_id: eventData.conversation_id,  // ✅ 提取会话ID
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
              session_id: eventData.conversation_id,  // ✅ 提取会话ID
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
              session_id: eventData.conversation_id,  // ✅ 提取会话ID
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
              session_id: eventData.conversation_id,  // ✅ 提取会话ID
              event_id: Number(envelope.event_id),
              event_type: eventType
            };
          }
          break;

        case EventType.LLM_INVOCATION_COMPLETE:
          return {
            type: 'llm_invocation_complete',
            session_id: eventData.conversation_id,
            invocation: (eventData as any).invocation,
            session_cumulative_tokens: (eventData as any).session_cumulative_tokens,
            context_usage_percent: (eventData as any).context_usage_percent,
            event_id: Number(envelope.event_id),
            event_type: eventType
          };

        case EventType.ERROR:
          if (eventData.message) {
            const content = JSON.parse(eventData.message.content);
            return {
              type: 'error',
              error: content.error || '未知错误',
              session_id: eventData.conversation_id,  // ✅ 提取会话ID
              event_id: Number(envelope.event_id),
              event_type: eventType
            };
          }
          break;

        case EventType.PONG:
          return { type: 'pong' };

        case EventType.SESSION_TITLE_UPDATED:
          return {
            type: 'session_title_updated',
            session_id: eventData.conversation_id,
            title: (eventData as any).title,
            event_id: Number(envelope.event_id),
            event_type: eventType
          };

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
    const { currentSession, messageTimeout } = get();

    // ✅ 会话归属验证：如果消息不属于当前会话
    if (message.session_id && currentSession) {
      const currentSessionId = currentSession.session_id || currentSession.id;
      if (message.session_id !== currentSessionId) {
        // ✅ 如果是 MESSAGE_DONE，标记该会话有新消息并更新消息数
        if (message.type === 'done') {
          console.log(`[WebSocket] 后台会话完成: ${message.session_id}`);
          set((state) => ({
            sessions: state.sessions.map((s) => {
              if (s.id === message.session_id || s.session_id === message.session_id) {
                // ✅ 更新消息数和token统计
                return {
                  ...s,
                  hasNewMessage: true,
                  message_count: message.session_info?.message_count ?? s.message_count,
                  total_tokens: message.session_info?.total_tokens ?? s.total_tokens,
                  current_context_tokens: message.context_info?.current_context_tokens ?? s.current_context_tokens,
                  max_context_tokens: message.context_info?.max_context_tokens ?? s.max_context_tokens
                };
              }
              return s;
            })
          }));
        }
        return;  // 忽略不属于当前会话的其他消息
      }
    }

    // ✅ 清除超时定时器（除了 connected 和 pong）
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
        console.log('[WebSocket] 开始生成, message_id:', message.message_id, 'session_id:', message.session_id);
        set({
          streamingMessage: {
            id: message.message_id,
            session_id: message.session_id || '',  // ✅ 记录会话ID
            role: 'assistant',
            content: '',
            isStreaming: true,
            toolCalls: [],
            timeline: [],  // ✅ 初始化 timeline
            thinkingBuffer: '',  // ✅ 用于累积当前正在进行的 thinking
            currentThinkingId: null  // ✅ 当前正在进行的 thinking 块 ID
          },
          status: 'generating'
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
        if (currentSession) {
          if (streamingMessage) {
            // ✅ 有流式消息，正常保存
            const finalMessage: ChatMessage = {
              id: message.message_id,
              session_id: currentSession.session_id || currentSession.id,
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

            // ✅ 更新会话信息（上下文和消息数）
            let updatedSession = { ...currentSession };

            // 更新上下文信息
            if (message.context_info) {
              updatedSession = {
                ...updatedSession,
                current_context_tokens: message.context_info.current_context_tokens,
                max_context_tokens: message.context_info.max_context_tokens,
                context_usage_percent: (message.context_info.current_context_tokens / message.context_info.max_context_tokens) * 100
              };
            }

            // ✅ 更新消息数和 token 统计
            if (message.session_info) {
              updatedSession = {
                ...updatedSession,
                message_count: message.session_info.message_count,
                total_tokens: message.session_info.total_tokens
              };
            }

            set((state) => ({
              messages: [...state.messages, finalMessage],
              streamingMessage: null,
              status: 'connected',
              currentSession: updatedSession,
              // ✅ 同时更新 sessions 列表中的对应会话
              sessions: state.sessions.map((s) =>
                (s.id === updatedSession.id || s.session_id === updatedSession.session_id)
                  ? updatedSession
                  : s
              )
            }));
          } else {
            // ✅ 没有流式消息（说明是切换回来的），重新加载消息
            console.log('[WebSocket] 后台生成完成，重新加载消息');
            const sessionId = currentSession.session_id || currentSession.id;
            get().loadMessages(sessionId);

            // ✅ 更新会话信息
            if (message.session_info) {
              set((state) => ({
                currentSession: {
                  ...state.currentSession!,
                  message_count: message.session_info?.message_count || state.currentSession!.message_count,
                  total_tokens: message.session_info?.total_tokens || state.currentSession!.total_tokens
                },
                sessions: state.sessions.map((s) =>
                  (s.id === sessionId || s.session_id === sessionId)
                    ? {
                        ...s,
                        message_count: message.session_info?.message_count || s.message_count,
                        total_tokens: message.session_info?.total_tokens || s.total_tokens
                      }
                    : s
                )
              }));
            }

            set({ status: 'connected' });
          }
        }
        break;

      case 'llm_invocation_complete':
        // ✅ 记录每次LLM调用的token统计
        const invocationMsg = message as any;
        console.log(
          `[LLM调用 #${invocationMsg.invocation?.sequence}] ` +
          `Tokens: ${invocationMsg.invocation?.tokens?.prompt}(输入) + ` +
          `${invocationMsg.invocation?.tokens?.completion}(输出) = ` +
          `${invocationMsg.invocation?.tokens?.total}(总计), ` +
          `耗时: ${invocationMsg.invocation?.duration_ms}ms, ` +
          `会话累计: ${invocationMsg.session_cumulative_tokens} tokens, ` +
          `上下文使用率: ${invocationMsg.context_usage_percent}%`
        );

        // ✅ 实时更新：显示本次LLM调用的token使用量（总计）
        set((state) => {
          if (!state.currentSession) return {};

          const currentTotal = invocationMsg.invocation?.tokens?.total || 0;
          const maxTokens = state.currentSession.max_context_tokens || 32000;

          return {
            currentSession: {
              ...state.currentSession,
              // 实时显示本次调用的token数
              current_context_tokens: currentTotal,
              total_tokens: invocationMsg.session_cumulative_tokens,
              context_usage_percent: (currentTotal / maxTokens) * 100
            },
            // 同时更新 sessions 列表中的对应会话
            sessions: state.sessions.map((s) =>
              (s.id === state.currentSession?.id || s.session_id === state.currentSession?.session_id)
                ? {
                    ...s,
                    current_context_tokens: currentTotal,
                    total_tokens: invocationMsg.session_cumulative_tokens,
                    context_usage_percent: (currentTotal / maxTokens) * 100
                  }
                : s
            )
          };
        });
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

      case 'session_title_updated':
        // ✅ 处理会话标题更新
        console.log('Session title updated:', message.session_id, message.title);
        set((state) => {
          const updatedSessions = state.sessions.map((s) =>
            s.id === message.session_id || s.session_id === message.session_id
              ? { ...s, title: message.title }
              : s
          );
          const updatedCurrentSession = state.currentSession &&
            (state.currentSession.id === message.session_id || state.currentSession.session_id === message.session_id)
            ? { ...state.currentSession, title: message.title }
            : state.currentSession;

          return {
            sessions: updatedSessions,
            currentSession: updatedCurrentSession
          };
        });
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

