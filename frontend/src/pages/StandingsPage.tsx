import React, { useState, useEffect } from 'react';
import { useLanguage } from '../contexts/LanguageContext';
import { usePageMeta } from '../hooks/usePageMeta';

interface DriverStanding {
  position: number;
  driver_number: number;
  name: string;
  code: string;
  team: string;
  points: number;
  wins: number;
}

interface ConstructorStanding {
  position: number;
  team: string;
  nationality: string;
  points: number;
  wins: number;
}

const StandingsPage: React.FC = () => {
  const { t } = useLanguage();
  usePageMeta('standings');
  const [activeTab, setActiveTab] = useState<'drivers' | 'constructors'>('drivers');
  const [selectedYear, setSelectedYear] = useState(2025);
  const [driverStandings, setDriverStandings] = useState<DriverStanding[]>([]);
  const [constructorStandings, setConstructorStandings] = useState<ConstructorStanding[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchStandingsData();
  }, [selectedYear, activeTab]);

  const fetchStandingsData = async () => {
    setLoading(true);
    setError(null);
    
    try {
      if (activeTab === 'drivers') {
        const response = await fetch(`http://localhost:8000/api/v1/driver-standings?year=${selectedYear}`);
        if (!response.ok) throw new Error('Failed to fetch driver standings');
        const data = await response.json();
        setDriverStandings(data.data || []);
      } else {
        const response = await fetch(`http://localhost:8000/api/v1/constructor-standings?year=${selectedYear}`);
        if (!response.ok) throw new Error('Failed to fetch constructor standings');
        const data = await response.json();
        setConstructorStandings(data.data || []);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  };

  const getPositionClass = (position: number) => {
    if (position === 1) return 'p1';
    if (position === 2) return 'p2';
    if (position === 3) return 'p3';
    return '';
  };

  const getPositionIcon = (position: number) => {
    switch (position) {
      case 1: return '🏆';
      case 2: return '🥈';
      case 3: return '🥉';
      default: return position.toString();
    }
  };

  if (loading) return <div className="f1-loading">{t('common.loading')} {t('standings.title')}...</div>;
  if (error) return <div className="f1-error">{t('common.error')}: {error}</div>;

  return (
    <div>
      <h1 className="f1-card-title">{t('standings.title')}</h1>
      
      {/* Year Selector */}
      <div className="f1-card">
        <div style={{ display: 'flex', gap: '1rem', alignItems: 'center', marginBottom: '1rem' }}>
          <label>{t('standings.season')}:</label>
          <select 
            value={selectedYear} 
            onChange={(e) => setSelectedYear(Number(e.target.value))}
            style={{
              background: 'rgba(255, 255, 255, 0.1)',
              border: '1px solid rgba(255, 255, 255, 0.2)',
              color: '#fff',
              padding: '0.5rem',
              borderRadius: '4px'
            }}
          >
            <option value={2025}>2025</option>
            <option value={2024}>2024</option>
            <option value={2023}>2023</option>
          </select>
        </div>

        {/* Tab Buttons */}
        <div style={{ display: 'flex', gap: '0.5rem' }}>
          <button
            className={`f1-nav-links button ${activeTab === 'drivers' ? 'active' : ''}`}
            onClick={() => setActiveTab('drivers')}
            style={{
              background: activeTab === 'drivers' ? 'linear-gradient(45deg, #ff6b35, #f7931e)' : 'transparent',
              border: '1px solid rgba(255, 255, 255, 0.2)',
              color: '#fff',
              padding: '0.5rem 1rem',
              cursor: 'pointer',
              borderRadius: '4px'
            }}
          >
            {t('standings.drivers')}
          </button>
          <button
            className={`f1-nav-links button ${activeTab === 'constructors' ? 'active' : ''}`}
            onClick={() => setActiveTab('constructors')}
            style={{
              background: activeTab === 'constructors' ? 'linear-gradient(45deg, #ff6b35, #f7931e)' : 'transparent',
              border: '1px solid rgba(255, 255, 255, 0.2)',
              color: '#fff',
              padding: '0.5rem 1rem',
              cursor: 'pointer',
              borderRadius: '4px'
            }}
          >
            {t('standings.constructors')}
          </button>
        </div>
      </div>

      {/* Driver Standings */}
      {activeTab === 'drivers' && (
        <div className="f1-card">
          <h3 className="f1-card-title">{t('standings.drivers')}</h3>
          
          {driverStandings.length === 0 ? (
            <p style={{ textAlign: 'center', color: '#ccc', padding: '2rem' }}>
              {t('common.noData')} ({selectedYear})
            </p>
          ) : (
            <table className="f1-table">
              <thead>
                <tr>
                  <th>{t('standings.position')}</th>
                  <th>{t('standings.driver')}</th>
                  <th>{t('standings.team')}</th>
                  <th>{t('standings.points')}</th>
                  <th>{t('standings.wins')}</th>
                </tr>
              </thead>
              <tbody>
                {driverStandings.map((driver) => (
                  <tr key={driver.driver_number}>
                    <td>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                        <span className={`position ${getPositionClass(driver.position)}`}>
                          {getPositionIcon(driver.position)}
                        </span>
                      </div>
                    </td>
                    <td>
                      <div>
                        <div style={{ fontWeight: '600', marginBottom: '0.25rem' }}>{driver.name}</div>
                        <div style={{ fontSize: '0.8rem', color: '#ccc' }}>
                          #{driver.driver_number} • {driver.code}
                        </div>
                      </div>
                    </td>
                    <td style={{ color: '#ccc' }}>{driver.team}</td>
                    <td>
                      <span style={{ 
                        color: '#ff6b35', 
                        fontWeight: '700',
                        fontSize: '1.1rem'
                      }}>
                        {driver.points}
                      </span>
                    </td>
                    <td style={{ textAlign: 'center' }}>
                      {driver.wins > 0 ? (
                        <span style={{ color: '#ffd700', fontWeight: '600' }}>{driver.wins}</span>
                      ) : (
                        <span style={{ color: '#666' }}>0</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      )}

      {/* Constructor Standings */}
      {activeTab === 'constructors' && (
        <div className="f1-card">
          <h3 className="f1-card-title">{t('standings.constructors')}</h3>
          
          {constructorStandings.length === 0 ? (
            <p style={{ textAlign: 'center', color: '#ccc', padding: '2rem' }}>
              {t('common.noData')} ({selectedYear})
            </p>
          ) : (
            <table className="f1-table">
              <thead>
                <tr>
                  <th>{t('standings.position')}</th>
                  <th>{t('standings.team')}</th>
                  <th>Nationality</th>
                  <th>{t('standings.points')}</th>
                  <th>{t('standings.wins')}</th>
                </tr>
              </thead>
              <tbody>
                {constructorStandings.map((constructor) => (
                  <tr key={constructor.team}>
                    <td>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                        <span className={`position ${getPositionClass(constructor.position)}`}>
                          {getPositionIcon(constructor.position)}
                        </span>
                      </div>
                    </td>
                    <td>
                      <div style={{ fontWeight: '600' }}>{constructor.team}</div>
                    </td>
                    <td style={{ color: '#ccc' }}>{constructor.nationality}</td>
                    <td>
                      <span style={{ 
                        color: '#ff6b35', 
                        fontWeight: '700',
                        fontSize: '1.1rem'
                      }}>
                        {constructor.points}
                      </span>
                    </td>
                    <td style={{ textAlign: 'center' }}>
                      {constructor.wins > 0 ? (
                        <span style={{ color: '#ffd700', fontWeight: '600' }}>{constructor.wins}</span>
                      ) : (
                        <span style={{ color: '#666' }}>0</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      )}

      {/* Championship Analysis */}
      {(driverStandings.length > 0 || constructorStandings.length > 0) && (
        <div className="f1-card">
          <h3 className="f1-card-title">📊 {t('standings.battle')}</h3>
          
          <div className="f1-grid f1-grid-2">
            {driverStandings.length > 1 && (
              <div>
                <h4 style={{ color: '#ff6b35', marginBottom: '1rem' }}>{t('standings.driverChampionship')}</h4>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                  <span style={{ fontWeight: '600' }}>{t('standings.leader')}:</span>
                  <span>{driverStandings[0]?.name}</span>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                  <span style={{ fontWeight: '600' }}>{t('standings.points')}:</span>
                  <span style={{ color: '#ff6b35' }}>{driverStandings[0]?.points}</span>
                </div>
                {driverStandings.length > 1 && (
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                    <span style={{ fontWeight: '600' }}>{t('standings.gapToSecond')}:</span>
                    <span style={{ color: '#ffd700' }}>
                      +{driverStandings[0]?.points - driverStandings[1]?.points} pts
                    </span>
                  </div>
                )}
              </div>
            )}

            {constructorStandings.length > 1 && (
              <div>
                <h4 style={{ color: '#ff6b35', marginBottom: '1rem' }}>{t('standings.constructorChampionship')}</h4>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                  <span style={{ fontWeight: '600' }}>{t('standings.leader')}:</span>
                  <span>{constructorStandings[0]?.team}</span>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                  <span style={{ fontWeight: '600' }}>{t('standings.points')}:</span>
                  <span style={{ color: '#ff6b35' }}>{constructorStandings[0]?.points}</span>
                </div>
                {constructorStandings.length > 1 && (
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                    <span style={{ fontWeight: '600' }}>{t('standings.gapToSecond')}:</span>
                    <span style={{ color: '#ffd700' }}>
                      +{constructorStandings[0]?.points - constructorStandings[1]?.points} pts
                    </span>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default StandingsPage;