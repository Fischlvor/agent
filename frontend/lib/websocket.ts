/**
 * 全局WebSocket管理器（单例模式）
 *
 * 所有页面共享同一个WebSocket连接，通过event_type区分消息用途
 */

type MessageHandler = (message: any) => void;

class WebSocketManager {
  private static instance: WebSocketManager | null = null;
  private ws: WebSocket | null = null;
  private handlers: Map<number, Set<MessageHandler>> = new Map();
  private reconnectTimer: NodeJS.Timeout | null = null;
  private disconnectTimer: NodeJS.Timeout | null = null;
  private isConnecting = false;

  private constructor() {}

  static getInstance(): WebSocketManager {
    if (!WebSocketManager.instance) {
      WebSocketManager.instance = new WebSocketManager();
    }
    return WebSocketManager.instance;
  }

  /**
   * 连接WebSocket（如果未连接）
   */
  connect(): void {
    // 如果已连接或正在连接，直接返回
    if (this.ws?.readyState === WebSocket.OPEN ||
        this.ws?.readyState === WebSocket.CONNECTING ||
        this.isConnecting) {
      console.log('[WebSocket] Already connected or connecting, skip');
      return;
    }

    const token = localStorage.getItem('access_token');
    if (!token) {
      console.warn('[WebSocket] No access token, skipping connection');
      return;
    }

    this.isConnecting = true;
    const wsUrl = `ws://localhost:8000/api/v1/ws/chat?token=${token}`;

    console.log('[WebSocket] Connecting...');
    this.ws = new WebSocket(wsUrl);

    this.ws.onopen = () => {
      this.isConnecting = false;
      console.log('[WebSocket] Connected');
    };

    this.ws.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data);
        const eventType = message.event_type;

        // 分发消息给对应的处理器
        if (eventType && this.handlers.has(eventType)) {
          const handlers = this.handlers.get(eventType)!;
          handlers.forEach(handler => {
            try {
              handler(message);
            } catch (error) {
              console.error('[WebSocket] Handler error:', error);
            }
          });
        }
      } catch (error) {
        console.error('[WebSocket] Failed to parse message:', error);
      }
    };

    this.ws.onerror = (error) => {
      this.isConnecting = false;
      console.error('[WebSocket] Error:', error);
    };

    this.ws.onclose = () => {
      this.isConnecting = false;
      console.log('[WebSocket] Disconnected');
      this.ws = null;

      // 5秒后自动重连
      if (!this.reconnectTimer) {
        this.reconnectTimer = setTimeout(() => {
          this.reconnectTimer = null;
          if (this.handlers.size > 0) {
            console.log('[WebSocket] Auto reconnecting...');
            this.connect();
          }
        }, 5000);
      }
    };
  }

  /**
   * 订阅特定事件类型的消息
   */
  subscribe(eventType: number, handler: MessageHandler): () => void {
    // 取消延迟断开（有新订阅者）
    if (this.disconnectTimer) {
      clearTimeout(this.disconnectTimer);
      this.disconnectTimer = null;
    }

    if (!this.handlers.has(eventType)) {
      this.handlers.set(eventType, new Set());
    }
    this.handlers.get(eventType)!.add(handler);

    // 确保连接
    this.connect();

    // 返回取消订阅函数
    return () => {
      this.unsubscribe(eventType, handler);
    };
  }

  /**
   * 取消订阅
   */
  unsubscribe(eventType: number, handler: MessageHandler): void {
    if (this.handlers.has(eventType)) {
      this.handlers.get(eventType)!.delete(handler);

      // 如果该事件类型没有订阅者了，移除
      if (this.handlers.get(eventType)!.size === 0) {
        this.handlers.delete(eventType);
      }
    }

    // 如果没有任何订阅者，延迟1秒后断开（避免 React Strict Mode 快速重连）
    if (this.handlers.size === 0 && this.ws) {
      if (this.disconnectTimer) {
        clearTimeout(this.disconnectTimer);
      }

      this.disconnectTimer = setTimeout(() => {
        if (this.handlers.size === 0) {
          console.log('[WebSocket] No subscribers for 1s, disconnecting...');
          this.disconnect();
        }
        this.disconnectTimer = null;
      }, 1000);
    }
  }

  /**
   * 断开连接
   */
  disconnect(): void {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }

    if (this.disconnectTimer) {
      clearTimeout(this.disconnectTimer);
      this.disconnectTimer = null;
    }

    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }

  /**
   * 发送消息
   */
  send(message: any): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message));
    } else {
      console.warn('[WebSocket] Not connected, cannot send message');
    }
  }
}

// 导出单例实例（用于知识库等简单场景）
export const wsManager = WebSocketManager.getInstance();

/**
 * ChatWebSocketManager 适配器
 * 为 chatStore 提供事件驱动的 API，内部使用全局 wsManager
 */
