import React, { useState, useEffect } from 'react';
import { useWebSocket } from '../../contexts/WebSocketContext';
import './WeatherWidget.css';

interface WeatherCondition {
  air_temperature: number;
  track_temperature: number;
  humidity: number;
  pressure: number;
  wind_speed: number;
  wind_direction?: number;
  rainfall: number;
}

interface TireRecommendation {
  compound: string;
  confidence: number;
  reasoning: string[];
  risk_factors: string[];
  expected_degradation: string;
}

interface WeatherData {
  current_conditions: WeatherCondition;
  tire_recommendation: TireRecommendation;
  race_impact: {
    pit_strategy_impact: string;
    safety_car_probability: string;
    tire_degradation_factor: number;
    lap_time_impact: number;
    strategic_considerations: string[];
  };
  trends: {
    [key: string]: {
      type: string;
      rate: number;
      confidence: number;
    };
  };
}

interface WeatherWidgetProps {
  sessionKey?: number;
  showDetails?: boolean;
}

const WeatherWidget: React.FC<WeatherWidgetProps> = ({ 
  sessionKey = 9222, 
  showDetails = true 
}) => {
  const [weatherData, setWeatherData] = useState<WeatherData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);
  const { isConnected } = useWebSocket();

  useEffect(() => {
    fetchWeatherData();
    const interval = setInterval(fetchWeatherData, 30000); // Update every 30 seconds
    return () => clearInterval(interval);
  }, [sessionKey]);

  const fetchWeatherData = async () => {
    try {
      setError(null);
      const response = await fetch(`http://localhost:8000/api/v1/weather/analysis?session_key=${sessionKey}`);
      
      if (!response.ok) {
        throw new Error('Failed to fetch weather data');
      }
      
      const data = await response.json();
      
      // Check if API returned an error
      if (data.error) {
        setError(data.error);
        setWeatherData(null);
      } else {
        setWeatherData(data);
        setLastUpdated(new Date());
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
      console.error('Error fetching weather data:', err);
    } finally {
      setLoading(false);
    }
  };

  const getWeatherIcon = (condition: WeatherCondition): string => {
    if (condition.rainfall > 2) return '🌧️';
    if (condition.rainfall > 0) return '🌦️';
    if (condition.humidity > 80) return '☁️';
    if (condition.air_temperature > 30) return '☀️';
    if (condition.air_temperature < 15) return '🌥️';
    return '⛅';
  };

  const getTireIcon = (compound: string): string => {
    switch (compound) {
      case 'soft': return '🔴';
      case 'medium': return '🟡';
      case 'hard': return '⚪';
      case 'intermediate': return '🟢';
      case 'full_wet': return '🔵';
      default: return '⚫';
    }
  };

  const getTrendIcon = (trend: string): string => {
    switch (trend) {
      case 'rising': return '↗️';
      case 'falling': return '↘️';
      case 'stable': return '➡️';
      default: return '➡️';
    }
  };

  const formatTemperature = (temp: number): string => {
    return `${Math.round(temp)}°C`;
  };

  const formatWindDirection = (direction?: number): string => {
    if (!direction) return 'N/A';
    const directions = ['N', 'NNE', 'NE', 'ENE', 'E', 'ESE', 'SE', 'SSE', 
                      'S', 'SSW', 'SW', 'WSW', 'W', 'WNW', 'NW', 'NNW'];
    const index = Math.round(direction / 22.5) % 16;
    return directions[index];
  };

  if (loading) {
    return (
      <div className="weather-widget loading">
        <div className="loading-spinner">🌀</div>
        <p>Loading weather data...</p>
      </div>
    );
  }

  if (error || !weatherData) {
    return (
      <div className="weather-widget error">
        <div className="error-icon">⚠️</div>
        <h3>No Weather Data Available</h3>
        <p className="error-message">{error || 'Weather data unavailable for this session'}</p>
        <div className="error-details">
          <p>Possible reasons:</p>
          <ul>
            <li>This session might not have weather data</li>
            <li>The session might be too old</li>
            <li>OpenF1 API might be temporarily unavailable</li>
          </ul>
        </div>
        <button onClick={fetchWeatherData} className="retry-btn">
          🔄 Try Again
        </button>
      </div>
    );
  }

  const { current_conditions, tire_recommendation, race_impact, trends } = weatherData;

  return (
    <div className="weather-widget">
      <div className="weather-header">
        <div className="weather-title">
          <span className="weather-icon">{getWeatherIcon(current_conditions)}</span>
          <h3>Weather Conditions</h3>
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

      <div className="weather-content">
        {/* Current Conditions */}
        <div className="conditions-section">
          <div className="condition-grid">
            <div className="condition-item">
              <span className="condition-label">Air Temp</span>
              <span className="condition-value">
                {formatTemperature(current_conditions.air_temperature)}
                {trends.air_temperature && (
                  <span className="trend-indicator">
                    {getTrendIcon(trends.air_temperature.type)}
                  </span>
                )}
              </span>
            </div>
            
            <div className="condition-item">
              <span className="condition-label">Track Temp</span>
              <span className="condition-value">
                {formatTemperature(current_conditions.track_temperature)}
                {trends.track_temperature && (
                  <span className="trend-indicator">
                    {getTrendIcon(trends.track_temperature.type)}
                  </span>
                )}
              </span>
            </div>
            
            <div className="condition-item">
              <span className="condition-label">Humidity</span>
              <span className="condition-value">{Math.round(current_conditions.humidity)}%</span>
            </div>
            
            <div className="condition-item">
              <span className="condition-label">Wind</span>
              <span className="condition-value">
                {Math.round(current_conditions.wind_speed)} km/h
                <span className="wind-direction">
                  {formatWindDirection(current_conditions.wind_direction)}
                </span>
              </span>
            </div>
          </div>

          {current_conditions.rainfall > 0 && (
            <div className="rainfall-alert">
              <span className="rain-icon">🌧️</span>
              <span>Rainfall: {current_conditions.rainfall}mm</span>
            </div>
          )}
        </div>

        {showDetails && (
          <>
            {/* Tire Recommendation */}
            <div className="tire-section">
              <h4>Tire Strategy</h4>
              <div className="tire-recommendation">
                <div className="tire-compound">
                  <span className="tire-icon">{getTireIcon(tire_recommendation.compound)}</span>
                  <span className="compound-name">
                    {tire_recommendation.compound.replace('_', ' ')}
                  </span>
                  <span className="confidence-badge">
                    {Math.round(tire_recommendation.confidence * 100)}%
                  </span>
                </div>
                
                <div className="tire-details">
                  <div className="reasoning">
                    {tire_recommendation.reasoning.map((reason, index) => (
                      <div key={index} className="reason-item">
                        ✓ {reason}
                      </div>
                    ))}
                  </div>
                  
                  {tire_recommendation.risk_factors.length > 0 && (
                    <div className="risk-factors">
                      <strong>Risk Factors:</strong>
                      {tire_recommendation.risk_factors.map((risk, index) => (
                        <div key={index} className="risk-item">
                          ⚠️ {risk}
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            </div>

            {/* Race Impact */}
            <div className="impact-section">
              <h4>Race Impact</h4>
              <div className="impact-grid">
                <div className="impact-item">
                  <span className="impact-label">Safety Car Risk</span>
                  <span className={`impact-value risk-${race_impact.safety_car_probability}`}>
                    {race_impact.safety_car_probability}
                  </span>
                </div>
                
                <div className="impact-item">
                  <span className="impact-label">Tire Degradation</span>
                  <span className="impact-value">
                    {race_impact.tire_degradation_factor}x
                  </span>
                </div>
                
                {race_impact.lap_time_impact > 0 && (
                  <div className="impact-item">
                    <span className="impact-label">Lap Time Impact</span>
                    <span className="impact-value">
                      +{race_impact.lap_time_impact}s
                    </span>
                  </div>
                )}
              </div>
              
              {race_impact.strategic_considerations.length > 0 && (
                <div className="strategic-notes">
                  <strong>Strategic Considerations:</strong>
                  {race_impact.strategic_considerations.map((note, index) => (
                    <div key={index} className="strategy-note">
                      📋 {note}
                    </div>
                  ))}
                </div>
              )}
            </div>
          </>
        )}
      </div>
    </div>
  );
};

export default WeatherWidget;