import { io, Socket } from 'socket.io-client';
import { Position, Weather, LapTime, PitStop, TeamRadio, Driver } from '../types/f1Types';
import { API_ENDPOINTS } from '../config/api';

export type SubscriptionTopic = 'positions' | 'weather' | 'lap_times' | 'pit_stops' | 'team_radio' | 'drivers' | 'race_events';

interface StreamData<T> {
  data: T;
  timestamp: string;
}

type StreamCallback<T> = (data: StreamData<T>) => void;

class WebSocketService {
  private socket: Socket | null = null;
  private callbacks: Map<string, Set<Function>> = new Map();
  private subscriptions: Set<string> = new Set();
  private reconnectAttempts: number = 0;
  private maxReconnectAttempts: number = 5;
  private reconnectDelay: number = 1000;
  private isConnecting: boolean = false;

  connect(): Promise<void> {
    return new Promise((resolve, reject) => {
      if (this.socket?.connected) {
        console.log('✅ WebSocket already connected');
        resolve();
        return;
      }

      if (this.isConnecting) {
        console.log('⏳ WebSocket connection already in progress');
        return;
      }

      this.isConnecting = true;

      // API_ENDPOINTS.websocket에서 기본 URL을 추출
      const wsUrl = API_ENDPOINTS.websocket || 'http://localhost:8000';
      
      console.log(`🔌 Attempting WebSocket connection to: ${wsUrl} (attempt ${this.reconnectAttempts + 1}/${this.maxReconnectAttempts})`);
      console.log(`🔍 API_ENDPOINTS.websocket:`, API_ENDPOINTS.websocket);
      console.log(`🔍 window.location:`, window.location.href);
      
      this.socket = io(wsUrl, {
        path: '/socket.io',
        transports: ['polling', 'websocket'],
        upgrade: true,
        timeout: 20000,
        forceNew: true,
        reconnection: true,
        reconnectionAttempts: this.maxReconnectAttempts,
        reconnectionDelay: this.reconnectDelay,
        reconnectionDelayMax: 5000,
      });

      this.socket.on('connect', () => {
        console.log('✅ WebSocket connected successfully');
        this.reconnectAttempts = 0;
        this.isConnecting = false;
        this.emit('connected', true);
        
        // Re-subscribe to all previous subscriptions
        this.resubscribeAll();
        
        resolve();
      });

      this.socket.on('disconnect', (reason) => {
        console.log('❌ WebSocket disconnected:', reason);
        this.isConnecting = false;
        this.emit('disconnect', reason);
        
        // Don't auto-reconnect if it's a manual disconnect
        if (reason === 'io client disconnect') {
          return;
        }
        
        // Start reconnection process
        this.attemptReconnect();
      });

      this.socket.on('connect_error', (error) => {
        console.error('💥 WebSocket connection error:', error);
        this.isConnecting = false;
        this.reconnectAttempts++;
        
        if (this.reconnectAttempts >= this.maxReconnectAttempts) {
          console.error('🚫 Max reconnection attempts reached');
          this.emit('connection_failed', error);
          reject(error);
        } else {
          this.attemptReconnect();
        }
      });

      this.socket.on('error', (error: any) => {
        console.error('⚠️ WebSocket error:', error);
        this.emit('error', error);
      });

      this.socket.on('stream_error', (data: { topic: string; error: string }) => {
        console.error(`📡 Stream error for ${data.topic}:`, data.error);
        this.emit('stream_error', data);
      });

      this.socket.on('reconnect', (attemptNumber) => {
        console.log(`🔄 WebSocket reconnected after ${attemptNumber} attempts`);
        this.reconnectAttempts = 0;
        this.emit('reconnected', attemptNumber);
      });

      this.socket.on('reconnect_attempt', (attemptNumber) => {
        console.log(`🔄 WebSocket reconnection attempt ${attemptNumber}`);
        this.emit('reconnect_attempt', attemptNumber);
      });

      this.socket.on('reconnect_failed', () => {
        console.error('🚫 WebSocket reconnection failed');
        this.emit('reconnect_failed', true);
      });

      // Set up listeners for each topic
      this.setupTopicListeners();
    });
  }

  private attemptReconnect(): void {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error('🚫 Maximum reconnection attempts reached');
      return;
    }

    const delay = Math.min(this.reconnectDelay * Math.pow(2, this.reconnectAttempts), 30000);
    console.log(`⏱️ Attempting reconnection in ${delay}ms (attempt ${this.reconnectAttempts + 1}/${this.maxReconnectAttempts})`);
    
