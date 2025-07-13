import React, { useState, useEffect } from 'react';
import { useLanguage } from '../contexts/LanguageContext';

interface DriverStat {
  position: number;
  driver_name: string;
  driver_code: string;
  team: string;
  points: number;
  wins: number;
  podiums: number;
  dnfs: number;
  fastest_laps: number;
}

interface TeamStat {
  position: number;
  team_name: string;
  nationality: string;
  points: number;
  wins: number;
  podiums: number;
  dnfs: number;
  fastest_laps: number;
  one_twos: number;
}

interface StatisticsData {
  drivers?: DriverStat[];
  teams?: TeamStat[];
  total_drivers?: number;
  total_teams?: number;
  year: number;
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
      const endpoint = viewType === 'drivers' ? 'driver-statistics' : 'team-statistics';
      const response = await fetch(`http://localhost:8000/api/v1/${endpoint}?year=${selectedYear}`);
      if (!response.ok) throw new Error('Failed to fetch statistics data');
      const data = await response.json();
      setStatisticsData(data.data);
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
    if (!statisticsData?.drivers) return null;

    const drivers = statisticsData.drivers;
    const maxWins = Math.max(...drivers.map(d => d.wins));
    const maxPodiums = Math.max(...drivers.map(d => d.podiums));
    const maxDNFs = Math.max(...drivers.map(d => d.dnfs));
    const maxFastestLaps = Math.max(...drivers.map(d => d.fastest_laps));

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
                <th style={{ textAlign: 'center', padding: '1rem 0.5rem', color: '#ff6b35' }}>FL</th>
                <th style={{ textAlign: 'center', padding: '1rem 0.5rem', color: '#ff6b35' }}>DNF</th>
              </tr>
            </thead>
            <tbody>
              {drivers.map((driver, index) => (
                <tr 
                  key={driver.driver_name}
                  style={{ 
                    borderBottom: '1px solid rgba(255, 255, 255, 0.1)',
                    backgroundColor: index % 2 === 0 ? 'rgba(255, 255, 255, 0.02)' : 'transparent'
                  }}
                >
                  <td style={{ padding: '1rem 0.5rem', fontWeight: '600' }}>
                    <span style={{ 
                      color: driver.position <= 3 ? '#ffd700' : '#fff',
                      fontSize: driver.position <= 3 ? '1.1rem' : '1rem'
                    }}>
                      {driver.position}
                    </span>
                  </td>
                  <td style={{ padding: '1rem 0.5rem' }}>
                    <div>
                      <div style={{ fontWeight: '600', marginBottom: '0.25rem' }}>
                        {driver.driver_name}
                      </div>
                      <div style={{ fontSize: '0.8rem', color: '#ccc' }}>
                        {driver.driver_code}
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
                    {driver.points}
                  </td>
                  <td style={{ 
                    padding: '1rem 0.5rem', 
                    textAlign: 'center',
                    background: driver.wins > 0 ? getStatColor(driver.wins, maxWins, 'good') : 'transparent',
                    borderRadius: '4px'
                  }}>
                    {driver.wins}
                  </td>
                  <td style={{ 
                    padding: '1rem 0.5rem', 
                    textAlign: 'center',
                    background: driver.podiums > 0 ? getStatColor(driver.podiums, maxPodiums, 'good') : 'transparent',
                    borderRadius: '4px'
                  }}>
                    {driver.podiums}
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
                    background: driver.dnfs > 0 ? getStatColor(driver.dnfs, maxDNFs, 'bad') : 'transparent',
                    borderRadius: '4px'
                  }}>
                    {driver.dnfs}
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
    if (!statisticsData?.teams) return null;

    const teams = statisticsData.teams;
    const maxWins = Math.max(...teams.map(t => t.wins));
    const maxPodiums = Math.max(...teams.map(t => t.podiums));
    const maxDNFs = Math.max(...teams.map(t => t.dnfs));
    const maxFastestLaps = Math.max(...teams.map(t => t.fastest_laps));
    const maxOneTwos = Math.max(...teams.map(t => t.one_twos));

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
                <th style={{ textAlign: 'center', padding: '1rem 0.5rem', color: '#ff6b35' }}>1-2s</th>
                <th style={{ textAlign: 'center', padding: '1rem 0.5rem', color: '#ff6b35' }}>FL</th>
                <th style={{ textAlign: 'center', padding: '1rem 0.5rem', color: '#ff6b35' }}>DNF</th>
              </tr>
            </thead>
            <tbody>
              {teams.map((team, index) => (
                <tr 
                  key={team.team_name}
                  style={{ 
                    borderBottom: '1px solid rgba(255, 255, 255, 0.1)',
                    backgroundColor: index % 2 === 0 ? 'rgba(255, 255, 255, 0.02)' : 'transparent'
                  }}
                >
                  <td style={{ padding: '1rem 0.5rem', fontWeight: '600' }}>
                    <span style={{ 
                      color: team.position <= 3 ? '#ffd700' : '#fff',
                      fontSize: team.position <= 3 ? '1.1rem' : '1rem'
                    }}>
                      {team.position}
                    </span>
                  </td>
                  <td style={{ padding: '1rem 0.5rem' }}>
                    <div>
                      <div style={{ fontWeight: '600', marginBottom: '0.25rem' }}>
                        {team.team_name}
                      </div>
                      <div style={{ fontSize: '0.8rem', color: '#ccc' }}>
                        {team.nationality}
                      </div>
                    </div>
                  </td>
                  <td style={{ 
                    padding: '1rem 0.5rem', 
                    textAlign: 'center', 
                    fontWeight: '600',
                    color: '#10b981'
                  }}>
                    {team.points}
                  </td>
                  <td style={{ 
                    padding: '1rem 0.5rem', 
                    textAlign: 'center',
                    background: team.wins > 0 ? getStatColor(team.wins, maxWins, 'good') : 'transparent',
                    borderRadius: '4px'
                  }}>
                    {team.wins}
                  </td>
                  <td style={{ 
                    padding: '1rem 0.5rem', 
                    textAlign: 'center',
                    background: team.podiums > 0 ? getStatColor(team.podiums, maxPodiums, 'good') : 'transparent',
                    borderRadius: '4px'
                  }}>
                    {team.podiums}
                  </td>
                  <td style={{ 
                    padding: '1rem 0.5rem', 
                    textAlign: 'center',
                    background: team.one_twos > 0 ? getStatColor(team.one_twos, maxOneTwos, 'good') : 'transparent',
                    borderRadius: '4px'
                  }}>
                    {team.one_twos}
                  </td>
                  <td style={{ 
                    padding: '1rem 0.5rem', 
                    textAlign: 'center',
                    background: team.fastest_laps > 0 ? getStatColor(team.fastest_laps, maxFastestLaps, 'good') : 'transparent',
                    borderRadius: '4px'
                  }}>
                    {team.fastest_laps}
                  </td>
                  <td style={{ 
                    padding: '1rem 0.5rem', 
                    textAlign: 'center',
                    background: team.dnfs > 0 ? getStatColor(team.dnfs, maxDNFs, 'bad') : 'transparent',
                    borderRadius: '4px'
                  }}>
                    {team.dnfs}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    );
  };

  const renderSummaryCards = () => {
    if (!statisticsData) return null;

    let totalWins = 0;
    let totalPodiums = 0;
    let totalDNFs = 0;
    let totalFastestLaps = 0;

    if (viewType === 'drivers' && statisticsData.drivers) {
      totalWins = statisticsData.drivers.reduce((sum: number, item: DriverStat) => sum + item.wins, 0);
      totalPodiums = statisticsData.drivers.reduce((sum: number, item: DriverStat) => sum + item.podiums, 0);
      totalDNFs = statisticsData.drivers.reduce((sum: number, item: DriverStat) => sum + item.dnfs, 0);
      totalFastestLaps = statisticsData.drivers.reduce((sum: number, item: DriverStat) => sum + item.fastest_laps, 0);
    } else if (viewType === 'teams' && statisticsData.teams) {
      totalWins = statisticsData.teams.reduce((sum: number, item: TeamStat) => sum + item.wins, 0);
      totalPodiums = statisticsData.teams.reduce((sum: number, item: TeamStat) => sum + item.podiums, 0);
      totalDNFs = statisticsData.teams.reduce((sum: number, item: TeamStat) => sum + item.dnfs, 0);
      totalFastestLaps = statisticsData.teams.reduce((sum: number, item: TeamStat) => sum + item.fastest_laps, 0);
    }

    const summaryStats = [
      { label: t('statistics.totalWins'), value: totalWins, icon: '🏆', color: '#ffd700' },
      { label: t('statistics.totalPodiums'), value: totalPodiums, icon: '🥇', color: '#10b981' },
      { label: t('statistics.fastestLaps'), value: totalFastestLaps, icon: '⚡', color: '#3b82f6' },
      { label: t('statistics.dnfs'), value: totalDNFs, icon: '❌', color: '#ef4444' }
    ];

    if (viewType === 'teams' && statisticsData.teams) {
      const totalOneTwos = statisticsData.teams.reduce((sum: number, team: TeamStat) => sum + team.one_twos, 0);
      summaryStats.splice(2, 0, { label: '1-2 Finishes', value: totalOneTwos, icon: '🥇🥈', color: '#f59e0b' });
    }

    return (
      <div className="f1-grid f1-grid-5">
        {summaryStats.map((stat, index) => (
          <div key={index} className="f1-card" style={{ marginBottom: 0, textAlign: 'center' }}>
            <div style={{ fontSize: '2rem', marginBottom: '0.5rem' }}>{stat.icon}</div>
            <div style={{ fontSize: '1.5rem', fontWeight: '600', color: stat.color, marginBottom: '0.25rem' }}>
              {stat.value}
            </div>
            <div style={{ fontSize: '0.9rem', color: '#ccc' }}>{stat.label}</div>
          </div>
        ))}
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

      {/* Summary Cards */}
      {renderSummaryCards()}

      {/* Statistics Table */}
      {viewType === 'drivers' ? renderDriverStatistics() : renderTeamStatistics()}

      {/* Legend */}
      <div className="f1-card">
        <h3 className="f1-card-title">📖 Legend</h3>
        <div className="f1-grid f1-grid-4">
          <div style={{ fontSize: '0.9rem' }}>
            <span style={{ fontWeight: '600', color: '#ff6b35' }}>PTS:</span> Championship points
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