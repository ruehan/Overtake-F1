import React, { useEffect, useState } from 'react';
import api from '../services/api';
import { Session, Driver, SessionType } from '../types/f1Types';
import F1LiveMap from '../components/LiveMap/F1LiveMap';

function Dashboard() {
  const [currentSession, setCurrentSession] = useState<Session | null>(null);
  const [drivers, setDrivers] = useState<Driver[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        
        // Try to get current session
        try {
          const session = await api.getCurrentSession();
          setCurrentSession(session);
          
          // Fetch drivers for current session
          if (session?.session_key) {
            const driversData = await api.getDrivers(session.session_key);
            setDrivers(driversData);
          }
        } catch (sessionError) {
          console.warn('No current session found:', sessionError);
          // If no current session, use a recent session for demo
          const sessionKey = 9222;
          const driversData = await api.getDrivers(sessionKey);
          setDrivers(driversData);
          
          // Set a mock session to indicate no active session
          setCurrentSession({
            session_key: sessionKey,
            session_name: 'No Active Session',
            session_type: SessionType.PRACTICE_1,
            country: 'Demo',
            circuit: 'Demo Circuit',
            date: new Date().toISOString(),
            status: 'Inactive',
            is_active: false,
            time_since: 'No recent sessions'
          } as Session & { is_active: boolean; time_since: string });
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to fetch data');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  if (loading) return <div style={{ padding: '2rem', textAlign: 'center' }}>Loading...</div>;
  if (error) return <div style={{ padding: '2rem', textAlign: 'center', color: 'red' }}>Error: {error}</div>;

  return (
    <div>
      {/* Session Info Header */}
      <div style={{ marginBottom: '2rem', textAlign: 'center' }}>
        {currentSession ? (
          <div>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '1rem', marginBottom: '0.5rem' }}>
              <h2 style={{ margin: 0, color: '#333' }}>{currentSession.session_name}</h2>
              <span style={{
                padding: '0.25rem 0.75rem',
                borderRadius: '12px',
                fontSize: '0.8rem',
                fontWeight: '600',
                backgroundColor: (currentSession as any).is_active === false ? '#fee' : '#e8f5e8',
                color: (currentSession as any).is_active === false ? '#c53030' : '#2e7d2e'
              }}>
                {(currentSession as any).is_active === false ? 'No Active Session' : 'Live'}
              </span>
            </div>
            <p style={{ margin: 0, color: '#666', fontSize: '1.1rem' }}>
              {currentSession.circuit} - {currentSession.country}
            </p>
            {(currentSession as any).time_since && (
              <p style={{ margin: '0.25rem 0 0 0', color: '#888', fontSize: '0.9rem' }}>
                {(currentSession as any).time_since}
              </p>
            )}
          </div>
        ) : (
          <div>
            <h2 style={{ margin: '0 0 0.5rem 0', color: '#333' }}>No Session Data</h2>
            <p style={{ margin: 0, color: '#666', fontSize: '1.1rem' }}>Unable to fetch session information</p>
          </div>
        )}
      </div>

      {/* Live Map Section */}
      <div style={{ 
        marginBottom: '3rem',
        background: '#fff',
        borderRadius: '8px',
        padding: '1rem',
        boxShadow: '0 2px 8px rgba(0,0,0,0.1)'
      }}>
        <h3 style={{ margin: '0 0 1rem 0', color: '#333' }}>Live Track Map</h3>
        <div style={{ height: '600px' }}>
          <F1LiveMap sessionKey={currentSession?.session_key} circuitId="bahrain" />
        </div>
      </div>

      {/* Drivers Grid */}
      <div style={{
        background: '#fff',
        borderRadius: '8px',
        padding: '1.5rem',
        boxShadow: '0 2px 8px rgba(0,0,0,0.1)'
      }}>
        <h3 style={{ margin: '0 0 1.5rem 0', color: '#333' }}>Drivers ({drivers.length})</h3>
        <div style={{ 
          display: 'grid', 
          gridTemplateColumns: 'repeat(auto-fill, minmax(280px, 1fr))', 
          gap: '1rem' 
        }}>
          {drivers.map(driver => (
            <div 
              key={driver.driver_number} 
              style={{ 
                border: '1px solid #e0e0e0', 
                borderRadius: '6px',
                padding: '1rem',
                borderLeft: `4px solid ${driver.team_colour}`,
                background: '#fafafa',
                transition: 'transform 0.2s, box-shadow 0.2s'
              }}
              onMouseEnter={(e) => {
                e.currentTarget.style.transform = 'translateY(-2px)';
                e.currentTarget.style.boxShadow = '0 4px 12px rgba(0,0,0,0.15)';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.transform = 'translateY(0)';
                e.currentTarget.style.boxShadow = 'none';
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem' }}>
                <span style={{ 
                  fontSize: '1.2rem', 
                  fontWeight: 'bold', 
                  color: driver.team_colour,
                  minWidth: '3rem'
                }}>
                  #{driver.driver_number}
                </span>
                <span style={{ 
                  fontSize: '1.1rem', 
                  fontWeight: '600', 
                  color: '#333'
                }}>
                  {driver.abbreviation}
                </span>
              </div>
              <p style={{ margin: '0 0 0.25rem 0', fontSize: '1rem', fontWeight: '500', color: '#333' }}>
                {driver.name}
              </p>
              <p style={{ margin: 0, fontSize: '0.9em', color: '#666' }}>
                {driver.team_name}
              </p>
              {driver.country_code && (
                <p style={{ margin: '0.25rem 0 0 0', fontSize: '0.8em', color: '#888' }}>
                  {driver.country_code}
                </p>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

export default Dashboard;