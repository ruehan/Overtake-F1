import React, { useState } from 'react';
import { Driver } from '../../types/f1Types';
import './DriverSelector.css';

interface DriverSelectorProps {
  drivers: Driver[];
  selectedDrivers: number[];
  onSelectionChange: (driverNumbers: number[]) => void;
  multiSelect?: boolean;
}

const DriverSelector: React.FC<DriverSelectorProps> = ({
  drivers,
  selectedDrivers,
  onSelectionChange,
  multiSelect = true
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');

  const filteredDrivers = (drivers || []).filter(driver => 
    driver.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    driver.abbreviation.toLowerCase().includes(searchTerm.toLowerCase()) ||
    driver.team_name.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const handleDriverClick = (driverNumber: number) => {
    if (multiSelect) {
      const newSelection = selectedDrivers.includes(driverNumber)
        ? selectedDrivers.filter(d => d !== driverNumber)
        : [...selectedDrivers, driverNumber];
      onSelectionChange(newSelection);
    } else {
      onSelectionChange([driverNumber]);
      setIsOpen(false);
    }
  };

  const handleSelectAll = () => {
    if (selectedDrivers.length === drivers.length) {
      onSelectionChange([]);
    } else {
      onSelectionChange(drivers.map(d => d.driver_number));
    }
  };

  const getSelectedDriversText = () => {
    if (selectedDrivers.length === 0) {
      return 'Select drivers...';
    } else if (selectedDrivers.length === 1) {
      const driver = drivers.find(d => d.driver_number === selectedDrivers[0]);
      return driver ? `${driver.abbreviation} - ${driver.name}` : 'Unknown driver';
    } else if (selectedDrivers.length <= 3) {
      return selectedDrivers
        .map(driverNum => {
          const driver = drivers.find(d => d.driver_number === driverNum);
          return driver?.abbreviation || driverNum;
        })
        .join(', ');
    } else {
      return `${selectedDrivers.length} drivers selected`;
    }
  };

  return (
    <div className="driver-selector">
      <label className="selector-label">
        {multiSelect ? 'Select Drivers' : 'Select Driver'}
      </label>
      
      <div className="selector-container">
        <button
          className="selector-button"
          onClick={() => setIsOpen(!isOpen)}
          type="button"
        >
          <span className="selector-text">{getSelectedDriversText()}</span>
          <span className={`selector-arrow ${isOpen ? 'open' : ''}`}>▼</span>
        </button>

        {isOpen && (
          <div className="selector-dropdown">
            <div className="dropdown-header">
              <input
                type="text"
                placeholder="Search drivers..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="driver-search"
              />
              
              {multiSelect && (
                <button
                  className="select-all-button"
                  onClick={handleSelectAll}
                  type="button"
                >
                  {selectedDrivers.length === drivers.length ? 'Deselect All' : 'Select All'}
                </button>
              )}
            </div>

            <div className="drivers-list">
              {filteredDrivers.length === 0 ? (
                <div className="no-drivers">No drivers found</div>
              ) : (
                filteredDrivers.map(driver => (
                  <div
                    key={driver.driver_number}
                    className={`driver-item ${
                      selectedDrivers.includes(driver.driver_number) ? 'selected' : ''
                    }`}
                    onClick={() => handleDriverClick(driver.driver_number)}
                  >
                    <div className="driver-info">
                      <div className="driver-main">
                        <span 
                          className="driver-number"
                          style={{ backgroundColor: driver.team_colour }}
                        >
                          #{driver.driver_number}
                        </span>
                        <span className="driver-name">{driver.name}</span>
                        <span className="driver-abbr">{driver.abbreviation}</span>
                      </div>
                      <div className="driver-team">
                        <span 
                          className="team-indicator"
                          style={{ backgroundColor: driver.team_colour }}
                        ></span>
                        {driver.team_name}
                      </div>
                    </div>
                    
                    {multiSelect && (
                      <div className="checkbox-container">
                        <input
                          type="checkbox"
                          checked={selectedDrivers.includes(driver.driver_number)}
                          onChange={() => {}} // Handled by parent click
                          className="driver-checkbox"
                        />
                      </div>
                    )}
                  </div>
                ))
              )}
            </div>

            {multiSelect && selectedDrivers.length > 0 && (
              <div className="selection-summary">
                {selectedDrivers.length} of {drivers.length} drivers selected
              </div>
            )}
          </div>
        )}
      </div>

      {/* Overlay to close dropdown when clicking outside */}
      {isOpen && (
        <div 
          className="selector-overlay"
          onClick={() => setIsOpen(false)}
        />
      )}
    </div>
  );
};

export default DriverSelector;