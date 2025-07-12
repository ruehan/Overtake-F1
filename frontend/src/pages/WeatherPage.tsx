import React, { useState } from 'react';
import WeatherWidget from '../components/Weather/WeatherWidget';
import WeatherChart from '../components/Weather/WeatherChart';
import TireStrategyPanel from '../components/Weather/TireStrategyPanel';
import './WeatherPage.css';

const WeatherPage: React.FC = () => {
  const [sessionKey, setSessionKey] = useState(9222);
  const [chartHours, setChartHours] = useState(3);
  const [activeTab, setActiveTab] = useState<'overview' | 'trends' | 'strategy'>('overview');

  return (
    <div className="weather-page">
      <div className="weather-page-header">
        <div className="header-content">
          <h1>Weather Impact Analysis</h1>
          <p>Real-time weather conditions and their impact on race strategy</p>
        </div>
        
        <div className="weather-controls">
          <div className="control-group">
            <label htmlFor="session-select">Session:</label>
            <select 
              id="session-select"
              value={sessionKey} 
              onChange={(e) => setSessionKey(Number(e.target.value))}
              className="session-select"
            >
              <option value={9222}>Current Session (9222)</option>
              <option value={9221}>Previous Session (9221)</option>
              <option value={9220}>Practice Session (9220)</option>
            </select>
          </div>
          
          <div className="control-group">
            <label htmlFor="hours-select">Trend Period:</label>
            <select 
              id="hours-select"
              value={chartHours} 
              onChange={(e) => setChartHours(Number(e.target.value))}
              className="hours-select"
            >
              <option value={1}>1 Hour</option>
              <option value={3}>3 Hours</option>
              <option value={6}>6 Hours</option>
              <option value={12}>12 Hours</option>
            </select>
          </div>
        </div>
      </div>

      <div className="weather-tabs">
        <button
          className={`tab-button ${activeTab === 'overview' ? 'active' : ''}`}
          onClick={() => setActiveTab('overview')}
        >
          <span className="tab-icon">🌤️</span>
          Current Conditions
        </button>
        <button
          className={`tab-button ${activeTab === 'trends' ? 'active' : ''}`}
          onClick={() => setActiveTab('trends')}
        >
          <span className="tab-icon">📈</span>
          Weather Trends
        </button>
        <button
          className={`tab-button ${activeTab === 'strategy' ? 'active' : ''}`}
          onClick={() => setActiveTab('strategy')}
        >
          <span className="tab-icon">🏁</span>
          Tire Strategy
        </button>
      </div>

      <div className="weather-content">
        {activeTab === 'overview' && (
          <div className="overview-tab">
            <div className="overview-grid">
              <div className="widget-section">
                <WeatherWidget 
                  sessionKey={sessionKey} 
                  showDetails={true}
                />
              </div>
              
              <div className="summary-section">
                <div className="weather-summary-card">
                  <h3>🎯 Key Insights</h3>
                  <div className="insights-list">
                    <div className="insight-item">
                      <span className="insight-icon">🌡️</span>
                      <div className="insight-content">
                        <strong>Temperature Impact</strong>
                        <p>Track temperature affects tire performance and degradation rates significantly.</p>
                      </div>
                    </div>
                    
                    <div className="insight-item">
                      <span className="insight-icon">💨</span>
                      <div className="insight-content">
                        <strong>Wind Conditions</strong>
                        <p>Wind speed and direction can affect aerodynamics and fuel consumption.</p>
                      </div>
                    </div>
                    
                    <div className="insight-item">
                      <span className="insight-icon">🌧️</span>
                      <div className="insight-content">
                        <strong>Rain Probability</strong>
                        <p>Monitor humidity levels and pressure changes for rain prediction.</p>
                      </div>
                    </div>
                    
                    <div className="insight-item">
                      <span className="insight-icon">🏎️</span>
                      <div className="insight-content">
                        <strong>Race Strategy</strong>
                        <p>Weather conditions directly influence optimal tire compound selection.</p>
                      </div>
                    </div>
                  </div>
                </div>
                
                <div className="quick-stats-card">
                  <h3>📊 Quick Stats</h3>
                  <div className="quick-stats-grid">
                    <div className="stat-box">
                      <div className="stat-icon">⏱️</div>
                      <div className="stat-info">
                        <div className="stat-label">Update Frequency</div>
                        <div className="stat-value">30 seconds</div>
                      </div>
                    </div>
                    
                    <div className="stat-box">
                      <div className="stat-icon">🎯</div>
                      <div className="stat-info">
                        <div className="stat-label">Prediction Accuracy</div>
                        <div className="stat-value">95%</div>
                      </div>
                    </div>
                    
                    <div className="stat-box">
                      <div className="stat-icon">📡</div>
                      <div className="stat-info">
                        <div className="stat-label">Data Sources</div>
                        <div className="stat-value">OpenF1 API</div>
                      </div>
                    </div>
                    
                    <div className="stat-box">
                      <div className="stat-icon">🔄</div>
                      <div className="stat-info">
                        <div className="stat-label">Real-time</div>
                        <div className="stat-value">Live</div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'trends' && (
          <div className="trends-tab">
            <WeatherChart 
              sessionKey={sessionKey} 
              hours={chartHours}
              showMetrics={['air_temperature', 'track_temperature', 'humidity', 'rainfall']}
            />
            
            <div className="trends-insights">
              <div className="insights-card">
                <h3>📈 Trend Analysis</h3>
                <div className="trend-explanations">
                  <div className="trend-item">
                    <strong>🌡️ Temperature Trends:</strong>
                    <p>Track temperature typically rises throughout the day due to sun exposure and cars running. Watch for sudden drops that might indicate changing weather.</p>
                  </div>
                  
                  <div className="trend-item">
                    <strong>💧 Humidity Patterns:</strong>
                    <p>Rising humidity often precedes rain. Values above 80% significantly increase the probability of precipitation.</p>
                  </div>
                  
                  <div className="trend-item">
                    <strong>🌪️ Pressure Changes:</strong>
                    <p>Falling barometric pressure is a strong indicator of approaching weather systems and potential rain.</p>
                  </div>
                  
                  <div className="trend-item">
                    <strong>💨 Wind Variations:</strong>
                    <p>Consistent wind patterns help teams plan aerodynamic setups, while sudden changes can affect lap times.</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'strategy' && (
          <div className="strategy-tab">
            <TireStrategyPanel sessionKey={sessionKey} />
            
            <div className="strategy-insights">
              <div className="strategy-tips-card">
                <h3>💡 Strategy Tips</h3>
                <div className="tips-grid">
                  <div className="tip-item">
                    <div className="tip-icon">🔴</div>
                    <div className="tip-content">
                      <strong>Soft Tires</strong>
                      <p>Best for short stints and maximum grip. Ideal in cooler conditions (20-35°C track temp).</p>
                    </div>
                  </div>
                  
                  <div className="tip-item">
                    <div className="tip-icon">🟡</div>
                    <div className="tip-content">
                      <strong>Medium Tires</strong>
                      <p>Balanced performance for most conditions. Good compromise between grip and durability.</p>
                    </div>
                  </div>
                  
                  <div className="tip-item">
                    <div className="tip-icon">⚪</div>
                    <div className="tip-content">
                      <strong>Hard Tires</strong>
                      <p>Long stint specialists. Excel in hot conditions (45°C+ track temp) with lower degradation.</p>
                    </div>
                  </div>
                  
                  <div className="tip-item">
                    <div className="tip-icon">🟢</div>
                    <div className="tip-content">
                      <strong>Intermediates</strong>
                      <p>Crossover compound for damp conditions. Perfect for light rain or drying track.</p>
                    </div>
                  </div>
                  
                  <div className="tip-item">
                    <div className="tip-icon">🔵</div>
                    <div className="tip-content">
                      <strong>Full Wet</strong>
                      <p>Heavy rain specialists. Essential when rainfall exceeds 2mm or standing water present.</p>
                    </div>
                  </div>
                  
                  <div className="tip-item">
                    <div className="tip-icon">⚡</div>
                    <div className="tip-content">
                      <strong>Quick Changes</strong>
                      <p>Weather can change rapidly. Monitor trends and be ready for strategy adjustments.</p>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default WeatherPage;