export interface WebSocketMessage {
  status: 'connected' | 'processing' | 'chunk' | 'complete' | 'error' | 'finished' | 'pong';
  data?: string;
  message?: string;
  elapsedTime?: number;
  timestamp?: string;
} 