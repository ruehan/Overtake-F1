import React, { useEffect, useState } from 'react';
import './App.css';
import api from './services/api';
import { Session, Driver } from './types';

function App() {
  const [currentSession, setCurrentSession] = useState<Session | null>(null);
  const [drivers, setDrivers] = useState<Driver[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        // Fetch current session
        const session = await api.getCurrentSession();
        setCurrentSession(session);

        // Fetch drivers for current session
        if (session?.session_key) {
          const driversData = await api.getDrivers(session.session_key);
          setDrivers(driversData);
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to fetch data');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  if (loading) return <div className="App">Loading...</div>;
  if (error) return <div className="App">Error: {error}</div>;

  return (
    <div className="App">
      <header className="App-header">
        <h1>OpenF1 Dashboard</h1>
        {currentSession && (
          <div>
            <h2>{currentSession.session_name}</h2>
            <p>{currentSession.circuit} - {currentSession.country}</p>
          </div>
        )}
        <div className="drivers-grid">
          <h3>Drivers</h3>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', gap: '1rem' }}>
            {drivers.map(driver => (
              <div key={driver.driver_number} style={{ 
                border: '1px solid #ccc', 
                padding: '1rem',
                borderLeft: `4px solid ${driver.team_colour}`
              }}>
                <h4>#{driver.driver_number} {driver.abbreviation}</h4>
                <p>{driver.name}</p>
                <p style={{ fontSize: '0.9em', color: '#666' }}>{driver.team_name}</p>
              </div>
            ))}
          </div>
        </div>
      </header>
    </div>
  );
}

export default App;
