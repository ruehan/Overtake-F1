import React, { useState, useEffect } from 'react';
import { useLanguage } from '../contexts/LanguageContext';
import { API_ENDPOINTS } from '../config/api';
import { useApiCache } from '../hooks/useApiCache';

interface CircuitLocation {
  locality: string;
  country: string;
  lat?: string;
  lng?: string;
}

interface Circuit {
  circuit_id: string;
  name: string;
  location: CircuitLocation;
  url: string;
}

interface LapRecord {
  time: string;
  driver: string;
  year: string;
  race: string;
}

interface WinnerStats {
  drivers: { [key: string]: number };
  constructors: { [key: string]: number };
}

interface RaceHistory {
  round: string;
  raceName: string;
  date: string;
  season: string;
  Results?: any[];
}

interface CircuitDetail {
  circuit_info: Circuit;
  race_history: RaceHistory[];
  lap_records: LapRecord[];
  winner_statistics: WinnerStats;
  total_races: number;
  year: number;
}

interface CircuitsData {
  circuits?: Circuit[];
  total_circuits?: number;
  year?: number;
  // For detailed view
  circuit_info?: Circuit;
  race_history?: RaceHistory[];
  lap_records?: LapRecord[];
  winner_statistics?: WinnerStats;
  total_races?: number;
}

