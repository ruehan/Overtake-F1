import React, { useState, useEffect } from 'react';
import { useWebSocket } from '../../contexts/WebSocketContext';
import './RadioMessageList.css';

interface RadioMessage {
  session_key: number;
  driver_number: number;
  date: string;
  recording_url?: string;
  driver_name?: string;
  team_name?: string;
  category?: string;
  importance?: number;
  duration?: number;
}

interface RadioMessageListProps {
  sessionKey?: number;
  driverNumber?: number;
  limit?: number;
  showFilters?: boolean;
  autoRefresh?: boolean;
}

const RadioMessageList: React.FC<RadioMessageListProps> = ({
  sessionKey = 9158,
  driverNumber,
  limit = 50,
  showFilters = true,
  autoRefresh = true
}) => {
  const [messages, setMessages] = useState<RadioMessage[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedDriver, setSelectedDriver] = useState<number | null>(driverNumber || null);
  const [categoryFilter, setCategoryFilter] = useState<string>('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);
  const { isConnected } = useWebSocket();

  const messageCategories = {
    all: { label: 'All Messages', icon: '📻' },
    strategy: { label: 'Strategy', icon: '🎯' },
    technical: { label: 'Technical', icon: '🔧' },
    motivational: { label: 'Motivational', icon: '💪' },
    warning: { label: 'Warnings', icon: '⚠️' },
    general: { label: 'General', icon: '💬' }
  };

  const driverList = [
    { number: 1, name: 'Max Verstappen', team: 'Red Bull Racing', color: '#0600ef' },
    { number: 11, name: 'Sergio Perez', team: 'Red Bull Racing', color: '#0600ef' },
    { number: 44, name: 'Lewis Hamilton', team: 'Mercedes', color: '#00d2be' },
    { number: 63, name: 'George Russell', team: 'Mercedes', color: '#00d2be' },
    { number: 16, name: 'Charles Leclerc', team: 'Ferrari', color: '#dc0000' },
    { number: 55, name: 'Carlos Sainz', team: 'Ferrari', color: '#dc0000' },
    { number: 4, name: 'Lando Norris', team: 'McLaren', color: '#ff8700' },
    { number: 81, name: 'Oscar Piastri', team: 'McLaren', color: '#ff8700' }
  ];

  useEffect(() => {
    fetchMessages();
    
    if (autoRefresh) {
      const interval = setInterval(fetchMessages, 30000); // Update every 30 seconds
      return () => clearInterval(interval);
    }
  }, [sessionKey, selectedDriver, categoryFilter, searchQuery]);

  const fetchMessages = async () => {
    try {
      setError(null);
      
      let url = `http://localhost:8000/api/v1/team-radio?session_key=${sessionKey}&limit=${limit}`;
      
      if (selectedDriver) {
        url += `&driver_number=${selectedDriver}`;
      }

      const response = await fetch(url);
      
      if (!response.ok) {
        throw new Error('Failed to fetch radio messages');
      }
      
      const data = await response.json();
      
      // Apply local filters
      let filteredData = data;
      
      if (categoryFilter !== 'all') {
        filteredData = filteredData.filter((msg: RadioMessage) => 
          msg.category === categoryFilter
        );
      }
      
      if (searchQuery) {
        const query = searchQuery.toLowerCase();
        filteredData = filteredData.filter((msg: RadioMessage) =>
          msg.driver_name?.toLowerCase().includes(query) ||
          msg.team_name?.toLowerCase().includes(query) ||
          msg.driver_number.toString().includes(query)
        );
      }
      
      setMessages(filteredData);
      setLastUpdated(new Date());
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
      console.error('Error fetching radio messages:', err);
    } finally {
      setLoading(false);
    }
  };

  const getDriverInfo = (driverNumber: number) => {
    return driverList.find(d => d.number === driverNumber) || {
      number: driverNumber,
      name: `Driver ${driverNumber}`,
      team: 'Unknown Team',
      color: '#666'
    };
  };

  const getCategoryIcon = (category?: string) => {
    const categoryKey = category as keyof typeof messageCategories;
    return messageCategories[categoryKey]?.icon || messageCategories.general.icon;
  };

  const getImportanceColor = (importance?: number) => {
    switch (importance) {
      case 5: return '#dc3545'; // Critical
      case 4: return '#fd7e14'; // Important
      case 3: return '#ffc107'; // Normal
      case 2: return '#20c997'; // Low
      case 1: return '#6c757d'; // Minimal
      default: return '#6c757d';
    }
  };

  const formatDuration = (duration?: number) => {
    if (!duration) return 'N/A';
    return `${duration.toFixed(1)}s`;
  };

  const formatTimestamp = (dateString: string) => {
    try {
      const date = new Date(dateString);
      return date.toLocaleTimeString();
    } catch {
      return 'Invalid time';
    }
  };

  const getRelativeTime = (dateString: string) => {
    try {
      const date = new Date(dateString);
      const now = new Date();
      const diffInSeconds = Math.floor((now.getTime() - date.getTime()) / 1000);
      
      if (diffInSeconds < 60) return `${diffInSeconds}s ago`;
      if (diffInSeconds < 3600) return `${Math.floor(diffInSeconds / 60)}m ago`;
      if (diffInSeconds < 86400) return `${Math.floor(diffInSeconds / 3600)}h ago`;
      return `${Math.floor(diffInSeconds / 86400)}d ago`;
    } catch {
      return 'Unknown';
    }
  };

  if (loading) {
    return (
      <div className="radio-message-list loading">
        <div className="loading-spinner">📻</div>
        <p>Loading team radio messages...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="radio-message-list error">
        <div className="error-icon">📻</div>
        <h3>No Team Radio Data</h3>
        <p className="error-message">{error}</p>
        <div className="error-details">
          <p>Team radio messages might not be available because:</p>
          <ul>
            <li>This session doesn't have radio data</li>
            <li>Radio communications are still being processed</li>
            <li>The session is too old or from practice</li>
          </ul>
        </div>
        <button onClick={fetchMessages} className="retry-btn">
          🔄 Retry
        </button>
      </div>
    );
  }

  return (
    <div className="radio-message-list">
      <div className="list-header">
        <div className="header-title">
          <span className="radio-icon">📻</span>
          <h3>Team Radio Messages</h3>
          <div className="message-count">
            {messages.length} message{messages.length !== 1 ? 's' : ''}
          </div>
        </div>
        
        <div className="connection-status">
          <span className={`status-dot ${isConnected ? 'connected' : 'disconnected'}`}></span>
          {lastUpdated && (
            <span className="last-updated">
              Updated {lastUpdated.toLocaleTimeString()}
            </span>
          )}
        </div>
      </div>

      {showFilters && (
        <div className="filters-section">
          <div className="filter-row">
            <div className="filter-group">
              <label>Driver:</label>
              <select 
                value={selectedDriver || ''} 
                onChange={(e) => setSelectedDriver(e.target.value ? Number(e.target.value) : null)}
                className="driver-select"
              >
                <option value="">All Drivers</option>
                {driverList.map(driver => (
                  <option key={driver.number} value={driver.number}>
                    #{driver.number} {driver.name}
                  </option>
                ))}
              </select>
            </div>

            <div className="filter-group">
              <label>Category:</label>
              <select 
                value={categoryFilter} 
                onChange={(e) => setCategoryFilter(e.target.value)}
                className="category-select"
              >
                {Object.entries(messageCategories).map(([key, category]) => (
                  <option key={key} value={key}>
                    {category.icon} {category.label}
                  </option>
                ))}
              </select>
            </div>

            <div className="filter-group">
              <label>Search:</label>
              <input
                type="text"
                placeholder="Search driver, team..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="search-input"
              />
            </div>

            <button onClick={fetchMessages} className="refresh-btn">
              🔄 Refresh
            </button>
          </div>
        </div>
      )}

      <div className="messages-container">
        {messages.length === 0 ? (
          <div className="no-messages">
            <div className="no-messages-icon">🔇</div>
            <h4>No radio messages found</h4>
            <p>Try adjusting your filters or check a different session.</p>
          </div>
        ) : (
          <div className="messages-list">
            {messages.map((message, index) => {
              const driverInfo = getDriverInfo(message.driver_number);
              
              return (
                <div key={index} className="message-item">
                  <div className="message-header">
                    <div className="driver-info">
                      <div 
                        className="driver-number"
                        style={{ backgroundColor: driverInfo.color }}
                      >
                        {message.driver_number}
                      </div>
                      <div className="driver-details">
                        <div className="driver-name">{driverInfo.name}</div>
                        <div className="team-name">{driverInfo.team}</div>
                      </div>
                    </div>
                    
                    <div className="message-meta">
                      <div className="category-badge">
                        <span className="category-icon">
                          {getCategoryIcon(message.category)}
                        </span>
                        <span className="category-text">
                          {message.category || 'general'}
                        </span>
                      </div>
                      
                      <div 
                        className="importance-indicator"
                        style={{ backgroundColor: getImportanceColor(message.importance) }}
                        title={`Importance: ${message.importance || 3}/5`}
                      ></div>
                    </div>
                  </div>

                  <div className="message-content">
                    {message.recording_url ? (
                      <div className="audio-section">
                        <div className="audio-info">
                          <span className="audio-icon">🎵</span>
                          <span className="duration">{formatDuration(message.duration)}</span>
                          <span className="audio-available">Audio Available</span>
                        </div>
                        {/* Audio player would go here */}
                      </div>
                    ) : (
                      <div className="no-audio">
                        <span className="no-audio-icon">🔇</span>
                        <span>No audio available</span>
                      </div>
                    )}
                  </div>

                  <div className="message-footer">
                    <div className="timestamp">
                      <span className="time">{formatTimestamp(message.date)}</span>
                      <span className="relative-time">{getRelativeTime(message.date)}</span>
                    </div>
                    
                    {message.recording_url && (
                      <button className="play-btn" title="Play audio">
                        ▶️ Play
                      </button>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
};

export default RadioMessageList;