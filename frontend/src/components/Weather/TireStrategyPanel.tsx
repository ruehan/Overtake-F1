import React, { useState, useEffect } from 'react';
import { useWebSocket } from '../../contexts/WebSocketContext';
import './TireStrategyPanel.css';

interface TireStrategy {
  compound: string;
  confidence: number;
  reasoning: string[];
  risk_factors: string[];
  expected_degradation: string;
}

interface WeatherCondition {
  air_temperature: number;
  track_temperature: number;
  humidity: number;
  pressure: number;
  wind_speed: number;
  rainfall: number;
}

interface TireStrategyData {
  current_weather: WeatherCondition;
  tire_strategy: TireStrategy;
  timestamp: string;
}

interface TirePrediction {
  compound: string;
  performance_window: number; // laps
  optimal_conditions: string[];
  degradation_rate: string;
  pit_window: {
    earliest: number;
    optimal: number;
    latest: number;
  };
}

interface TireStrategyPanelProps {
  sessionKey?: number;
}

const TireStrategyPanel: React.FC<TireStrategyPanelProps> = ({ 
  sessionKey = 9222 
}) => {
  const [strategyData, setStrategyData] = useState<TireStrategyData | null>(null);
  const [predictions, setPredictions] = useState<TirePrediction[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);
  const { isConnected } = useWebSocket();

  // Tire compound data
  const tireCompounds = {
    soft: {
      icon: '🔴',
      name: 'Soft',
      color: '#ff4757',
      typical_laps: 15,
      optimal_temp: [25, 45],
      advantages: ['Maximum grip', 'Fast lap times', 'Quick warm-up'],
      disadvantages: ['High degradation', 'Short stint length']
    },
    medium: {
      icon: '🟡',
      name: 'Medium',
      color: '#ffa502',
      typical_laps: 25,
      optimal_temp: [30, 55],
      advantages: ['Balanced performance', 'Moderate degradation', 'Versatile'],
      disadvantages: ['Compromised peak grip', 'Slower warm-up than soft']
    },
    hard: {
      icon: '⚪',
      name: 'Hard',
      color: '#747d8c',
      typical_laps: 35,
      optimal_temp: [40, 70],
      advantages: ['Low degradation', 'Long stint length', 'Heat resistant'],
      disadvantages: ['Slow warm-up', 'Lower peak grip', 'Poor in cool conditions']
    },
    intermediate: {
      icon: '🟢',
      name: 'Intermediate',
      color: '#2ed573',
      typical_laps: 20,
      optimal_temp: [10, 45],
      advantages: ['Damp conditions', 'Crossover performance', 'Aquaplaning resistance'],
      disadvantages: ['Poor in fully dry/wet', 'Overheats quickly in dry']
    },
    full_wet: {
      icon: '🔵',
      name: 'Full Wet',
      color: '#3742fa',
      typical_laps: 30,
      optimal_temp: [5, 40],
      advantages: ['Heavy rain', 'Maximum water clearance', 'Aquaplaning protection'],
      disadvantages: ['Terrible in dry', 'Slow lap times', 'High rolling resistance']
    }
  };

  useEffect(() => {
    fetchStrategyData();
    const interval = setInterval(fetchStrategyData, 45000); // Update every 45 seconds
    return () => clearInterval(interval);
  }, [sessionKey]);

  useEffect(() => {
    if (strategyData) {
      generateTirePredictions();
    }
  }, [strategyData]);

  const fetchStrategyData = async () => {
    try {
      setError(null);
      const response = await fetch(
        `http://localhost:8000/api/v1/weather/tire-strategy?session_key=${sessionKey}`
      );
      
      if (!response.ok) {
        throw new Error('Failed to fetch tire strategy data');
      }
      
      const data = await response.json();
      
      // Check if API returned an error
      if (data.error) {
        setError(data.error);
        setStrategyData(null);
        setLoading(false);
        return;
      }
      setStrategyData(data);
      setLastUpdated(new Date());
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
      console.error('Error fetching tire strategy:', err);
    } finally {
      setLoading(false);
    }
  };

  const generateTirePredictions = () => {
    if (!strategyData) return;

    const { current_weather } = strategyData;
    const predictions: TirePrediction[] = [];

    // Generate predictions for all available compounds
    Object.entries(tireCompounds).forEach(([compound, config]) => {
      const prediction = calculateTirePerformance(compound, current_weather, config);
      predictions.push(prediction);
    });

    // Sort by suitability (combination of performance and conditions)
    predictions.sort((a, b) => {
      const scoreA = calculateSuitabilityScore(a, current_weather);
      const scoreB = calculateSuitabilityScore(b, current_weather);
      return scoreB - scoreA;
    });

    setPredictions(predictions);
  };

  const calculateTirePerformance = (
    compound: string, 
    weather: WeatherCondition, 
    config: any
  ): TirePrediction => {
    const trackTemp = weather.track_temperature;
    const rainfall = weather.rainfall;
    
    let performance_window = config.typical_laps;
    let degradation_rate = 'medium';
    let optimal_conditions: string[] = [];

    // Adjust based on conditions
    if (rainfall > 0) {
      if (compound === 'intermediate' || compound === 'full_wet') {
        optimal_conditions.push('wet conditions');
        if (compound === 'full_wet' && rainfall > 2) {
          performance_window += 10;
          degradation_rate = 'low';
        }
      } else {
        performance_window -= 10;
        degradation_rate = 'high';
        optimal_conditions.push('dry conditions only');
      }
    } else {
      // Dry conditions
      const [minTemp, maxTemp] = config.optimal_temp;
      if (trackTemp >= minTemp && trackTemp <= maxTemp) {
        optimal_conditions.push('optimal temperature');
        degradation_rate = 'low';
      } else if (trackTemp > maxTemp) {
        if (compound === 'hard') {
          optimal_conditions.push('high temperature');
          degradation_rate = 'low';
        } else {
          performance_window *= 0.7;
          degradation_rate = 'high';
          optimal_conditions.push('overheating risk');
        }
      } else {
        if (compound === 'soft') {
          optimal_conditions.push('cool temperature');
        } else {
          performance_window *= 0.8;
          degradation_rate = 'medium';
          optimal_conditions.push('slow warm-up');
        }
      }
    }

    // Calculate pit windows
    const earliest = Math.max(5, Math.floor(performance_window * 0.6));
    const optimal = Math.floor(performance_window * 0.8);
    const latest = Math.floor(performance_window * 1.2);

    return {
      compound,
      performance_window: Math.max(5, Math.floor(performance_window)),
      optimal_conditions,
      degradation_rate,
      pit_window: { earliest, optimal, latest }
    };
  };

  const calculateSuitabilityScore = (prediction: TirePrediction, weather: WeatherCondition): number => {
    let score = 0;
    
    // Base score from performance window
    score += prediction.performance_window;
    
    // Bonus for optimal conditions
    score += prediction.optimal_conditions.length * 10;
    
    // Penalty for high degradation
    if (prediction.degradation_rate === 'high') score -= 20;
    if (prediction.degradation_rate === 'low') score += 10;
    
    // Weather-specific bonuses
    if (weather.rainfall > 0) {
      if (prediction.compound === 'intermediate' || prediction.compound === 'full_wet') {
        score += 30;
      }
    } else {
      if (prediction.compound !== 'intermediate' && prediction.compound !== 'full_wet') {
        score += 20;
      }
    }
    
    return score;
  };

  const getTireIcon = (compound: string): string => {
    return tireCompounds[compound as keyof typeof tireCompounds]?.icon || '⚫';
  };

  const getTireColor = (compound: string): string => {
    return tireCompounds[compound as keyof typeof tireCompounds]?.color || '#666';
  };

  const getDegradationColor = (rate: string): string => {
    switch (rate) {
      case 'low': return '#28a745';
      case 'medium': return '#ffc107';
      case 'high': return '#dc3545';
      default: return '#6c757d';
    }
  };

  const generateMockTireData = (): TireStrategyData => {
    return {
      current_weather: {
        air_temperature: 25.5,
        track_temperature: 38.2,
        humidity: 65,
        pressure: 1013.2,
        wind_speed: 12.5,
        rainfall: 0
      },
      tire_strategy: {
        compound: 'medium',
        confidence: 0.85,
        reasoning: [
          'Moderate track temperature (38.2°C)',
          'Dry conditions expected',
          'Small temperature delta - consistent conditions'
        ],
        risk_factors: [],
        expected_degradation: 'medium'
      },
      timestamp: new Date().toISOString()
    };
  };

  if (loading) {
    return (
      <div className="tire-strategy-panel loading">
        <div className="loading-spinner">🏎️</div>
        <p>Analyzing tire strategy...</p>
      </div>
    );
  }

  if (error || !strategyData) {
    return (
      <div className="tire-strategy-panel error">
        <div className="error-icon">🏁</div>
        <h3>No Tire Strategy Data</h3>
        <p className="error-message">{error || 'Unable to analyze tire strategy for this session'}</p>
        <div className="error-details">
          <p>Tire strategy analysis requires:</p>
          <ul>
            <li>Current weather conditions data</li>
            <li>Track temperature information</li>
            <li>Recent session data</li>
          </ul>
        </div>
        <button onClick={fetchStrategyData} className="retry-btn">
          🔄 Retry
        </button>
      </div>
    );
  }

  const recommendedCompound = strategyData.tire_strategy.compound;
  const recommendedConfig = tireCompounds[recommendedCompound as keyof typeof tireCompounds];

  return (
    <div className="tire-strategy-panel">
      <div className="panel-header">
        <div className="panel-title">
          <span className="tire-icon">🏁</span>
          <h3>Tire Strategy Analysis</h3>
        </div>
        <div className="connection-status">
          <span className={`status-dot ${isConnected ? 'connected' : 'disconnected'}`}></span>
          {lastUpdated && (
            <span className="last-updated">
              Updated {lastUpdated.toLocaleTimeString()}
            </span>
          )}
        </div>
      </div>

      {/* Current Recommendation */}
      <div className="current-recommendation">
        <h4>🎯 Current Recommendation</h4>
        <div className="recommendation-card">
          <div className="tire-header">
            <span className="tire-icon-large" style={{ color: getTireColor(recommendedCompound) }}>
              {getTireIcon(recommendedCompound)}
            </span>
            <div className="tire-info">
              <div className="tire-name">{recommendedConfig?.name} Compound</div>
              <div className="confidence">
                Confidence: {Math.round(strategyData.tire_strategy.confidence * 100)}%
              </div>
            </div>
          </div>
          
          <div className="reasoning-section">
            <strong>Why this choice:</strong>
            <ul className="reasoning-list">
              {strategyData.tire_strategy.reasoning.map((reason, index) => (
                <li key={index}>{reason}</li>
              ))}
            </ul>
          </div>

          {strategyData.tire_strategy.risk_factors.length > 0 && (
            <div className="risk-section">
              <strong>⚠️ Risk Factors:</strong>
              <ul className="risk-list">
                {strategyData.tire_strategy.risk_factors.map((risk, index) => (
                  <li key={index}>{risk}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      </div>

      {/* All Tire Predictions */}
      <div className="predictions-section">
        <h4>📊 All Compound Analysis</h4>
        <div className="predictions-grid">
          {predictions.map((prediction, index) => {
            const config = tireCompounds[prediction.compound as keyof typeof tireCompounds];
            const isRecommended = prediction.compound === recommendedCompound;
            
            return (
              <div 
                key={prediction.compound} 
                className={`prediction-card ${isRecommended ? 'recommended' : ''}`}
              >
                <div className="card-header">
                  <span 
                    className="compound-icon"
                    style={{ color: getTireColor(prediction.compound) }}
                  >
                    {getTireIcon(prediction.compound)}
                  </span>
                  <div className="compound-name">{config?.name}</div>
                  {isRecommended && <div className="recommended-badge">RECOMMENDED</div>}
                </div>
                
                <div className="prediction-stats">
                  <div className="stat-item">
                    <span className="stat-label">Performance Window</span>
                    <span className="stat-value">{prediction.performance_window} laps</span>
                  </div>
                  
                  <div className="stat-item">
                    <span className="stat-label">Degradation</span>
                    <span 
                      className="stat-value degradation"
                      style={{ color: getDegradationColor(prediction.degradation_rate) }}
                    >
                      {prediction.degradation_rate}
                    </span>
                  </div>
                  
                  <div className="stat-item">
                    <span className="stat-label">Pit Window</span>
                    <span className="stat-value">
                      L{prediction.pit_window.optimal}
                      <span className="pit-range">
                        ({prediction.pit_window.earliest}-{prediction.pit_window.latest})
                      </span>
                    </span>
                  </div>
                </div>
                
                <div className="conditions-list">
                  {prediction.optimal_conditions.map((condition, idx) => (
                    <div key={idx} className="condition-tag">
                      {condition}
                    </div>
                  ))}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Current Weather Summary */}
      <div className="weather-summary">
        <h4>🌤️ Current Conditions</h4>
        <div className="weather-grid">
          <div className="weather-item">
            <span className="weather-label">Track Temp</span>
            <span className="weather-value">
              {Math.round(strategyData.current_weather.track_temperature)}°C
            </span>
          </div>
          <div className="weather-item">
            <span className="weather-label">Air Temp</span>
            <span className="weather-value">
              {Math.round(strategyData.current_weather.air_temperature)}°C
            </span>
          </div>
          <div className="weather-item">
            <span className="weather-label">Humidity</span>
            <span className="weather-value">
              {Math.round(strategyData.current_weather.humidity)}%
            </span>
          </div>
          <div className="weather-item">
            <span className="weather-label">Rainfall</span>
            <span className="weather-value">
              {strategyData.current_weather.rainfall}mm
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};

export default TireStrategyPanel;