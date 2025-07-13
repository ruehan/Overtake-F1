import React, { useState, useEffect } from 'react';

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

const Dashboard: React.FC = () => {
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
    
    // Set up WebSocket connection for live data
    const ws = new WebSocket('ws://localhost:8000/ws');
    
    ws.onopen = () => {
      console.log('WebSocket connected');
      setIsConnected(true);
      ws.send('ping'); // Keep-alive
    };
    
    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.type === 'live_timing') {
          setLiveTiming(data.data);
          setLastUpdate(new Date().toLocaleTimeString());
        }
      } catch (err) {
        console.error('Error parsing WebSocket message:', err);
      }
    };
    
    ws.onclose = () => {
      console.log('WebSocket disconnected');
      setIsConnected(false);
    };
    
    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
      setIsConnected(false);
    };
    
    // Clean up on unmount
    return () => {
      ws.close();
    };
  }, []);

  const fetchInitialData = async () => {
    setLoading(true);
    setError(null);
    
    try {
      // Fetch drivers
      const driversResponse = await fetch('http://localhost:8000/api/v1/drivers');
      if (driversResponse.ok) {
        const driversData = await driversResponse.json();
        setDrivers(driversData.data || []);
      }

      // Fetch weather
      const weatherResponse = await fetch('http://localhost:8000/api/v1/weather');
      if (weatherResponse.ok) {
        const weatherData = await weatherResponse.json();
        setWeather(weatherData.data || {});
      }

      // Fetch next race
      const nextRaceResponse = await fetch('http://localhost:8000/api/v1/calendar/next');
      if (nextRaceResponse.ok) {
        const nextRaceData = await nextRaceResponse.json();
        setNextRace(nextRaceData.data);
      }

      // Fetch current race
      const currentRaceResponse = await fetch('http://localhost:8000/api/v1/calendar/current');
      if (currentRaceResponse.ok) {
        const currentRaceData = await currentRaceResponse.json();
        setCurrentRace(currentRaceData.data);
      }

      // Fetch initial live timing
      const timingResponse = await fetch('http://localhost:8000/api/v1/live-timing');
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

  if (loading) return <div className="f1-loading">Loading Live Dashboard...</div>;
  if (error) return <div className="f1-error">Error: {error}</div>;

  return (
    <div>
      <h1 className="f1-card-title">🔴 F1 Live Dashboard</h1>
      
      {/* Connection Status */}
      <div className="f1-card">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <h3 className="f1-card-title" style={{ marginBottom: '0.5rem' }}>📡 Live Connection</h3>
            <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
              <div className={`f1-status ${isConnected ? 'live' : 'completed'}`}>
                {isConnected ? 'CONNECTED' : 'DISCONNECTED'}
              </div>
              {lastUpdate && (
                <span style={{ color: '#ccc', fontSize: '0.9rem' }}>
                  Last update: {lastUpdate}
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
            <h3 className="f1-card-title">🔴 Current Race Weekend</h3>
            <h2 style={{ fontSize: '1.5rem', marginBottom: '0.5rem' }}>{currentRace.race_name}</h2>
            <p style={{ color: '#ccc', marginBottom: '1rem' }}>{currentRace.circuit_name}</p>
            <div className="f1-status live">RACE WEEKEND</div>
          </div>
        )}
        
        {nextRace && !currentRace && (
          <div className="f1-card">
            <h3 className="f1-card-title">⏭️ Next Race</h3>
            <h2 style={{ fontSize: '1.5rem', marginBottom: '0.5rem' }}>{nextRace.race_name}</h2>
            <p style={{ color: '#ccc', marginBottom: '0.5rem' }}>{nextRace.circuit_name}</p>
            <p style={{ marginBottom: '1rem' }}>{formatDate(nextRace.date, nextRace.time)}</p>
            <div className="f1-status upcoming">Round {nextRace.round}</div>
          </div>
        )}
        
        {/* Live Timing Status */}
        <div className="f1-card">
          <h3 className="f1-card-title">⏱️ Live Timing</h3>
          <div style={{ marginBottom: '1rem' }}>
            {liveTiming ? (
              <div>
                <div style={{ marginBottom: '0.5rem' }}>
                  <span style={{ color: '#ccc' }}>Timing Data:</span>
                  <span style={{ marginLeft: '0.5rem', color: (liveTiming.timing && Object.keys(liveTiming.timing).length > 0) ? '#10b981' : '#666' }}>
                    {(liveTiming.timing && Object.keys(liveTiming.timing).length > 0) ? '✅ Active' : '❌ No Data'}
                  </span>
                </div>
                <div style={{ marginBottom: '0.5rem' }}>
                  <span style={{ color: '#ccc' }}>Position Data:</span>
                  <span style={{ marginLeft: '0.5rem', color: (liveTiming.positions && Object.keys(liveTiming.positions).length > 0) ? '#10b981' : '#666' }}>
                    {(liveTiming.positions && Object.keys(liveTiming.positions).length > 0) ? '✅ Active' : '❌ No Data'}
                  </span>
                </div>
                <div style={{ fontSize: '0.8rem', color: '#666' }}>
                  Last update: {new Date(liveTiming.timestamp).toLocaleTimeString()}
                </div>
                {liveTiming.status && (
                  <div style={{ fontSize: '0.8rem', color: '#ccc', marginTop: '0.5rem' }}>
                    Status: {liveTiming.status === 'no_active_session' ? 'No active F1 session' : 'Connection error'}
                  </div>
                )}
              </div>
            ) : (
              <p style={{ color: '#666' }}>No timing data available</p>
            )}
          </div>
          
          {!currentRace && (
            <div className="f1-status completed">NO ACTIVE SESSION</div>
          )}
        </div>
      </div>

      {/* Weather Data */}
      <div className="f1-card">
        <h3 className="f1-card-title">🌤️ Track Conditions</h3>
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
              🌤️ No Live Weather Data
            </div>
            <p style={{ color: '#666', fontSize: '0.9rem' }}>
              {weather?.message || "Weather data only available during active F1 sessions"}
            </p>
          </div>
        )}
      </div>

      {/* Drivers Grid */}
      <div className="f1-card">
        <h3 className="f1-card-title">🏎️ Current Drivers ({drivers.length})</h3>
        
        {drivers.length === 0 ? (
          <p style={{ color: '#666', textAlign: 'center', padding: '2rem' }}>
            No driver data available
          </p>
        ) : (
          <div className="f1-grid f1-grid-4">
            {drivers.map((driver) => (
              <div key={driver.driver_number} className="f1-card" style={{ marginBottom: 0 }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', marginBottom: '1rem' }}>
                  <div style={{
                    background: driver.team_colour || '#ff6b35',
                    color: '#fff',
                    width: '3rem',
                    height: '3rem',
                    borderRadius: '50%',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontWeight: '700',
                    fontSize: '1.1rem'
                  }}>
                    {driver.driver_number}
                  </div>
                  <div style={{ flex: 1 }}>
                    <div style={{ fontWeight: '600', marginBottom: '0.25rem' }}>
                      {driver.abbreviation}
                    </div>
                    <div style={{ fontSize: '0.8rem', color: '#ccc' }}>
                      {driver.country_code}
                    </div>
                  </div>
                </div>
                
                <div style={{ marginBottom: '0.5rem' }}>
                  <div style={{ fontSize: '0.9rem', fontWeight: '500' }}>
                    {driver.full_name || driver.name}
                  </div>
                </div>
                
                <div style={{ fontSize: '0.8rem', color: '#ccc' }}>
                  {driver.team_name}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* System Status */}
      <div className="f1-card">
        <h3 className="f1-card-title">🔧 System Status</h3>
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
              {isConnected ? 'CONNECTED' : 'DISCONNECTED'}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;