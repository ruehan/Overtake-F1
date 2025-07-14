import React, { useState, useEffect } from 'react';
import { useLanguage } from '../contexts/LanguageContext';
import { API_ENDPOINTS } from '../config/api';

interface Session {
  session_type: string;
  date: string;
  time?: string;
  status: 'completed' | 'scheduled';
  results?: any[];
}

interface RaceWeekend {
  round: number;
  race_name: string;
  circuit_name: string;
  circuit_id: string;
  country: string;
  locality: string;
  date: string;
  url: string;
  season: string;
  sessions: Session[];
  weekend_status: 'completed' | 'upcoming';
}

interface RaceWeekendsData {
  race_weekends: RaceWeekend[];
  total_weekends: number;
  year: number;
}

const RaceWeekendsPage: React.FC = () => {
  const { t, translateCountry, formatMessage } = useLanguage();
  const [weekendsData, setWeekendsData] = useState<RaceWeekendsData | null>(null);
  const [selectedYear, setSelectedYear] = useState(2025); // 2025가 기본값
  const [selectedWeekend, setSelectedWeekend] = useState<RaceWeekend | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchRaceWeekends();
  }, [selectedYear]);

  const fetchRaceWeekends = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await fetch(API_ENDPOINTS.raceWeekends(selectedYear));
      if (!response.ok) throw new Error('Failed to fetch race weekends');
      const data = await response.json();
      setWeekendsData(data.data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  };

  const formatDateTime = (dateString: string, timeString?: string) => {
    const date = new Date(dateString);
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

    const isQualifying = session.session_type.toLowerCase() === 'qualifying';
    
    return (
      <div style={{ marginTop: '1rem' }}>
        <h5 style={{ color: '#ff6b35', marginBottom: '0.5rem' }}>
          {translateSessionType(session.session_type)} {t('weekends.results')}
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
                  {isQualifying 
                    ? `${result.Driver.givenName} ${result.Driver.familyName}`
                    : `${result.Driver.givenName} ${result.Driver.familyName}`
                  }
                </span>
                <span style={{ color: '#ccc', fontSize: '0.8rem' }}>
                  {isQualifying ? result.Constructor.name : result.Constructor.name}
                </span>
              </div>
              <div style={{ textAlign: 'right' }}>
                {isQualifying ? (
                  <div>
                    <div style={{ fontWeight: '600', color: '#ff6b35' }}>
                      {result.Q3 || result.Q2 || result.Q1 || 'No time'}
                    </div>
                    {result.Q1 && (
                      <div style={{ fontSize: '0.7rem', color: '#666' }}>
                        Q1: {result.Q1} {result.Q2 && `• Q2: ${result.Q2}`} {result.Q3 && `• Q3: ${result.Q3}`}
                      </div>
                    )}
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
          {session.results.length > 10 && (
            <p style={{ textAlign: 'center', color: '#666', margin: '0.5rem 0', fontSize: '0.8rem' }}>
              ... and {session.results.length - 10} more
            </p>
          )}
        </div>
      </div>
    );
  };

  if (loading) return <div className="f1-loading">{t('common.loading')} {t('weekends.title')}...</div>;
  if (error) return <div className="f1-error">{t('common.error')}: {error}</div>;
  if (!weekendsData) return <div className="f1-error">{t('common.noData')}</div>;

  return (
    <div>
      <h1 className="f1-card-title">🏁 {t('weekends.title')}</h1>
      
      {/* Controls */}
      <div className="f1-card">
        <div style={{ display: 'flex', gap: '1rem', alignItems: 'center', marginBottom: '1rem' }}>
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
        
        <div style={{ fontSize: '0.9rem', color: '#ccc' }}>
          {weekendsData.total_weekends} race weekends • 
          {weekendsData.race_weekends.filter(w => w.weekend_status === 'completed').length} completed • 
          {weekendsData.race_weekends.filter(w => w.weekend_status === 'upcoming').length} upcoming
        </div>
      </div>

      {/* Race Weekends Grid */}
      <div className="f1-grid f1-grid-2">
        {weekendsData.race_weekends.map((weekend) => (
          <div key={weekend.round} className="f1-card" style={{ marginBottom: 0 }}>
            <div 
              style={{ cursor: 'pointer' }}
              onClick={() => setSelectedWeekend(selectedWeekend?.round === weekend.round ? null : weekend)}
            >
              {/* Weekend Header */}
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '1rem' }}>
                <div>
                  <div style={{ fontSize: '0.9rem', color: '#ccc' }}>Round {weekend.round}</div>
                  <h3 style={{ fontSize: '1.2rem', marginBottom: '0.5rem' }}>{weekend.race_name}</h3>
                  <div style={{ color: '#ccc', fontSize: '0.9rem' }}>
                    {weekend.circuit_name} • {weekend.locality}, {translateCountry(weekend.country)}
                  </div>
                </div>
                <div className={`f1-status ${weekend.weekend_status === 'completed' ? 'completed' : 'upcoming'}`}>
                  {weekend.weekend_status.toUpperCase()}
                </div>
              </div>

              {/* Session Overview */}
              <div style={{ marginBottom: '1rem' }}>
                <div style={{ fontSize: '0.9rem', color: '#ff6b35', marginBottom: '0.5rem' }}>
                  {t('weekends.raceWeekend')}: {formatDateTime(weekend.date)}
                </div>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
                  {weekend.sessions.map((session, index) => (
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
              </div>
            </div>

            {/* Expanded Details */}
            {selectedWeekend?.round === weekend.round && (
              <div style={{ 
                marginTop: '1rem', 
                borderTop: '1px solid rgba(255, 255, 255, 0.1)', 
                paddingTop: '1rem' 
              }}>
                <h4 style={{ color: '#ff6b35', marginBottom: '1rem' }}>{t('weekends.sessionSchedule')}</h4>
                
                {weekend.sessions.map((session, index) => (
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
                          {formatDateTime(session.date, session.time)}
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
                    
                    {session.status === 'completed' && renderSessionResults(session)}
                  </div>
                ))}
                
                {weekend.url && (
                  <div style={{ textAlign: 'center', marginTop: '1rem' }}>
                    <a
                      href={weekend.url}
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
    </div>
  );
};

export default RaceWeekendsPage;