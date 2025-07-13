import React, { useState, useEffect } from 'react';

interface ProgressionPoint {
  race: string;
  position: number;
  points: number;
  round: number;
}

interface StandingsProgression {
  driver_progression: { [driverName: string]: ProgressionPoint[] };
  constructor_progression: { [teamName: string]: ProgressionPoint[] };
  race_labels: string[];
  total_races: number;
  year: number;
}

const StandingsProgressionPage: React.FC = () => {
  const [progression, setProgression] = useState<StandingsProgression | null>(null);
  const [selectedYear, setSelectedYear] = useState(2024); // 2024가 데이터가 많음
  const [viewType, setViewType] = useState<'drivers' | 'constructors'>('drivers');
  const [selectedItems, setSelectedItems] = useState<Set<string>>(new Set());
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchProgressionData();
  }, [selectedYear]);

  const fetchProgressionData = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await fetch(`http://localhost:8000/api/v1/standings-progression?year=${selectedYear}`);
      if (!response.ok) throw new Error('Failed to fetch progression data');
      const data = await response.json();
      setProgression(data.data);
      
      // 자동으로 상위 8명/팀 선택 (더 많은 선수 표시)
      if (data.data) {
        const items = viewType === 'drivers' ? data.data.driver_progression : data.data.constructor_progression;
        const topItems = Object.keys(items).slice(0, 8);
        setSelectedItems(new Set(topItems));
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (progression) {
      const items = viewType === 'drivers' ? progression.driver_progression : progression.constructor_progression;
      const topItems = Object.keys(items).slice(0, 8);
      setSelectedItems(new Set(topItems));
    }
  }, [viewType, progression]);

  const toggleItemSelection = (itemName: string) => {
    const newSelected = new Set(selectedItems);
    if (newSelected.has(itemName)) {
      newSelected.delete(itemName);
    } else {
      newSelected.add(itemName);
    }
    setSelectedItems(newSelected);
  };

  const selectAll = () => {
    if (!progression) return;
    const items = viewType === 'drivers' ? progression.driver_progression : progression.constructor_progression;
    setSelectedItems(new Set(Object.keys(items)));
  };

  const selectNone = () => {
    setSelectedItems(new Set());
  };

  const getColorForIndex = (index: number) => {
    const colors = [
      '#ff6b35', '#f7931e', '#ffd700', '#10b981', '#3b82f6',
      '#8b5cf6', '#ef4444', '#06b6d4', '#84cc16', '#f59e0b'
    ];
    return colors[index % colors.length];
  };

  const renderPositionChart = () => {
    if (!progression) return null;

    const items = viewType === 'drivers' ? progression.driver_progression : progression.constructor_progression;
    const maxRounds = progression.race_labels.length;
    
    // 차트 크기 계산
    const chartWidth = Math.max(800, maxRounds * 60);
    const chartHeight = 400;
    const padding = { top: 40, right: 40, bottom: 60, left: 80 };
    
    const innerWidth = chartWidth - padding.left - padding.right;
    const innerHeight = chartHeight - padding.top - padding.bottom;

    return (
      <div style={{ overflowX: 'auto', marginBottom: '2rem' }}>
        <svg width={chartWidth} height={chartHeight} style={{ background: 'rgba(255, 255, 255, 0.02)' }}>
          {/* Grid lines */}
          {[1, 5, 10, 15, 20].map(position => {
            const y = padding.top + (position - 1) * (innerHeight / 19); // Top 20 positions
            return (
              <g key={position}>
                <line
                  x1={padding.left}
                  y1={y}
                  x2={chartWidth - padding.right}
                  y2={y}
                  stroke="rgba(255, 255, 255, 0.1)"
                  strokeDasharray="2,2"
                />
                <text
                  x={padding.left - 10}
                  y={y + 4}
                  fill="#666"
                  fontSize="12"
                  textAnchor="end"
                >
                  P{position}
                </text>
              </g>
            );
          })}

          {/* Race labels */}
          {progression.race_labels.map((label, index) => {
            const x = padding.left + (index + 1) * (innerWidth / maxRounds);
            return (
              <text
                key={label}
                x={x}
                y={chartHeight - 20}
                fill="#666"
                fontSize="10"
                textAnchor="middle"
                transform={`rotate(-45, ${x}, ${chartHeight - 20})`}
              >
                {label}
              </text>
            );
          })}

          {/* Position lines for selected items */}
          {Object.entries(items)
            .filter(([name]) => selectedItems.has(name))
            .map(([name, data], index) => {
              const color = getColorForIndex(index);
              
              // Create path for line chart
              const pathPoints = data.map((point, pointIndex) => {
                const x = padding.left + (pointIndex + 1) * (innerWidth / maxRounds);
                const y = padding.top + Math.min(point.position - 1, 19) * (innerHeight / 19);
                return `${pointIndex === 0 ? 'M' : 'L'} ${x} ${y}`;
              }).join(' ');

              return (
                <g key={name}>
                  {/* Line */}
                  <path
                    d={pathPoints}
                    stroke={color}
                    strokeWidth="3"
                    fill="none"
                    opacity="0.8"
                  />
                  
                  {/* Points */}
                  {data.map((point, pointIndex) => {
                    const x = padding.left + (pointIndex + 1) * (innerWidth / maxRounds);
                    const y = padding.top + Math.min(point.position - 1, 19) * (innerHeight / 19);
                    
                    return (
                      <circle
                        key={pointIndex}
                        cx={x}
                        cy={y}
                        r="4"
                        fill={color}
                        stroke="#fff"
                        strokeWidth="1"
                      />
                    );
                  })}
                </g>
              );
            })}

          {/* Chart title */}
          <text
            x={chartWidth / 2}
            y={20}
            fill="#ff6b35"
            fontSize="16"
            fontWeight="600"
            textAnchor="middle"
          >
            {viewType === 'drivers' ? 'Driver' : 'Constructor'} Championship Position Progress
          </text>
        </svg>
      </div>
    );
  };

  const renderPointsChart = () => {
    if (!progression) return null;

    const items = viewType === 'drivers' ? progression.driver_progression : progression.constructor_progression;
    const maxRounds = progression.race_labels.length;
    
    // 최대 포인트 계산
    const maxPoints = Math.max(...Object.values(items).flat().map(p => p.points));
    
    const chartWidth = Math.max(800, maxRounds * 60);
    const chartHeight = 400;
    const padding = { top: 40, right: 40, bottom: 60, left: 80 };
    
    const innerWidth = chartWidth - padding.left - padding.right;
    const innerHeight = chartHeight - padding.top - padding.bottom;

    return (
      <div style={{ overflowX: 'auto' }}>
        <svg width={chartWidth} height={chartHeight} style={{ background: 'rgba(255, 255, 255, 0.02)' }}>
          {/* Grid lines */}
          {[0, Math.floor(maxPoints * 0.25), Math.floor(maxPoints * 0.5), Math.floor(maxPoints * 0.75), maxPoints].map(points => {
            const y = padding.top + innerHeight - (points / maxPoints) * innerHeight;
            return (
              <g key={points}>
                <line
                  x1={padding.left}
                  y1={y}
                  x2={chartWidth - padding.right}
                  y2={y}
                  stroke="rgba(255, 255, 255, 0.1)"
                  strokeDasharray="2,2"
                />
                <text
                  x={padding.left - 10}
                  y={y + 4}
                  fill="#666"
                  fontSize="12"
                  textAnchor="end"
                >
                  {points}
                </text>
              </g>
            );
          })}

          {/* Race labels */}
          {progression.race_labels.map((label, index) => {
            const x = padding.left + (index + 1) * (innerWidth / maxRounds);
            return (
              <text
                key={label}
                x={x}
                y={chartHeight - 20}
                fill="#666"
                fontSize="10"
                textAnchor="middle"
                transform={`rotate(-45, ${x}, ${chartHeight - 20})`}
              >
                {label}
              </text>
            );
          })}

          {/* Points lines for selected items */}
          {Object.entries(items)
            .filter(([name]) => selectedItems.has(name))
            .map(([name, data], index) => {
              const color = getColorForIndex(index);
              
              const pathPoints = data.map((point, pointIndex) => {
                const x = padding.left + (pointIndex + 1) * (innerWidth / maxRounds);
                const y = padding.top + innerHeight - (point.points / maxPoints) * innerHeight;
                return `${pointIndex === 0 ? 'M' : 'L'} ${x} ${y}`;
              }).join(' ');

              return (
                <g key={name}>
                  <path
                    d={pathPoints}
                    stroke={color}
                    strokeWidth="3"
                    fill="none"
                    opacity="0.8"
                  />
                  
                  {data.map((point, pointIndex) => {
                    const x = padding.left + (pointIndex + 1) * (innerWidth / maxRounds);
                    const y = padding.top + innerHeight - (point.points / maxPoints) * innerHeight;
                    
                    return (
                      <circle
                        key={pointIndex}
                        cx={x}
                        cy={y}
                        r="4"
                        fill={color}
                        stroke="#fff"
                        strokeWidth="1"
                      />
                    );
                  })}
                </g>
              );
            })}

          {/* Chart title */}
          <text
            x={chartWidth / 2}
            y={20}
            fill="#ff6b35"
            fontSize="16"
            fontWeight="600"
            textAnchor="middle"
          >
            {viewType === 'drivers' ? 'Driver' : 'Constructor'} Championship Points Progress
          </text>
        </svg>
      </div>
    );
  };

  if (loading) return <div className="f1-loading">Loading Standings Progression...</div>;
  if (error) return <div className="f1-error">Error: {error}</div>;
  if (!progression) return <div className="f1-error">No progression data available</div>;

  const items = viewType === 'drivers' ? progression.driver_progression : progression.constructor_progression;

  return (
    <div>
      <h1 className="f1-card-title">📈 Championship Progression</h1>
      
      {/* Controls */}
      <div className="f1-card">
        <div style={{ display: 'flex', gap: '2rem', alignItems: 'center', flexWrap: 'wrap' }}>
          <div>
            <label style={{ marginRight: '0.5rem' }}>Season:</label>
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
              <option value={2024}>2024</option>
              <option value={2023}>2023</option>
              <option value={2025}>2025</option>
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
              onClick={() => setViewType('constructors')}
              style={{
                background: viewType === 'constructors' ? 'linear-gradient(45deg, #ff6b35, #f7931e)' : 'transparent',
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

      {/* Item Selection */}
      <div className="f1-card">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
          <h3 className="f1-card-title" style={{ margin: 0 }}>
            Select {viewType === 'drivers' ? 'Drivers' : 'Teams'} to Display ({Object.keys(items).length} available)
          </h3>
          <div style={{ display: 'flex', gap: '0.5rem' }}>
            <button
              onClick={selectAll}
              style={{
                background: 'rgba(16, 185, 129, 0.2)',
                border: '1px solid #10b981',
                color: '#10b981',
                padding: '0.25rem 0.75rem',
                cursor: 'pointer',
                borderRadius: '4px',
                fontSize: '0.8rem'
              }}
            >
              Select All
            </button>
            <button
              onClick={selectNone}
              style={{
                background: 'rgba(239, 68, 68, 0.2)',
                border: '1px solid #ef4444',
                color: '#ef4444',
                padding: '0.25rem 0.75rem',
                cursor: 'pointer',
                borderRadius: '4px',
                fontSize: '0.8rem'
              }}
            >
              Clear All
            </button>
          </div>
        </div>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
          {Object.keys(items).map((name, index) => (
            <button
              key={name}
              onClick={() => toggleItemSelection(name)}
              style={{
                background: selectedItems.has(name) ? getColorForIndex(index) : 'rgba(255, 255, 255, 0.1)',
                border: `2px solid ${selectedItems.has(name) ? getColorForIndex(index) : 'rgba(255, 255, 255, 0.2)'}`,
                color: '#fff',
                padding: '0.5rem 1rem',
                cursor: 'pointer',
                borderRadius: '20px',
                fontSize: '0.9rem',
                fontWeight: selectedItems.has(name) ? '600' : '400'
              }}
            >
              {name}
            </button>
          ))}
        </div>
        <div style={{ marginTop: '1rem', fontSize: '0.8rem', color: '#ccc' }}>
          {selectedItems.size} of {Object.keys(items).length} {viewType === 'drivers' ? 'drivers' : 'teams'} selected
        </div>
      </div>

      {/* Position Chart */}
      <div className="f1-card">
        <h3 className="f1-card-title">📊 Championship Position Over Time</h3>
        {renderPositionChart()}
      </div>

      {/* Points Chart */}
      <div className="f1-card">
        <h3 className="f1-card-title">🏆 Points Accumulation</h3>
        {renderPointsChart()}
      </div>

      {/* Legend */}
      <div className="f1-card">
        <h3 className="f1-card-title">🎨 Legend</h3>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '1rem' }}>
          {Object.keys(items)
            .filter(name => selectedItems.has(name))
            .map((name, index) => (
              <div key={name} style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <div
                  style={{
                    width: '20px',
                    height: '4px',
                    background: getColorForIndex(index),
                    borderRadius: '2px'
                  }}
                />
                <span style={{ fontSize: '0.9rem' }}>{name}</span>
                {items[name].length > 0 && (
                  <span style={{ 
                    fontSize: '0.8rem', 
                    color: '#ccc',
                    marginLeft: '0.5rem'
                  }}>
                    {items[name][items[name].length - 1].points} pts
                  </span>
                )}
              </div>
            ))}
        </div>
      </div>
    </div>
  );
};

export default StandingsProgressionPage;