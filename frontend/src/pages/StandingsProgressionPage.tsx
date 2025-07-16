import React, { useState, useEffect } from 'react';
import { useLanguage } from '../contexts/LanguageContext';
import { API_ENDPOINTS } from '../config/api';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  ChartOptions,
} from 'chart.js';
import { Line } from 'react-chartjs-2';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend
);

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
  const { t } = useLanguage();
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
      console.log('🔄 Fetching progression data from:', API_ENDPOINTS.standingsProgression(selectedYear));
      const response = await fetch(API_ENDPOINTS.standingsProgression(selectedYear));
      console.log('📥 Progression response:', response.status, response.statusText);
      if (!response.ok) {
        throw new Error(`Failed to fetch progression data: ${response.status} ${response.statusText}`);
      }
      const data = await response.json();
      console.log('✅ Progression data:', data);
      setProgression(data.progression);
      
      // 자동으로 상위 8명/팀 선택
      if (data.progression) {
        const items = viewType === 'drivers' ? data.progression.driver_progression : data.progression.constructor_progression;
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
    
    const datasets = Object.entries(items)
      .filter(([name]) => selectedItems.has(name))
      .map(([name, data], index) => {
        const color = getColorForIndex(index);
        return {
          label: name,
          data: data.map(point => point.position),
          borderColor: color,
          backgroundColor: color + '20',
          pointBackgroundColor: color,
          pointBorderColor: '#fff',
          pointBorderWidth: 2,
          pointRadius: 6,
          pointHoverRadius: 8,
          borderWidth: 3,
          tension: 0.1,
        };
      });

    const chartData = {
      labels: progression.race_labels,
      datasets: datasets,
    };

    const options: ChartOptions<'line'> = {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: 'top' as const,
          labels: {
            color: '#fff',
            usePointStyle: true,
            pointStyle: 'circle',
            padding: 20,
            font: {
              size: 12,
            },
          },
        },
        title: {
          display: true,
          text: t('progression.championshipPositionProgress'),
          color: '#ff6b35',
          font: {
            size: 16,
            weight: 'bold',
          },
        },
        tooltip: {
          mode: 'index',
          intersect: false,
          backgroundColor: 'rgba(0, 0, 0, 0.8)',
          titleColor: '#fff',
          bodyColor: '#fff',
          borderColor: '#ff6b35',
          borderWidth: 1,
          callbacks: {
            title: (context) => {
              return `${context[0].label}`;
            },
            label: (context) => {
              const datasetLabel = context.dataset.label || '';
              const position = context.parsed.y;
              return `${datasetLabel}: P${position}`;
            },
          },
        },
      },
      scales: {
        x: {
          display: true,
          title: {
            display: true,
            text: 'Race',
            color: '#ccc',
          },
          ticks: {
            color: '#ccc',
            maxRotation: 45,
          },
          grid: {
            color: 'rgba(255, 255, 255, 0.1)',
          },
        },
        y: {
          display: true,
          title: {
            display: true,
            text: 'Position',
            color: '#ccc',
          },
          reverse: true,
          min: 1,
          max: 20,
          ticks: {
            color: '#ccc',
            stepSize: 1,
            callback: (value) => `P${value}`,
          },
          grid: {
            color: 'rgba(255, 255, 255, 0.1)',
          },
        },
      },
      interaction: {
        mode: 'nearest',
        axis: 'x',
        intersect: false,
      },
    };

    return (
      <div style={{ height: '500px', marginBottom: '2rem' }}>
        <Line data={chartData} options={options} />
      </div>
    );
  };

  const renderPointsChart = () => {
    if (!progression) return null;

    const items = viewType === 'drivers' ? progression.driver_progression : progression.constructor_progression;
    
    const datasets = Object.entries(items)
      .filter(([name]) => selectedItems.has(name))
      .map(([name, data], index) => {
        const color = getColorForIndex(index);
        return {
          label: name,
          data: data.map(point => point.points),
          borderColor: color,
          backgroundColor: color + '20',
          pointBackgroundColor: color,
          pointBorderColor: '#fff',
          pointBorderWidth: 2,
          pointRadius: 6,
          pointHoverRadius: 8,
          borderWidth: 3,
          tension: 0.1,
          fill: false,
        };
      });

    const chartData = {
      labels: progression.race_labels,
      datasets: datasets,
    };

    const options: ChartOptions<'line'> = {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: 'top' as const,
          labels: {
            color: '#fff',
            usePointStyle: true,
            pointStyle: 'circle',
            padding: 20,
            font: {
              size: 12,
            },
          },
        },
        title: {
          display: true,
          text: t('progression.championshipPointsProgress'),
          color: '#ff6b35',
          font: {
            size: 16,
            weight: 'bold',
          },
        },
        tooltip: {
          mode: 'index',
          intersect: false,
          backgroundColor: 'rgba(0, 0, 0, 0.8)',
          titleColor: '#fff',
          bodyColor: '#fff',
          borderColor: '#ff6b35',
          borderWidth: 1,
          callbacks: {
            title: (context) => {
              return `${context[0].label}`;
            },
            label: (context) => {
              const datasetLabel = context.dataset.label || '';
              const points = context.parsed.y;
              return `${datasetLabel}: ${points} pts`;
            },
            afterBody: (context) => {
              if (context.length > 1) {
                const sortedContext = [...context].sort((a, b) => b.parsed.y - a.parsed.y);
                return ['', 'Ranking at this point:', ...sortedContext.map((ctx, idx) => `${idx + 1}. ${ctx.dataset.label}: ${ctx.parsed.y} pts`)];
              }
              return [];
            },
          },
        },
      },
      scales: {
        x: {
          display: true,
          title: {
            display: true,
            text: 'Race',
            color: '#ccc',
          },
          ticks: {
            color: '#ccc',
            maxRotation: 45,
          },
          grid: {
            color: 'rgba(255, 255, 255, 0.1)',
          },
        },
        y: {
          display: true,
          title: {
            display: true,
            text: 'Points',
            color: '#ccc',
          },
          beginAtZero: true,
          ticks: {
            color: '#ccc',
            callback: (value) => `${value} pts`,
          },
          grid: {
            color: 'rgba(255, 255, 255, 0.1)',
          },
        },
      },
      interaction: {
        mode: 'nearest',
        axis: 'x',
        intersect: false,
      },
    };

    return (
      <div style={{ height: '500px', marginBottom: '2rem' }}>
        <Line data={chartData} options={options} />
      </div>
    );
  };

  if (loading) return <div className="f1-loading">{t('common.loading')} {t('nav.progression')}...</div>;
  if (error) return <div className="f1-error">{t('common.error')}: {error}</div>;
  if (!progression) return <div className="f1-error">No progression data available</div>;

  const items = viewType === 'drivers' ? progression.driver_progression : progression.constructor_progression;

  return (
    <div>
      <h1 className="f1-card-title">📈 {t('nav.progression')}</h1>
      
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
            {viewType === 'drivers' ? t('progression.selectDrivers') : t('progression.selectTeams')} ({Object.keys(items).length} {t('progression.available')})
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
        <h3 className="f1-card-title">📊 {t('progression.positionOverTime')}</h3>
        {renderPositionChart()}
      </div>

      {/* Points Chart */}
      <div className="f1-card">
        <h3 className="f1-card-title">🏆 {t('progression.pointsAccumulation')}</h3>
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