import React, { useState, useEffect } from 'react';
import toast from 'react-hot-toast';
import { notificationService } from '../../services/notificationService';
import './AlertSettings.css';

export interface AlertType {
  OVERTAKES: boolean;
  PIT_STOPS: boolean;
  LEAD_CHANGES: boolean;
  FASTEST_LAPS: boolean;
  WEATHER_CHANGES: boolean;
  INCIDENTS: boolean;
}

interface AlertSettingsProps {
  onSettingsChange: (settings: AlertType) => void;
  initialSettings?: AlertType;
}

const AlertSettings: React.FC<AlertSettingsProps> = ({ 
  onSettingsChange, 
  initialSettings 
}) => {
  const [settings, setSettings] = useState<AlertType>(() => {
    // Initialize from notificationService to ensure consistency
    const savedSettings = notificationService?.getSettings();
    return {
      ...{
        OVERTAKES: true,
        PIT_STOPS: true,
        LEAD_CHANGES: true,
        FASTEST_LAPS: false,
        WEATHER_CHANGES: false,
        INCIDENTS: true
      },
      ...savedSettings,
      ...initialSettings
    };
  });

  const [notificationPermission, setNotificationPermission] = useState<NotificationPermission>('default');

  useEffect(() => {
    if ('Notification' in window) {
      setNotificationPermission(Notification.permission);
    }
    
    // Sync with notificationService on mount
    const currentSettings = notificationService.getSettings();
    setSettings(currentSettings);
  }, []);

  // Sync when initialSettings prop changes
  useEffect(() => {
    if (initialSettings) {
      const currentSettings = notificationService.getSettings();
      const mergedSettings = { ...currentSettings, ...initialSettings };
      setSettings(mergedSettings);
      notificationService.updateSettings(mergedSettings);
    }
  }, [initialSettings]);

  const handleToggle = (alertType: keyof AlertType) => {
    const newSettings = {
      ...settings,
      [alertType]: !settings[alertType]
    };
    setSettings(newSettings);
    onSettingsChange(newSettings);
    
    // Show toast feedback
    const alertLabels: Record<keyof AlertType, string> = {
      OVERTAKES: 'Overtakes',
      PIT_STOPS: 'Pit Stops', 
      LEAD_CHANGES: 'Lead Changes',
      FASTEST_LAPS: 'Fastest Laps',
      WEATHER_CHANGES: 'Weather Changes',
      INCIDENTS: 'Incidents'
    };
    
    const label = alertLabels[alertType];
    const enabled = newSettings[alertType];
    
    if (enabled) {
      toast.success(`${label} notifications enabled`, {
        icon: '🔔',
        duration: 2000,
      });
    } else {
      toast(`${label} notifications disabled`, {
        icon: '🔕',
        duration: 2000,
      });
    }
  };

  const requestNotificationPermission = async () => {
    if ('Notification' in window) {
      const permission = await Notification.requestPermission();
      setNotificationPermission(permission);
      
      if (permission === 'granted') {
        toast.success('Browser notifications enabled!', {
          icon: '🔔',
          duration: 3000,
        });
      } else if (permission === 'denied') {
        toast.error('Browser notifications blocked. You can still see in-app notifications.', {
          duration: 5000,
        });
      }
    }
  };

  const alertOptions = [
    {
      key: 'OVERTAKES' as keyof AlertType,
      label: 'Overtakes',
      description: 'Get notified when drivers overtake each other',
      icon: '🏎️'
    },
    {
      key: 'PIT_STOPS' as keyof AlertType,
      label: 'Pit Stops',
      description: 'Alerts for pit stop activities',
      icon: '🔧'
    },
    {
      key: 'LEAD_CHANGES' as keyof AlertType,
      label: 'Lead Changes',
      description: 'When the race leader changes',
      icon: '🏆'
    },
    {
      key: 'FASTEST_LAPS' as keyof AlertType,
      label: 'Fastest Laps',
      description: 'New fastest lap records',
      icon: '⚡'
    },
    {
      key: 'WEATHER_CHANGES' as keyof AlertType,
      label: 'Weather Changes',
      description: 'Significant weather condition changes',
      icon: '🌧️'
    },
    {
      key: 'INCIDENTS' as keyof AlertType,
      label: 'Incidents',
      description: 'Safety cars, crashes, and penalties',
      icon: '⚠️'
    }
  ];

  return (
    <div className="alert-settings">
      <div className="alert-settings-header">
        <h3>Alert Settings</h3>
        <p>Customize your race notifications</p>
      </div>

      {notificationPermission !== 'granted' && (
        <div className="notification-permission-prompt">
          <div className="permission-warning">
            <span className="warning-icon">🔔</span>
            <div>
              <h4>Enable Browser Notifications</h4>
              <p>Allow notifications to receive real-time race alerts</p>
            </div>
            <button 
              className="permission-button"
              onClick={requestNotificationPermission}
            >
              Enable Notifications
            </button>
          </div>
        </div>
      )}

      <div className="alert-options">
        {alertOptions.map((option) => (
          <div key={option.key} className="alert-option">
            <div className="alert-option-info">
              <div className="alert-icon">{option.icon}</div>
              <div className="alert-text">
                <h4>{option.label}</h4>
                <p>{option.description}</p>
              </div>
            </div>
            <label className="toggle-switch">
              <input
                type="checkbox"
                checked={!!settings[option.key]}
                onChange={() => handleToggle(option.key)}
              />
              <span className="toggle-slider"></span>
            </label>
          </div>
        ))}
      </div>

      <div className="alert-settings-footer">
        <div className="notification-status">
          <span className={`status-indicator ${notificationPermission}`}>
            {notificationPermission === 'granted' ? '✅' : 
             notificationPermission === 'denied' ? '❌' : '⏳'}
          </span>
          <span>
            Notifications: {
              notificationPermission === 'granted' ? 'Enabled' :
              notificationPermission === 'denied' ? 'Blocked' : 'Not enabled'
            }
          </span>
        </div>
      </div>
    </div>
  );
};

export default AlertSettings;