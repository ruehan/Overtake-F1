import React, { useState, useEffect } from 'react';
import toast from 'react-hot-toast';
import { notificationService, AlertHistory as AlertHistoryItem, RaceEvent } from '../../services/notificationService';
import './AlertHistory.css';

interface AlertHistoryProps {
  maxItems?: number;
  showFilters?: boolean;
}

const AlertHistory: React.FC<AlertHistoryProps> = ({ 
  maxItems = 50, 
  showFilters = true 
}) => {
  const [history, setHistory] = useState<AlertHistoryItem[]>([]);
  const [filteredHistory, setFilteredHistory] = useState<AlertHistoryItem[]>([]);
  const [selectedEventTypes, setSelectedEventTypes] = useState<Set<RaceEvent['event_type']>>(new Set());
  const [showUnreadOnly, setShowUnreadOnly] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');

  useEffect(() => {
    loadHistory();
    
    // Listen for new notifications
    const handleNewNotification = (event: RaceEvent) => {
      loadHistory();
    };
    
    notificationService.addListener(handleNewNotification);
    
    return () => {
      notificationService.removeListener(handleNewNotification);
    };
  }, []);

  useEffect(() => {
    applyFilters();
  }, [history, selectedEventTypes, showUnreadOnly, searchTerm]);

  const loadHistory = () => {
    const allHistory = notificationService.getHistory();
    setHistory(allHistory.slice(0, maxItems));
  };

  const applyFilters = () => {
    let filtered = [...history];

    // Filter by event type
    if (selectedEventTypes.size > 0) {
      filtered = filtered.filter(item => selectedEventTypes.has(item.event.event_type));
    }

    // Filter by read status
    if (showUnreadOnly) {
      filtered = filtered.filter(item => !item.read);
    }

    // Filter by search term
    if (searchTerm.trim()) {
      const term = searchTerm.toLowerCase();
      filtered = filtered.filter(item => 
        item.event.message.toLowerCase().includes(term) ||
        (item.event.data?.driver_name && item.event.data.driver_name.toLowerCase().includes(term))
      );
    }

    setFilteredHistory(filtered);
  };

  const handleEventTypeToggle = (eventType: RaceEvent['event_type']) => {
    const newSelected = new Set(selectedEventTypes);
    if (newSelected.has(eventType)) {
      newSelected.delete(eventType);
    } else {
      newSelected.add(eventType);
    }
    setSelectedEventTypes(newSelected);
  };

  const handleMarkAsRead = (id: string) => {
    notificationService.markAsRead(id);
    loadHistory();
  };

  const handleMarkAllAsRead = () => {
    notificationService.markAllAsRead();
    loadHistory();
  };

  const handleClearHistory = () => {
    // Create a custom confirmation toast
    toast((t) => (
      <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
        <span>Clear all notification history?</span>
        <div style={{ display: 'flex', gap: '8px' }}>
          <button
            style={{
              background: '#dc3545',
              color: 'white',
              border: 'none',
              padding: '4px 12px',
              borderRadius: '4px',
              fontSize: '12px',
              cursor: 'pointer'
            }}
            onClick={() => {
              notificationService.clearHistory();
              loadHistory();
              toast.dismiss(t.id);
              toast.success('Notification history cleared');
            }}
          >
            Clear
          </button>
          <button
            style={{
              background: '#6c757d',
              color: 'white',
              border: 'none',
              padding: '4px 12px',
              borderRadius: '4px',
              fontSize: '12px',
              cursor: 'pointer'
            }}
            onClick={() => toast.dismiss(t.id)}
          >
            Cancel
          </button>
        </div>
      </div>
    ), {
      duration: 5000,
      style: {
        background: '#fff',
        color: '#333',
        maxWidth: '350px',
      }
    });
  };

  const formatTime = (date: Date): string => {
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;
    
    return date.toLocaleDateString();
  };

  const eventTypeOptions: { type: RaceEvent['event_type']; label: string; icon: string }[] = [
    { type: 'overtake', label: 'Overtakes', icon: '🏎️' },
    { type: 'pit_stop', label: 'Pit Stops', icon: '🔧' },
    { type: 'lead_change', label: 'Lead Changes', icon: '🏆' },
    { type: 'fastest_lap', label: 'Fastest Laps', icon: '⚡' },
    { type: 'weather_change', label: 'Weather', icon: '🌧️' },
    { type: 'incident', label: 'Incidents', icon: '⚠️' }
  ];

  const unreadCount = notificationService.getUnreadCount();

  return (
    <div className="alert-history">
      <div className="alert-history-header">
        <div className="header-title">
          <h3>Notification History</h3>
          {unreadCount > 0 && (
            <span className="unread-badge">{unreadCount}</span>
          )}
        </div>
        
        <div className="header-actions">
          {unreadCount > 0 && (
            <button 
              className="mark-all-read-btn"
              onClick={handleMarkAllAsRead}
            >
              Mark all as read
            </button>
          )}
          <button 
            className="clear-history-btn"
            onClick={handleClearHistory}
          >
            Clear history
          </button>
        </div>
      </div>

      {showFilters && (
        <div className="alert-filters">
          <div className="search-filter">
            <input
              type="text"
              placeholder="Search notifications..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="search-input"
            />
          </div>

          <div className="event-type-filters">
            {eventTypeOptions.map((option) => (
              <button
                key={option.type}
                className={`event-filter ${selectedEventTypes.has(option.type) ? 'active' : ''}`}
                onClick={() => handleEventTypeToggle(option.type)}
              >
                <span className="filter-icon">{option.icon}</span>
                <span className="filter-label">{option.label}</span>
              </button>
            ))}
          </div>

          <label className="unread-filter">
            <input
              type="checkbox"
              checked={showUnreadOnly}
              onChange={(e) => setShowUnreadOnly(e.target.checked)}
            />
            <span>Show unread only</span>
          </label>
        </div>
      )}

      <div className="alert-list">
        {filteredHistory.length === 0 ? (
          <div className="empty-state">
            <div className="empty-icon">📭</div>
            <h4>No notifications found</h4>
            <p>
              {history.length === 0 
                ? "You'll see race notifications here when events happen."
                : "No notifications match your current filters."
              }
            </p>
          </div>
        ) : (
          filteredHistory.map((item) => (
            <div
              key={item.id}
              className={`alert-item ${!item.read ? 'unread' : ''}`}
              onClick={() => !item.read && handleMarkAsRead(item.id)}
            >
              <div className="alert-content">
                <div className="alert-header">
                  <span 
                    className="alert-icon"
                    style={{ color: notificationService.getEventColor(item.event.event_type) }}
                  >
                    {notificationService.getEventIcon(item.event.event_type)}
                  </span>
                  <span className="alert-time">{formatTime(item.timestamp)}</span>
                  {!item.read && <span className="unread-dot"></span>}
                </div>
                
                <div className="alert-message">
                  {item.event.message}
                </div>

                {item.event.data && (
                  <div className="alert-details">
                    {item.event.lap_number && (
                      <span className="detail-item">Lap {item.event.lap_number}</span>
                    )}
                    {item.event.data.lap_time && (
                      <span className="detail-item">
                        Time: {Number(item.event.data.lap_time).toFixed(3)}s
                      </span>
                    )}
                    {item.event.data.pit_duration && (
                      <span className="detail-item">
                        Duration: {Number(item.event.data.pit_duration).toFixed(3)}s
                      </span>
                    )}
                  </div>
                )}
              </div>
            </div>
          ))
        )}
      </div>

      {filteredHistory.length > 0 && filteredHistory.length < history.length && (
        <div className="history-footer">
          <p>Showing {filteredHistory.length} of {history.length} notifications</p>
        </div>
      )}
    </div>
  );
};

export default AlertHistory;