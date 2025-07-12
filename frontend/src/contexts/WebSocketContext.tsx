import React, { createContext, useContext, useEffect, useState, ReactNode } from 'react';
import websocketService from '../services/websocket';

interface WebSocketContextType {
  isConnected: boolean;
  connect: () => Promise<void>;
  disconnect: () => void;
  subscribe: (topic: string, callback?: (data: any) => void, sessionKey?: number) => void;
  unsubscribe: (topic: string) => void;
  on: (event: string, callback: Function) => void;
  off: (event: string, callback: Function) => void;
}

const WebSocketContext = createContext<WebSocketContextType | undefined>(undefined);

interface WebSocketProviderProps {
  children: ReactNode;
}

export const WebSocketProvider: React.FC<WebSocketProviderProps> = ({ children }) => {
  const [isConnected, setIsConnected] = useState(false);

  useEffect(() => {
    // Auto-connect on mount
    const initializeConnection = async () => {
      try {
        await websocketService.connect();
        setIsConnected(true);
      } catch (error) {
        console.error('Failed to connect WebSocket on mount:', error);
      }
    };

    initializeConnection();

    // Set up connection event listeners
    const handleConnect = () => {
      setIsConnected(true);
    };

    const handleDisconnect = () => {
      setIsConnected(false);
    };

    websocketService.on('connected', handleConnect);
    websocketService.on('disconnect', handleDisconnect);

    // Cleanup on unmount
    return () => {
      websocketService.off('connected', handleConnect);
      websocketService.off('disconnect', handleDisconnect);
      websocketService.disconnect();
    };
  }, []);

  const connect = async (): Promise<void> => {
    try {
      await websocketService.connect();
      setIsConnected(true);
    } catch (error) {
      console.error('Failed to connect WebSocket:', error);
      throw error;
    }
  };

  const disconnect = (): void => {
    websocketService.disconnect();
    setIsConnected(false);
  };

  const subscribe = (topic: string, callback?: (data: any) => void, sessionKey?: number): void => {
    try {
      websocketService.subscribe(topic as any, callback, sessionKey);
    } catch (error) {
      console.error(`Failed to subscribe to ${topic}:`, error);
    }
  };

  const unsubscribe = (topic: string): void => {
    websocketService.unsubscribe(topic as any);
  };

  const on = (event: string, callback: Function): void => {
    websocketService.on(event, callback);
  };

  const off = (event: string, callback: Function): void => {
    websocketService.off(event, callback);
  };

  const value: WebSocketContextType = {
    isConnected,
    connect,
    disconnect,
    subscribe,
    unsubscribe,
    on,
    off,
  };

  return (
    <WebSocketContext.Provider value={value}>
      {children}
    </WebSocketContext.Provider>
  );
};

export const useWebSocket = (): WebSocketContextType => {
  const context = useContext(WebSocketContext);
  if (context === undefined) {
    throw new Error('useWebSocket must be used within a WebSocketProvider');
  }
  return context;
};