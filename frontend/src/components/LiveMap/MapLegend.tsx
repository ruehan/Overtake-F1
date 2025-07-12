import React from 'react';
import { Driver } from '../../types/f1Types';

interface MapLegendProps {
  drivers: Driver[];
  isConnected: boolean;
}

const MapLegend: React.FC<MapLegendProps> = ({ drivers, isConnected }) => {
  const getTeamDrivers = () => {
    const teams = new Map<string, Driver[]>();
    
    drivers.forEach(driver => {
      if (!teams.has(driver.team_name)) {
        teams.set(driver.team_name, []);
      }
      teams.get(driver.team_name)!.push(driver);
    });
    
    return teams;
  };

  const teamDrivers = getTeamDrivers();

  return (
    <div className="map-legend-panel">
      <div className="legend-header">
        <h4>Drivers & Teams</h4>
        <div className={`legend-status ${isConnected ? 'connected' : 'disconnected'}`}>
          {isConnected ? '🟢 Live Data' : '🔴 No Data'}
        </div>
      </div>
      
      <div className="legend-content">
        <div className="legend-section">
          <h5>Race Information</h5>
          <div className="legend-items">
            <div className="legend-item">
              <div className="legend-color drs-active"></div>
              <span>DRS Active</span>
            </div>
            <div className="legend-item">
              <div className="legend-color speed-indicator"></div>
              <span>Speed Display</span>
            </div>
            <div className="legend-item">
              <div className="legend-color position-marker"></div>
              <span>Car Position</span>
            </div>
          </div>
        </div>

        {teamDrivers.size > 0 && (
          <div className="legend-section">
            <h5>Teams & Drivers</h5>
            <div className="teams-list">
              {Array.from(teamDrivers.entries()).map(([teamName, teamDrivers]) => (
                <div key={teamName} className="team-group">
                  <div className="team-header">
                    <div 
                      className="team-color-indicator"
                      style={{ backgroundColor: teamDrivers[0]?.team_colour || '#666' }}
                    ></div>
                    <span className="team-name">{teamName}</span>
                  </div>
                  <div className="drivers-list">
                    {teamDrivers.map(driver => (
                      <div key={driver.driver_number} className="driver-item">
                        <span className="driver-number">#{driver.driver_number}</span>
                        <span className="driver-name">{driver.name}</span>
                        <span className="driver-abbr">{driver.abbreviation}</span>
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        <div className="legend-section">
          <h5>Map Controls</h5>
          <div className="legend-items">
            <div className="legend-item">
              <span className="control-icon">🖱️</span>
              <span>Click & drag to pan</span>
            </div>
            <div className="legend-item">
              <span className="control-icon">🔍</span>
              <span>Scroll to zoom</span>
            </div>
            <div className="legend-item">
              <span className="control-icon">🔄</span>
              <span>Reset zoom button</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default MapLegend;