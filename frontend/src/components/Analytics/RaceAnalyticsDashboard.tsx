import React, { useState, useEffect } from 'react';
import { Session, Driver, LapTime, PitStop } from '../../types/f1Types';
import api from '../../services/api';
import DriverSelector from './DriverSelector';
import DataTypeSelector from './DataTypeSelector';
import LapTimeChart from './LapTimeChart';
import PitStopTimeline from './PitStopTimeline';
import TireStrategyVisualizer from './TireStrategyVisualizer';
import DataTable from './DataTable';
import './RaceAnalyticsDashboard.css';

export type AnalyticsDataType = 'lapTimes' | 'pitStops' | 'tireStrategy';

interface RaceAnalyticsDashboardProps {
  sessionKey?: number;
}

const RaceAnalyticsDashboard: React.FC<RaceAnalyticsDashboardProps> = ({ 
  sessionKey = 9222 
}) => {
  const [selectedDrivers, setSelectedDrivers] = useState<number[]>([]);
  const [dataType, setDataType] = useState<AnalyticsDataType>('lapTimes');
  const [drivers, setDrivers] = useState<Driver[]>([]);
  const [lapTimes, setLapTimes] = useState<LapTime[]>([]);
  const [pitStops, setPitStops] = useState<PitStop[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [session, setSession] = useState<Session | null>(null);

  // Fetch initial data
  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        setError(null);

        // Fetch session info
        try {
          const sessionData = await api.getCurrentSession();
          setSession(sessionData);
        } catch (err) {
          console.warn('Using fallback session data');
          setSession({
            session_key: sessionKey,
            session_name: 'Demo Session',
            session_type: 'Race',
            country: 'Demo',
            circuit: 'Demo Circuit',
            date: new Date().toISOString()
          } as Session);
        }

        // Fetch drivers
        const driversData = await api.getDrivers(sessionKey);
        setDrivers(driversData);
        
        // Auto-select first 3 drivers for better demo
        if (driversData.length > 0) {
          setSelectedDrivers(driversData.slice(0, 3).map(d => d.driver_number));
        }

        // Fetch lap times and pit stops
        await Promise.all([
          fetchLapTimes(sessionKey),
          fetchPitStops(sessionKey)
        ]);

      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to fetch data');
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [sessionKey]);

  const fetchLapTimes = async (sessionKey: number) => {
    try {
      // For demo purposes, we'll generate some sample lap times
      // In real implementation, this would call: await api.getLapTimes(sessionKey);
      const sampleLapTimes: LapTime[] = [];
      
      drivers.slice(0, 5).forEach(driver => {
        for (let lap = 1; lap <= 20; lap++) {
          const baseTime = 90 + Math.random() * 10; // 90-100 second lap times
          const variation = (Math.random() - 0.5) * 2; // ±1 second variation
          
          sampleLapTimes.push({
            driver_number: driver.driver_number,
            session_key: sessionKey,
            lap_number: lap,
            lap_time: baseTime + variation,
            sector_1: (baseTime + variation) * 0.35,
            sector_2: (baseTime + variation) * 0.40,
            sector_3: (baseTime + variation) * 0.25,
            is_personal_best: Math.random() > 0.9,
            timestamp: Date.now() + lap * 60000
          });
        }
      });
      
      setLapTimes(sampleLapTimes);
    } catch (err) {
      console.error('Failed to fetch lap times:', err);
    }
  };

  const fetchPitStops = async (sessionKey: number) => {
    try {
      // Generate sample pit stop data
      const samplePitStops: PitStop[] = [];
      
      drivers.slice(0, 5).forEach(driver => {
        // 1-2 pit stops per driver
        const numPitStops = Math.floor(Math.random() * 2) + 1;
        
        for (let i = 0; i < numPitStops; i++) {
          const lapNumber = Math.floor(Math.random() * 15) + 5; // Pit between lap 5-20
          const duration = 2.5 + Math.random() * 1.5; // 2.5-4 second pit stops
          
          samplePitStops.push({
            driver_number: driver.driver_number,
            session_key: sessionKey,
            pit_duration: duration,
            lap_number: lapNumber,
            timestamp: Date.now() + lapNumber * 60000
          });
        }
      });
      
      setPitStops(samplePitStops);
    } catch (err) {
      console.error('Failed to fetch pit stops:', err);
    }
  };

  const getFilteredData = () => {
    const driverNumbers = selectedDrivers.length > 0 ? selectedDrivers : drivers.map(d => d.driver_number);
    
    switch (dataType) {
      case 'lapTimes':
        return lapTimes.filter(lt => driverNumbers.includes(lt.driver_number));
      case 'pitStops':
        return pitStops.filter(ps => driverNumbers.includes(ps.driver_number));
      case 'tireStrategy':
        // For tire strategy, we'll combine lap times and pit stops
        return {
          lapTimes: lapTimes.filter(lt => driverNumbers.includes(lt.driver_number)),
          pitStops: pitStops.filter(ps => driverNumbers.includes(ps.driver_number))
        };
      default:
        return [];
    }
  };

  const handleDriverSelectionChange = (driverNumbers: number[]) => {
    setSelectedDrivers(driverNumbers);
  };

  const handleDataTypeChange = (newDataType: AnalyticsDataType) => {
    setDataType(newDataType);
  };

  if (loading) {
    return (
      <div className="analytics-loading">
        <div className="loading-spinner"></div>
        <p>Loading race analytics data...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="analytics-error">
        <h3>Error Loading Analytics</h3>
        <p>{error}</p>
        <button onClick={() => window.location.reload()}>Retry</button>
      </div>
    );
  }

  return (
    <div className="race-analytics-dashboard">
      {/* Header */}
      <div className="dashboard-header">
        <div className="header-info">
          <h2>Race Analytics Dashboard</h2>
          {session && (
            <p className="session-info">
              {session.session_name} - {session.circuit}, {session.country}
            </p>
          )}
        </div>
        
        <div className="header-stats">
          <div className="stat-item">
            <span className="stat-label">Drivers</span>
            <span className="stat-value">{drivers.length}</span>
          </div>
          <div className="stat-item">
            <span className="stat-label">Lap Times</span>
            <span className="stat-value">{lapTimes.length}</span>
          </div>
          <div className="stat-item">
            <span className="stat-label">Pit Stops</span>
            <span className="stat-value">{pitStops.length}</span>
          </div>
        </div>
      </div>

      {/* Controls */}
      <div className="dashboard-controls">
        <DriverSelector
          drivers={drivers}
          selectedDrivers={selectedDrivers}
          onSelectionChange={handleDriverSelectionChange}
          multiSelect={true}
        />
        
        <DataTypeSelector
          options={['lapTimes', 'pitStops', 'tireStrategy']}
          selected={dataType}
          onChange={handleDataTypeChange}
        />
      </div>

      {/* Main Content */}
      <div className="dashboard-content">
        {dataType === 'lapTimes' && (
          <LapTimeChart 
            lapTimes={getFilteredData() as LapTime[]}
            drivers={drivers}
            selectedDrivers={selectedDrivers}
          />
        )}
        
        {dataType === 'pitStops' && (
          <PitStopTimeline 
            pitStops={getFilteredData() as PitStop[]}
            drivers={drivers}
            selectedDrivers={selectedDrivers}
          />
        )}
        
        {dataType === 'tireStrategy' && (
          <TireStrategyVisualizer 
            data={getFilteredData() as { lapTimes: LapTime[]; pitStops: PitStop[] }}
            drivers={drivers}
            selectedDrivers={selectedDrivers}
          />
        )}
      </div>

      {/* Data Table */}
      <div className="dashboard-table">
        <DataTable
          data={getFilteredData()}
          dataType={dataType}
          drivers={drivers}
          exportable={true}
        />
      </div>
    </div>
  );
};

export default RaceAnalyticsDashboard;