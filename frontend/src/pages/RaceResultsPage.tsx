import React, { useState, useEffect } from 'react';

interface DriverResult {
  position: number;
  driver_number: number;
  driver_name: string;
  driver_code: string;
  team: string;
  grid: number;
  laps: number;
  status: string;
  time?: string;
  points: number;
  fastest_lap?: string;
}

interface RaceResult {
  round: number;
  race_name: string;
  circuit_name: string;
  country: string;
  date: string;
  season: string;
  results: DriverResult[];
}

const RaceResultsPage: React.FC = () => {
  const [raceResults, setRaceResults] = useState<RaceResult[]>([]);
  const [latestRace, setLatestRace] = useState<RaceResult | null>(null);
  const [selectedYear, setSelectedYear] = useState(2025); // Default to 2025 season
  const [selectedRace, setSelectedRace] = useState<RaceResult | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchRaceResults();
  }, [selectedYear]);

  const fetchRaceResults = async () => {
    setLoading(true);
    setError(null);
    
    try {
      // Fetch all race results for the year
      const response = await fetch(`http://localhost:8000/api/v1/race-results?year=${selectedYear}`);
      if (!response.ok) throw new Error('Failed to fetch race results');
      const data = await response.json();
      setRaceResults(data.data || []);

      // Fetch latest completed race
      const latestResponse = await fetch('http://localhost:8000/api/v1/race-results/latest');
      if (latestResponse.ok) {
        const latestData = await latestResponse.json();
        setLatestRace(latestData.data);
      }

    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', { 
      month: 'short', 
      day: 'numeric',
      year: 'numeric'
    });
  };

  const getPositionClass = (position: number) => {
    if (position === 1) return 'p1';
    if (position === 2) return 'p2';
    if (position === 3) return 'p3';
    return '';
  };

  const getStatusColor = (status: string) => {
    if (status === 'Finished') return '#10b981';
    if (status.includes('Lap')) return '#f59e0b';
    return '#ef4444';
  };

  if (loading) return <div className="f1-loading">Loading Race Results...</div>;
  if (error) return <div className="f1-error">Error: {error}</div>;

  return (
    <div>
      <h1 className="f1-card-title">🏆 Race Results</h1>
      
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

      {/* Latest Race Result */}
      {latestRace && (
        <div className="f1-card">
          <h3 className="f1-card-title">🥇 Latest Race Result</h3>
          <div style={{ marginBottom: '1rem' }}>
            <h2 style={{ fontSize: '1.5rem', marginBottom: '0.5rem' }}>{latestRace.race_name}</h2>
            <p style={{ color: '#ccc' }}>{latestRace.circuit_name} • {formatDate(latestRace.date)}</p>
          </div>
          
          {latestRace.results.length > 0 && (
            <div className="f1-grid f1-grid-3">
              {latestRace.results.slice(0, 3).map((result, index) => (
                <div key={result.driver_number} className="f1-card" style={{ marginBottom: 0 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                    <div className={`position ${getPositionClass(result.position)}`} style={{ fontSize: '2rem' }}>
                      {result.position}
                    </div>
                    <div>
                      <div style={{ fontWeight: '600', fontSize: '1.1rem' }}>{result.driver_name}</div>
                      <div style={{ color: '#ccc', fontSize: '0.9rem' }}>{result.team}</div>
                      <div style={{ marginTop: '0.5rem' }}>
                        <span style={{ color: '#ff6b35' }}>{result.points} pts</span>
                        {result.time && <span style={{ marginLeft: '1rem', color: '#ccc' }}>{result.time}</span>}
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Race List */}
      <div className="f1-card">
        <h3 className="f1-card-title">📋 {selectedYear} Season Results</h3>
        
        {raceResults.length === 0 ? (
          <p style={{ textAlign: 'center', color: '#ccc', padding: '2rem' }}>
            No race results available for {selectedYear}
          </p>
        ) : (
          <div className="f1-grid f1-grid-2">
            {raceResults.map((race) => (
              <div key={race.round} className="f1-card" style={{ marginBottom: 0 }}>
                <div 
                  style={{ cursor: 'pointer' }}
                  onClick={() => setSelectedRace(selectedRace?.round === race.round ? null : race)}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
                    <div>
                      <div style={{ fontSize: '0.9rem', color: '#ccc' }}>Round {race.round}</div>
                      <h4 style={{ fontSize: '1.1rem' }}>{race.race_name}</h4>
                      <div style={{ color: '#ccc', fontSize: '0.9rem' }}>{race.circuit_name}</div>
                    </div>
                    <div style={{ textAlign: 'right' }}>
                      <div style={{ fontSize: '0.9rem', color: '#ccc' }}>{formatDate(race.date)}</div>
                      <div className="f1-status completed">
                        {race.results.length > 0 ? `${race.results.length} finishers` : 'No results'}
                      </div>
                    </div>
                  </div>
                  
                  {race.results.length > 0 && (
                    <div>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                        <div className="position p1" style={{ fontSize: '1.5rem' }}>🥇</div>
                        <div>
                          <div style={{ fontWeight: '600' }}>{race.results[0].driver_name}</div>
                          <div style={{ color: '#ccc', fontSize: '0.9rem' }}>{race.results[0].team}</div>
                        </div>
                      </div>
                    </div>
                  )}
                </div>
                
                {/* Expanded Race Details */}
                {selectedRace?.round === race.round && (
                  <div style={{ marginTop: '1rem', borderTop: '1px solid rgba(255, 255, 255, 0.1)', paddingTop: '1rem' }}>
                    <table className="f1-table">
                      <thead>
                        <tr>
                          <th>Pos</th>
                          <th>Driver</th>
                          <th>Team</th>
                          <th>Time/Status</th>
                          <th>Pts</th>
                        </tr>
                      </thead>
                      <tbody>
                        {race.results.slice(0, 10).map((result) => (
                          <tr key={result.driver_number}>
                            <td>
                              <span className={`position ${getPositionClass(result.position)}`}>
                                {result.position}
                              </span>
                            </td>
                            <td>
                              <div>
                                <div style={{ fontWeight: '600' }}>{result.driver_name}</div>
                                <div style={{ fontSize: '0.8rem', color: '#ccc' }}>#{result.driver_number}</div>
                              </div>
                            </td>
                            <td>{result.team}</td>
                            <td>
                              {result.time ? (
                                <span>{result.time}</span>
                              ) : (
                                <span style={{ color: getStatusColor(result.status) }}>
                                  {result.status}
                                </span>
                              )}
                            </td>
                            <td style={{ color: '#ff6b35', fontWeight: '600' }}>{result.points}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                    
                    {race.results.length > 10 && (
                      <p style={{ textAlign: 'center', color: '#ccc', marginTop: '1rem' }}>
                        ... and {race.results.length - 10} more finishers
                      </p>
                    )}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default RaceResultsPage;