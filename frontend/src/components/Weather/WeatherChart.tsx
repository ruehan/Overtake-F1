import React, { useState, useEffect, useRef } from 'react';
import * as d3 from 'd3';
import { useWebSocket } from '../../contexts/WebSocketContext';
import './WeatherChart.css';

interface WeatherDataPoint {
  timestamp: string;
  air_temperature: number;
  track_temperature: number;
  humidity: number;
  pressure: number;
  wind_speed: number;
  rainfall: number;
}

interface WeatherChartProps {
  sessionKey?: number;
  hours?: number;
  showMetrics?: string[];
}

const WeatherChart: React.FC<WeatherChartProps> = ({ 
  sessionKey = 9222, 
  hours = 3,
  showMetrics = ['air_temperature', 'track_temperature', 'humidity', 'rainfall']
}) => {
  const svgRef = useRef<SVGSVGElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const [weatherData, setWeatherData] = useState<WeatherDataPoint[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [dimensions, setDimensions] = useState({ width: 800, height: 400 });
  const [selectedMetrics, setSelectedMetrics] = useState<string[]>(showMetrics);
  const { isConnected } = useWebSocket();

  // Metric configurations
  const metricConfigs = {
    air_temperature: {
      label: 'Air Temperature',
      color: '#ff6b6b',
      unit: '°C',
      scale: 'linear',
      domain: [0, 50]
    },
    track_temperature: {
      label: 'Track Temperature',
      color: '#4ecdc4',
      unit: '°C',
      scale: 'linear',
      domain: [0, 70]
    },
    humidity: {
      label: 'Humidity',
      color: '#45b7d1',
      unit: '%',
      scale: 'linear',
      domain: [0, 100]
    },
    pressure: {
      label: 'Pressure',
      color: '#96ceb4',
      unit: 'mbar',
      scale: 'linear',
      domain: [980, 1030]
    },
    wind_speed: {
      label: 'Wind Speed',
      color: '#ffeaa7',
      unit: 'km/h',
      scale: 'linear',
      domain: [0, 40]
    },
    rainfall: {
      label: 'Rainfall',
      color: '#74b9ff',
      unit: 'mm',
      scale: 'linear',
      domain: [0, 10]
    }
  };

  useEffect(() => {
    fetchWeatherData();
    const interval = setInterval(fetchWeatherData, 60000); // Update every minute
    return () => clearInterval(interval);
  }, [sessionKey, hours]);

  useEffect(() => {
    const handleResize = () => {
      if (containerRef.current) {
        const rect = containerRef.current.getBoundingClientRect();
        setDimensions({
          width: rect.width,
          height: Math.max(rect.height, 400)
        });
      }
    };

    window.addEventListener('resize', handleResize);
    handleResize();

    return () => window.removeEventListener('resize', handleResize);
  }, []);

  useEffect(() => {
    if (weatherData.length > 0 && !loading) {
      drawChart();
    }
  }, [weatherData, dimensions, selectedMetrics, loading]);

  const fetchWeatherData = async () => {
    try {
      setError(null);
      const response = await fetch(
        `http://localhost:8000/api/v1/weather?session_key=${sessionKey}`
      );
      
      if (!response.ok) {
        throw new Error('Failed to fetch weather data');
      }
      
      const data = await response.json();
      
      // Check if data is empty
      if (!data || data.length === 0) {
        setError('No weather data available for this session');
        setWeatherData([]);
        setLoading(false);
        return;
      }
      
      // Filter data to last N hours and sort by timestamp
      const cutoffTime = new Date(Date.now() - hours * 60 * 60 * 1000);
      const filteredData = data
        .filter((item: any) => {
          const timestamp = new Date(item.timestamp);
          return timestamp >= cutoffTime;
        })
        .map((item: any) => ({
          timestamp: item.timestamp,
          air_temperature: item.air_temperature || 0,
          track_temperature: item.track_temperature || 0,
          humidity: item.humidity || 0,
          pressure: item.pressure || 0,
          wind_speed: item.wind_speed || 0,
          rainfall: item.rainfall || 0
        }))
        .sort((a: WeatherDataPoint, b: WeatherDataPoint) => 
          new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime()
        );
      
      // Check if we have any data after filtering
      if (filteredData.length === 0) {
        setError(`No weather data available for the last ${hours} hours`);
      }
      
      setWeatherData(filteredData);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
      console.error('Error fetching weather data:', err);
    } finally {
      setLoading(false);
    }
  };

  const drawChart = () => {
    if (!svgRef.current || weatherData.length === 0) return;

    const svg = d3.select(svgRef.current);
    svg.selectAll('*').remove();

    const margin = { top: 20, right: 80, bottom: 60, left: 60 };
    const chartWidth = dimensions.width - margin.left - margin.right;
    const chartHeight = dimensions.height - margin.top - margin.bottom;

    const chartGroup = svg
      .append('g')
      .attr('transform', `translate(${margin.left}, ${margin.top})`);

    // Time scale
    const timeExtent = d3.extent(weatherData, d => new Date(d.timestamp)) as [Date, Date];
    const xScale = d3.scaleTime()
      .domain(timeExtent)
      .range([0, chartWidth]);

    // Create scales for each metric
    const yScales: { [key: string]: d3.ScaleLinear<number, number> } = {};
    selectedMetrics.forEach(metric => {
      const config = metricConfigs[metric as keyof typeof metricConfigs];
      if (config) {
        yScales[metric] = d3.scaleLinear()
          .domain(config.domain)
          .range([chartHeight, 0]);
      }
    });

    // Add grid lines
    const gridGroup = chartGroup.append('g').attr('class', 'grid');
    
    // Horizontal grid lines (using first metric's scale)
    if (selectedMetrics.length > 0) {
      const firstMetric = selectedMetrics[0];
      gridGroup
        .selectAll('.grid-line-horizontal')
        .data(yScales[firstMetric].ticks(6))
        .enter()
        .append('line')
        .attr('class', 'grid-line-horizontal')
        .attr('x1', 0)
        .attr('x2', chartWidth)
        .attr('y1', d => yScales[firstMetric](d))
        .attr('y2', d => yScales[firstMetric](d))
        .attr('stroke', '#f0f0f0')
        .attr('stroke-width', 1);
    }

    // Vertical grid lines
    gridGroup
      .selectAll('.grid-line-vertical')
      .data(xScale.ticks(8))
      .enter()
      .append('line')
      .attr('class', 'grid-line-vertical')
      .attr('x1', d => xScale(d))
      .attr('x2', d => xScale(d))
      .attr('y1', 0)
      .attr('y2', chartHeight)
      .attr('stroke', '#f0f0f0')
      .attr('stroke-width', 1);

    // Draw lines for each selected metric
    selectedMetrics.forEach((metric, index) => {
      const config = metricConfigs[metric as keyof typeof metricConfigs];
      if (!config || !yScales[metric]) return;

      const line = d3.line<WeatherDataPoint>()
        .x(d => xScale(new Date(d.timestamp)))
        .y(d => yScales[metric](d[metric as keyof WeatherDataPoint] as number))
        .curve(d3.curveMonotoneX);

      // Draw line
      chartGroup
        .append('path')
        .datum(weatherData)
        .attr('class', `line line-${metric}`)
        .attr('d', line)
        .attr('fill', 'none')
        .attr('stroke', config.color)
        .attr('stroke-width', 2)
        .attr('opacity', 0.8);

      // Draw dots
      chartGroup
        .selectAll(`.dot-${metric}`)
        .data(weatherData)
        .enter()
        .append('circle')
        .attr('class', `dot dot-${metric}`)
        .attr('cx', d => xScale(new Date(d.timestamp)))
        .attr('cy', d => yScales[metric](d[metric as keyof WeatherDataPoint] as number))
        .attr('r', 3)
        .attr('fill', config.color)
        .on('mouseover', function(event, d) {
          // Tooltip
          const tooltip = d3.select('body')
            .append('div')
            .attr('class', 'weather-tooltip')
            .style('position', 'absolute')
            .style('background', 'rgba(0, 0, 0, 0.8)')
            .style('color', 'white')
            .style('padding', '8px')
            .style('border-radius', '4px')
            .style('font-size', '12px')
            .style('pointer-events', 'none')
            .style('opacity', 0);

          tooltip.transition().duration(200).style('opacity', 1);
          tooltip.html(`
            <div><strong>${config.label}</strong></div>
            <div>${(d[metric as keyof WeatherDataPoint] as number).toFixed(1)} ${config.unit}</div>
            <div>${new Date(d.timestamp).toLocaleTimeString()}</div>
          `)
          .style('left', (event.pageX + 10) + 'px')
          .style('top', (event.pageY - 10) + 'px');
        })
        .on('mouseout', function() {
          d3.selectAll('.weather-tooltip').remove();
        });
    });

    // Add axes
    const xAxis = d3.axisBottom(xScale)
      .tickFormat((domainValue) => {
        return d3.timeFormat('%H:%M')(domainValue as Date);
      });
    
    chartGroup
      .append('g')
      .attr('class', 'x-axis')
      .attr('transform', `translate(0, ${chartHeight})`)
      .call(xAxis as any);

    // Y-axis for primary metric
    if (selectedMetrics.length > 0) {
      const primaryMetric = selectedMetrics[0];
      const config = metricConfigs[primaryMetric as keyof typeof metricConfigs];
      
      const yAxis = d3.axisLeft(yScales[primaryMetric])
        .tickFormat((d) => `${d}${config.unit}`);
      
      chartGroup
        .append('g')
        .attr('class', 'y-axis')
        .call(yAxis as any);

      // Y-axis label
      chartGroup
        .append('text')
        .attr('transform', 'rotate(-90)')
        .attr('y', 0 - margin.left)
        .attr('x', 0 - (chartHeight / 2))
        .attr('dy', '1em')
        .style('text-anchor', 'middle')
        .style('font-size', '12px')
        .style('fill', '#666')
        .text(config.label);
    }

    // Add legend
    const legend = chartGroup
      .append('g')
      .attr('class', 'legend')
      .attr('transform', `translate(${chartWidth + 10}, 20)`);

    selectedMetrics.forEach((metric, index) => {
      const config = metricConfigs[metric as keyof typeof metricConfigs];
      if (!config) return;

      const legendItem = legend
        .append('g')
        .attr('transform', `translate(0, ${index * 20})`);

      legendItem
        .append('line')
        .attr('x1', 0)
        .attr('x2', 15)
        .attr('y1', 0)
        .attr('y2', 0)
        .attr('stroke', config.color)
        .attr('stroke-width', 2);

      legendItem
        .append('text')
        .attr('x', 20)
        .attr('y', 0)
        .attr('dy', '0.35em')
        .style('font-size', '12px')
        .style('fill', '#333')
        .text(config.label);
    });
  };

  const toggleMetric = (metric: string) => {
    setSelectedMetrics(prev => 
      prev.includes(metric) 
        ? prev.filter(m => m !== metric)
        : [...prev, metric]
    );
  };

  const generateMockWeatherData = (hours: number): WeatherDataPoint[] => {
    const data: WeatherDataPoint[] = [];
    const now = new Date();
    const dataPoints = hours * 4; // One data point every 15 minutes
    
    for (let i = 0; i < dataPoints; i++) {
      const timestamp = new Date(now.getTime() - (dataPoints - i) * 15 * 60 * 1000);
      data.push({
        timestamp: timestamp.toISOString(),
        air_temperature: 22 + Math.random() * 8 + Math.sin(i / 10) * 3,
        track_temperature: 35 + Math.random() * 10 + Math.sin(i / 8) * 5,
        humidity: 60 + Math.random() * 20,
        pressure: 1010 + Math.random() * 10,
        wind_speed: 5 + Math.random() * 15,
        rainfall: Math.random() > 0.9 ? Math.random() * 2 : 0
      });
    }
    
    return data;
  };

  if (loading) {
    return (
      <div className="weather-chart loading">
        <div className="loading-spinner">🌀</div>
        <p>Loading weather trends...</p>
      </div>
    );
  }

  if (error || weatherData.length === 0) {
    return (
      <div className="weather-chart error">
        <div className="error-icon">📊</div>
        <h3>No Weather Trend Data</h3>
        <p className="error-message">{error || 'No weather data available for this session'}</p>
        <div className="error-details">
          <p>Weather trend data might not be available because:</p>
          <ul>
            <li>This is a practice or old session</li>
            <li>Weather sensors were not active</li>
            <li>Data is still being processed</li>
          </ul>
        </div>
        <button onClick={fetchWeatherData} className="retry-btn">
          🔄 Retry
        </button>
      </div>
    );
  }

  return (
    <div className="weather-chart">
      <div className="chart-header">
        <div className="chart-title">
          <h3>Weather Trends ({hours}h)</h3>
          <div className="connection-status">
            <span className={`status-dot ${isConnected ? 'connected' : 'disconnected'}`}></span>
            <span>Live Data</span>
          </div>
        </div>
        
        <div className="metric-toggles">
          {Object.entries(metricConfigs).map(([metric, config]) => (
            <button
              key={metric}
              className={`metric-toggle ${selectedMetrics.includes(metric) ? 'active' : ''}`}
              onClick={() => toggleMetric(metric)}
              style={{ 
                borderColor: config.color,
                backgroundColor: selectedMetrics.includes(metric) ? config.color : 'transparent',
                color: selectedMetrics.includes(metric) ? 'white' : config.color
              }}
            >
              {config.label}
            </button>
          ))}
        </div>
      </div>

      <div className="chart-container" ref={containerRef}>
        <svg
          ref={svgRef}
          width={dimensions.width}
          height={dimensions.height}
          className="weather-chart-svg"
        />
      </div>

      <div className="chart-info">
        <div className="data-points">
          📊 {weatherData.length} data points
        </div>
        <div className="time-range">
          🕒 Last {hours} hours
        </div>
      </div>
    </div>
  );
};

export default WeatherChart;