import { io, Socket } from 'socket.io-client';
import { Position, Weather, LapTime, PitStop, TeamRadio } from '../types';

export type SubscriptionTopic = 'positions' | 'weather' | 'lap_times' | 'pit_stops' | 'team_radio';

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
  }

  subscribe(topic: SubscriptionTopic, sessionKey: number): Promise<void> {
    return new Promise((resolve, reject) => {
      if (!this.socket?.connected) {
        reject(new Error('WebSocket not connected'));
        return;
      }

      const subscriptionKey = `${topic}_${sessionKey}`;
      if (this.subscriptions.has(subscriptionKey)) {
        resolve();
        return;
      }

      this.socket.emit('subscribe', { topic, session_key: sessionKey });

      this.socket.once('subscribed', (data: { topic: string; session_key: number }) => {
        if (data.topic === topic && data.session_key === sessionKey) {
          this.subscriptions.add(subscriptionKey);
          resolve();
        }
      });

      setTimeout(() => {
        reject(new Error('Subscription timeout'));
      }, 5000);
    });
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

  on(event: 'positions', callback: StreamCallback<Position[]>): void;
  on(event: 'weather', callback: StreamCallback<Weather>): void;
  on(event: 'lap_times', callback: StreamCallback<LapTime[]>): void;
  on(event: 'pit_stops', callback: StreamCallback<PitStop[]>): void;
  on(event: 'team_radio', callback: StreamCallback<TeamRadio[]>): void;
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