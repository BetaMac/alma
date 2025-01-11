class WebSocketManager {
    private static instance: WebSocketManager;
    private ws: WebSocket | null = null;
    private subscribers: ((connected: boolean) => void)[] = [];
    private messageHandlers: ((event: MessageEvent) => void)[] = [];
    private url: string | null = null;
    private heartbeatInterval: NodeJS.Timeout | null = null;
    private reconnectAttempts: number = 0;
    private readonly MAX_RECONNECT_ATTEMPTS = 5;
  
    private constructor() {}
  
    static getInstance(): WebSocketManager {
      if (!WebSocketManager.instance) {
        WebSocketManager.instance = new WebSocketManager();
      }
      return WebSocketManager.instance;
    }
  
    connect(url: string) {
      console.log('WebSocketManager: Connecting to', url);
      this.url = url;
      this.reconnectAttempts = 0;
      if (!this.ws || this.ws.readyState === WebSocket.CLOSED) {
        try {
          this.ws = new WebSocket(url);
          this.setupWebSocket();
          console.log('WebSocketManager: WebSocket instance created');
        } catch (error) {
          console.error('WebSocketManager: Error creating WebSocket:', error);
          this.notifySubscribers(false);
        }
      }
    }
  
    reconnect() {
      console.log('WebSocketManager: Attempting to reconnect');
      if (this.url && this.reconnectAttempts < this.MAX_RECONNECT_ATTEMPTS) {
        this.reconnectAttempts++;
        if (this.ws) {
          console.log('WebSocketManager: Closing existing connection');
          this.ws.close();
        }
        this.connect(this.url);
      } else {
        console.error('WebSocketManager: Max reconnection attempts reached or no URL available');
        this.notifySubscribers(false);
      }
    }
  
    private setupWebSocket() {
      if (!this.ws) {
        console.error('WebSocketManager: No WebSocket instance available');
        return;
      }
  
      this.ws.onopen = () => {
        console.log('WebSocketManager: Connection opened');
        this.notifySubscribers(true);
        this.startHeartbeat();
      };
  
      this.ws.onclose = () => {
        console.log('WebSocketManager: Connection closed');
        this.stopHeartbeat();
        this.notifySubscribers(false);
        // Attempt to reconnect
        setTimeout(() => this.reconnect(), 2000);
      };
  
      this.ws.onerror = (error) => {
        console.error('WebSocketManager: WebSocket error:', error);
        this.notifySubscribers(false);
      };
  
      this.ws.onmessage = (event) => {
        console.log('WebSocketManager: Message received:', event.data);
        try {
          const data = JSON.parse(event.data);
          if (data.status === 'pong') {
            console.log('WebSocketManager: Heartbeat received');
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
      this.heartbeatInterval = setInterval(() => {
        if (this.ws?.readyState === WebSocket.OPEN) {
          console.log('WebSocketManager: Sending heartbeat');
          this.ws.send('ping');
        }
      }, 30000); // Send heartbeat every 30 seconds
    }
  
    private stopHeartbeat() {
      if (this.heartbeatInterval) {
        clearInterval(this.heartbeatInterval);
        this.heartbeatInterval = null;
      }
    }
  
    subscribe(callback: (connected: boolean) => void) {
      console.log('WebSocketManager: New subscriber added');
      this.subscribers.push(callback);
      // Immediately notify the new subscriber of the current connection state
      if (this.ws) {
        callback(this.ws.readyState === WebSocket.OPEN);
      } else {
        callback(false);
      }
      return () => {
        console.log('WebSocketManager: Subscriber removed');
        this.subscribers = this.subscribers.filter(cb => cb !== callback);
      };
    }
  
    addMessageHandler(handler: (event: MessageEvent) => void) {
      console.log('WebSocketManager: New message handler added');
      this.messageHandlers.push(handler);
      return () => {
        console.log('WebSocketManager: Message handler removed');
        this.messageHandlers = this.messageHandlers.filter(h => h !== handler);
      };
    }
  
    send(message: any) {
      if (this.ws?.readyState === WebSocket.OPEN) {
        console.log('WebSocketManager: Sending message:', message);
        this.ws.send(JSON.stringify(message));
      } else {
        console.error('WebSocketManager: Cannot send message, connection not open');
        this.notifySubscribers(false);
      }
    }
  
    private notifySubscribers(isConnected: boolean) {
      console.log('WebSocketManager: Notifying subscribers of connection state:', isConnected);
      this.subscribers.forEach(callback => callback(isConnected));
    }
  }
  
  export const wsManager = WebSocketManager.getInstance();