export class ChatWebSocketManager {
  private baseUrl: string;
  private token: string;
  private eventHandlers: Map<string, Set<Function>> = new Map();
  private unsubscribers: (() => void)[] = [];
  private messageQueue: any[] = []; // ✅ 消息队列，用于连接建立前的消息

  constructor(baseUrl: string, token: string) {
    this.baseUrl = baseUrl;
    this.token = token;
  }

  get isConnected(): boolean {
    return wsManager['ws']?.readyState === WebSocket.OPEN;
  }

  /**
   * ✅ 等待 WebSocket 连接建立
   * @param timeout 超时时间（毫秒）
   * @returns 是否成功连接
   */
  async waitForConnection(timeout: number = 3000): Promise<boolean> {
    const startTime = Date.now();

    while (Date.now() - startTime < timeout) {
      if (this.isConnected) {
        return true;
      }
      // 每 100ms 检查一次
      await new Promise(resolve => setTimeout(resolve, 100));
    }

    console.warn('[ChatWebSocketManager] 等待连接超时');
    return false;
  }

  on(event: string, handler: Function): void {
    if (!this.eventHandlers.has(event)) {
      this.eventHandlers.set(event, new Set());
    }
    this.eventHandlers.get(event)!.add(handler);
  }

  async connect(): Promise<void> {
    // 先确保全局 wsManager 已连接
    wsManager.connect();

    // 订阅聊天相关的事件类型
    const chatEventTypes = [
      2000, 2001, 2002,  // MESSAGE_START, MESSAGE_CONTENT, MESSAGE_DONE
      3000, 3001, 3002,  // THINKING_START, THINKING_DELTA, THINKING_COMPLETE
      4000, 4001,        // TOOL_CALL, TOOL_RESULT
      5000, 5001,        // LLM_INVOCATION_COMPLETE, TOOL_INVOCATION_COMPLETE
      6000               // SESSION_TITLE_UPDATED
    ];

    chatEventTypes.forEach(eventType => {
      const unsub = wsManager.subscribe(eventType, (message) => {
        // 触发 'message' 事件，原样转发（chatStore 会自动解析）
        const handlers = this.eventHandlers.get('message');
        if (handlers) {
          handlers.forEach(handler => handler(message));
        }
      });
      this.unsubscribers.push(unsub);
    });

    // 等待连接建立，然后监听 close 和 error 事件
    await new Promise<void>((resolve) => {
      const checkConnection = () => {
        const ws = (wsManager as any).ws;
        if (ws?.readyState === WebSocket.OPEN) {
          // 监听底层 WebSocket 的 close 和 error 事件
          const closeHandler = () => {
            const handlers = this.eventHandlers.get('close');
            if (handlers) {
              handlers.forEach(handler => handler());
            }
          };

          const errorHandler = (error: Event) => {
            const handlers = this.eventHandlers.get('error');
            if (handlers) {
              handlers.forEach(handler => handler(error));
            }
          };

          ws.addEventListener('close', closeHandler);
          ws.addEventListener('error', errorHandler);

          // 保存以便清理
          this.unsubscribers.push(() => {
            ws.removeEventListener('close', closeHandler);
            ws.removeEventListener('error', errorHandler);
          });

          resolve();
        } else if (ws) {
          // 连接中，等待 onopen
          ws.addEventListener('open', () => {
            checkConnection();
          }, { once: true });
        } else {
          // 还没开始连接，稍后重试
          setTimeout(checkConnection, 100);
        }
      };
      checkConnection();
    });
  }

  send(message: any): void {
    wsManager.send(message);
  }

  /**
   * ✅ 发送消息（带自动等待连接）
   * @param message 要发送的消息
   * @param timeout 等待连接的超时时间（毫秒）
   * @returns 是否成功发送
   */
  async sendWithWait(message: any, timeout: number = 2000): Promise<boolean> {
    // 如果已连接，直接发送
    if (this.isConnected) {
      wsManager.send(message);
      return true;
    }

    // 等待连接
    console.log('[ChatWebSocketManager] WebSocket 未连接，等待连接...');
    const connected = await this.waitForConnection(timeout);

    if (connected) {
      wsManager.send(message);
      return true;
    } else {
      console.error('[ChatWebSocketManager] 等待连接超时，无法发送消息');
      return false;
    }
  }

  disconnect(): void {
    // 清空消息队列
    this.messageQueue = [];

    // 取消所有订阅
    this.unsubscribers.forEach(unsub => unsub());
    this.unsubscribers = [];
    this.eventHandlers.clear();
  }
}

// 事件类型常量
export const EventType = {
  DOCUMENT_STATUS_UPDATE: 7000,
  MESSAGE_CONTENT: 2001,
  MESSAGE_DONE: 2002,
  // ... 其他事件类型
} as const;
