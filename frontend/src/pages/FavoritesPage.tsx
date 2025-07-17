import React, { useState, useEffect } from 'react';
import { useLanguage } from '../contexts/LanguageContext';
import { API_ENDPOINTS } from '../config/api';
import { Driver } from '../types/f1Types';
import DriverSelector from '../components/Analytics/DriverSelector';
import './FavoritesPage.css';

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

interface Team {
  name: string;
  full_name: string;
  colour: string;
  drivers?: string[];
}

const FavoritesPage: React.FC = () => {
  const { t } = useLanguage();
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  
  // Data
  const [drivers, setDrivers] = useState<Driver[]>([]);
  const [teams, setTeams] = useState<Team[]>([]);
  const [preferences, setPreferences] = useState<UserPreferences | null>(null);
  
  // Form state
  const [selectedDrivers, setSelectedDrivers] = useState<number[]>([]);
  const [selectedTeams, setSelectedTeams] = useState<string[]>([]);
  const [alertSettings, setAlertSettings] = useState<Record<string, boolean>>({
    overtakes: true,
    pit_stops: true,
    lead_changes: true,
    fastest_laps: false,
    weather_changes: false,
    incidents: true
  });
  
  const [dashboardLayout, setDashboardLayout] = useState<Record<string, boolean>>({
    live_map: true,
    driver_standings: true,
    weather: true,
    recent_radio: false,
    lap_times: true,
    pit_stops: true
  });

  // Get current user ID (임시로 하드코딩, 실제로는 인증 시스템에서)
  const currentUserId = 'demo_user_001';

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      setLoading(true);
      setError(null);

      // 드라이버 목록 가져오기 (최신 세션 기준)
      try {
        const driversResponse = await fetch(`${API_ENDPOINTS.drivers}?session_key=latest`);
        if (driversResponse.ok) {
          const driversData = await driversResponse.json();
          setDrivers(driversData);
        } else {
          // Fallback: 스탠딩에서 드라이버 정보 가져오기
          const standingsResponse = await fetch(`${API_ENDPOINTS.driverStandings}?year=2025`);
          if (standingsResponse.ok) {
            const standingsData = await standingsResponse.json();
            const driversList = standingsData.drivers || [];
            setDrivers(driversList.map((driver: any, index: number) => ({
              driver_number: index + 1,
              name: driver.driver_name || driver.name,
              abbreviation: driver.driver_name?.split(' ').map((n: string) => n[0]).join('').toUpperCase() || 'UNK',
              team_name: driver.team_name || 'Unknown Team',
              team_colour: '#cccccc'
            })));
          }
        }
      } catch (err) {
        console.warn('Failed to fetch drivers, using fallback');
      }

      // 팀 목록 가져오기
      try {
        const teamsResponse = await fetch(`${API_ENDPOINTS.teams}?year=2025`);
        if (teamsResponse.ok) {
          const teamsData = await teamsResponse.json();
          setTeams(teamsData.teams || []);
        } else {
          // Fallback: 하드코딩된 팀 목록
          setTeams([
            { name: 'Red Bull Racing', full_name: 'Oracle Red Bull Racing', colour: '#1E41FF' },
            { name: 'Mercedes', full_name: 'Mercedes-AMG PETRONAS F1 Team', colour: '#00D2BE' },
            { name: 'Ferrari', full_name: 'Scuderia Ferrari', colour: '#DC143C' },
            { name: 'McLaren', full_name: 'McLaren F1 Team', colour: '#FF8700' },
            { name: 'Aston Martin', full_name: 'Aston Martin Aramco F1 Team', colour: '#006F62' },
            { name: 'Alpine', full_name: 'BWT Alpine F1 Team', colour: '#0082FA' },
            { name: 'Williams', full_name: 'Williams Racing', colour: '#005AFF' },
            { name: 'RB', full_name: 'Visa Cash App RB F1 Team', colour: '#6692FF' },
            { name: 'Kick Sauber', full_name: 'Stake F1 Team Kick Sauber', colour: '#52E252' },
            { name: 'Haas', full_name: 'MoneyGram Haas F1 Team', colour: '#FFFFFF' }
          ]);
        }
      } catch (err) {
        console.warn('Failed to fetch teams, using fallback');
      }

      // 사용자 선호도 가져오기
      try {
        const prefsResponse = await fetch(`${API_ENDPOINTS.users}/preferences/${currentUserId}`);
        if (prefsResponse.ok) {
          const prefsData = await prefsResponse.json();
          const userPrefs = prefsData.preferences;
          setPreferences(userPrefs);
          
          // 폼 상태 업데이트
          setSelectedDrivers(userPrefs.favorite_drivers || []);
          setSelectedTeams(userPrefs.favorite_teams || []);
          setAlertSettings(userPrefs.alert_settings || alertSettings);
          setDashboardLayout(userPrefs.dashboard_layout || dashboardLayout);
        }
      } catch (err) {
        console.warn('Failed to fetch user preferences, using defaults');
      }

    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load data');
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    try {
      setSaving(true);
      setError(null);
      setSuccess(null);

      const updateData = {
        favorite_drivers: selectedDrivers,
        favorite_teams: selectedTeams,
        alert_settings: alertSettings,
        dashboard_layout: dashboardLayout
      };

      const response = await fetch(`${API_ENDPOINTS.users}/preferences/${currentUserId}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(updateData)
      });

      if (response.ok) {
        const result = await response.json();
        setPreferences(result.preferences);
        setSuccess('즐겨찾기 설정이 저장되었습니다!');
        
        // 성공 메시지 3초 후 제거
        setTimeout(() => setSuccess(null), 3000);
      } else {
        throw new Error('Failed to save preferences');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save preferences');
    } finally {
      setSaving(false);
    }
  };

  const handleTeamToggle = (teamName: string) => {
    setSelectedTeams(prev => 
      prev.includes(teamName) 
        ? prev.filter(t => t !== teamName)
        : [...prev, teamName]
    );
  };

  const handleAlertToggle = (alertType: string) => {
    setAlertSettings(prev => ({
      ...prev,
      [alertType]: !prev[alertType]
    }));
  };

  const handleWidgetToggle = (widget: string) => {
    setDashboardLayout(prev => ({
      ...prev,
      [widget]: !prev[widget]
    }));
  };

  if (loading) {
    return (
      <div className="favorites-loading">
        <div className="loading-spinner"></div>
        <p>즐겨찾기 설정을 불러오는 중...</p>
      </div>
    );
  }

  return (
    <div className="favorites-page">
      <div className="page-header">
        <h1>⭐ 즐겨찾기 및 개인 설정</h1>
        <p>관심 있는 드라이버와 팀을 선택하고 개인화된 대시보드를 설정하세요</p>
      </div>

      {error && (
        <div className="alert alert-error">
          <strong>오류:</strong> {error}
        </div>
      )}

      {success && (
        <div className="alert alert-success">
          <strong>완료:</strong> {success}
        </div>
      )}

      <div className="favorites-content">
        {/* 즐겨찾기 드라이버 */}
        <div className="favorites-section">
          <div className="section-header">
            <h2>🏎️ 즐겨찾기 드라이버</h2>
            <p>관심 있는 드라이버들을 선택하세요 (최대 10명)</p>
          </div>
          
          <div className="driver-selection">
            <DriverSelector
              drivers={drivers}
              selectedDrivers={selectedDrivers}
              onSelectionChange={setSelectedDrivers}
              multiSelect={true}
            />
            
            {selectedDrivers.length > 0 && (
              <div className="selection-summary">
                <h4>선택된 드라이버 ({selectedDrivers.length}/10)</h4>
                <div className="selected-drivers">
                  {selectedDrivers.map(driverNum => {
                    const driver = drivers.find(d => d.driver_number === driverNum);
                    return driver ? (
                      <div key={driverNum} className="selected-driver">
                        <span 
                          className="driver-number"
                          style={{ backgroundColor: driver.team_colour }}
                        >
                          #{driver.driver_number}
                        </span>
                        <span className="driver-name">{driver.name}</span>
                        <span className="driver-team">{driver.team_name}</span>
                      </div>
                    ) : null;
                  })}
                </div>
              </div>
            )}
          </div>
        </div>

        {/* 즐겨찾기 팀 */}
        <div className="favorites-section">
          <div className="section-header">
            <h2>🏁 즐겨찾기 팀</h2>
            <p>관심 있는 팀들을 선택하세요 (최대 5개)</p>
          </div>
          
          <div className="team-selection">
            <div className="teams-grid">
              {teams.map(team => (
                <div
                  key={team.name}
                  className={`team-card ${selectedTeams.includes(team.name) ? 'selected' : ''}`}
                  onClick={() => handleTeamToggle(team.name)}
                >
                  <div 
                    className="team-color-bar"
                    style={{ backgroundColor: team.colour }}
                  ></div>
                  <div className="team-info">
                    <h4>{team.name}</h4>
                    <p>{team.full_name}</p>
                  </div>
                  <div className="team-checkbox">
                    <input
                      type="checkbox"
                      checked={selectedTeams.includes(team.name)}
                      onChange={() => {}} // Handled by parent click
                    />
                  </div>
                </div>
              ))}
            </div>
            
            {selectedTeams.length > 0 && (
              <div className="selection-summary">
                <h4>선택된 팀 ({selectedTeams.length}/5)</h4>
                <div className="selected-teams">
                  {selectedTeams.map(teamName => {
                    const team = teams.find(t => t.name === teamName);
                    return team ? (
                      <div key={teamName} className="selected-team">
                        <span 
                          className="team-indicator"
                          style={{ backgroundColor: team.colour }}
                        ></span>
                        <span className="team-name">{team.name}</span>
                      </div>
                    ) : null;
                  })}
                </div>
              </div>
            )}
          </div>
        </div>

        {/* 알림 설정 */}
        <div className="favorites-section">
          <div className="section-header">
            <h2>🔔 알림 설정</h2>
            <p>받고 싶은 알림 유형을 선택하세요</p>
          </div>
          
          <div className="alerts-grid">
            {Object.entries(alertSettings).map(([alertType, enabled]) => (
              <div key={alertType} className="alert-option">
                <label className="switch">
                  <input
                    type="checkbox"
                    checked={enabled}
                    onChange={() => handleAlertToggle(alertType)}
                  />
                  <span className="slider"></span>
                </label>
                <div className="alert-info">
                  <h4>{getAlertLabel(alertType)}</h4>
                  <p>{getAlertDescription(alertType)}</p>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* 대시보드 레이아웃 */}
        <div className="favorites-section">
          <div className="section-header">
            <h2>📊 대시보드 위젯</h2>
            <p>대시보드에서 보고 싶은 위젯들을 선택하세요</p>
          </div>
          
          <div className="widgets-grid">
            {Object.entries(dashboardLayout).map(([widget, enabled]) => (
              <div key={widget} className="widget-option">
                <label className="switch">
                  <input
                    type="checkbox"
                    checked={enabled}
                    onChange={() => handleWidgetToggle(widget)}
                  />
                  <span className="slider"></span>
                </label>
                <div className="widget-info">
                  <h4>{getWidgetLabel(widget)}</h4>
                  <p>{getWidgetDescription(widget)}</p>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* 저장 버튼 */}
        <div className="save-section">
          <button
            className="save-button"
            onClick={handleSave}
            disabled={saving}
          >
            {saving ? (
              <>
                <span className="loading-spinner small"></span>
                저장 중...
              </>
            ) : (
              <>
                💾 설정 저장
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
};

// Helper functions
const getAlertLabel = (alertType: string): string => {
  const labels: Record<string, string> = {
    overtakes: '추월',
    pit_stops: '피트스톱',
    lead_changes: '선두 변경',
    fastest_laps: '최고속랩',
    weather_changes: '날씨 변화',
    incidents: '사고/인시던트'
  };
  return labels[alertType] || alertType;
};

const getAlertDescription = (alertType: string): string => {
  const descriptions: Record<string, string> = {
    overtakes: '드라이버 간 추월 상황 알림',
    pit_stops: '피트스톱 진입 및 완료 알림',
    lead_changes: '레이스 선두 변경 알림',
    fastest_laps: '최고속랩 기록 갱신 알림',
    weather_changes: '날씨 및 트랙 상태 변화 알림',
    incidents: '사고, 세이프티카, 옐로우 플래그 등 알림'
  };
  return descriptions[alertType] || '';
};

const getWidgetLabel = (widget: string): string => {
  const labels: Record<string, string> = {
    live_map: '라이브 맵',
    driver_standings: '드라이버 스탠딩',
    weather: '날씨 정보',
    recent_radio: '팀 라디오',
    lap_times: '랩타임',
    pit_stops: '피트스톱'
  };
  return labels[widget] || widget;
};

const getWidgetDescription = (widget: string): string => {
  const descriptions: Record<string, string> = {
    live_map: '실시간 드라이버 위치 표시',
    driver_standings: '현재 챔피언십 순위',
    weather: '서킷 날씨 및 조건',
    recent_radio: '최근 팀 라디오 메시지',
    lap_times: '실시간 랩타임 비교',
    pit_stops: '피트스톱 현황 및 전략'
  };
  return descriptions[widget] || '';
};

export default FavoritesPage; 