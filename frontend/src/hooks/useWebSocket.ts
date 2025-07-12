import { useEffect, useState, useCallback, useRef } from 'react';
import webSocketService, { SubscriptionTopic } from '../services/websocket';

export const useWebSocket = () => {
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const connect = async () => {
      try {
        await webSocketService.connect();
        setIsConnected(true);
        setError(null);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to connect');
        setIsConnected(false);
      }
    };

    connect();

    return () => {
      webSocketService.disconnect();
    };
  }, []);

  const subscribe = useCallback(async (topic: SubscriptionTopic, sessionKey: number) => {
    if (!isConnected) {
      throw new Error('WebSocket not connected');
    }
    return webSocketService.subscribe(topic, sessionKey);
  }, [isConnected]);

  const unsubscribe = useCallback((topic: SubscriptionTopic) => {
    webSocketService.unsubscribe(topic);
  }, []);

  return {
    isConnected,
    error,
    subscribe,
    unsubscribe,
  };
};