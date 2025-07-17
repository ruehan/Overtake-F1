import React, { useState, useEffect } from 'react';
import { useLanguage } from '../contexts/LanguageContext';
import { API_ENDPOINTS } from '../config/api';
import { useApiCache } from '../hooks/useApiCache';
import './PersonalizedDashboard.css';

interface UserPreferences {
  user_id: string;
  favorite_drivers: number[];
  favorite_teams: string[];
  alert_settings: Record<string, boolean>;
  dashboard_layout: Record<string, boolean>;
  theme: string;
  timezone: string;
  language: string;
}

interface DriverStats {
  driver_name: string;
  driver_number: number;
  team_name: string;
  points: number;
  wins: number;
  podiums: number;
  pole_positions: number;
  fastest_laps: number;
  races_entered: number;
  championship_position: number;
  last_result?: string;
  avg_position?: number;
}

interface TeamStats {
  team_name: string;
  points: number;
  wins: number;
  podiums: number;
  pole_positions: number;
  fastest_laps: number;
  drivers_count: number;
  championship_position: number;
  avg_position?: number;
}

interface DashboardData {
  favorite_driver_stats: DriverStats[];
  favorite_team_stats: TeamStats[];
  last_update: string;
}

interface PersonalizedDashboardProps {
  userId?: string;
}

