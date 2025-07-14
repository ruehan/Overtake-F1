import React, { useState, useEffect } from 'react';
import { useLanguage } from '../contexts/LanguageContext';
import { API_ENDPOINTS } from '../config/api';
import websocketService from '../services/websocket';

interface Driver {
  driver_number: number;
  full_name: string;
  name: string;
  abbreviation: string;
  team_name: string;
  team_colour: string;
  country_code: string;
  headshot_url: string;
}

interface LiveTiming {
  timing: any;
  positions: any;
  timestamp: string;
  status?: string;
}

interface Weather {
  [key: string]: any;
  status?: string;
  message?: string;
}

interface NextRace {
  round: number;
  race_name: string;
  circuit_name: string;
  country: string;
  date: string;
  time?: string;
}

interface DashboardProps {
  onDriverClick?: (driverNumber: number) => void;
}

const Dashboard: React.FC<DashboardProps> = ({ onDriverClick }) => {
  const { t, translateCountry, formatMessage } = useLanguage();
  const [drivers, setDrivers] = useState<Driver[]>([]);
  const [liveTiming, setLiveTiming] = useState<LiveTiming | null>(null);
  const [weather, setWeather] = useState<Weather | null>(null);
  const [nextRace, setNextRace] = useState<NextRace | null>(null);
  const [currentRace, setCurrentRace] = useState<NextRace | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdate, setLastUpdate] = useState<string>('');
  const [isConnected, setIsConnected] = useState(false);

  useEffect(() => {
    fetchInitialData();
    
    // Set up Socket.IO connection for live data
    const connectWebSocket = async () => {
      try {
        await websocketService.connect();
        setIsConnected(true);
        
        // Listen for connection events
        websocketService.on('connected', () => {
          console.log('Socket.IO connected');
          setIsConnected(true);
        });
        
        websocketService.on('disconnect', () => {
          console.log('Socket.IO disconnected');
          setIsConnected(false);
        });
        
        // Listen for live timing data
        websocketService.on('live_timing', (data: any) => {
          setLiveTiming(data.data);
          setLastUpdate(new Date().toLocaleTimeString());
        });
        
      } catch (error) {
        console.error('Socket.IO connection error:', error);
        setIsConnected(false);
      }
    };
    
    connectWebSocket();
    
    // Clean up on unmount
    return () => {
      websocketService.disconnect();
    };
  }, []);

  const fetchInitialData = async () => {
    setLoading(true);
    setError(null);
    
    try {
      // Fetch drivers
      const driversResponse = await fetch(API_ENDPOINTS.drivers);
      if (driversResponse.ok) {
        const driversData = await driversResponse.json();
        setDrivers(driversData.data || []);
      }

      // Fetch weather
      const weatherResponse = await fetch(API_ENDPOINTS.weather);
      if (weatherResponse.ok) {
        const weatherData = await weatherResponse.json();
        setWeather(weatherData.data || {});
      }

      // Fetch next race
      const nextRaceResponse = await fetch(API_ENDPOINTS.nextRace);
      if (nextRaceResponse.ok) {
        const nextRaceData = await nextRaceResponse.json();
        setNextRace(nextRaceData.data);
      }

      // Fetch current race
      const currentRaceResponse = await fetch(API_ENDPOINTS.currentRace);
      if (currentRaceResponse.ok) {
        const currentRaceData = await currentRaceResponse.json();
        setCurrentRace(currentRaceData.data);
      }

      // Fetch initial live timing
      const timingResponse = await fetch(API_ENDPOINTS.liveTiming);
      if (timingResponse.ok) {
        const timingData = await timingResponse.json();
        setLiveTiming(timingData.data || {});
      }

    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateString: string, timeString?: string) => {
    const date = new Date(dateString);
    const options: Intl.DateTimeFormatOptions = { 
      month: 'short', 
      day: 'numeric',
      weekday: 'short'
    };
    
    let formatted = date.toLocaleDateString('en-US', options);
    if (timeString) {
      formatted += ` ${timeString}`;
    }
    return formatted;
  };

  if (loading) return <div className="f1-loading">{t('common.loading')} {t('dashboard.title')}...</div>;
  if (error) return <div className="f1-error">{t('common.error')}: {error}</div>;

  return (
    <div>
      <h1 className="f1-card-title">{t('dashboard.title')}</h1>
      
      {/* Connection Status */}
      <div className="f1-card">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <h3 className="f1-card-title" style={{ marginBottom: '0.5rem' }}>{t('dashboard.connection')}</h3>
            <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
              <div className={`f1-status ${isConnected ? 'live' : 'completed'}`}>
                {isConnected ? t('dashboard.connected') : t('dashboard.disconnected')}
              </div>
              {lastUpdate && (
                <span style={{ color: '#ccc', fontSize: '0.9rem' }}>
                  {t('dashboard.lastUpdate')}: {lastUpdate}
                </span>
              )}
            </div>
          </div>
          <div style={{ textAlign: 'right' }}>
            <div style={{ fontSize: '0.9rem', color: '#ccc' }}>LiveF1 Data Stream</div>
            <div style={{ fontSize: '0.8rem', color: '#666' }}>Real-time telemetry</div>
          </div>
        </div>
      </div>

      {/* Current/Next Race */}
      <div className="f1-grid f1-grid-2">
        {currentRace && (
          <div className="f1-card">
            <h3 className="f1-card-title">{t('dashboard.currentRace')}</h3>
            <h2 style={{ fontSize: '1.5rem', marginBottom: '0.5rem' }}>{currentRace.race_name}</h2>
            <p style={{ color: '#ccc', marginBottom: '1rem' }}>{currentRace.circuit_name}</p>
            <div className="f1-status live">{t('data.raceWeekend')}</div>
          </div>
        )}
        
        {nextRace && !currentRace && (
          <div className="f1-card">
            <h3 className="f1-card-title">{t('dashboard.nextRace')}</h3>
            <h2 style={{ fontSize: '1.5rem', marginBottom: '0.5rem' }}>{nextRace.race_name}</h2>
            <p style={{ color: '#ccc', marginBottom: '0.5rem' }}>{nextRace.circuit_name}</p>
            <p style={{ marginBottom: '1rem' }}>{formatDate(nextRace.date, nextRace.time)}</p>
            <div className="f1-status upcoming">{t('common.round')} {nextRace.round}</div>
          </div>
        )}
        
        {/* Live Timing Status */}
        <div className="f1-card">
          <h3 className="f1-card-title">{t('dashboard.liveTiming')}</h3>
          <div style={{ marginBottom: '1rem' }}>
            {liveTiming ? (
              <div>
                <div style={{ marginBottom: '0.5rem' }}>
                  <span style={{ color: '#ccc' }}>Timing Data:</span>
                  <span style={{ marginLeft: '0.5rem', color: (liveTiming.timing && Object.keys(liveTiming.timing).length > 0) ? '#10b981' : '#666' }}>
                    {(liveTiming.timing && Object.keys(liveTiming.timing).length > 0) ? `✅ ${t('data.timingDataActive')}` : `❌ ${t('data.timingDataNoData')}`}
                  </span>
                </div>
                <div style={{ marginBottom: '0.5rem' }}>
                  <span style={{ color: '#ccc' }}>Position Data:</span>
                  <span style={{ marginLeft: '0.5rem', color: (liveTiming.positions && Object.keys(liveTiming.positions).length > 0) ? '#10b981' : '#666' }}>
                    {(liveTiming.positions && Object.keys(liveTiming.positions).length > 0) ? `✅ ${t('data.timingDataActive')}` : `❌ ${t('data.timingDataNoData')}`}
                  </span>
                </div>
                <div style={{ fontSize: '0.8rem', color: '#666' }}>
                  {t('dashboard.lastUpdate')}: {new Date(liveTiming.timestamp).toLocaleTimeString()}
                </div>
                {liveTiming.status && (
                  <div style={{ fontSize: '0.8rem', color: '#ccc', marginTop: '0.5rem' }}>
                    Status: {liveTiming.status === 'no_active_session' ? t('data.noActiveSession') : 'Connection error'}
                  </div>
                )}
              </div>
            ) : (
              <p style={{ color: '#666' }}>{t('common.noData')}</p>
            )}
          </div>
          
          {!currentRace && (
            <div className="f1-status completed">{t('dashboard.noActiveSession')}</div>
          )}
        </div>
      </div>

      {/* Weather Data */}
      <div className="f1-card">
        <h3 className="f1-card-title">{t('dashboard.trackConditions')}</h3>
        {weather && Object.keys(weather).length > 0 && !weather.status ? (
          <div style={{ 
            display: 'grid', 
            gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', 
            gap: '1rem' 
          }}>
            {Object.entries(weather).map(([key, value]) => (
              <div key={key} style={{ 
                background: 'rgba(255, 255, 255, 0.02)',
                padding: '1rem',
                borderRadius: '8px',
                border: '1px solid rgba(255, 255, 255, 0.1)'
              }}>
                <div style={{ fontSize: '0.9rem', color: '#ccc', marginBottom: '0.5rem' }}>
                  {key.replace(/([A-Z])/g, ' $1').replace(/^./, str => str.toUpperCase())}
                </div>
                <div style={{ fontSize: '1.1rem', fontWeight: '600' }}>
                  {typeof value === 'object' ? JSON.stringify(value) : String(value)}
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div style={{ textAlign: 'center', padding: '2rem' }}>
            <div style={{ fontSize: '1.1rem', marginBottom: '0.5rem', color: '#ccc' }}>
              {t('dashboard.noWeatherData')}
            </div>
            <p style={{ color: '#666', fontSize: '0.9rem' }}>
              {weather?.message || t('data.weatherUnavailable')}
            </p>
          </div>
        )}
      </div>

      {/* Drivers Grid */}
      <div className="f1-card">
        <h3 className="f1-card-title">{t('dashboard.drivers')} ({drivers.length})</h3>
        
        {drivers.length === 0 ? (
          <p style={{ color: '#666', textAlign: 'center', padding: '2rem' }}>
            {t('common.noData')}
          </p>
        ) : (
          <div className="f1-grid f1-grid-4">
            {drivers.map((driver) => (
              <div 
                key={driver.driver_number} 
                className="f1-card" 
                style={{ 
                  marginBottom: 0, 
                  padding: '1.2rem',
                  cursor: onDriverClick ? 'pointer' : 'default',
                  transition: 'transform 0.2s ease, box-shadow 0.2s ease'
                }}
                onClick={() => onDriverClick && onDriverClick(driver.driver_number)}
                onMouseEnter={(e) => {
                  if (onDriverClick) {
                    e.currentTarget.style.transform = 'translateY(-2px)';
                    e.currentTarget.style.boxShadow = `0 8px 16px ${driver.team_colour || '#ff6b35'}33`;
                  }
                }}
                onMouseLeave={(e) => {
                  if (onDriverClick) {
                    e.currentTarget.style.transform = 'translateY(0)';
                    e.currentTarget.style.boxShadow = 'none';
                  }
                }}>
                <div style={{ display: 'flex', gap: '1.2rem', height: '140px' }}>
                  {/* 왼쪽 정보 영역 */}
                  <div style={{ flex: 1, display: 'flex', flexDirection: 'column', justifyContent: 'space-between', paddingTop: '0.5rem', paddingBottom: '0.5rem' }}>
                    {/* 드라이버 번호 */}
                    <div style={{
                      background: driver.team_colour || '#ff6b35',
                      color: '#fff',
                      width: '3rem',
                      height: '3rem',
                      borderRadius: '6px',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      fontWeight: '700',
                      fontSize: '1.3rem',
                      boxShadow: `0 4px 8px ${driver.team_colour || '#ff6b35'}33`
                    }}>
                      {driver.driver_number}
                    </div>
                    
                    {/* 드라이버 이름 */}
                    <div style={{ marginTop: '0.5rem' }}>
                      <div style={{ fontWeight: '700', fontSize: '1.1rem', marginBottom: '0.4rem', color: '#fff' }}>
                        {driver.abbreviation}
                      </div>
                      <div style={{ fontSize: '0.85rem', fontWeight: '500', color: '#e0e0e0', marginBottom: '0.4rem', lineHeight: '1.2' }}>
                        {driver.full_name || driver.name}
                      </div>
                      <div style={{ fontSize: '0.75rem', color: '#aaa', lineHeight: '1.2' }}>
                        {driver.team_name}
                      </div>
                    </div>
                  </div>
                  
                  {/* 오른쪽 이미지 영역 */}
                  <div style={{ width: '120px', height: '140px', position: 'relative' }}>
                    {driver.headshot_url ? (
                      <img 
                        src={driver.headshot_url.startsWith('/') ? driver.headshot_url : `/${driver.headshot_url}`} 
                        alt={driver.name}
                        style={{
                          width: '100%',
                          height: '100%',
                          borderRadius: '10px',
                          objectFit: 'cover',
                          objectPosition: 'center top',
                          border: `3px solid ${driver.team_colour || '#ff6b35'}`,
                          boxShadow: `0 4px 12px ${driver.team_colour || '#ff6b35'}33`
                        }}
                        onError={(e) => {
                          const target = e.target as HTMLImageElement;
                          target.style.display = 'none';
                          const fallback = target.nextElementSibling as HTMLElement;
                          if (fallback) fallback.style.display = 'flex';
                        }}
                      />
                    ) : null}
                    <div style={{
                      background: `linear-gradient(135deg, ${driver.team_colour || '#ff6b35'}, ${driver.team_colour || '#ff6b35'}88, #333)`,
                      color: '#fff',
                      width: '100%',
                      height: '100%',
                      borderRadius: '10px',
                      display: driver.headshot_url ? 'none' : 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      fontWeight: '700',
                      fontSize: '1.8rem',
                      border: `3px solid ${driver.team_colour || '#ff6b35'}`,
                      boxShadow: `0 4px 12px ${driver.team_colour || '#ff6b35'}33`
                    }}>
                      {driver.abbreviation}
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* System Status */}
      <div className="f1-card">
        <h3 className="f1-card-title">{t('dashboard.systemStatus')}</h3>
        <div className="f1-grid f1-grid-3">
          <div>
            <div style={{ fontWeight: '600', marginBottom: '0.5rem' }}>LiveF1 API</div>
            <div className="f1-status live">OPERATIONAL</div>
          </div>
          <div>
            <div style={{ fontWeight: '600', marginBottom: '0.5rem' }}>F1 Data API</div>
            <div className="f1-status live">OPERATIONAL</div>
          </div>
          <div>
            <div style={{ fontWeight: '600', marginBottom: '0.5rem' }}>WebSocket</div>
            <div className={`f1-status ${isConnected ? 'live' : 'completed'}`}>
              {isConnected ? t('dashboard.connected') : t('dashboard.disconnected')}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;