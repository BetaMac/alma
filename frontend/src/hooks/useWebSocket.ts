import { useEffect, useCallback } from 'react';
import { wsManager } from '@/lib/websocketManager';
import { WebSocketMessage } from '@/lib/types';

interface WebSocketHookOptions {
  onOpen?: () => void;
  onClose?: (event?: CloseEvent) => void;
  onMessage?: (message: WebSocketMessage) => void;
  onError?: (event: Event) => void;
}

export function useWebSocket(url: string, options: WebSocketHookOptions) {
  useEffect(() => {
    // Setup message handler
    const messageHandler = (event: MessageEvent) => {
      if (options.onMessage) {
        try {
          const message = JSON.parse(event.data);
          options.onMessage(message);
        } catch (error) {
          console.error('Failed to parse WebSocket message:', error);
        }
      }
    };

    // Add handlers
    const unsubscribeMessage = wsManager.addMessageHandler(messageHandler);
    const unsubscribeStatus = wsManager.subscribe((connected, event?) => {
      if (connected && options.onOpen) {
        options.onOpen();
      } else if (!connected && options.onClose) {
        options.onClose(event);
      }
    });

    // Initial connection
    wsManager.connect(url);

    // Cleanup
    return () => {
      unsubscribeMessage();
      unsubscribeStatus();
    };
  }, [url]); // Only reconnect if URL changes

  const sendMessage = useCallback((message: any) => {
    wsManager.send(message);
  }, []);

  return {
    isConnected: wsManager.isConnected(),
    sendMessage
  };
}