const PersonalizedDashboard: React.FC<PersonalizedDashboardProps> = ({ 
  userId = 'demo_user_001' 
}) => {
  const { t } = useLanguage();
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  // Data
  const [preferences, setPreferences] = useState<UserPreferences | null>(null);
  const [dashboardData, setDashboardData] = useState<DashboardData | null>(null);
  const [driverStandings, setDriverStandings] = useState<any[]>([]);
  const [teamStandings, setTeamStandings] = useState<any[]>([]);
  const [lastUpdate, setLastUpdate] = useState<string>('');

  useEffect(() => {
    fetchPersonalizedData();
    // 5분마다 데이터 자동 갱신
    const interval = setInterval(fetchPersonalizedData, 5 * 60 * 1000);
    return () => clearInterval(interval);
  }, [userId]);

  const fetchPersonalizedData = async () => {
    try {
      setLoading(true);
      setError(null);

      // 병렬로 데이터 가져오기
      const [prefsResponse, dashboardResponse, standingsResponse] = await Promise.all([
        fetch(`${API_ENDPOINTS.users}/preferences/${userId}`),
        fetch(`${API_ENDPOINTS.users}/stats/${userId}/dashboard`),
        fetchStandings()
      ]);

      // 사용자 선호도 처리
      if (prefsResponse.ok) {
        const prefsData = await prefsResponse.json();
        setPreferences(prefsData.preferences);
      } else if (prefsResponse.status === 404) {
        // 사용자 선호도가 없는 경우
        setPreferences(null);
      } else {
        throw new Error('사용자 선호도를 불러올 수 없습니다');
      }

      // 대시보드 데이터 처리
      if (dashboardResponse.ok) {
        const dashData = await dashboardResponse.json();
        setDashboardData(dashData);
        setLastUpdate(new Date(dashData.last_update).toLocaleString('ko-KR'));
      } else {
        console.warn('Dashboard data not available, using fallback');
        setLastUpdate(new Date().toLocaleString('ko-KR'));
      }

    } catch (err) {
      console.error('Error fetching personalized data:', err);
      setError(err instanceof Error ? err.message : '데이터를 불러오는 중 오류가 발생했습니다');
    } finally {
      setLoading(false);
    }
  };

  const fetchStandings = async () => {
    try {
      const [driverResponse, teamResponse] = await Promise.all([
        fetch(`${API_ENDPOINTS.driverStandings}?year=2025`),
        fetch(`${API_ENDPOINTS.teamStandings}?year=2025`)
      ]);

      if (driverResponse.ok) {
        const driverData = await driverResponse.json();
        const drivers = driverData.drivers || driverData || [];
        setDriverStandings(drivers.slice(0, 5));
      }

      if (teamResponse.ok) {
        const teamData = await teamResponse.json();
        const teams = teamData.teams || teamData || [];
        setTeamStandings(teams.slice(0, 5));
      }
    } catch (err) {
      console.warn('Failed to fetch standings:', err);
    }
  };

  const getDriverPositionChange = (driverNumber: number): string => {
    // 실제로는 이전 레이스와 비교하여 순위 변화를 계산
    const changes = ['+2', '-1', '=', '+3', '-2', '+1', '='];
    return changes[driverNumber % changes.length];
  };

  const getTeamPositionChange = (teamName: string): string => {
    // 실제로는 이전 레이스와 비교하여 순위 변화를 계산
    const changes = ['+1', '=', '-1', '+2', '='];
    return changes[teamName.length % changes.length];
  };

  const navigateTo = (path: string) => {
    window.location.href = path;
  };

  if (loading) {
    return (
      <div className="personalized-loading">
        <div className="loading-spinner"></div>
        <p>🏁 개인화된 대시보드를 불러오는 중...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="personalized-error">
        <h3>⚠️ 개인화 대시보드 오류</h3>
        <p>{error}</p>
        <button onClick={fetchPersonalizedData}>다시 시도</button>
      </div>
    );
  }

  if (!preferences) {
    return (
      <div className="no-preferences">
        <h3>🎉 개인화된 대시보드에 오신 것을 환영합니다!</h3>
        <p>즐겨찾기를 설정하여 맞춤형 F1 경험을 시작하세요.</p>
        <p style={{ fontSize: '0.9rem', opacity: 0.8, marginTop: '1rem' }}>
          좋아하는 드라이버와 팀을 선택하면 실시간 통계와 성과를 확인할 수 있습니다.
        </p>
        <button onClick={() => navigateTo('/favorites')}>
          ⚙️ 즐겨찾기 설정하기
        </button>
      </div>
    );
  }

  const favoriteDriverStats = dashboardData?.favorite_driver_stats || [];
  const favoriteTeamStats = dashboardData?.favorite_team_stats || [];

  return (
    <div className="personalized-dashboard">
      <div className="dashboard-header">
        <div className="header-info">
          <h1>🌟 나의 F1 대시보드</h1>
          <p>즐겨찾기 드라이버와 팀의 최신 성과를 확인하세요</p>
        </div>
        <div className="last-update">
          <small>마지막 업데이트: {lastUpdate}</small>
          <br />
          <button 
            onClick={fetchPersonalizedData}
            style={{ 
              background: 'none', 
              border: '1px solid rgba(212, 175, 55, 0.5)', 
              color: '#D4AF37',
              padding: '0.25rem 0.5rem',
              borderRadius: '4px',
              cursor: 'pointer',
              fontSize: '0.8rem',
              marginTop: '0.5rem'
            }}
          >
            🔄 새로고침
          </button>
        </div>
      </div>

      <div className="dashboard-grid">
        {/* 즐겨찾기 드라이버 통계 */}
        {favoriteDriverStats.length > 0 && (
          <div className="dashboard-card favorite-drivers">
            <h2>🏎️ 내 드라이버들</h2>
            <div className="drivers-grid">
              {favoriteDriverStats.map((driver) => (
                <div key={driver.driver_number} className="driver-card">
                  <div className="driver-header">
                    <div className="driver-number">#{driver.driver_number}</div>
                    <div className="driver-info">
                      <h3>{driver.driver_name}</h3>
                      <p>{driver.team_name}</p>
                    </div>
                    <div className="position-badge">
                      P{driver.championship_position}
                      <span className={`position-change ${getDriverPositionChange(driver.driver_number).startsWith('+') ? 'up' : getDriverPositionChange(driver.driver_number).startsWith('-') ? 'down' : 'same'}`}>
                        {getDriverPositionChange(driver.driver_number)}
                      </span>
                    </div>
                  </div>
                  
                  <div className="driver-stats">
                    <div className="stat-item">
                      <span className="stat-value">{driver.points}</span>
                      <span className="stat-label">포인트</span>
                    </div>
                    <div className="stat-item">
                      <span className="stat-value">{driver.wins}</span>
                      <span className="stat-label">승수</span>
                    </div>
                    <div className="stat-item">
                      <span className="stat-value">{driver.podiums}</span>
                      <span className="stat-label">포디움</span>
                    </div>
                  </div>
                  
                  {driver.last_result && (
                    <div style={{ marginTop: '0.75rem', fontSize: '0.8rem', opacity: 0.8 }}>
                      마지막 레이스: {driver.last_result}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* 즐겨찾기 팀 통계 */}
        {favoriteTeamStats.length > 0 && (
          <div className="dashboard-card favorite-teams">
            <h2>🏁 내 팀들</h2>
            <div className="teams-grid">
              {favoriteTeamStats.map((team) => (
                <div key={team.team_name} className="team-card">
                  <div className="team-header">
                    <div className="team-info">
                      <h3>{team.team_name}</h3>
                      <p>{team.drivers_count} 드라이버</p>
                    </div>
                    <div className="position-badge">
                      P{team.championship_position}
                      <span className={`position-change ${getTeamPositionChange(team.team_name).startsWith('+') ? 'up' : getTeamPositionChange(team.team_name).startsWith('-') ? 'down' : 'same'}`}>
                        {getTeamPositionChange(team.team_name)}
                      </span>
                    </div>
                  </div>
                  
                  <div className="team-stats">
                    <div className="stat-item">
                      <span className="stat-value">{team.points}</span>
                      <span className="stat-label">포인트</span>
                    </div>
                    <div className="stat-item">
                      <span className="stat-value">{team.wins}</span>
                      <span className="stat-label">승수</span>
                    </div>
                    <div className="stat-item">
                      <span className="stat-value">{team.podiums}</span>
                      <span className="stat-label">포디움</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* 전체 드라이버 스탠딩 (상위 5위) */}
        <div className="dashboard-card standings-preview">
          <h2>🏆 드라이버 챔피언십 (상위 5위)</h2>
          <div className="standings-list">
            {driverStandings.length > 0 ? driverStandings.map((driver, index) => {
              const isFavorite = preferences.favorite_drivers?.includes(driver.driver_number);
              return (
                <div 
                  key={driver.driver_number || index} 
                  className={`standings-item ${isFavorite ? 'favorite' : ''}`}
                >
                  <div className="position">{index + 1}</div>
                  <div className="driver-info">
                    <span className="name">{driver.driver_name || driver.name}</span>
                    <span className="team">{driver.team_name}</span>
                  </div>
                  <div className="points">{driver.season_points || driver.points}pts</div>
                  {isFavorite && (
                    <div className="favorite-indicator">⭐</div>
                  )}
                </div>
              );
            }) : (
              <p style={{ textAlign: 'center', opacity: 0.6 }}>스탠딩 데이터를 불러오는 중...</p>
            )}
          </div>
        </div>

        {/* 전체 팀 스탠딩 (상위 5위) */}
        <div className="dashboard-card standings-preview">
          <h2>🏁 컨스트럭터 챔피언십 (상위 5위)</h2>
          <div className="standings-list">
            {teamStandings.length > 0 ? teamStandings.map((team, index) => {
              const isFavorite = preferences.favorite_teams?.includes(team.team_name);
              return (
                <div 
                  key={team.team_name || index} 
                  className={`standings-item ${isFavorite ? 'favorite' : ''}`}
                >
                  <div className="position">{index + 1}</div>
                  <div className="team-info">
                    <span className="name">{team.team_name}</span>
                  </div>
                  <div className="points">{team.season_points || team.points}pts</div>
                  {isFavorite && (
                    <div className="favorite-indicator">⭐</div>
                  )}
                </div>
              );
            }) : (
              <p style={{ textAlign: 'center', opacity: 0.6 }}>스탠딩 데이터를 불러오는 중...</p>
            )}
          </div>
        </div>

        {/* 퀵 액션 */}
        <div className="dashboard-card quick-actions">
          <h2>⚡ 빠른 메뉴</h2>
          <div className="actions-grid">
            <button 
              className="action-button"
              onClick={() => navigateTo('/standings')}
            >
              📊 전체 스탠딩 보기
            </button>
            <button 
              className="action-button"
              onClick={() => navigateTo('/calendar')}
            >
              📅 레이스 캘린더
            </button>
            <button 
              className="action-button"
              onClick={() => navigateTo('/statistics')}
            >
              📈 시즌 통계
            </button>
            <button 
              className="action-button"
              onClick={() => navigateTo('/favorites')}
            >
              ⚙️ 즐겨찾기 설정
            </button>
          </div>
        </div>

        {/* 개인화 힌트 */}
        {(favoriteDriverStats.length === 0 && favoriteTeamStats.length === 0) && (
          <div className="dashboard-card personalization-hint">
            <h2>💡 맞춤 설정 안내</h2>
            <p>아직 즐겨찾기 데이터가 없거나 로딩 중입니다!</p>
            <ul>
              <li>🏎️ 응원하는 드라이버를 즐겨찾기에 추가하세요</li>
              <li>🏁 좋아하는 팀을 선택하세요</li>
              <li>🔔 원하는 알림을 설정하세요</li>
              <li>📊 대시보드 위젯을 커스터마이징하세요</li>
            </ul>
            <button 
              className="setup-button"
              onClick={() => navigateTo('/favorites')}
            >
              지금 설정하기
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

export default PersonalizedDashboard; 