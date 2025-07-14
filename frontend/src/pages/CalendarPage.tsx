import React, { useState, useEffect } from 'react';
import { useLanguage } from '../contexts/LanguageContext';
import { API_ENDPOINTS } from '../config/api';

interface Race {
  round: number;
  race_name: string;
  circuit_name: string;
  country: string;
  locality: string;
  date: string;
  time?: string;
  first_practice?: string;
  second_practice?: string;
  third_practice?: string;
  qualifying?: string;
  sprint?: string;
}

interface NextRaceData {
  data: Race | null;
  message?: string;
}

const CalendarPage: React.FC = () => {
  const { t, translateCountry } = useLanguage();
  const [races, setRaces] = useState<Race[]>([]);
  const [nextRace, setNextRace] = useState<Race | null>(null);
  const [currentRace, setCurrentRace] = useState<Race | null>(null);
  const [selectedYear, setSelectedYear] = useState(2025);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchCalendarData();
  }, [selectedYear]);

  const fetchCalendarData = async () => {
    setLoading(true);
    setError(null);
    
    try {
      // Fetch calendar
      const calendarResponse = await fetch(API_ENDPOINTS.calendar(selectedYear));
      if (!calendarResponse.ok) throw new Error('Failed to fetch calendar');
      const calendarData = await calendarResponse.json();
      setRaces(calendarData.data || []);

      // Fetch next race
      const nextResponse = await fetch(API_ENDPOINTS.nextRace);
      if (nextResponse.ok) {
        const nextData: NextRaceData = await nextResponse.json();
        setNextRace(nextData.data);
      }

      // Fetch current race
      const currentResponse = await fetch(API_ENDPOINTS.currentRace);
      if (currentResponse.ok) {
        const currentData: NextRaceData = await currentResponse.json();
        setCurrentRace(currentData.data);
      }

    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateString: string, timeString?: string) => {
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

  if (loading) return <div className="f1-loading">{t('common.loading')} {t('nav.calendar')}...</div>;
  if (error) return <div className="f1-error">{t('common.error')}: {error}</div>;

  return (
    <div>
      <h1 className="f1-card-title">🏁 F1 {t('nav.calendar')}</h1>
      
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

      {/* Full Calendar */}
      <div className="f1-card">
        <h3 className="f1-card-title">📅 {selectedYear} {t('standings.season')} {t('nav.calendar')}</h3>
        <div className="f1-grid f1-grid-3">
          {races.map((race) => {
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
      </div>
    </div>
  );
};

export default CalendarPage;