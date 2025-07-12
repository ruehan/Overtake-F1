import { useEffect, useState, useRef } from 'react';
import { useWebSocket } from './useWebSocket';
import webSocketService, { SubscriptionTopic } from '../services/websocket';

interface UseRealtimeDataOptions {
  topic: SubscriptionTopic;
  sessionKey: number;
  enabled?: boolean;
}

export function useRealtimeData<T>({ topic, sessionKey, enabled = true }: UseRealtimeDataOptions) {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const { isConnected, subscribe, unsubscribe } = useWebSocket();
  const callbackRef = useRef<((data: any) => void) | null>(null);

  useEffect(() => {
    if (!isConnected || !enabled) return;

    const setupSubscription = async () => {
      try {
        setLoading(true);
        setError(null);

        // Subscribe to the topic
        await subscribe(topic, sessionKey);

        // Set up the callback
        callbackRef.current = (streamData: { data: T; timestamp: string }) => {
          setData(streamData.data);
          setLoading(false);
        };

        webSocketService.on(topic as any, callbackRef.current);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to subscribe');
        setLoading(false);
      }
    };

    setupSubscription();

    return () => {
      if (callbackRef.current) {
        webSocketService.off(topic, callbackRef.current);
      }
      unsubscribe(topic);
    };
  }, [isConnected, enabled, topic, sessionKey, subscribe, unsubscribe]);

  return { data, loading, error };
}