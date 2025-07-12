import toast from 'react-hot-toast';

export interface RaceEvent {
  event_type: 'overtake' | 'pit_stop' | 'lead_change' | 'fastest_lap' | 'weather_change' | 'incident';
  timestamp: string;
  session_key: number;
  driver_number?: number;
  target_driver_number?: number;
  position_gained?: number;
  lap_number?: number;
  data?: Record<string, any>;
  message: string;
}

export interface AlertHistory {
  id: string;
  event: RaceEvent;
  timestamp: Date;
  read: boolean;
}

export interface NotificationSettings {
  OVERTAKES: boolean;
  PIT_STOPS: boolean;
  LEAD_CHANGES: boolean;
  FASTEST_LAPS: boolean;
  WEATHER_CHANGES: boolean;
  INCIDENTS: boolean;
}

class NotificationService {
  private settings: NotificationSettings;
  private history: AlertHistory[] = [];
  private listeners: Array<(event: RaceEvent) => void> = [];
  private maxHistorySize = 100;

  constructor() {
    this.settings = this.loadSettings();
    this.loadHistory();
  }

  private loadSettings(): NotificationSettings {
    const saved = localStorage.getItem('f1-notification-settings');
    if (saved) {
      try {
        return JSON.parse(saved);
      } catch (e) {
        console.error('Error loading notification settings:', e);
      }
    }
    
    // Default settings
    return {
      OVERTAKES: true,
      PIT_STOPS: true,
      LEAD_CHANGES: true,
      FASTEST_LAPS: false,
      WEATHER_CHANGES: false,
      INCIDENTS: true
    };
  }

  private saveSettings(): void {
    try {
      localStorage.setItem('f1-notification-settings', JSON.stringify(this.settings));
      console.log('Settings saved to localStorage:', this.settings);
    } catch (e) {
      console.error('Error saving settings to localStorage:', e);
    }
  }

  private loadHistory(): void {
    const saved = localStorage.getItem('f1-notification-history');
    if (saved) {
      try {
        const parsed = JSON.parse(saved);
        this.history = parsed.map((item: any) => ({
          ...item,
          timestamp: new Date(item.timestamp)
        }));
      } catch (e) {
        console.error('Error loading notification history:', e);
        this.history = [];
      }
    }
  }

  private saveHistory(): void {
    localStorage.setItem('f1-notification-history', JSON.stringify(this.history));
  }

  public updateSettings(newSettings: Partial<NotificationSettings>): void {
    console.log('Updating settings from:', this.settings, 'to:', newSettings);
    this.settings = { ...this.settings, ...newSettings };
    this.saveSettings();
  }

  public getSettings(): NotificationSettings {
    return { ...this.settings };
  }

  public async requestPermission(): Promise<NotificationPermission> {
    if (!('Notification' in window)) {
      console.warn('This browser does not support notifications');
      return 'denied';
    }

    if (Notification.permission === 'granted') {
      return 'granted';
    }

    if (Notification.permission === 'denied') {
      return 'denied';
    }

    const permission = await Notification.requestPermission();
    return permission;
  }

  public isEventEnabled(eventType: RaceEvent['event_type']): boolean {
    const settingMap: Record<RaceEvent['event_type'], keyof NotificationSettings> = {
      'overtake': 'OVERTAKES',
      'pit_stop': 'PIT_STOPS',
      'lead_change': 'LEAD_CHANGES',
      'fastest_lap': 'FASTEST_LAPS',
      'weather_change': 'WEATHER_CHANGES',
      'incident': 'INCIDENTS'
    };

    const settingKey = settingMap[eventType];
    return this.settings[settingKey] || false;
  }

  public async showNotification(event: RaceEvent): Promise<void> {
    // Check if this event type is enabled
    if (!this.isEventEnabled(event.event_type)) {
      return;
    }

    // Add to history
    const historyItem: AlertHistory = {
      id: `${event.session_key}-${event.timestamp}-${Math.random()}`,
      event,
      timestamp: new Date(),
      read: false
    };

    this.history.unshift(historyItem);
    
    // Limit history size
    if (this.history.length > this.maxHistorySize) {
      this.history = this.history.slice(0, this.maxHistorySize);
    }
    
    this.saveHistory();

    // Notify listeners
    this.listeners.forEach(listener => {
      try {
        listener(event);
      } catch (e) {
        console.error('Error in notification listener:', e);
      }
    });

    // Show toast notification (always shown)
    this.showToastNotification(event);

    // Show browser notification if permission granted
    if (Notification.permission === 'granted') {
      await this.showBrowserNotification(event);
    }
  }

