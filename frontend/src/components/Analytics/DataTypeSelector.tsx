import React from 'react';
import { AnalyticsDataType } from './RaceAnalyticsDashboard';
import './DataTypeSelector.css';

interface DataTypeSelectorProps {
  options: AnalyticsDataType[];
  selected: AnalyticsDataType;
  onChange: (dataType: AnalyticsDataType) => void;
}

const DataTypeSelector: React.FC<DataTypeSelectorProps> = ({
  options,
  selected,
  onChange
}) => {
  const getOptionLabel = (option: AnalyticsDataType): string => {
    switch (option) {
      case 'lapTimes':
        return 'Lap Times';
      case 'pitStops':
        return 'Pit Stops';
      case 'tireStrategy':
        return 'Tire Strategy';
      default:
        return option;
    }
  };

  const getOptionIcon = (option: AnalyticsDataType): string => {
    switch (option) {
      case 'lapTimes':
        return '⏱️';
      case 'pitStops':
        return '🏁';
      case 'tireStrategy':
        return '🏎️';
      default:
        return '📊';
    }
  };

  const getOptionDescription = (option: AnalyticsDataType): string => {
    switch (option) {
      case 'lapTimes':
        return 'Compare lap times and performance across drivers';
      case 'pitStops':
        return 'Analyze pit stop timing and duration';
      case 'tireStrategy':
        return 'Visualize tire compound strategies throughout the race';
      default:
        return '';
    }
  };

  return (
    <div className="data-type-selector">
      <label className="selector-label">Data View</label>
      
      <div className="data-type-options">
        {options.map(option => (
          <button
            key={option}
            className={`data-type-option ${selected === option ? 'selected' : ''}`}
            onClick={() => onChange(option)}
            type="button"
          >
            <div className="option-header">
              <span className="option-icon">{getOptionIcon(option)}</span>
              <span className="option-label">{getOptionLabel(option)}</span>
            </div>
            <div className="option-description">
              {getOptionDescription(option)}
            </div>
          </button>
        ))}
      </div>
    </div>
  );
};

export default DataTypeSelector;