const CircuitsPage: React.FC = () => {
  const { t, translateCountry } = useLanguage();
  const [selectedYear, setSelectedYear] = useState(2025);
  const [selectedCircuit, setSelectedCircuit] = useState<string | null>(null);

  // 서킷 데이터 캐싱
  const {
    data: circuitsData,
    loading,
    error,
    refetch
  } = useApiCache<CircuitsData>(
    `circuits-${selectedYear}-${selectedCircuit || 'all'}`,
    async () => {
      let url = API_ENDPOINTS.circuits(selectedYear);
      if (selectedCircuit) {
        url += `&circuit_id=${selectedCircuit}`;
      }
      
      const response = await fetch(url);
      if (!response.ok) throw new Error('Failed to fetch circuits data');
      return await response.json();
    },
    { staleTime: 60 * 60 * 1000 } // 1시간 동안 신선한 데이터로 간주
  );



  const renderCircuitsList = () => {
    if (!circuitsData?.circuits) return null;

    return (
      <div className="f1-card">
        <h3 className="f1-card-title">🏁 {t('circuits.title')} ({circuitsData.circuits.length})</h3>
        
        <div className="f1-grid f1-grid-3">
          {circuitsData.circuits.map((circuit) => (
            <div 
              key={circuit.circuit_id} 
              className="f1-card" 
              style={{ 
                marginBottom: 0, 
                cursor: 'pointer',
                border: selectedCircuit === circuit.circuit_id ? '2px solid #ff6b35' : '1px solid rgba(255, 255, 255, 0.1)'
              }}
              onClick={() => setSelectedCircuit(circuit.circuit_id)}
            >
              <div style={{ marginBottom: '1rem' }}>
                <h4 style={{ fontSize: '1.1rem', marginBottom: '0.5rem' }}>
                  {circuit.name}
                </h4>
                <div style={{ color: '#ccc', fontSize: '0.9rem', marginBottom: '0.5rem' }}>
                  📍 {circuit.location.locality}, {translateCountry(circuit.location.country)}
                </div>
              </div>
              
              <div style={{ 
                display: 'flex', 
                justifyContent: 'space-between', 
                alignItems: 'center',
                fontSize: '0.8rem',
                color: '#666'
              }}>
                <span>{t('circuits.clickDetails')}</span>
                {circuit.url && (
                  <a
                    href={circuit.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    style={{ color: '#ff6b35', textDecoration: 'none' }}
                    onClick={(e) => e.stopPropagation()}
                  >
                    {t('circuits.info')}
                  </a>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  };

  const renderCircuitDetail = () => {
    if (!selectedCircuit || !circuitsData?.circuit_info) return null;

    const circuit = circuitsData.circuit_info;
    const lapRecords = circuitsData.lap_records || [];
    const winnerStats = circuitsData.winner_statistics;
    const raceHistory = circuitsData.race_history || [];

    return (
      <div>
        {/* Circuit Header */}
        <div className="f1-card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '1rem' }}>
            <div style={{ flex: 1 }}>
              <h3 className="f1-card-title" style={{ fontSize: '1.5rem', marginBottom: '0.5rem' }}>
                🏁 {circuit.name}
              </h3>
              <div style={{ fontSize: '1.1rem', color: '#ccc', marginBottom: '1rem' }}>
                📍 {circuit.location.locality}, {translateCountry(circuit.location.country)}
              </div>
              
              <div className="f1-grid f1-grid-3">
                <div style={{ textAlign: 'center' }}>
                  <div style={{ fontSize: '1.5rem', fontWeight: '600', color: '#ff6b35' }}>
                    {circuitsData.total_races || 0}
                  </div>
                  <div style={{ fontSize: '0.9rem', color: '#ccc' }}>{t('circuits.totalRaces')}</div>
                </div>
                <div style={{ textAlign: 'center' }}>
                  <div style={{ fontSize: '1.5rem', fontWeight: '600', color: '#10b981' }}>
                    {lapRecords.length}
                  </div>
                  <div style={{ fontSize: '0.9rem', color: '#ccc' }}>{t('circuits.lapRecords')}</div>
                </div>
                <div style={{ textAlign: 'center' }}>
                  <div style={{ fontSize: '1.5rem', fontWeight: '600', color: '#3b82f6' }}>
                    {Object.keys(winnerStats?.drivers || {}).length}
                  </div>
                  <div style={{ fontSize: '0.9rem', color: '#ccc' }}>{t('circuits.differentWinners')}</div>
                </div>
              </div>
            </div>
            
            <button
              onClick={() => setSelectedCircuit(null)}
              style={{
                background: 'rgba(239, 68, 68, 0.2)',
                border: '1px solid #ef4444',
                color: '#ef4444',
                padding: '0.5rem 1rem',
                cursor: 'pointer',
                borderRadius: '4px'
              }}
            >
              {t('circuits.backToList')}
            </button>
          </div>
        </div>

        {/* Lap Records */}
        {lapRecords.length > 0 && (
          <div className="f1-card">
            <h3 className="f1-card-title">⚡ Fastest Lap Records</h3>
            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.9rem' }}>
                <thead>
                  <tr style={{ borderBottom: '2px solid rgba(255, 255, 255, 0.2)' }}>
                    <th style={{ textAlign: 'left', padding: '1rem 0.5rem', color: '#ff6b35' }}>RANK</th>
                    <th style={{ textAlign: 'left', padding: '1rem 0.5rem', color: '#ff6b35' }}>TIME</th>
                    <th style={{ textAlign: 'left', padding: '1rem 0.5rem', color: '#ff6b35' }}>DRIVER</th>
                    <th style={{ textAlign: 'left', padding: '1rem 0.5rem', color: '#ff6b35' }}>YEAR</th>
                    <th style={{ textAlign: 'left', padding: '1rem 0.5rem', color: '#ff6b35' }}>RACE</th>
                  </tr>
                </thead>
                <tbody>
                  {lapRecords.map((record, index) => (
                    <tr 
                      key={index}
                      style={{ 
                        borderBottom: '1px solid rgba(255, 255, 255, 0.1)',
                        backgroundColor: index % 2 === 0 ? 'rgba(255, 255, 255, 0.02)' : 'transparent'
                      }}
                    >
                      <td style={{ padding: '1rem 0.5rem', fontWeight: '600' }}>
                        <span style={{ color: index === 0 ? '#ffd700' : '#fff' }}>
                          {index + 1}
                        </span>
                      </td>
                      <td style={{ padding: '1rem 0.5rem', fontWeight: '600', color: '#10b981' }}>
                        {record.time}
                      </td>
                      <td style={{ padding: '1rem 0.5rem' }}>{record.driver}</td>
                      <td style={{ padding: '1rem 0.5rem', color: '#ccc' }}>{record.year}</td>
                      <td style={{ padding: '1rem 0.5rem', color: '#ccc' }}>{record.race}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Winner Statistics */}
        {winnerStats && (
          <div className="f1-grid f1-grid-2">
            {/* Driver Winners */}
            <div className="f1-card" style={{ marginBottom: 0 }}>
              <h3 className="f1-card-title">🏆 Most Successful Drivers</h3>
              <div style={{ maxHeight: '300px', overflowY: 'auto' }}>
                {Object.entries(winnerStats.drivers).map(([driver, wins], index) => (
                  <div
                    key={driver}
                    style={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                      padding: '0.75rem 0',
                      borderBottom: '1px solid rgba(255, 255, 255, 0.1)'
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                      <span style={{ 
                        fontWeight: '600', 
                        minWidth: '2rem',
                        color: index < 3 ? '#ffd700' : '#fff'
                      }}>
                        {index + 1}
                      </span>
                      <span>{driver}</span>
                    </div>
                    <div style={{ 
                      fontWeight: '600', 
                      color: '#ff6b35',
                      background: 'rgba(255, 107, 53, 0.2)',
                      padding: '0.25rem 0.75rem',
                      borderRadius: '12px'
                    }}>
                      {wins} win{wins !== 1 ? 's' : ''}
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Constructor Winners */}
            <div className="f1-card" style={{ marginBottom: 0 }}>
              <h3 className="f1-card-title">🏭 Most Successful Teams</h3>
              <div style={{ maxHeight: '300px', overflowY: 'auto' }}>
                {Object.entries(winnerStats.constructors).map(([constructor, wins], index) => (
                  <div
                    key={constructor}
                    style={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'center',
                      padding: '0.75rem 0',
                      borderBottom: '1px solid rgba(255, 255, 255, 0.1)'
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                      <span style={{ 
                        fontWeight: '600', 
                        minWidth: '2rem',
                        color: index < 3 ? '#ffd700' : '#fff'
                      }}>
                        {index + 1}
                      </span>
                      <span>{constructor}</span>
                    </div>
                    <div style={{ 
                      fontWeight: '600', 
                      color: '#10b981',
                      background: 'rgba(16, 185, 129, 0.2)',
                      padding: '0.25rem 0.75rem',
                      borderRadius: '12px'
                    }}>
                      {wins} win{wins !== 1 ? 's' : ''}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Recent Race History */}
        {raceHistory.length > 0 && (
          <div className="f1-card">
            <h3 className="f1-card-title">📅 Recent Race History ({raceHistory.length} races)</h3>
            <div style={{ overflowX: 'auto' }}>
              <div className="f1-grid f1-grid-2">
                {raceHistory.slice(0, 6).map((race, index) => (
                  <div
                    key={`${race.season}-${race.round}`}
                    style={{
                      background: 'rgba(255, 255, 255, 0.02)',
                      borderRadius: '8px',
                      padding: '1rem',
                      border: '1px solid rgba(255, 255, 255, 0.1)',
                      marginBottom: '1rem'
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
                      <div style={{ fontWeight: '600', fontSize: '1.1rem' }}>
                        {race.raceName}
                      </div>
                      <div style={{ color: '#ccc', fontSize: '0.9rem' }}>
                        {race.season}
                      </div>
                    </div>
                    <div style={{ color: '#ccc', fontSize: '0.9rem', marginBottom: '0.5rem' }}>
                      Round {race.round} • {race.date}
                    </div>
                    
                    {race.Results && race.Results.length > 0 && (
                      <div style={{ fontSize: '0.8rem' }}>
                        <div style={{ color: '#ff6b35', marginBottom: '0.25rem' }}>Winner:</div>
                        <div style={{ fontWeight: '600' }}>
                          {race.Results[0].Driver.givenName} {race.Results[0].Driver.familyName}
                        </div>
                        <div style={{ color: '#ccc' }}>
                          {race.Results[0].Constructor.name}
                        </div>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>
    );
  };

  if (loading) return <div className="f1-loading">{t('common.loading')} {t('circuits.title')}...</div>;
  if (error) return <div className="f1-error">{t('common.error')}: {error}</div>;
  if (!circuitsData) return <div className="f1-error">{t('common.noData')}</div>;

  return (
    <div>
      <h1 className="f1-card-title">{t('circuits.title')}</h1>
      
      {/* Controls */}
      <div className="f1-card">
        <div style={{ display: 'flex', gap: '2rem', alignItems: 'center', flexWrap: 'wrap', justifyContent: 'space-between' }}>
          <div>
            <label style={{ marginRight: '0.5rem' }}>{t('circuits.season')}:</label>
            <select 
              value={selectedYear} 
              onChange={(e) => {
                setSelectedYear(Number(e.target.value));
                setSelectedCircuit(null); // Reset circuit selection when changing year
              }}
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
          
          <div style={{ display: 'flex', gap: '1rem', alignItems: 'center' }}>
            {selectedCircuit && (
              <div style={{ fontSize: '0.9rem', color: '#ccc' }}>
                Viewing: <span style={{ color: '#ff6b35', fontWeight: '600' }}>
                  {circuitsData?.circuit_info?.name}
                </span>
              </div>
            )}
            
            {/* 새로고침 버튼 */}
            <button
              onClick={refetch}
              disabled={loading}
              style={{
                background: 'rgba(212, 175, 55, 0.2)',
                border: '1px solid rgba(212, 175, 55, 0.5)',
                color: '#D4AF37',
                padding: '0.5rem',
                borderRadius: '4px',
                cursor: loading ? 'not-allowed' : 'pointer',
                opacity: loading ? 0.6 : 1
              }}
              title="데이터 새로고침"
            >
              {loading ? '⏳' : '🔄'}
            </button>
          </div>
        </div>
      </div>

      {/* Content */}
      {selectedCircuit ? renderCircuitDetail() : renderCircuitsList()}
    </div>
  );
};

export default CircuitsPage;