  private showToastNotification(event: RaceEvent): void {
    const iconMap: Record<RaceEvent['event_type'], string> = {
      'overtake': '🏎️',
      'pit_stop': '🔧',
      'lead_change': '🏆',
      'fastest_lap': '⚡',
      'weather_change': '🌧️',
      'incident': '⚠️'
    };

    const colorMap: Record<RaceEvent['event_type'], string> = {
      'overtake': '#007bff',
      'pit_stop': '#28a745',
      'lead_change': '#ffc107',
      'fastest_lap': '#e83e8c',
      'weather_change': '#6c757d',
      'incident': '#dc3545'
    };

    const icon = iconMap[event.event_type];
    const color = colorMap[event.event_type];

    toast.success(event.message, {
      icon: icon,
      style: {
        background: color,
        color: '#fff',
        borderRadius: '8px',
        fontSize: '14px',
        fontWeight: '500',
        padding: '12px 16px',
        boxShadow: '0 4px 12px rgba(0, 0, 0, 0.15)',
        maxWidth: '400px',
      },
      duration: 5000,
    });
  }

  private async showBrowserNotification(event: RaceEvent): Promise<void> {
    const iconMap: Record<RaceEvent['event_type'], string> = {
      'overtake': '🏎️',
      'pit_stop': '🔧',
      'lead_change': '🏆',
      'fastest_lap': '⚡',
      'weather_change': '🌧️',
      'incident': '⚠️'
    };

    const titleMap: Record<RaceEvent['event_type'], string> = {
      'overtake': 'Overtake!',
      'pit_stop': 'Pit Stop',
      'lead_change': 'Lead Change!',
      'fastest_lap': 'Fastest Lap!',
      'weather_change': 'Weather Update',
      'incident': 'Race Incident'
    };

    const icon = iconMap[event.event_type];
    const title = `${icon} ${titleMap[event.event_type]}`;

    try {
      const notification = new Notification(title, {
        body: event.message,
        icon: '/favicon.ico',
        badge: '/favicon.ico',
        tag: `f1-${event.event_type}`,
        requireInteraction: false,
        silent: false
      });

      // Auto-close after 5 seconds
      setTimeout(() => {
        notification.close();
      }, 5000);

    } catch (e) {
      console.error('Error showing browser notification:', e);
    }
  }

  public addListener(callback: (event: RaceEvent) => void): void {
    this.listeners.push(callback);
  }

  public removeListener(callback: (event: RaceEvent) => void): void {
    const index = this.listeners.indexOf(callback);
    if (index > -1) {
      this.listeners.splice(index, 1);
    }
  }

  public getHistory(): AlertHistory[] {
    return [...this.history];
  }

  public getUnreadCount(): number {
    return this.history.filter(item => !item.read).length;
  }

  public markAsRead(id: string): void {
    const item = this.history.find(h => h.id === id);
    if (item) {
      item.read = true;
      this.saveHistory();
    }
  }

  public markAllAsRead(): void {
    this.history.forEach(item => {
      item.read = true;
    });
    this.saveHistory();
  }

  public clearHistory(): void {
    this.history = [];
    this.saveHistory();
  }

  public getEventIcon(eventType: RaceEvent['event_type']): string {
    const iconMap: Record<RaceEvent['event_type'], string> = {
      'overtake': '🏎️',
      'pit_stop': '🔧',
      'lead_change': '🏆',
      'fastest_lap': '⚡',
      'weather_change': '🌧️',
      'incident': '⚠️'
    };
    return iconMap[eventType] || '📢';
  }

  public getEventColor(eventType: RaceEvent['event_type']): string {
    const colorMap: Record<RaceEvent['event_type'], string> = {
      'overtake': '#007bff',
      'pit_stop': '#28a745',
      'lead_change': '#ffc107',
      'fastest_lap': '#e83e8c',
      'weather_change': '#6c757d',
      'incident': '#dc3545'
    };
    return colorMap[eventType] || '#6c757d';
  }
}

export const notificationService = new NotificationService();