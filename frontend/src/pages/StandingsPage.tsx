import React, { useState, useEffect } from 'react';
import { useLanguage } from '../contexts/LanguageContext';
import { API_ENDPOINTS } from '../config/api';
import { usePageMeta } from '../hooks/usePageMeta';
import { useApiCache } from '../hooks/useApiCache';

interface DriverStanding {
  position: number;
  driver_number: number;
  name: string;
  code: string;
  team: string;
  points: number;
  wins: number;
  headshot_url?: string;
}

interface ConstructorStanding {
  position: number;
  team: string;
  nationality: string;
  points: number;
  wins: number;
  logo_url?: string;
}

interface StandingsPageProps {
  onDriverClick?: (driverNumber: number) => void;
}

const StandingsPage: React.FC<StandingsPageProps> = ({ onDriverClick }) => {
  const { t } = useLanguage();
  usePageMeta('standings');
  const [activeTab, setActiveTab] = useState<'drivers' | 'constructors'>('drivers');
  const [selectedYear, setSelectedYear] = useState(2025);

  // 드라이버 스탠딩 캐시
  const {
    data: driverStandings,
    loading: driversLoading,
    error: driversError,
    refetch: refetchDrivers
  } = useApiCache<DriverStanding[]>(
    `drivers-standings-${selectedYear}`,
    async () => {
      console.log('🔄 Fetching driver standings from:', API_ENDPOINTS.allDriversSeasonStats(selectedYear));
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 30000);
      
      const response = await fetch(API_ENDPOINTS.allDriversSeasonStats(selectedYear), {
        signal: controller.signal,
        headers: { 'Content-Type': 'application/json' }
      });
      clearTimeout(timeoutId);
      
      if (!response.ok) {
        throw new Error(`Failed to fetch driver standings: ${response.status} ${response.statusText}`);
      }
      
      const data = await response.json();
      console.log('✅ Driver standings data:', data);
      
      return (data.data || []).map((driver: any) => ({
        position: parseInt(driver.championship_position) || 0,
        driver_number: driver.driver_number,
        name: driver.name,
        code: driver.slug?.substring(0, 3).toUpperCase() || driver.name.substring(0, 3).toUpperCase(),
        team: driver.team,
        points: driver.season_points || 0,
        wins: driver.season_wins || 0,
        headshot_url: `/images/drivers/${driver.name}.webp`
      }));
    },
    { staleTime: 60 * 60 * 1000 } // 1시간 동안 신선한 데이터로 간주
  );

  // 컨스트럭터 스탠딩 캐시
  const {
    data: constructorStandings,
    loading: constructorsLoading,
    error: constructorsError,
    refetch: refetchConstructors
  } = useApiCache<ConstructorStanding[]>(
    `constructors-standings-${selectedYear}`,
    async () => {
      console.log('🔄 Fetching constructor standings from:', API_ENDPOINTS.constructorStandings(selectedYear));
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 30000);
      
      const response = await fetch(API_ENDPOINTS.constructorStandings(selectedYear), {
        signal: controller.signal,
        headers: { 'Content-Type': 'application/json' }
      });
      clearTimeout(timeoutId);
      
      if (!response.ok) {
        throw new Error(`Failed to fetch constructor standings: ${response.status} ${response.statusText}`);
      }
      
      const data = await response.json();
      console.log('✅ Constructor standings data:', data);
      return data.standings || [];
    },
    { staleTime: 60 * 60 * 1000 }
  );

  // 현재 탭에 따른 로딩/에러 상태
  const loading = activeTab === 'drivers' ? driversLoading : constructorsLoading;
  const error = activeTab === 'drivers' ? driversError : constructorsError;

  // 새로고침 함수
  const handleRefresh = () => {
    if (activeTab === 'drivers') {
      refetchDrivers();
    } else {
      refetchConstructors();
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
        <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
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
          
          {/* 새로고침 버튼 */}
          <button
            onClick={handleRefresh}
            disabled={loading}
            style={{
              background: 'rgba(212, 175, 55, 0.2)',
              border: '1px solid rgba(212, 175, 55, 0.5)',
              color: '#D4AF37',
              padding: '0.5rem',
              borderRadius: '4px',
              cursor: loading ? 'not-allowed' : 'pointer',
              opacity: loading ? 0.6 : 1,
              display: 'flex',
              alignItems: 'center',
              gap: '0.25rem'
            }}
            title="데이터 새로고침"
          >
            {loading ? '⏳' : '🔄'}
          </button>
        </div>
      </div>

      {/* Driver Standings */}
      {activeTab === 'drivers' && (
        <div className="f1-card">
          <h3 className="f1-card-title">{t('standings.drivers')}</h3>
          
          {!driverStandings || driverStandings.length === 0 ? (
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
                {(driverStandings || []).map((driver) => (
                  <tr 
                    key={driver.driver_number}
                    style={{ 
                      cursor: onDriverClick ? 'pointer' : 'default',
                      transition: 'background-color 0.2s ease'
                    }}
                    onClick={() => onDriverClick && onDriverClick(driver.driver_number)}
                    onMouseEnter={(e) => {
                      if (onDriverClick) {
                        e.currentTarget.style.backgroundColor = 'rgba(255, 107, 53, 0.1)';
                      }
                    }}
                    onMouseLeave={(e) => {
                      if (onDriverClick) {
                        e.currentTarget.style.backgroundColor = 'transparent';
                      }
                    }}>
                    <td>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                        <span className={`position ${getPositionClass(driver.position)}`}>
                          {getPositionIcon(driver.position)}
                        </span>
                      </div>
                    </td>
                    <td>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                        {driver.headshot_url && (
                          <img 
                            src={driver.headshot_url.startsWith('/') ? driver.headshot_url : `/${driver.headshot_url}`} 
                            alt={driver.name}
                            style={{
                              width: '50px',
                              height: '50px',
                              borderRadius: '50%',
                              objectFit: 'cover',
                              border: '2px solid rgba(255, 255, 255, 0.1)',
                              background: '#333'
                            }}
                            onError={(e) => {
                              const target = e.target as HTMLImageElement;
                              target.src = '/images/drivers/default.svg';
                            }}
                          />
                        )}
                        <div>
                          <div style={{ fontWeight: '600', marginBottom: '0.25rem' }}>{driver.name}</div>
                          <div style={{ fontSize: '0.8rem', color: '#ccc' }}>
                            #{driver.driver_number} • {driver.code}
                          </div>
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
          
          {!constructorStandings || constructorStandings.length === 0 ? (
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
                {(constructorStandings || []).map((constructor) => (
                  <tr key={constructor.team}>
                    <td>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                        <span className={`position ${getPositionClass(constructor.position)}`}>
                          {getPositionIcon(constructor.position)}
                        </span>
                      </div>
                    </td>
                    <td>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                        {constructor.logo_url && (
                          <img 
                            src={constructor.logo_url} 
                            alt={constructor.team}
                            style={{
                              width: '60px',
                              height: '40px',
                              objectFit: 'contain'
                            }}
                            onError={(e) => {
                              (e.target as HTMLImageElement).style.display = 'none';
                            }}
                          />
                        )}
                        <div style={{ fontWeight: '600' }}>{constructor.team}</div>
                      </div>
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
      {((driverStandings && driverStandings.length > 0) || (constructorStandings && constructorStandings.length > 0)) && (
        <div className="f1-card">
          <h3 className="f1-card-title">📊 {t('standings.battle')}</h3>
          
          <div className="f1-grid f1-grid-2">
            {driverStandings && driverStandings.length > 1 && (
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

            {constructorStandings && constructorStandings.length > 1 && (
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