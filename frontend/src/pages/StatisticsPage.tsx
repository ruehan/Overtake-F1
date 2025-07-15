import React, { useState, useEffect } from 'react';
import { useLanguage } from '../contexts/LanguageContext';
import { API_ENDPOINTS } from '../config/api';

interface DriverStat {
  driver_number: number;
  name: string;
  slug: string;
  season_wins: number;
  season_podiums: number;
  season_points: number;
  races_entered: number;
  best_finish: number | null;
  average_finish: number;
  fastest_laps: number;
  poles: number;
  dnf: number;
  championship_position: string | null;
  team: string;
  data_source: string;
}

interface TeamStat {
  team_slug: string;
  name: string;
  full_name: string;
  season_wins: number;
  season_podiums: number;
  season_poles: number;
  season_fastest_laps: number;
  season_points: number;
  season_races: number;
  season_dnf: number;
  championship_position: string | null;
  drivers_count: string | null;
  data_source: string;
}

interface StatisticsData {
  data?: DriverStat[] | TeamStat[];
  total_drivers?: number;
  total_teams?: number;
  year: number;
  data_source?: string;
}

const StatisticsPage: React.FC = () => {
  const { t } = useLanguage();
  const [statisticsData, setStatisticsData] = useState<StatisticsData | null>(null);
  const [selectedYear, setSelectedYear] = useState(2025); // 2025가 기본값
  const [viewType, setViewType] = useState<'drivers' | 'teams'>('drivers');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchStatisticsData();
  }, [selectedYear, viewType]);

  const fetchStatisticsData = async () => {
    setLoading(true);
    setError(null);
    
    try {
      let response;
      if (viewType === 'drivers') {
        // 새로운 JSON 기반 API 사용 (2025년용)
        if (selectedYear === 2025) {
          response = await fetch(API_ENDPOINTS.allDriversSeasonStats(selectedYear));
        } else {
          response = await fetch(API_ENDPOINTS.statistics(selectedYear, viewType));
        }
      } else {
        // 팀 통계는 새로운 JSON 기반 API 사용 (2025년용)
        if (selectedYear === 2025) {
          response = await fetch(API_ENDPOINTS.allTeamsSeasonStats(selectedYear));
        } else {
          response = await fetch(API_ENDPOINTS.statistics(selectedYear, viewType));
        }
      }
      
      if (!response.ok) throw new Error('Failed to fetch statistics data');
      const data = await response.json();
      setStatisticsData(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  };

  const getStatColor = (value: number, max: number, type: 'good' | 'bad' = 'good') => {
    const intensity = Math.min(value / max, 1);
    if (type === 'good') {
      return `rgba(16, 185, 129, ${0.2 + intensity * 0.6})`;
    } else {
      return `rgba(239, 68, 68, ${0.2 + intensity * 0.6})`;
    }
  };

  const renderDriverStatistics = () => {
    if (!statisticsData?.data || !Array.isArray(statisticsData.data)) return null;

    const drivers = statisticsData.data as DriverStat[];
    const maxWins = Math.max(...drivers.map(d => d.season_wins));
    const maxPodiums = Math.max(...drivers.map(d => d.season_podiums));
    const maxDNFs = Math.max(...drivers.map(d => d.dnf));
    const maxFastestLaps = Math.max(...drivers.map(d => d.fastest_laps));
    const maxPoles = Math.max(...drivers.map(d => d.poles));

    return (
      <div className="f1-card">
        <h3 className="f1-card-title">{t('statistics.driverStats')} ({drivers.length} {t('statistics.drivers').toLowerCase()})</h3>
        
        <div style={{ overflowX: 'auto' }}>
          <table style={{ 
            width: '100%', 
            borderCollapse: 'collapse',
            fontSize: '0.9rem'
          }}>
            <thead>
              <tr style={{ borderBottom: '2px solid rgba(255, 255, 255, 0.2)' }}>
                <th style={{ textAlign: 'left', padding: '1rem 0.5rem', color: '#ff6b35' }}>POS</th>
                <th style={{ textAlign: 'left', padding: '1rem 0.5rem', color: '#ff6b35' }}>DRIVER</th>
                <th style={{ textAlign: 'left', padding: '1rem 0.5rem', color: '#ff6b35' }}>TEAM</th>
                <th style={{ textAlign: 'center', padding: '1rem 0.5rem', color: '#ff6b35' }}>PTS</th>
                <th style={{ textAlign: 'center', padding: '1rem 0.5rem', color: '#ff6b35' }}>WINS</th>
                <th style={{ textAlign: 'center', padding: '1rem 0.5rem', color: '#ff6b35' }}>PODIUMS</th>
                <th style={{ textAlign: 'center', padding: '1rem 0.5rem', color: '#ff6b35' }}>POLES</th>
                <th style={{ textAlign: 'center', padding: '1rem 0.5rem', color: '#ff6b35' }}>FL</th>
                <th style={{ textAlign: 'center', padding: '1rem 0.5rem', color: '#ff6b35' }}>DNF</th>
              </tr>
            </thead>
            <tbody>
              {drivers.map((driver, index) => (
                <tr 
                  key={driver.name}
                  style={{ 
                    borderBottom: '1px solid rgba(255, 255, 255, 0.1)',
                    backgroundColor: index % 2 === 0 ? 'rgba(255, 255, 255, 0.02)' : 'transparent'
                  }}
                >
                  <td style={{ padding: '1rem 0.5rem', fontWeight: '600' }}>
                    <span style={{ 
                      color: index + 1 <= 3 ? '#ffd700' : '#fff',
                      fontSize: index + 1 <= 3 ? '1.1rem' : '1rem'
                    }}>
                      {driver.championship_position || (index + 1)}
                    </span>
                  </td>
                  <td style={{ padding: '1rem 0.5rem' }}>
                    <div>
                      <div style={{ fontWeight: '600', marginBottom: '0.25rem' }}>
                        {driver.name}
                      </div>
                      <div style={{ fontSize: '0.8rem', color: '#ccc' }}>
                        #{driver.driver_number}
                      </div>
                    </div>
                  </td>
                  <td style={{ padding: '1rem 0.5rem', color: '#ccc', fontSize: '0.9rem' }}>
                    {driver.team}
                  </td>
                  <td style={{ 
                    padding: '1rem 0.5rem', 
                    textAlign: 'center', 
                    fontWeight: '600',
                    color: '#10b981'
                  }}>
                    {driver.season_points}
                  </td>
                  <td style={{ 
                    padding: '1rem 0.5rem', 
                    textAlign: 'center',
                    background: driver.season_wins > 0 ? getStatColor(driver.season_wins, maxWins, 'good') : 'transparent',
                    borderRadius: '4px'
                  }}>
                    {driver.season_wins}
                  </td>
                  <td style={{ 
                    padding: '1rem 0.5rem', 
                    textAlign: 'center',
                    background: driver.season_podiums > 0 ? getStatColor(driver.season_podiums, maxPodiums, 'good') : 'transparent',
                    borderRadius: '4px'
                  }}>
                    {driver.season_podiums}
                  </td>
                  <td style={{ 
                    padding: '1rem 0.5rem', 
                    textAlign: 'center',
                    background: driver.poles > 0 ? getStatColor(driver.poles, maxPoles, 'good') : 'transparent',
                    borderRadius: '4px'
                  }}>
                    {driver.poles}
                  </td>
                  <td style={{ 
                    padding: '1rem 0.5rem', 
                    textAlign: 'center',
                    background: driver.fastest_laps > 0 ? getStatColor(driver.fastest_laps, maxFastestLaps, 'good') : 'transparent',
                    borderRadius: '4px'
                  }}>
                    {driver.fastest_laps}
                  </td>
                  <td style={{ 
                    padding: '1rem 0.5rem', 
                    textAlign: 'center',
                    background: driver.dnf > 0 ? getStatColor(driver.dnf, maxDNFs, 'bad') : 'transparent',
                    borderRadius: '4px'
                  }}>
                    {driver.dnf}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    );
  };

  const renderTeamStatistics = () => {
    if (!statisticsData?.data || !Array.isArray(statisticsData.data)) return null;

    const teams = statisticsData.data as TeamStat[];
    const maxWins = Math.max(...teams.map(t => t.season_wins));
    const maxPodiums = Math.max(...teams.map(t => t.season_podiums));
    const maxDNFs = Math.max(...teams.map(t => t.season_dnf));
    const maxFastestLaps = Math.max(...teams.map(t => t.season_fastest_laps));
    const maxPoles = Math.max(...teams.map(t => t.season_poles));

    return (
      <div className="f1-card">
        <h3 className="f1-card-title">🏭 Constructor Statistics ({teams.length} teams)</h3>
        
        <div style={{ overflowX: 'auto' }}>
          <table style={{ 
            width: '100%', 
            borderCollapse: 'collapse',
            fontSize: '0.9rem'
          }}>
            <thead>
              <tr style={{ borderBottom: '2px solid rgba(255, 255, 255, 0.2)' }}>
                <th style={{ textAlign: 'left', padding: '1rem 0.5rem', color: '#ff6b35' }}>POS</th>
                <th style={{ textAlign: 'left', padding: '1rem 0.5rem', color: '#ff6b35' }}>TEAM</th>
                <th style={{ textAlign: 'center', padding: '1rem 0.5rem', color: '#ff6b35' }}>PTS</th>
                <th style={{ textAlign: 'center', padding: '1rem 0.5rem', color: '#ff6b35' }}>WINS</th>
                <th style={{ textAlign: 'center', padding: '1rem 0.5rem', color: '#ff6b35' }}>PODIUMS</th>
                <th style={{ textAlign: 'center', padding: '1rem 0.5rem', color: '#ff6b35' }}>POLES</th>
                <th style={{ textAlign: 'center', padding: '1rem 0.5rem', color: '#ff6b35' }}>FL</th>
                <th style={{ textAlign: 'center', padding: '1rem 0.5rem', color: '#ff6b35' }}>DNF</th>
              </tr>
            </thead>
            <tbody>
              {teams.map((team, index) => (
                <tr 
                  key={team.name}
                  style={{ 
                    borderBottom: '1px solid rgba(255, 255, 255, 0.1)',
                    backgroundColor: index % 2 === 0 ? 'rgba(255, 255, 255, 0.02)' : 'transparent'
                  }}
                >
                  <td style={{ padding: '1rem 0.5rem', fontWeight: '600' }}>
                    <span style={{ 
                      color: index + 1 <= 3 ? '#ffd700' : '#fff',
                      fontSize: index + 1 <= 3 ? '1.1rem' : '1rem'
                    }}>
                      {team.championship_position || (index + 1)}
                    </span>
                  </td>
                  <td style={{ padding: '1rem 0.5rem' }}>
                    <div>
                      <div style={{ fontWeight: '600', marginBottom: '0.25rem' }}>
                        {team.name}
                      </div>
                      <div style={{ fontSize: '0.8rem', color: '#ccc' }}>
                        {team.drivers_count || 'N/A'}
                      </div>
                    </div>
                  </td>
                  <td style={{ 
                    padding: '1rem 0.5rem', 
                    textAlign: 'center', 
                    fontWeight: '600',
                    color: '#10b981'
                  }}>
                    {team.season_points}
                  </td>
                  <td style={{ 
                    padding: '1rem 0.5rem', 
                    textAlign: 'center',
                    background: team.season_wins > 0 ? getStatColor(team.season_wins, maxWins, 'good') : 'transparent',
                    borderRadius: '4px'
                  }}>
                    {team.season_wins}
                  </td>
                  <td style={{ 
                    padding: '1rem 0.5rem', 
                    textAlign: 'center',
                    background: team.season_podiums > 0 ? getStatColor(team.season_podiums, maxPodiums, 'good') : 'transparent',
                    borderRadius: '4px'
                  }}>
                    {team.season_podiums}
                  </td>
                  <td style={{ 
                    padding: '1rem 0.5rem', 
                    textAlign: 'center',
                    background: team.season_poles > 0 ? getStatColor(team.season_poles, maxPoles, 'good') : 'transparent',
                    borderRadius: '4px'
                  }}>
                    {team.season_poles}
                  </td>
                  <td style={{ 
                    padding: '1rem 0.5rem', 
                    textAlign: 'center',
                    background: team.season_fastest_laps > 0 ? getStatColor(team.season_fastest_laps, maxFastestLaps, 'good') : 'transparent',
                    borderRadius: '4px'
                  }}>
                    {team.season_fastest_laps}
                  </td>
                  <td style={{ 
                    padding: '1rem 0.5rem', 
                    textAlign: 'center',
                    background: team.season_dnf > 0 ? getStatColor(team.season_dnf, maxDNFs, 'bad') : 'transparent',
                    borderRadius: '4px'
                  }}>
                    {team.season_dnf}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    );
  };


  if (loading) return <div className="f1-loading">{t('common.loading')} {t('statistics.title')}...</div>;
  if (error) return <div className="f1-error">{t('common.error')}: {error}</div>;
  if (!statisticsData) return <div className="f1-error">{t('common.noData')}</div>;

  return (
    <div>
      <h1 className="f1-card-title">{t('statistics.title')}</h1>
      
      {/* Controls */}
      <div className="f1-card">
        <div style={{ display: 'flex', gap: '2rem', alignItems: 'center', flexWrap: 'wrap' }}>
          <div>
            <label style={{ marginRight: '0.5rem' }}>{t('statistics.season')}:</label>
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

          <div style={{ display: 'flex', gap: '0.5rem' }}>
            <button
              onClick={() => setViewType('drivers')}
              style={{
                background: viewType === 'drivers' ? 'linear-gradient(45deg, #ff6b35, #f7931e)' : 'transparent',
                border: '1px solid rgba(255, 255, 255, 0.2)',
                color: '#fff',
                padding: '0.5rem 1rem',
                cursor: 'pointer',
                borderRadius: '4px'
              }}
            >
              🏎️ DRIVERS
            </button>
            <button
              onClick={() => setViewType('teams')}
              style={{
                background: viewType === 'teams' ? 'linear-gradient(45deg, #ff6b35, #f7931e)' : 'transparent',
                border: '1px solid rgba(255, 255, 255, 0.2)',
                color: '#fff',
                padding: '0.5rem 1rem',
                cursor: 'pointer',
                borderRadius: '4px'
              }}
            >
              🏭 CONSTRUCTORS
            </button>
          </div>
        </div>
      </div>

      {/* Statistics Table */}
      {viewType === 'drivers' ? renderDriverStatistics() : renderTeamStatistics()}

      {/* Legend */}
      <div className="f1-card">
        <h3 className="f1-card-title">📖 Legend</h3>
        <div className="f1-grid f1-grid-5">
          <div style={{ fontSize: '0.9rem' }}>
            <span style={{ fontWeight: '600', color: '#ff6b35' }}>PTS:</span> Championship points
          </div>
          <div style={{ fontSize: '0.9rem' }}>
            <span style={{ fontWeight: '600', color: '#ff6b35' }}>POLES:</span> Pole positions
          </div>
          <div style={{ fontSize: '0.9rem' }}>
            <span style={{ fontWeight: '600', color: '#ff6b35' }}>FL:</span> Fastest laps
          </div>
          <div style={{ fontSize: '0.9rem' }}>
            <span style={{ fontWeight: '600', color: '#ff6b35' }}>DNF:</span> Did not finish
          </div>
          <div style={{ fontSize: '0.9rem' }}>
            <span style={{ fontWeight: '600', color: '#ff6b35' }}>1-2s:</span> One-two finishes (teams only)
          </div>
        </div>
        <div style={{ marginTop: '1rem', fontSize: '0.8rem', color: '#666' }}>
          <span style={{ background: 'rgba(16, 185, 129, 0.3)', padding: '0.25rem 0.5rem', borderRadius: '4px', marginRight: '1rem' }}>
            Good performance indicators
          </span>
          <span style={{ background: 'rgba(239, 68, 68, 0.3)', padding: '0.25rem 0.5rem', borderRadius: '4px' }}>
            Reliability issues
          </span>
        </div>
      </div>
    </div>
  );
};

export default StatisticsPage;