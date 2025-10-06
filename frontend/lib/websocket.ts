/**
 * WebSocket 管理类
 * 负责 WebSocket 连接、重连、心跳、消息收发
 */

import type { WSMessage, WSSendMessageRequest, WSStopGenerationRequest } from '@/types/chat';

export type WSEventType = 'open' | 'close' | 'error' | 'message';

export type WSEventHandler = (data?: any) => void;

export class ChatWebSocketManager {
  private ws: WebSocket | null = null;
  private url: string;
  private token: string;
  private eventHandlers: Map<WSEventType, Set<WSEventHandler>> = new Map();
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000; // 初始重连延迟 1 秒
  private heartbeatInterval: NodeJS.Timeout | null = null;
  private isManualClose = false;
  private isConnecting = false;

  constructor(baseUrl: string, token: string) {
    // 将 http(s) 转换为 ws(s)
    const wsUrl = baseUrl.replace(/^http/, 'ws');
    this.url = `${wsUrl}/ws/chat?token=${encodeURIComponent(token)}`;
    this.token = token;
  }

  /**
   * 连接 WebSocket
   */
  connect(): Promise<void> {
    return new Promise((resolve, reject) => {
      if (this.ws?.readyState === WebSocket.OPEN) {
        resolve();
        return;
      }

      if (this.isConnecting) {
        reject(new Error('Already connecting'));
        return;
      }

      this.isConnecting = true;
      this.isManualClose = false;

      try {
        this.ws = new WebSocket(this.url);

        this.ws.onopen = () => {
          console.log('[WebSocket] Connected');
          this.isConnecting = false;
          this.reconnectAttempts = 0;
          this.startHeartbeat();
          this.emit('open');
          resolve();
        };

        this.ws.onclose = (event) => {
          console.log('[WebSocket] Closed', event.code, event.reason);
          this.isConnecting = false;
          this.stopHeartbeat();
          this.emit('close', event);

          // 如果不是手动关闭，尝试重连
          if (!this.isManualClose && this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnect();
          }
        };

        this.ws.onerror = (error) => {
          console.error('[WebSocket] Error', error);
          this.isConnecting = false;
          this.emit('error', error);
          reject(error);
        };

        this.ws.onmessage = (event) => {
          try {
            const message: WSMessage = JSON.parse(event.data);
            this.handleMessage(message);
          } catch (error) {
            console.error('[WebSocket] Failed to parse message', error);
          }
        };
      } catch (error) {
        this.isConnecting = false;
        reject(error);
      }
    });
  }

  /**
   * 断开连接
   */
  disconnect(): void {
    this.isManualClose = true;
    this.stopHeartbeat();
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }

  /**
   * 重连
   */
  private reconnect(): void {
    this.reconnectAttempts++;
    const delay = Math.min(
      this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1),
      30000 // 最多 30 秒
    );

    console.log(`[WebSocket] Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts})`);

    setTimeout(() => {
      this.connect().catch((error) => {
        console.error('[WebSocket] Reconnect failed', error);
      });
    }, delay);
  }

  /**
   * 启动心跳
   */
  private startHeartbeat(): void {
    this.stopHeartbeat();
    // 每 25 秒发送一次 ping（服务端 30 秒超时）
    this.heartbeatInterval = setInterval(() => {
      this.send({ type: 'ping' });
    }, 25000);
  }

  /**
   * 停止心跳
   */
  private stopHeartbeat(): void {
    if (this.heartbeatInterval) {
      clearInterval(this.heartbeatInterval);
      this.heartbeatInterval = null;
    }
  }

  /**
   * 发送消息
   */
  send(message: WSSendMessageRequest | WSStopGenerationRequest | { type: 'ping' }): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message));
    } else {
      console.error('[WebSocket] Cannot send message, connection not open');
    }
  }

  /**
   * 处理收到的消息
   */
  private handleMessage(message: WSMessage): void {
    // console.log('[WebSocket] Received message', message.type);
    this.emit('message', message);
  }

  /**
   * 注册事件监听器
   */
  on(event: WSEventType, handler: WSEventHandler): void {
    if (!this.eventHandlers.has(event)) {
      this.eventHandlers.set(event, new Set());
    }
    this.eventHandlers.get(event)!.add(handler);
  }

  /**
   * 取消事件监听器
   */
  off(event: WSEventType, handler: WSEventHandler): void {
    const handlers = this.eventHandlers.get(event);
    if (handlers) {
      handlers.delete(handler);
    }
  }

  /**
   * 触发事件
   */
  private emit(event: WSEventType, data?: any): void {
    const handlers = this.eventHandlers.get(event);
    if (handlers) {
      handlers.forEach((handler) => handler(data));
    }
  }

  /**
   * 获取连接状态
   */
  get readyState(): number {
    return this.ws?.readyState ?? WebSocket.CLOSED;
  }

  /**
   * 是否已连接
   */
  get isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN;
  }
}