    setTimeout(() => {
      if (!this.socket?.connected && !this.isConnecting) {
        this.connect().catch(error => {
          console.error('🔄 Reconnection attempt failed:', error);
        });
      }
    }, delay);
  }

  private resubscribeAll(): void {
    console.log(`🔄 Re-subscribing to ${this.subscriptions.size} topics`);
    const currentSubscriptions = Array.from(this.subscriptions);
    this.subscriptions.clear();
    
    currentSubscriptions.forEach(subscriptionKey => {
      const [topic, sessionKey] = subscriptionKey.split('_');
      const sessionKeyNum = sessionKey ? parseInt(sessionKey) : undefined;
      
      try {
        this.subscribe(topic as SubscriptionTopic, undefined, sessionKeyNum);
      } catch (error) {
        console.error(`Failed to re-subscribe to ${topic}:`, error);
      }
    });
  }

  disconnect(): void {
    console.log('🔌 Manually disconnecting WebSocket');
    this.isConnecting = false;
    this.reconnectAttempts = 0;
    
    if (this.socket) {
      this.socket.disconnect();
      this.socket = null;
      this.callbacks.clear();
      this.subscriptions.clear();
    }
  }

  private setupTopicListeners(): void {
    if (!this.socket) return;

    // Positions stream
    this.socket.on('positions', (data: StreamData<Position[]>) => {
      this.emit('positions', data);
    });

    // Weather stream
    this.socket.on('weather', (data: StreamData<Weather>) => {
      this.emit('weather', data);
    });

    // Lap times stream
    this.socket.on('lap_times', (data: StreamData<LapTime[]>) => {
      this.emit('lap_times', data);
    });

    // Pit stops stream
    this.socket.on('pit_stops', (data: StreamData<PitStop[]>) => {
      this.emit('pit_stops', data);
    });

    // Team radio stream
    this.socket.on('team_radio', (data: StreamData<TeamRadio[]>) => {
      this.emit('team_radio', data);
    });

    // Drivers stream
    this.socket.on('drivers', (data: StreamData<Driver[]>) => {
      this.emit('drivers', data);
    });

    // Race events stream
    this.socket.on('race_event', (data: any) => {
      this.emit('race_event', data);
    });
  }

  subscribe(topic: SubscriptionTopic, callback?: (data: any) => void, sessionKey?: number): void {
    if (!this.socket?.connected) {
      console.warn(`⚠️ Cannot subscribe to ${topic}: WebSocket not connected`);
      throw new Error('WebSocket not connected');
    }

    // Add callback to the topic if provided
    if (callback) {
      this.on(topic, callback);
    }

    // Subscribe to the topic if not already subscribed
    const subscriptionKey = sessionKey ? `${topic}_${sessionKey}` : topic;
    if (!this.subscriptions.has(subscriptionKey)) {
      const subscribeData = sessionKey ? { topic, session_key: sessionKey } : { topic };
      console.log(`📡 Subscribing to topic: ${topic}${sessionKey ? ` (session: ${sessionKey})` : ''}`);
      this.socket.emit('subscribe', subscribeData);
      this.subscriptions.add(subscriptionKey);
    } else {
      console.log(`📡 Already subscribed to topic: ${topic}${sessionKey ? ` (session: ${sessionKey})` : ''}`);
    }
  }

  unsubscribe(topic: SubscriptionTopic): void {
    if (!this.socket?.connected) {
      console.warn(`⚠️ Cannot unsubscribe from ${topic}: WebSocket not connected`);
      return;
    }

    console.log(`📡 Unsubscribing from topic: ${topic}`);
    this.socket.emit('unsubscribe', { topic });
    
    // Remove all subscriptions for this topic
    Array.from(this.subscriptions).forEach(key => {
      if (key.startsWith(topic)) {
        this.subscriptions.delete(key);
      }
    });
  }

  on(event: string, callback: Function): void {
    if (!this.callbacks.has(event)) {
      this.callbacks.set(event, new Set());
    }
    this.callbacks.get(event)!.add(callback);
  }

  off(event: string, callback: Function): void {
    if (this.callbacks.has(event)) {
      this.callbacks.get(event)!.delete(callback);
    }
  }

  private emit(event: string, data: any): void {
    if (this.callbacks.has(event)) {
      this.callbacks.get(event)!.forEach(callback => {
        try {
          callback(data);
        } catch (error) {
          console.error(`Error in ${event} callback:`, error);
        }
      });
    }
  }

  isConnected(): boolean {
    return this.socket?.connected || false;
  }

  getConnectionStatus(): { 
    connected: boolean; 
    connecting: boolean; 
    reconnectAttempts: number; 
    subscriptions: number 
  } {
    return {
      connected: this.socket?.connected || false,
      connecting: this.isConnecting,
      reconnectAttempts: this.reconnectAttempts,
      subscriptions: this.subscriptions.size
    };
  }

  forceReconnect(): void {
    console.log('🔄 Force reconnecting WebSocket');
    this.reconnectAttempts = 0;
    this.disconnect();
    setTimeout(() => {
      this.connect().catch(error => {
        console.error('🔄 Force reconnection failed:', error);
      });
    }, 1000);
  }
}

const websocketService = new WebSocketService();
export { websocketService };
export default websocketService;