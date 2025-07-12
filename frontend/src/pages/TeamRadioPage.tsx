import React, { useState, useEffect } from 'react';
import RadioMessageList from '../components/TeamRadio/RadioMessageList';
import AudioPlayer from '../components/TeamRadio/AudioPlayer';
import './TeamRadioPage.css';

interface RadioStats {
  total_messages: number;
  drivers_with_radio: Array<{
    driver_number: number;
    message_count: number;
  }>;
  most_active_driver?: {
    driver_number: number;
    message_count: number;
    driver_name?: string;
  };
}

interface SelectedMessage {
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

interface SessionOption {
  session_key: number;
  location: string;
  session_name: string;
  radio_message_count: number;
  date_start: string;
}

const TeamRadioPage: React.FC = () => {
  const [sessionKey, setSessionKey] = useState(9158);
  const [selectedDriver, setSelectedDriver] = useState<number | null>(null);
  const [activeTab, setActiveTab] = useState<'messages' | 'statistics' | 'timeline'>('messages');
  const [radioStats, setRadioStats] = useState<RadioStats | null>(null);
  const [selectedMessage, setSelectedMessage] = useState<SelectedMessage | null>(null);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [availableSessions, setAvailableSessions] = useState<SessionOption[]>([]);
  const [sessionsLoading, setSessionsLoading] = useState(true);

  const driverList = [
    { number: 1, name: 'Max Verstappen', team: 'Red Bull Racing', color: '#0600ef' },
    { number: 11, name: 'Sergio Perez', team: 'Red Bull Racing', color: '#0600ef' },
    { number: 44, name: 'Lewis Hamilton', team: 'Mercedes', color: '#00d2be' },
    { number: 63, name: 'George Russell', team: 'Mercedes', color: '#00d2be' },
    { number: 16, name: 'Charles Leclerc', team: 'Ferrari', color: '#dc0000' },
    { number: 55, name: 'Carlos Sainz', team: 'Ferrari', color: '#dc0000' },
    { number: 4, name: 'Lando Norris', team: 'McLaren', color: '#ff8700' },
    { number: 81, name: 'Oscar Piastri', team: 'McLaren', color: '#ff8700' },
    { number: 14, name: 'Fernando Alonso', team: 'Aston Martin', color: '#006f62' },
    { number: 18, name: 'Lance Stroll', team: 'Aston Martin', color: '#006f62' }
  ];

  useEffect(() => {
    fetchAvailableSessions();
  }, []);

  useEffect(() => {
    if (activeTab === 'statistics') {
      fetchRadioStats();
    }
  }, [sessionKey, activeTab]);

  const fetchAvailableSessions = async () => {
    try {
      setSessionsLoading(true);
      const response = await fetch('http://localhost:8000/api/v1/sessions/with-radio?limit=20');
      
      if (response.ok) {
        const sessions = await response.json();
        setAvailableSessions(sessions);
        
        // Set the first available session as default if we have sessions
        if (sessions.length > 0) {
          setSessionKey(sessions[0].session_key);
        }
      }
    } catch (err) {
      console.error('Error fetching available sessions:', err);
    } finally {
      setSessionsLoading(false);
    }
  };

  const fetchRadioStats = async () => {
    try {
      const response = await fetch(
        `http://localhost:8000/api/v1/team-radio/stats?session_key=${sessionKey}`
      );
      
      if (response.ok) {
        const data = await response.json();
        setRadioStats(data);
      }
    } catch (err) {
      console.error('Error fetching radio stats:', err);
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

  const handleMessageSelect = (message: SelectedMessage) => {
    setSelectedMessage(message);
  };

  return (
    <div className="team-radio-page">
      <div className="radio-page-header">
        <div className="header-content">
          <h1>Team Radio Communications</h1>
          <p>Listen to real-time team radio messages and strategic communications</p>
        </div>
        
        <div className="radio-controls">
          <div className="control-group">
            <label htmlFor="session-select">Session:</label>
            <select 
              id="session-select"
              value={sessionKey} 
              onChange={(e) => setSessionKey(Number(e.target.value))}
              className="session-select"
              disabled={sessionsLoading}
            >
              {sessionsLoading ? (
                <option value="">Loading sessions...</option>
              ) : availableSessions.length > 0 ? (
                availableSessions.map(session => (
                  <option key={session.session_key} value={session.session_key}>
                    {session.location} {session.session_name} ({session.radio_message_count} messages)
                  </option>
                ))
              ) : (
                <option value={9158}>Singapore GP Practice 1 (Fallback)</option>
              )}
            </select>
          </div>
          
          <div className="control-group">
            <label htmlFor="driver-select">Driver Filter:</label>
            <select 
              id="driver-select"
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

          <div className="control-group">
            <label className="checkbox-label">
              <input
                type="checkbox"
                checked={autoRefresh}
                onChange={(e) => setAutoRefresh(e.target.checked)}
              />
              Auto Refresh
            </label>
          </div>
        </div>
      </div>

      <div className="radio-tabs">
        <button
          className={`tab-button ${activeTab === 'messages' ? 'active' : ''}`}
          onClick={() => setActiveTab('messages')}
        >
          <span className="tab-icon">📻</span>
          Radio Messages
        </button>
        <button
          className={`tab-button ${activeTab === 'statistics' ? 'active' : ''}`}
          onClick={() => setActiveTab('statistics')}
        >
          <span className="tab-icon">📊</span>
          Statistics
        </button>
        <button
          className={`tab-button ${activeTab === 'timeline' ? 'active' : ''}`}
          onClick={() => setActiveTab('timeline')}
        >
          <span className="tab-icon">⏰</span>
          Timeline
        </button>
      </div>

      <div className="radio-content">
        {activeTab === 'messages' && (
          <div className="messages-tab">
            <div className="messages-layout">
              <div className="messages-section">
                <RadioMessageList
                  sessionKey={sessionKey}
                  driverNumber={selectedDriver || undefined}
                  showFilters={true}
                  autoRefresh={autoRefresh}
                />
              </div>
              
              {selectedMessage && (
                <div className="player-section">
                  <h3>🎵 Now Playing</h3>
                  <AudioPlayer
                    audioUrl={selectedMessage.recording_url}
                    title="Team Radio"
                    driverName={selectedMessage.driver_name}
                    driverNumber={selectedMessage.driver_number}
                    teamColor={getDriverInfo(selectedMessage.driver_number).color}
                    duration={selectedMessage.duration}
                  />
                </div>
              )}
            </div>
          </div>
        )}

        {activeTab === 'statistics' && (
          <div className="statistics-tab">
            {radioStats ? (
              <div className="stats-grid">
                <div className="stat-card">
                  <div className="stat-header">
                    <h3>📻 Total Messages</h3>
                  </div>
                  <div className="stat-value">{radioStats.total_messages}</div>
                  <div className="stat-description">
                    Radio communications in this session
                  </div>
                </div>

                <div className="stat-card">
                  <div className="stat-header">
                    <h3>👥 Active Drivers</h3>
                  </div>
                  <div className="stat-value">{radioStats.drivers_with_radio.length}</div>
                  <div className="stat-description">
                    Drivers with radio activity
                  </div>
                </div>

                {radioStats.most_active_driver && (
                  <div className="stat-card featured">
                    <div className="stat-header">
                      <h3>🏆 Most Active</h3>
                    </div>
                    <div className="driver-stat">
                      <div 
                        className="driver-number"
                        style={{ 
                          backgroundColor: getDriverInfo(radioStats.most_active_driver.driver_number).color 
                        }}
                      >
                        {radioStats.most_active_driver.driver_number}
                      </div>
                      <div className="driver-details">
                        <div className="driver-name">
                          {getDriverInfo(radioStats.most_active_driver.driver_number).name}
                        </div>
                        <div className="message-count">
                          {radioStats.most_active_driver.message_count} messages
                        </div>
                      </div>
                    </div>
                  </div>
                )}

                <div className="drivers-breakdown stat-card wide">
                  <div className="stat-header">
                    <h3>📋 Driver Breakdown</h3>
                  </div>
                  <div className="drivers-list">
                    {radioStats.drivers_with_radio
                      .sort((a, b) => b.message_count - a.message_count)
                      .map(driver => {
                        const driverInfo = getDriverInfo(driver.driver_number);
                        return (
                          <div key={driver.driver_number} className="driver-row">
                            <div className="driver-info">
                              <div 
                                className="driver-number"
                                style={{ backgroundColor: driverInfo.color }}
                              >
                                {driver.driver_number}
                              </div>
                              <div className="driver-details">
                                <div className="driver-name">{driverInfo.name}</div>
                                <div className="team-name">{driverInfo.team}</div>
                              </div>
                            </div>
                            <div className="message-count-badge">
                              {driver.message_count}
                            </div>
                          </div>
                        );
                      })}
                  </div>
                </div>
              </div>
            ) : (
              <div className="stats-loading">
                <div className="loading-spinner">📊</div>
                <p>Loading radio statistics...</p>
              </div>
            )}
          </div>
        )}

        {activeTab === 'timeline' && (
          <div className="timeline-tab">
            <div className="timeline-placeholder">
              <div className="placeholder-icon">⏰</div>
              <h3>Timeline View</h3>
              <p>Chronological view of radio messages integrated with race events.</p>
              <p className="coming-soon">🚧 Coming Soon</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default TeamRadioPage;