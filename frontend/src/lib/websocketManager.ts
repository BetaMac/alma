import { config } from './config';
import { WebSocketMessage } from './types';

class WebSocketManager {
    private static instance: WebSocketManager;
    private ws: WebSocket | null = null;
    private subscribers: ((connected: boolean, event?: CloseEvent) => void)[] = [];
    private messageHandlers: ((event: MessageEvent) => void)[] = [];
    private url: string | null = null;
    private heartbeatInterval: NodeJS.Timeout | null = null;
    private reconnectAttempts: number = 0;
    private readonly MAX_RECONNECT_ATTEMPTS = 5;
    private isConnecting: boolean = false;
    private reconnectTimeout: NodeJS.Timeout | null = null;
  
    private constructor() {}
  
    static getInstance(): WebSocketManager {
      if (!WebSocketManager.instance) {
        WebSocketManager.instance = new WebSocketManager();
      }
      return WebSocketManager.instance;
    }
  
    connect(url: string = config.wsUrl) {
      if (this.isConnecting) {
        if (config.enableDebugMode) {
          console.log('WebSocketManager: Already attempting to connect');
        }
        return;
      }

      if (this.reconnectTimeout) {
        clearTimeout(this.reconnectTimeout);
        this.reconnectTimeout = null;
      }

      if (config.enableDebugMode) {
        console.log('WebSocketManager: Connecting to', url);
      }
      this.url = url;
      this.isConnecting = true;

      try {
        if (this.ws) {
          if (config.enableDebugMode) {
            console.log('WebSocketManager: Closing existing connection');
          }
          this.ws.close();
          this.ws = null;
        }

        this.ws = new WebSocket(url);
        this.setupWebSocket();
      } catch (error) {
        console.error('WebSocketManager: Error creating WebSocket:', error);
        this.handleConnectionFailure();
      }
    }

    private handleConnectionFailure(event?: CloseEvent) {
      this.isConnecting = false;
      this.notifySubscribers(false, event);
      
      if (this.reconnectAttempts < this.MAX_RECONNECT_ATTEMPTS) {
        const delay = Math.min(1000 * Math.pow(2, this.reconnectAttempts), 10000);
        console.log(`WebSocketManager: Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts + 1})`);
        this.reconnectTimeout = setTimeout(() => this.reconnect(), delay);
      } else {
        console.error('WebSocketManager: Max reconnection attempts reached');
      }
    }
  
    reconnect() {
      if (!this.url || this.isConnecting) return;
      
      this.reconnectAttempts++;
      console.log(`WebSocketManager: Attempting to reconnect (${this.reconnectAttempts}/${this.MAX_RECONNECT_ATTEMPTS})`);
      this.connect(this.url);
    }
  
    private setupWebSocket() {
      if (!this.ws) {
        console.error('WebSocketManager: No WebSocket instance available');
        this.handleConnectionFailure();
        return;
      }
  
      this.ws.onopen = () => {
        console.log('WebSocketManager: Connection opened successfully');
        this.isConnecting = false;
        this.reconnectAttempts = 0;
        this.notifySubscribers(true);
        this.startHeartbeat();
      };
  
      this.ws.onclose = (event) => {
        console.log('WebSocketManager: Connection closed', event.code, event.reason);
        this.isConnecting = false;
        this.stopHeartbeat();
        this.handleConnectionFailure(event);
      };
  
      this.ws.onerror = (error) => {
        console.error('WebSocketManager: WebSocket error:', error);
        this.isConnecting = false;
      };
  
      this.ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          if (data.status === 'pong') {
            console.log('WebSocketManager: Received pong');
            return;
          }
          this.messageHandlers.forEach(handler => handler(event));
        } catch (error) {
          console.error('WebSocketManager: Error parsing message:', error);
        }
      };
    }
  
    private startHeartbeat() {
      this.stopHeartbeat();
      if (config.enableDebugMode) {
        console.log('WebSocketManager: Starting heartbeat');
      }
      this.heartbeatInterval = setInterval(() => {
        if (this.ws?.readyState === WebSocket.OPEN) {
          if (config.enableDebugMode) {
            console.log('WebSocketManager: Sending ping');
          }
          this.ws.send('ping');
        }
      }, config.defaultTimeout * 1000);  // Convert to milliseconds
    }
  
    private stopHeartbeat() {
      if (this.heartbeatInterval) {
        console.log('WebSocketManager: Stopping heartbeat');
        clearInterval(this.heartbeatInterval);
        this.heartbeatInterval = null;
      }
    }
  
    subscribe(callback: (connected: boolean, event?: CloseEvent) => void) {
      this.subscribers.push(callback);
      if (this.ws) {
        callback(this.ws.readyState === WebSocket.OPEN);
      } else {
        callback(false);
      }
      return () => {
        this.subscribers = this.subscribers.filter(cb => cb !== callback);
      };
    }
  
    addMessageHandler(handler: (event: MessageEvent) => void) {
      this.messageHandlers.push(handler);
      return () => {
        this.messageHandlers = this.messageHandlers.filter(h => h !== handler);
      };
    }
  
    send(message: any) {
      if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
        console.error('WebSocketManager: Cannot send message, connection not open');
        this.notifySubscribers(false);
        return;
      }
      
      try {
        const messageStr = JSON.stringify(message);
        console.log('WebSocketManager: Sending message:', messageStr);
        this.ws.send(messageStr);
      } catch (error) {
        console.error('WebSocketManager: Error sending message:', error);
      }
    }
  
    private notifySubscribers(isConnected: boolean, event?: CloseEvent) {
      console.log('WebSocketManager: Notifying subscribers of connection state:', isConnected, event?.code || '');
      this.subscribers.forEach(callback => callback(isConnected, event));
    }

    isConnected(): boolean {
      return this.ws?.readyState === WebSocket.OPEN;
    }
}
  
export const wsManager = WebSocketManager.getInstance();