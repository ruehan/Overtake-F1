import React, { useState, useMemo } from 'react';
import { LapTime, PitStop, Driver } from '../../types/f1Types';
import { AnalyticsDataType } from './RaceAnalyticsDashboard';
import './DataTable.css';

interface DataTableProps {
  data: any;
  dataType: AnalyticsDataType;
  drivers: Driver[];
  exportable?: boolean;
}

type SortDirection = 'asc' | 'desc';

interface SortConfig {
  key: string;
  direction: SortDirection;
}

const DataTable: React.FC<DataTableProps> = ({
  data,
  dataType,
  drivers,
  exportable = true
}) => {
  const [sortConfig, setSortConfig] = useState<SortConfig | null>(null);
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage, setItemsPerPage] = useState(10);
  const [searchTerm, setSearchTerm] = useState('');

  const driverMap = useMemo(() => 
    new Map(drivers.map(d => [d.driver_number, d])), 
    [drivers]
  );

  // Prepare table data based on data type
  const tableData = useMemo(() => {
    let processedData: any[] = [];

    if (dataType === 'lapTimes' && Array.isArray(data)) {
      processedData = (data as LapTime[]).map(lt => ({
        ...lt,
        driver_name: driverMap.get(lt.driver_number)?.name || `Driver ${lt.driver_number}`,
        driver_abbr: driverMap.get(lt.driver_number)?.abbreviation || lt.driver_number.toString(),
        team_name: driverMap.get(lt.driver_number)?.team_name || 'Unknown',
        formatted_lap_time: formatTime(lt.lap_time),
        formatted_sector_1: lt.sector_1 ? formatTime(lt.sector_1) : '-',
        formatted_sector_2: lt.sector_2 ? formatTime(lt.sector_2) : '-',
        formatted_sector_3: lt.sector_3 ? formatTime(lt.sector_3) : '-'
      }));
    } else if (dataType === 'pitStops' && Array.isArray(data)) {
      processedData = (data as PitStop[]).map(ps => ({
        ...ps,
        driver_name: driverMap.get(ps.driver_number)?.name || `Driver ${ps.driver_number}`,
        driver_abbr: driverMap.get(ps.driver_number)?.abbreviation || ps.driver_number.toString(),
        team_name: driverMap.get(ps.driver_number)?.team_name || 'Unknown',
        formatted_duration: formatTime(ps.pit_duration)
      }));
    } else if (dataType === 'tireStrategy' && data && typeof data === 'object') {
      // Combine lap times and pit stops for tire strategy view
      const { lapTimes = [], pitStops = [] } = data as { lapTimes: LapTime[]; pitStops: PitStop[] };
      
      // Create a summary view of tire strategies
      const driverStrategies = new Map<number, any>();
      
      lapTimes.forEach(lt => {
        if (!driverStrategies.has(lt.driver_number)) {
          const driver = driverMap.get(lt.driver_number);
          driverStrategies.set(lt.driver_number, {
            driver_number: lt.driver_number,
            driver_name: driver?.name || `Driver ${lt.driver_number}`,
            driver_abbr: driver?.abbreviation || lt.driver_number.toString(),
            team_name: driver?.team_name || 'Unknown',
            total_laps: 0,
            pit_stops: 0,
            avg_lap_time: 0,
            best_lap_time: Infinity,
            worst_lap_time: 0,
            total_time: 0
          });
        }
        
        const strategy = driverStrategies.get(lt.driver_number)!;
        strategy.total_laps++;
        strategy.total_time += lt.lap_time;
        strategy.best_lap_time = Math.min(strategy.best_lap_time, lt.lap_time);
        strategy.worst_lap_time = Math.max(strategy.worst_lap_time, lt.lap_time);
      });

      pitStops.forEach(ps => {
        const strategy = driverStrategies.get(ps.driver_number);
        if (strategy) {
          strategy.pit_stops++;
        }
      });

      // Calculate averages and format
      processedData = Array.from(driverStrategies.values()).map(strategy => ({
        ...strategy,
        avg_lap_time: strategy.total_time / strategy.total_laps,
        formatted_avg_lap_time: formatTime(strategy.total_time / strategy.total_laps),
        formatted_best_lap_time: formatTime(strategy.best_lap_time),
        formatted_worst_lap_time: formatTime(strategy.worst_lap_time),
        formatted_total_time: formatTime(strategy.total_time)
      }));
    }

    // Apply search filter
    if (searchTerm) {
      processedData = processedData.filter(item =>
        item.driver_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        item.driver_abbr?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        item.team_name?.toLowerCase().includes(searchTerm.toLowerCase())
      );
    }

    return processedData;
  }, [data, dataType, driverMap, searchTerm]);

  // Sort data
  const sortedData = useMemo(() => {
    if (!sortConfig) return tableData;

    return [...tableData].sort((a, b) => {
      const aValue = a[sortConfig.key];
      const bValue = b[sortConfig.key];

      if (aValue < bValue) {
        return sortConfig.direction === 'asc' ? -1 : 1;
      }
      if (aValue > bValue) {
        return sortConfig.direction === 'asc' ? 1 : -1;
      }
      return 0;
    });
  }, [tableData, sortConfig]);

  // Paginate data
  const paginatedData = useMemo(() => {
    const startIndex = (currentPage - 1) * itemsPerPage;
    return sortedData.slice(startIndex, startIndex + itemsPerPage);
  }, [sortedData, currentPage, itemsPerPage]);

  const totalPages = Math.ceil(sortedData.length / itemsPerPage);

  const formatTime = (seconds: number): string => {
    if (seconds < 60) {
      return `${seconds.toFixed(3)}s`;
    } else {
      const minutes = Math.floor(seconds / 60);
      const remainingSeconds = seconds % 60;
      return `${minutes}:${remainingSeconds.toFixed(3)}`;
    }
  };

  const handleSort = (key: string) => {
    let direction: SortDirection = 'asc';
    if (sortConfig && sortConfig.key === key && sortConfig.direction === 'asc') {
      direction = 'desc';
    }
    setSortConfig({ key, direction });
  };

  const handleExport = (format: 'csv' | 'json') => {
    if (format === 'csv') {
      exportToCSV();
    } else {
      exportToJSON();
    }
  };

  const exportToCSV = () => {
    if (!sortedData.length) return;

    const headers = getColumnHeaders();
    const csvContent = [
      headers.join(','),
      ...sortedData.map(row => 
        headers.map(header => {
          const value = row[header.toLowerCase().replace(' ', '_')] || '';
          return `"${value}"`;
        }).join(',')
      )
    ].join('\n');

    downloadFile(csvContent, `f1_${dataType}_data.csv`, 'text/csv');
  };

  const exportToJSON = () => {
    const jsonContent = JSON.stringify(sortedData, null, 2);
    downloadFile(jsonContent, `f1_${dataType}_data.json`, 'application/json');
  };

  const downloadFile = (content: string, filename: string, contentType: string) => {
    const blob = new Blob([content], { type: contentType });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  const getColumnHeaders = (): string[] => {
    switch (dataType) {
      case 'lapTimes':
        return ['Driver', 'Team', 'Lap', 'Lap Time', 'Sector 1', 'Sector 2', 'Sector 3', 'Personal Best'];
      case 'pitStops':
        return ['Driver', 'Team', 'Lap', 'Duration', 'Timestamp'];
      case 'tireStrategy':
        return ['Driver', 'Team', 'Total Laps', 'Pit Stops', 'Avg Lap Time', 'Best Lap', 'Worst Lap'];
      default:
        return [];
    }
  };

  const renderTableHeaders = () => {
    const headers = getColumnHeaders();
    
    return (
      <tr>
        {headers.map(header => (
          <th 
            key={header}
            onClick={() => handleSort(header.toLowerCase().replace(' ', '_'))}
            className="sortable-header"
          >
            <div className="header-content">
              <span>{header}</span>
              {sortConfig?.key === header.toLowerCase().replace(' ', '_') && (
                <span className="sort-indicator">
                  {sortConfig.direction === 'asc' ? '↑' : '↓'}
                </span>
              )}
            </div>
          </th>
        ))}
      </tr>
    );
  };

  const renderTableRows = () => {
    return paginatedData.map((row, index) => (
      <tr key={`${row.driver_number}-${index}`} className="data-row">
        {dataType === 'lapTimes' && (
          <>
            <td>
              <div className="driver-cell">
                <span className="driver-abbr">{row.driver_abbr}</span>
                <span className="driver-name">{row.driver_name}</span>
              </div>
            </td>
            <td>{row.team_name}</td>
            <td className="lap-number">{row.lap_number}</td>
            <td className={`lap-time ${row.is_personal_best ? 'personal-best' : ''}`}>
              {row.formatted_lap_time}
              {row.is_personal_best && <span className="pb-indicator">⭐</span>}
            </td>
            <td>{row.formatted_sector_1}</td>
            <td>{row.formatted_sector_2}</td>
            <td>{row.formatted_sector_3}</td>
            <td>{row.is_personal_best ? 'Yes' : 'No'}</td>
          </>
        )}
        
        {dataType === 'pitStops' && (
          <>
            <td>
              <div className="driver-cell">
                <span className="driver-abbr">{row.driver_abbr}</span>
                <span className="driver-name">{row.driver_name}</span>
              </div>
            </td>
            <td>{row.team_name}</td>
            <td className="lap-number">{row.lap_number}</td>
            <td className="pit-duration">{row.formatted_duration}</td>
            <td>{new Date(row.timestamp).toLocaleTimeString()}</td>
          </>
        )}
        
        {dataType === 'tireStrategy' && (
          <>
            <td>
              <div className="driver-cell">
                <span className="driver-abbr">{row.driver_abbr}</span>
                <span className="driver-name">{row.driver_name}</span>
              </div>
            </td>
            <td>{row.team_name}</td>
            <td>{row.total_laps}</td>
            <td>{row.pit_stops}</td>
            <td>{row.formatted_avg_lap_time}</td>
            <td className="best-lap">{row.formatted_best_lap_time}</td>
            <td>{row.formatted_worst_lap_time}</td>
          </>
        )}
      </tr>
    ));
  };

  if (!tableData.length) {
    return (
      <div className="data-table-container">
        <div className="table-header">
          <h3>Data Table</h3>
        </div>
        <div className="no-data">
          <p>No data available for the current selection.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="data-table-container">
      <div className="table-header">
        <h3>Data Table - {getColumnHeaders()[0]?.includes('Driver') ? dataType.charAt(0).toUpperCase() + dataType.slice(1) : dataType}</h3>
        
        <div className="table-controls">
          <input
            type="text"
            placeholder="Search drivers..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="search-input"
          />
          
          {exportable && (
            <div className="export-buttons">
              <button 
                onClick={() => handleExport('csv')}
                className="export-button csv"
              >
                Export CSV
              </button>
              <button 
                onClick={() => handleExport('json')}
                className="export-button json"
              >
                Export JSON
              </button>
            </div>
          )}
        </div>
      </div>

      <div className="table-wrapper">
        <table className="data-table">
          <thead>
            {renderTableHeaders()}
          </thead>
          <tbody>
            {renderTableRows()}
          </tbody>
        </table>
      </div>

      {totalPages > 1 && (
        <div className="table-pagination">
          <div className="pagination-info">
            Showing {(currentPage - 1) * itemsPerPage + 1} to {Math.min(currentPage * itemsPerPage, sortedData.length)} of {sortedData.length} entries
          </div>
          
          <div className="pagination-controls">
            <select
              value={itemsPerPage}
              onChange={(e) => {
                setItemsPerPage(Number(e.target.value));
                setCurrentPage(1);
              }}
              className="items-per-page"
            >
              <option value={10}>10 per page</option>
              <option value={25}>25 per page</option>
              <option value={50}>50 per page</option>
              <option value={100}>100 per page</option>
            </select>
            
            <div className="page-buttons">
              <button
                onClick={() => setCurrentPage(prev => Math.max(prev - 1, 1))}
                disabled={currentPage === 1}
                className="page-button"
              >
                Previous
              </button>
              
              <span className="page-info">
                Page {currentPage} of {totalPages}
              </span>
              
              <button
                onClick={() => setCurrentPage(prev => Math.min(prev + 1, totalPages))}
                disabled={currentPage === totalPages}
                className="page-button"
              >
                Next
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default DataTable;