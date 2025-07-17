import React, { useState, useEffect } from 'react';
import { useLanguage } from '../contexts/LanguageContext';
import { API_ENDPOINTS } from '../config/api';
import { useApiCache } from '../hooks/useApiCache';

interface Session {
  session_type: string;
  date: string;
  time?: string;
  status: 'completed' | 'scheduled';
  results?: any[];
}

interface Race {
  round: number;
  race_name: string;
  circuit_name: string;
  circuit_id: string;
  country: string;
  locality: string;
  date: string;
  time?: string;
  url?: string;
  season?: string;
  sessions?: Session[];
  weekend_status?: 'completed' | 'upcoming';
  first_practice?: string;
  second_practice?: string;
  third_practice?: string;
  qualifying?: string;
  sprint?: string;
}

interface RaceWeekendsData {
  race_weekends: Race[];
  total_weekends: number;
  year: number;
}

const CalendarPage: React.FC = () => {
  const { t, translateCountry } = useLanguage();
  const [nextRace, setNextRace] = useState<Race | null>(null);
  const [currentRace, setCurrentRace] = useState<Race | null>(null);
  const [selectedYear, setSelectedYear] = useState(2025);
  const [selectedRace, setSelectedRace] = useState<Race | null>(null);
  const [viewMode, setViewMode] = useState<'calendar' | 'detailed'>('calendar');

  // 캘린더 데이터 캐싱
  const {
    data: races,
    loading,
    error,
    refetch
  } = useApiCache<Race[]>(
    `calendar-${viewMode}-${selectedYear}`,
    async () => {
      if (viewMode === 'calendar') {
        // Fetch basic calendar
        const calendarResponse = await fetch(API_ENDPOINTS.calendar(selectedYear));
        if (!calendarResponse.ok) throw new Error('Failed to fetch calendar');
        const calendarData = await calendarResponse.json();
        return calendarData.calendar || [];
      } else {
        // Fetch detailed race weekends
        const weekendsResponse = await fetch(API_ENDPOINTS.raceWeekends(selectedYear));
        if (!weekendsResponse.ok) throw new Error('Failed to fetch race weekends');
        const weekendsData = await weekendsResponse.json();
        return weekendsData.weekends || [];
      }
    },
    { staleTime: 60 * 60 * 1000 } // 1시간 동안 신선한 데이터로 간주
  );

  useEffect(() => {
    fetchNextAndCurrentRace();
  }, []);

  const fetchNextAndCurrentRace = async () => {
    try {
      // Fetch next race
      const nextResponse = await fetch(API_ENDPOINTS.nextRace);
      if (nextResponse.ok) {
        const nextData = await nextResponse.json();
        setNextRace(nextData.next_race);
      }

      // Fetch current race
      const currentResponse = await fetch(API_ENDPOINTS.currentRace);
      if (currentResponse.ok) {
        const currentData = await currentResponse.json();
        setCurrentRace(currentData.current_race);
      }

    } catch (err) {
      console.error('Error fetching next/current race:', err);
    }
  };

  // 날짜 유효성 체크 및 기본값 처리
  const formatDate = (dateString: string, timeString?: string) => {
    if (!dateString || dateString === 'null') return '-';
    const date = new Date(dateString);
    if (isNaN(date.getTime())) return '-';
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

  const getRaceStatus = (race: Race) => {
    const today = new Date();
    const raceDate = new Date(race.date);
    
    if (currentRace && race.round === currentRace.round) {
      return { status: 'live', label: t('calendar.live') };
    } else if (raceDate > today) {
      return { status: 'upcoming', label: t('calendar.upcoming') };
    } else {
      return { status: 'completed', label: t('calendar.completed') };
    }
  };

  const translateSessionType = (sessionType: string) => {
    switch (sessionType.toLowerCase()) {
      case 'practice 1':
        return t('weekends.practice1');
      case 'practice 2':
        return t('weekends.practice2');
      case 'practice 3':
        return t('weekends.practice3');
      case 'qualifying':
        return t('weekends.qualifying');
      case 'sprint':
        return t('weekends.sprint');
      case 'race':
        return t('weekends.race');
      default:
        return sessionType;
    }
  };

  const getSessionIcon = (sessionType: string) => {
    switch (sessionType.toLowerCase()) {
      case 'practice 1':
      case 'practice 2':
      case 'practice 3':
        return '🏃';
      case 'qualifying':
        return '⚡';
      case 'sprint':
        return '🏃‍♂️';
      case 'race':
        return '🏁';
      default:
        return '📅';
    }
  };

  const getStatusColor = (status: string) => {
    return status === 'completed' ? '#10b981' : '#f59e0b';
  };

  const renderSessionResults = (session: Session) => {
    if (!session.results || session.results.length === 0) {
      return (
        <p style={{ color: '#666', fontStyle: 'italic', margin: '0.5rem 0' }}>
          No results available
        </p>
      );
    }

    // motorsportstats 스타일 판별: 첫 번째 결과에 POS, DRIVER, TEAM 필드가 있으면 해당 분기
    const isMotorsportStats = session.results[0] && session.results[0].POS && session.results[0].DRIVER && session.results[0].TEAM;

    if (isMotorsportStats) {
      return (
        <div style={{ marginTop: '1rem' }}>
          <h5 style={{ color: '#ff6b35', marginBottom: '0.5rem' }}>
            {translateSessionType(session.session_type)} Results
          </h5>
          <div style={{
            maxHeight: '300px',
            overflowY: 'auto',
            background: 'rgba(255, 255, 255, 0.02)',
            borderRadius: '8px',
            padding: '0.5rem'
          }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.95rem' }}>
              <thead>
                <tr style={{ borderBottom: '1px solid #444' }}>
                  <th style={{ textAlign: 'left', padding: '0.25rem' }}>순위</th>
                  <th style={{ textAlign: 'left', padding: '0.25rem' }}>번호</th>
                  <th style={{ textAlign: 'left', padding: '0.25rem' }}>드라이버</th>
                  <th style={{ textAlign: 'left', padding: '0.25rem' }}>팀</th>
                  <th style={{ textAlign: 'left', padding: '0.25rem' }}>기록</th>
                </tr>
              </thead>
              <tbody>
                {session.results.map((result, idx) => (
                  <tr key={idx} style={{ borderBottom: '1px solid #222' }}>
                    <td style={{ padding: '0.25rem', fontWeight: idx < 3 ? 700 : 400, color: idx < 3 ? '#ffd700' : '#fff' }}>{result.POS}</td>
                    <td style={{ padding: '0.25rem' }}>{result['№']}</td>
                    <td style={{ padding: '0.25rem' }}>{result.DRIVER}</td>
                    <td style={{ padding: '0.25rem' }}>{result.TEAM}</td>
                    <td style={{ padding: '0.25rem' }}>{result.TIME || result.GAP || '-'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      );
    }

    // 기존(ergast/openf1) 스타일
    const isQualifying = session.session_type.toLowerCase() === 'qualifying';
    return (
      <div style={{ marginTop: '1rem' }}>
        <h5 style={{ color: '#ff6b35', marginBottom: '0.5rem' }}>
          {translateSessionType(session.session_type)} Results
        </h5>
        <div style={{
          maxHeight: '300px',
          overflowY: 'auto',
          background: 'rgba(255, 255, 255, 0.02)',
          borderRadius: '8px',
          padding: '0.5rem'
        }}>
          {session.results.slice(0, 10).map((result, index) => (
            <div
              key={index}
              style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                padding: '0.5rem',
                borderBottom: '1px solid rgba(255, 255, 255, 0.1)',
                fontSize: '0.9rem'
              }}
            >
              <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                <span style={{
                  fontWeight: '600',
                  minWidth: '2rem',
                  color: index < 3 ? '#ffd700' : '#fff'
                }}>
                  P{result.position}
                </span>
                <span style={{ fontWeight: '500' }}>
                  {result.Driver.givenName} {result.Driver.familyName}
                </span>
                <span style={{ color: '#ccc', fontSize: '0.8rem' }}>
                  {result.Constructor.name}
                </span>
              </div>
              <div style={{ textAlign: 'right' }}>
                {isQualifying ? (
                  <div>
                    <div style={{ fontWeight: '600', color: '#ff6b35' }}>
                      {result.Q3 || result.Q2 || result.Q1 || 'No time'}
                    </div>
                  </div>
                ) : (
                  <div>
                    <div style={{ fontWeight: '600', color: '#ff6b35' }}>
                      {result.points} pts
                    </div>
                    {result.Time && (
                      <div style={{ fontSize: '0.8rem', color: '#ccc' }}>
                        {result.Time.time}
                      </div>
                    )}
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>
    );
  };

  const renderBasicCalendar = () => (
    <div className="f1-grid f1-grid-3">
      {(races || []).map((race) => {
        const { status, label } = getRaceStatus(race);
        return (
          <div key={race.round} className="f1-card" style={{ marginBottom: 0 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '1rem' }}>
              <div>
                <div style={{ fontSize: '0.9rem', color: '#ccc' }}>{t('common.round')} {race.round}</div>
                <h4 style={{ fontSize: '1.1rem', marginBottom: '0.5rem' }}>{race.race_name}</h4>
              </div>
              <div className={`f1-status ${status}`}>{label}</div>
            </div>
            
            <div style={{ marginBottom: '1rem' }}>
              <div style={{ fontWeight: '600', marginBottom: '0.25rem' }}>{race.circuit_name}</div>
              <div style={{ color: '#ccc', fontSize: '0.9rem' }}>{race.locality}, {translateCountry(race.country)}</div>
            </div>
            
            <div style={{ fontSize: '0.9rem' }}>
              <div style={{ marginBottom: '0.25rem' }}>
                <strong>{t('calendar.race')}:</strong> {formatDate(race.date, race.time)}
              </div>
              {race.qualifying && (
                <div style={{ color: '#ccc' }}>
                  <strong>{t('calendar.qualifying')}:</strong> {formatDate(race.qualifying)}
                </div>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );

  const renderDetailedWeekends = () => (
    <div className="f1-grid f1-grid-2">
      {(races || []).map((race) => (
        <div key={race.round} className="f1-card" style={{ marginBottom: 0 }}>
          <div 
            style={{ cursor: 'pointer' }}
            onClick={() => setSelectedRace(selectedRace?.round === race.round ? null : race)}
          >
            {/* Weekend Header */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '1rem' }}>
              <div>
                <div style={{ fontSize: '0.9rem', color: '#ccc' }}>Round {race.round}</div>
                <h3 style={{ fontSize: '1.2rem', marginBottom: '0.5rem' }}>{race.race_name || '그랑프리명 정보 없음'}</h3>
                <div style={{ color: '#ccc', fontSize: '0.9rem' }}>
                  {(race.circuit_name || '서킷 정보 없음')} • {(race.locality || '도시 정보 없음')}, {translateCountry(race.country) || '국가 정보 없음'}
                </div>
              </div>
              <div className={`f1-status ${race.weekend_status === 'completed' ? 'completed' : 'upcoming'}`}>
                {race.weekend_status?.toUpperCase() || 'SCHEDULED'}
              </div>
            </div>

            {/* Session Overview */}
            <div style={{ marginBottom: '1rem' }}>
              <div style={{ fontSize: '0.9rem', color: '#ff6b35', marginBottom: '0.5rem' }}>
                {race.date && race.date !== 'null' && race.date !== null
                  ? `Race Weekend: ${formatDate(race.date)}`
                  : 'Race Weekend: 날짜 정보 없음'}
              </div>
              {race.sessions && (
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
                  {race.sessions.map((session, index) => (
                    <div
                      key={index}
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: '0.25rem',
                        padding: '0.25rem 0.5rem',
                        background: 'rgba(255, 255, 255, 0.05)',
                        borderRadius: '12px',
                        fontSize: '0.8rem',
                        border: `1px solid ${getStatusColor(session.status)}20`
                      }}
                    >
                      <span>{getSessionIcon(session.session_type)}</span>
                      <span>{translateSessionType(session.session_type)}</span>
                      <span style={{ color: getStatusColor(session.status) }}>
                        {session.status === 'completed' ? '✓' : '○'}
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Expanded Details */}
          {selectedRace?.round === race.round && race.sessions && (
            <div style={{ 
              marginTop: '1rem', 
              borderTop: '1px solid rgba(255, 255, 255, 0.1)', 
              paddingTop: '1rem' 
            }}>
              <h4 style={{ color: '#ff6b35', marginBottom: '1rem' }}>Session Schedule</h4>
              {race.sessions.map((session, index) => (
                <div
                  key={index}
                  style={{
                    marginBottom: '1.5rem',
                    padding: '1rem',
                    background: 'rgba(255, 255, 255, 0.02)',
                    borderRadius: '8px',
                    border: '1px solid rgba(255, 255, 255, 0.1)'
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                      <span style={{ fontSize: '1.2rem' }}>{getSessionIcon(session.session_type)}</span>
                      <h5 style={{ margin: 0, fontSize: '1.1rem' }}>{translateSessionType(session.session_type)}</h5>
                    </div>
                    <div style={{ textAlign: 'right' }}>
                      <div style={{ fontSize: '0.9rem', marginBottom: '0.25rem' }}>
                        {session.date && session.date !== 'null' && session.date !== null
                          ? formatDate(session.date, session.time)
                          : '날짜 정보 없음'}
                      </div>
                      <div style={{ 
                        fontSize: '0.8rem',
                        color: getStatusColor(session.status),
                        fontWeight: '600',
                        textTransform: 'uppercase'
                      }}>
                        {session.status}
                      </div>
                    </div>
                  </div>
                  {/* 세션 결과 표 항상 출력 */}
                  {renderSessionResults(session)}
                </div>
              ))}
              {race.url && (
                <div style={{ textAlign: 'center', marginTop: '1rem' }}>
                  <a
                    href={race.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    style={{
                      color: '#ff6b35',
                      textDecoration: 'none',
                      fontSize: '0.9rem',
                      borderBottom: '1px solid #ff6b35'
                    }}
                  >
                    🔗 View on Formula1.com
                  </a>
                </div>
              )}
            </div>
          )}
        </div>
      ))}
    </div>
  );

  if (loading) return <div className="f1-loading">{t('common.loading')} {t('nav.calendar')}...</div>;
  if (error) return <div className="f1-error">{t('common.error')}: {error}</div>;

  return (
    <div>
      <h1 className="f1-card-title">🏁 F1 {t('nav.calendar')}</h1>
      
      {/* Controls */}
      <div className="f1-card">
        <div style={{ display: 'flex', gap: '2rem', alignItems: 'center', flexWrap: 'wrap' }}>
          <div>
            <label style={{ marginRight: '0.5rem' }}>{t('standings.season')}:</label>
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
              onClick={() => setViewMode('calendar')}
              style={{
                background: viewMode === 'calendar' ? 'linear-gradient(45deg, #ff6b35, #f7931e)' : 'transparent',
                border: '1px solid rgba(255, 255, 255, 0.2)',
                color: '#fff',
                padding: '0.5rem 1rem',
                cursor: 'pointer',
                borderRadius: '4px'
              }}
            >
              📅 Calendar View
            </button>
            <button
              onClick={() => setViewMode('detailed')}
              style={{
                background: viewMode === 'detailed' ? 'linear-gradient(45deg, #ff6b35, #f7931e)' : 'transparent',
                border: '1px solid rgba(255, 255, 255, 0.2)',
                color: '#fff',
                padding: '0.5rem 1rem',
                cursor: 'pointer',
                borderRadius: '4px'
              }}
            >
              🏁 Weekend Details
            </button>
          </div>
        </div>
      </div>

      {/* Next/Current Race Highlight */}
      {(nextRace || currentRace) && (
        <div className="f1-grid f1-grid-2">
          {currentRace && (
            <div className="f1-card">
              <h3 className="f1-card-title">{t('dashboard.currentRace')}</h3>
              <h2 style={{ fontSize: '1.5rem', marginBottom: '0.5rem' }}>{currentRace.race_name}</h2>
              <p style={{ color: '#ccc', marginBottom: '1rem' }}>{currentRace.circuit_name}, {translateCountry(currentRace.country)}</p>
              <div className="f1-status live">{t('data.raceWeekend')}</div>
            </div>
          )}
          
          {nextRace && (
            <div className="f1-card">
              <h3 className="f1-card-title">{t('dashboard.nextRace')}</h3>
              <h2 style={{ fontSize: '1.5rem', marginBottom: '0.5rem' }}>{nextRace.race_name}</h2>
              <p style={{ color: '#ccc', marginBottom: '0.5rem' }}>{nextRace.circuit_name}, {translateCountry(nextRace.country)}</p>
              <p style={{ marginBottom: '1rem' }}>{formatDate(nextRace.date, nextRace.time)}</p>
              <div className="f1-status upcoming">{t('common.round')} {nextRace.round}</div>
            </div>
          )}
        </div>
      )}

      {/* Calendar Content */}
      <div className="f1-card">
        <h3 className="f1-card-title">
          {viewMode === 'calendar' ? '📅' : '🏁'} {selectedYear} {t('standings.season')} {viewMode === 'calendar' ? t('nav.calendar') : 'Race Weekends'}
        </h3>
        
        {viewMode === 'calendar' ? renderBasicCalendar() : renderDetailedWeekends()}
      </div>
    </div>
  );
};

export default CalendarPage;