import React, { useEffect, useRef, useState } from 'react';
import * as d3 from 'd3';
import { useWebSocket } from '../../hooks/useWebSocket';
import { Position, Driver } from '../../types/f1Types';
import MapLegend from './MapLegend';
import './F1LiveMap.css';
import './MapLegend.css';

interface F1LiveMapProps {
  sessionKey?: number;
  circuitId?: string;
}

const F1LiveMap: React.FC<F1LiveMapProps> = ({ sessionKey, circuitId = 'bahrain' }) => {
  const svgRef = useRef<SVGSVGElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const [drivers, setDrivers] = useState<Driver[]>([]);
  const [positions, setPositions] = useState<Position[]>([]);
  const [dimensions, setDimensions] = useState({ width: 800, height: 600 });

  const { isConnected, subscribe, unsubscribe } = useWebSocket();

  // WebSocket data subscriptions
  useEffect(() => {
    if (isConnected && sessionKey) {
      subscribe('positions', (data: any) => {
        setPositions(data.data || data);
      }, sessionKey);

      subscribe('drivers', (data: any) => {
        setDrivers(data.data || data);
      }, sessionKey);

      return () => {
        unsubscribe('positions');
        unsubscribe('drivers');
      };
    }
  }, [isConnected, sessionKey, subscribe, unsubscribe]);

  // Handle window resize
  useEffect(() => {
    const handleResize = () => {
      if (containerRef.current) {
        const rect = containerRef.current.getBoundingClientRect();
        setDimensions({
          width: rect.width,
          height: Math.max(rect.height, 600)
        });
      }
    };

    window.addEventListener('resize', handleResize);
    handleResize(); // Initial call

    return () => window.removeEventListener('resize', handleResize);
  }, []);

  // Initialize D3 circuit map
  useEffect(() => {
    if (!svgRef.current) return;

    const svg = d3.select(svgRef.current);
    svg.selectAll('*').remove(); // Clear previous render

    // Create main group for map elements
    const mapGroup = svg
      .append('g')
      .attr('class', 'map-group');

    // Add zoom and pan behavior
    const zoom = d3.zoom<SVGSVGElement, unknown>()
      .scaleExtent([0.5, 5])
      .on('zoom', (event) => {
        mapGroup.attr('transform', event.transform);
      });

    svg.call(zoom);

    // Reset zoom button functionality
    svg.append('g')
      .attr('class', 'zoom-controls')
      .attr('transform', 'translate(10, 10)')
      .append('rect')
      .attr('width', 80)
      .attr('height', 25)
      .attr('fill', '#fff')
      .attr('stroke', '#ccc')
      .attr('rx', 3)
      .style('cursor', 'pointer')
      .on('click', () => {
        svg.transition().duration(750).call(
          zoom.transform,
          d3.zoomIdentity
        );
      });

    svg.select('.zoom-controls')
      .append('text')
      .attr('x', 40)
      .attr('y', 17)
      .attr('text-anchor', 'middle')
      .attr('font-size', '12px')
      .attr('fill', '#333')
      .style('pointer-events', 'none')
      .text('Reset Zoom');

    // Create circuit track (simplified example for Bahrain)
    const trackData = generateTrackPath(circuitId);
    
    mapGroup
      .append('path')
      .attr('d', trackData)
      .attr('class', 'circuit-track')
      .attr('stroke', '#333')
      .attr('stroke-width', 8)
      .attr('fill', 'none');

    // Add grid lines
    const gridGroup = mapGroup.append('g').attr('class', 'grid');
    
    // Vertical grid lines
    for (let x = 0; x <= dimensions.width; x += 50) {
      gridGroup
        .append('line')
        .attr('x1', x)
        .attr('y1', 0)
        .attr('x2', x)
        .attr('y2', dimensions.height)
        .attr('stroke', '#f0f0f0')
        .attr('stroke-width', 0.5);
    }

    // Horizontal grid lines
    for (let y = 0; y <= dimensions.height; y += 50) {
      gridGroup
        .append('line')
        .attr('x1', 0)
        .attr('y1', y)
        .attr('x2', dimensions.width)
        .attr('y2', y)
        .attr('stroke', '#f0f0f0')
        .attr('stroke-width', 0.5);
    }

  }, [dimensions, circuitId]);

  // Update driver positions
  useEffect(() => {
    if (!svgRef.current || !positions.length || !drivers.length) return;

    const svg = d3.select(svgRef.current);
    const mapGroup = svg.select('.map-group');

    // Create scales for positioning
    const xExtent = d3.extent(positions, d => d.x_position) as [number, number];
    const yExtent = d3.extent(positions, d => d.y_position) as [number, number];

    const xScale = d3.scaleLinear()
      .domain(xExtent)
      .range([50, dimensions.width - 50]);

    const yScale = d3.scaleLinear()
      .domain(yExtent)
      .range([50, dimensions.height - 50]);

    // Create driver lookup map
    const driverMap = new Map(drivers.map(d => [d.driver_number, d]));

    // Update driver markers
    const driverMarkers = mapGroup
      .selectAll<SVGGElement, Position>('.driver-marker')
      .data(positions, (d: Position) => d.driver_number.toString());

    // Enter new markers
    const enterMarkers = driverMarkers
      .enter()
      .append('g')
      .attr('class', 'driver-marker')
      .attr('transform', d => `translate(${xScale(d.x_position)}, ${yScale(d.y_position)})`);

    // Add car circle
    enterMarkers
      .append('circle')
      .attr('class', 'car-body')
      .attr('r', 8)
      .attr('fill', d => {
        const driver = driverMap.get(d.driver_number);
        return driver?.team_colour || '#666';
      })
      .attr('stroke', '#fff')
      .attr('stroke-width', 2);

    // Add driver number text
    enterMarkers
      .append('text')
      .attr('class', 'driver-number')
      .attr('text-anchor', 'middle')
      .attr('dy', '0.35em')
      .attr('fill', '#fff')
      .attr('font-size', '10px')
      .attr('font-weight', 'bold')
      .text(d => d.driver_number.toString());

    // Add speed indicator
    enterMarkers
      .append('text')
      .attr('class', 'speed-indicator')
      .attr('text-anchor', 'middle')
      .attr('dy', '-15px')
      .attr('fill', '#333')
      .attr('font-size', '8px')
      .text(d => d.speed ? `${Math.round(d.speed)} km/h` : '');

    // Add DRS indicator
    enterMarkers
      .append('rect')
      .attr('class', 'drs-indicator')
      .attr('x', -6)
      .attr('y', -20)
      .attr('width', 12)
      .attr('height', 4)
      .attr('fill', d => d.drs ? '#00ff00' : 'transparent')
      .attr('stroke', d => d.drs ? '#00aa00' : 'transparent');

    // Merge update and enter selections
    const mergedMarkers = driverMarkers.merge(enterMarkers);

    // Update existing markers with smooth transition
    mergedMarkers
      .transition()
      .duration(200)
      .ease(d3.easeLinear)
      .attr('transform', d => `translate(${xScale(d.x_position)}, ${yScale(d.y_position)})`);

    // Add animation class for position updates
    mergedMarkers.classed('updating', true);

    // Remove animation class after animation
    setTimeout(() => {
      mergedMarkers.classed('updating', false);
    }, 200);

    // Update speed text
    mergedMarkers
      .select('.speed-indicator')
      .text(d => d.speed ? `${Math.round(d.speed)} km/h` : '');

    // Update DRS indicator
    mergedMarkers
      .select('.drs-indicator')
      .attr('fill', d => d.drs ? '#00ff00' : 'transparent')
      .attr('stroke', d => d.drs ? '#00aa00' : 'transparent');

    // Remove old markers
    driverMarkers.exit().remove();

  }, [positions, drivers, dimensions]);

  // Generate simplified track path (example for Bahrain)
  const generateTrackPath = (circuit: string): string => {
    // This is a simplified example - in real implementation, 
    // you'd load actual circuit data
    const centerX = dimensions.width / 2;
    const centerY = dimensions.height / 2;
    const radiusX = dimensions.width * 0.3;
    const radiusY = dimensions.height * 0.25;

    // Create a simplified oval track using arc method
    const path = d3.path();
    
    // Draw top arc
    path.arc(centerX, centerY - radiusY / 2, radiusX, 0, Math.PI);
    
    // Draw bottom arc
    path.arc(centerX, centerY + radiusY / 2, radiusX, Math.PI, 2 * Math.PI);
    
    path.closePath();

    return path.toString();
  };

  return (
    <div className="f1-live-map-container">
      <div className="f1-live-map" ref={containerRef}>
        <div className="map-header">
          <h3>F1 Live Track Map</h3>
          <div className="connection-status">
            <span className={`status-indicator ${isConnected ? 'connected' : 'disconnected'}`}>
              {isConnected ? '🟢 Live' : '🔴 Disconnected'}
            </span>
          </div>
        </div>
        
        <svg
          ref={svgRef}
          width={dimensions.width}
          height={dimensions.height}
          className="map-svg"
        >
        </svg>
      </div>

      <MapLegend drivers={drivers} isConnected={isConnected} />
    </div>
  );
};

export default F1LiveMap;