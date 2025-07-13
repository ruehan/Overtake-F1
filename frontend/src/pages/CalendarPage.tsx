import React, { useState, useEffect } from 'react';

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
      const calendarResponse = await fetch(`http://localhost:8000/api/v1/calendar?year=${selectedYear}`);
      if (!calendarResponse.ok) throw new Error('Failed to fetch calendar');
      const calendarData = await calendarResponse.json();
      setRaces(calendarData.data || []);

      // Fetch next race
      const nextResponse = await fetch('http://localhost:8000/api/v1/calendar/next');
      if (nextResponse.ok) {
        const nextData: NextRaceData = await nextResponse.json();
        setNextRace(nextData.data);
      }

      // Fetch current race
      const currentResponse = await fetch('http://localhost:8000/api/v1/calendar/current');
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
      return { status: 'live', label: 'LIVE' };
    } else if (raceDate > today) {
      return { status: 'upcoming', label: 'UPCOMING' };
    } else {
      return { status: 'completed', label: 'COMPLETED' };
    }
  };

  if (loading) return <div className="f1-loading">Loading Calendar...</div>;
  if (error) return <div className="f1-error">Error: {error}</div>;

  return (
    <div>
      <h1 className="f1-card-title">🏁 F1 Race Calendar</h1>
      
      {/* Year Selector */}
      <div className="f1-card">
        <div style={{ display: 'flex', gap: '1rem', alignItems: 'center', marginBottom: '1rem' }}>
          <label>Season:</label>
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
              <h3 className="f1-card-title">🔴 Current Race Weekend</h3>
              <h2 style={{ fontSize: '1.5rem', marginBottom: '0.5rem' }}>{currentRace.race_name}</h2>
              <p style={{ color: '#ccc', marginBottom: '1rem' }}>{currentRace.circuit_name}, {currentRace.country}</p>
              <div className="f1-status live">LIVE</div>
            </div>
          )}
          
          {nextRace && (
            <div className="f1-card">
              <h3 className="f1-card-title">⏭️ Next Race</h3>
              <h2 style={{ fontSize: '1.5rem', marginBottom: '0.5rem' }}>{nextRace.race_name}</h2>
              <p style={{ color: '#ccc', marginBottom: '0.5rem' }}>{nextRace.circuit_name}, {nextRace.country}</p>
              <p style={{ marginBottom: '1rem' }}>{formatDate(nextRace.date, nextRace.time)}</p>
              <div className="f1-status upcoming">Round {nextRace.round}</div>
            </div>
          )}
        </div>
      )}

      {/* Full Calendar */}
      <div className="f1-card">
        <h3 className="f1-card-title">📅 {selectedYear} Season Calendar</h3>
        <div className="f1-grid f1-grid-3">
          {races.map((race) => {
            const { status, label } = getRaceStatus(race);
            return (
              <div key={race.round} className="f1-card" style={{ marginBottom: 0 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '1rem' }}>
                  <div>
                    <div style={{ fontSize: '0.9rem', color: '#ccc' }}>Round {race.round}</div>
                    <h4 style={{ fontSize: '1.1rem', marginBottom: '0.5rem' }}>{race.race_name}</h4>
                  </div>
                  <div className={`f1-status ${status}`}>{label}</div>
                </div>
                
                <div style={{ marginBottom: '1rem' }}>
                  <div style={{ fontWeight: '600', marginBottom: '0.25rem' }}>{race.circuit_name}</div>
                  <div style={{ color: '#ccc', fontSize: '0.9rem' }}>{race.locality}, {race.country}</div>
                </div>
                
                <div style={{ fontSize: '0.9rem' }}>
                  <div style={{ marginBottom: '0.25rem' }}>
                    <strong>Race:</strong> {formatDate(race.date, race.time)}
                  </div>
                  {race.qualifying && (
                    <div style={{ color: '#ccc' }}>
                      <strong>Qualifying:</strong> {formatDate(race.qualifying)}
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