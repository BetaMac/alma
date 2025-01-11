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
    console.log('Attempting to connect to WebSocket:', url);
    
    try {
      wsManager.connect(url);
      
      const unsubscribe = wsManager.subscribe((connected) => {
        console.log('WebSocket connection status:', connected);
        setIsConnected(connected);
        if (connected) {
          console.log('WebSocket connected successfully');
          options.onOpen?.();
        } else {
          console.log('WebSocket disconnected');
          options.onClose?.();
        }
      });

      const unsubscribeMessage = wsManager.addMessageHandler((event) => {
        try {
          console.log('Received WebSocket message:', event.data);
          const message: WebSocketMessage = JSON.parse(event.data);
          options.onMessage?.(message);
        } catch (error) {
          console.error('Error parsing WebSocket message:', error);
          options.onError?.(new Event('parse_error'));
        }
      });

      return () => {
        console.log('Cleaning up WebSocket connections');
        unsubscribe();
        unsubscribeMessage();
      };
    } catch (error) {
      console.error('Error setting up WebSocket:', error);
      options.onError?.(new Event('setup_error'));
      return () => {};
    }
  }, [url, options]);

  const sendMessage = useCallback((message: any) => {
    console.log('Sending WebSocket message:', message);
    wsManager.send(message);
  }, []);

  return {
    isConnected,
    sendMessage,
  };
};