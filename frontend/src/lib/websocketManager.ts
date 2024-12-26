class WebSocketManager {
    private static instance: WebSocketManager;
    private socket: WebSocket | null = null;
    private subscribers = new Set<(isConnected: boolean) => void>();
    private reconnectTimeout: NodeJS.Timeout | null = null;
    private reconnectAttempts = 0;
    private readonly maxReconnectAttempts = 5;
    private messageHandlers = new Set<(event: MessageEvent) => void>();
  
    private constructor() {}
  
    static getInstance() {
      if (!WebSocketManager.instance) {
        WebSocketManager.instance = new WebSocketManager();
      }
      return WebSocketManager.instance;
    }
  
    connect(url: string) {
      if (this.socket?.readyState === WebSocket.OPEN || 
          this.socket?.readyState === WebSocket.CONNECTING) {
        return;
      }
  
      this.socket = new WebSocket(url);
  
      this.socket.onopen = () => {
        this.reconnectAttempts = 0;
        this.notifySubscribers(true);
      };
  
      this.socket.onclose = (event) => {
        this.notifySubscribers(false);
        
        if (event.code !== 1000 && event.code !== 1001) {
          if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            const delay = Math.min(1000 * Math.pow(2, this.reconnectAttempts), 10000);
            this.reconnectTimeout = setTimeout(() => this.connect(url), delay);
          }
        }
      };
  
      this.socket.onerror = () => {
        this.notifySubscribers(false);
      };
  
      this.socket.onmessage = (event) => {
        this.messageHandlers.forEach(handler => handler(event));
      };
    }
  
    subscribe(callback: (isConnected: boolean) => void) {
      this.subscribers.add(callback);
      if (this.socket) {
        callback(this.socket.readyState === WebSocket.OPEN);
      } else {
        callback(false);
      }
      return () => {
        this.subscribers.delete(callback);
      };
    }
  
    addMessageHandler(handler: (event: MessageEvent) => void) {
      this.messageHandlers.add(handler);
      return () => {
        this.messageHandlers.delete(handler);
      };
    }
  
    private notifySubscribers(isConnected: boolean) {
      this.subscribers.forEach(callback => callback(isConnected));
    }
  
    send(data: any) {
      if (this.socket?.readyState === WebSocket.OPEN) {
        this.socket.send(JSON.stringify(data));
      }
    }
  
    disconnect() {
      if (this.reconnectTimeout) {
        clearTimeout(this.reconnectTimeout);
      }
      if (this.socket) {
        this.socket.close(1000, 'Normal closure');
        this.socket = null;
      }
      this.messageHandlers.clear();
      this.subscribers.clear();
    }
  }
  
  export const wsManager = WebSocketManager.getInstance();