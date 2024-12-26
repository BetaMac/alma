import { useEffect, useCallback, useState } from 'react';
import { wsManager } from '../lib/websocketManager';

export interface WebSocketMessage {
  status: 'processing' | 'chunk' | 'complete' | 'error' | 'finished';
  data?: string;
  message?: string;
  elapsedTime?: number;
}

interface WebSocketHookOptions {
  onOpen?: () => void;
  onClose?: () => void;
  onMessage?: (message: WebSocketMessage) => void;
  onError?: (error: Event) => void;
}

export const useWebSocket = (url: string, options: WebSocketHookOptions) => {
  const [isConnected, setIsConnected] = useState(false);

  useEffect(() => {
    wsManager.connect(url);
    
    const unsubscribe = wsManager.subscribe((connected) => {
      setIsConnected(connected);
      if (connected) {
        options.onOpen?.();
      } else {
        options.onClose?.();
      }
    });

    const unsubscribeMessage = wsManager.addMessageHandler((event) => {
      try {
        const message: WebSocketMessage = JSON.parse(event.data);
        options.onMessage?.(message);
      } catch (error) {
        console.error('Error parsing WebSocket message:', error);
      }
    });

    return () => {
      unsubscribe();
      unsubscribeMessage();
    };
  }, [url, options]);

  const sendMessage = useCallback((message: any) => {
    wsManager.send(message);
  }, []);

  return {
    isConnected,
    sendMessage,
  };
};