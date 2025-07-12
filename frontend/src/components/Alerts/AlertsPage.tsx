import React, { useState, useEffect } from 'react';
import toast from 'react-hot-toast';
import AlertSettings, { AlertType } from './AlertSettings';
import AlertHistory from './AlertHistory';
import { notificationService, RaceEvent } from '../../services/notificationService';
import { useWebSocket } from '../../contexts/WebSocketContext';
import './AlertsPage.css';

const AlertsPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'settings' | 'history'>('settings');
  const [alertSettings, setAlertSettings] = useState<AlertType>(() => 
    notificationService.getSettings()
  );
  const [unreadCount, setUnreadCount] = useState(0);
  const { isConnected, subscribe, on, off } = useWebSocket();

  useEffect(() => {
    // Load initial settings and ensure they're synced
    const settings = notificationService.getSettings();
    setAlertSettings(settings);
    setUnreadCount(notificationService.getUnreadCount());

    // Set up WebSocket event handlers for race events
    const handleConnect = () => {
      // Subscribe to race events (no session key needed for race events)
      subscribe('race_events');
    };

    const handleRaceEvent = (data: any) => {
      const event: RaceEvent = {
        event_type: data.event_type,
        timestamp: data.timestamp,
        session_key: data.session_key,
        driver_number: data.driver_number,
        target_driver_number: data.target_driver_number,
        position_gained: data.position_gained,
        lap_number: data.lap_number,
        data: data.data,
        message: data.message
      };

      // Show notification through notification service
      notificationService.showNotification(event);
      setUnreadCount(notificationService.getUnreadCount());
    };

    // Set up notification listener for UI updates
    const handleNotificationUpdate = (event: RaceEvent) => {
      setUnreadCount(notificationService.getUnreadCount());
    };

    // Set up WebSocket event listeners
    on('connected', handleConnect);
    on('race_event', handleRaceEvent);
    
    // Listen for notification updates
    notificationService.addListener(handleNotificationUpdate);

    return () => {
      off('connected', handleConnect);
      off('race_event', handleRaceEvent);
      notificationService.removeListener(handleNotificationUpdate);
    };
  }, [isConnected]);
  
  // Subscribe to race events when connection state changes
  useEffect(() => {
    if (isConnected) {
      subscribe('race_events');
    }
  }, [isConnected, subscribe]);

  const handleSettingsChange = (newSettings: AlertType) => {
    // Update both local state and service
    setAlertSettings(newSettings);
    notificationService.updateSettings(newSettings);
    
    // Log for debugging
    console.log('Settings updated:', newSettings);
  };

  const handleTabChange = (tab: 'settings' | 'history') => {
    setActiveTab(tab);
    if (tab === 'history') {
      // Update unread count when viewing history
      setTimeout(() => {
        setUnreadCount(notificationService.getUnreadCount());
      }, 100);
    }
  };

  const handleTestNotification = async () => {
    try {
      // First check if notifications are supported
      if (!('Notification' in window)) {
        toast.error('This browser does not support notifications');
        return;
      }

      // Request permission if not already granted
      if (Notification.permission === 'default') {
        const permission = await notificationService.requestPermission();
        
        if (permission !== 'granted') {
          toast.error('Notification permission was denied. Please enable notifications in your browser settings.', {
            duration: 6000,
          });
          return;
        }
      } else if (Notification.permission === 'denied') {
        toast.error('Notifications are blocked. Please enable them in your browser settings and refresh the page.', {
          duration: 6000,
        });
        return;
      }

      // Create multiple test events to demonstrate different types
      const testEvents: RaceEvent[] = [
        {
          event_type: 'overtake',
          timestamp: new Date().toISOString(),
          session_key: 9222,
          driver_number: 44,
          target_driver_number: 1,
          message: "🏎️ Test: Hamilton overtakes Verstappen!"
        },
        {
          event_type: 'fastest_lap',
          timestamp: new Date().toISOString(),
          session_key: 9222,
          driver_number: 16,
          lap_number: 25,
          message: "⚡ Test: Leclerc sets fastest lap!"
        },
        {
          event_type: 'pit_stop',
          timestamp: new Date().toISOString(),
          session_key: 9222,
          driver_number: 63,
          lap_number: 30,
          message: "🔧 Test: Russell pits!"
        }
      ];

      // Show notifications with delay between them
      for (let i = 0; i < testEvents.length; i++) {
        const event = testEvents[i];
        
        // Only show if this event type is enabled
        if (notificationService.isEventEnabled(event.event_type)) {
          setTimeout(async () => {
            await notificationService.showNotification(event);
            setUnreadCount(notificationService.getUnreadCount());
          }, i * 1000); // 1 second delay between notifications
        }
      }

      // Show success message
      const enabledCount = testEvents.filter(e => notificationService.isEventEnabled(e.event_type)).length;
      
      if (enabledCount > 0) {
        toast.success(`🎉 Sending ${enabledCount} test notifications! Check your notification history and browser notifications.`, {
          duration: 4000,
        });
      } else {
        toast('ℹ️ No event types are enabled. Please enable some notification types first.', {
          duration: 4000,
        });
      }
      
    } catch (error) {
      console.error('Error sending test notification:', error);
      toast.error('Failed to send test notification. Please check the console for details.');
    }
  };

  return (
    <div className="alerts-page">
      <div className="alerts-page-header">
        <h1>Alert Settings</h1>
        <p>Manage your race notifications and view alert history</p>
        
        <div className="connection-status">
          <span className={`status-dot ${isConnected ? 'connected' : 'disconnected'}`}></span>
          <span>WebSocket: {isConnected ? 'Connected' : 'Disconnected'}</span>
        </div>
      </div>

      <div className="alerts-tabs">
        <button
          className={`tab-button ${activeTab === 'settings' ? 'active' : ''}`}
          onClick={() => handleTabChange('settings')}
        >
          <span className="tab-icon">⚙️</span>
          Settings
        </button>
        <button
          className={`tab-button ${activeTab === 'history' ? 'active' : ''}`}
          onClick={() => handleTabChange('history')}
        >
          <span className="tab-icon">📋</span>
          History
          {unreadCount > 0 && (
            <span className="tab-badge">{unreadCount}</span>
          )}
        </button>
      </div>

      <div className="alerts-content">
        {activeTab === 'settings' && (
          <div className="settings-tab">
            <AlertSettings
              initialSettings={alertSettings}
              onSettingsChange={handleSettingsChange}
            />
            
            <div className="test-section">
              <h3>Test Notifications</h3>
              <p>Test your notification settings to make sure everything works correctly. This will send sample notifications for each enabled event type.</p>
              <button 
                className="test-notification-btn"
                onClick={handleTestNotification}
              >
                🔔 Send Test Notifications
              </button>
              <div className="test-info">
                <p><strong>Note:</strong> Test notifications will only be sent for event types that are currently enabled in your settings above.</p>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'history' && (
          <div className="history-tab">
            <AlertHistory
              maxItems={50}
              showFilters={true}
            />
          </div>
        )}
      </div>
    </div>
  );
};

export default AlertsPage;