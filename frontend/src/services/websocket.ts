import { io, Socket } from 'socket.io-client';
import { Position, Weather, LapTime, PitStop, TeamRadio, Driver } from '../types/f1Types';

export type SubscriptionTopic = 'positions' | 'weather' | 'lap_times' | 'pit_stops' | 'team_radio' | 'drivers';

interface StreamData<T> {
  data: T;
  timestamp: string;
}

type StreamCallback<T> = (data: StreamData<T>) => void;

class WebSocketService {
  private socket: Socket | null = null;
  private callbacks: Map<string, Set<Function>> = new Map();
  private subscriptions: Set<string> = new Set();

  connect(): Promise<void> {
    return new Promise((resolve, reject) => {
      if (this.socket?.connected) {
        resolve();
        return;
      }

      this.socket = io(process.env.REACT_APP_WS_URL || 'http://localhost:8000', {
        path: '/socket.io',
        transports: ['websocket'],
      });

      this.socket.on('connect', () => {
        console.log('WebSocket connected');
        resolve();
      });

      this.socket.on('disconnect', () => {
        console.log('WebSocket disconnected');
      });

      this.socket.on('connect_error', (error) => {
        console.error('WebSocket connection error:', error);
        reject(error);
      });

      this.socket.on('error', (error: any) => {
        console.error('WebSocket error:', error);
      });

      this.socket.on('stream_error', (data: { topic: string; error: string }) => {
        console.error(`Stream error for ${data.topic}:`, data.error);
      });

      // Set up listeners for each topic
      this.setupTopicListeners();
    });
  }

  disconnect(): void {
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
  }

  subscribe(topic: SubscriptionTopic, callback: (data: any) => void, sessionKey?: number): void {
    if (!this.socket?.connected) {
      throw new Error('WebSocket not connected');
    }

    // Add callback to the topic
    this.on(topic, callback);

    // Subscribe to the topic if not already subscribed
    if (sessionKey) {
      const subscriptionKey = `${topic}_${sessionKey}`;
      if (!this.subscriptions.has(subscriptionKey)) {
        this.socket.emit('subscribe', { topic, session_key: sessionKey });
        this.subscriptions.add(subscriptionKey);
      }
    }
  }

  unsubscribe(topic: SubscriptionTopic): void {
    if (!this.socket?.connected) return;

    this.socket.emit('unsubscribe', { topic });
    
    // Remove all subscriptions for this topic
    Array.from(this.subscriptions).forEach(key => {
      if (key.startsWith(topic)) {
        this.subscriptions.delete(key);
      }
    });
  }

  on(event: SubscriptionTopic, callback: Function): void;
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
}

export default new WebSocketService();