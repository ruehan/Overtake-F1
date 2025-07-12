import React, { useEffect, useRef } from 'react';
import * as d3 from 'd3';
import { PitStop, Driver } from '../../types/f1Types';
import './PitStopTimeline.css';

interface PitStopTimelineProps {
  pitStops: PitStop[];
  drivers: Driver[];
  selectedDrivers: number[];
}

const PitStopTimeline: React.FC<PitStopTimelineProps> = ({
  pitStops,
  drivers,
  selectedDrivers
}) => {
  const svgRef = useRef<SVGSVGElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!svgRef.current || !pitStops.length) return;

    const svg = d3.select(svgRef.current);
    svg.selectAll('*').remove();

    // Get container dimensions
    const container = containerRef.current;
    if (!container) return;

    const containerRect = container.getBoundingClientRect();
    const margin = { top: 60, right: 80, bottom: 60, left: 100 };
    const width = containerRect.width - margin.left - margin.right;
    const height = 400 - margin.top - margin.bottom;

    // Set SVG dimensions
    svg.attr('width', containerRect.width).attr('height', 400);

    const g = svg.append('g')
      .attr('transform', `translate(${margin.left},${margin.top})`);

    // Filter data for selected drivers
    const displayDrivers = selectedDrivers.length > 0 ? selectedDrivers : drivers.slice(0, 5).map(d => d.driver_number);
    const filteredData = pitStops.filter(ps => displayDrivers.includes(ps.driver_number));

    if (!filteredData.length) {
      g.append('text')
        .attr('x', width / 2)
        .attr('y', height / 2)
        .attr('text-anchor', 'middle')
        .attr('class', 'no-data-text')
        .text('No pit stop data available for selected drivers');
      return;
    }

    // Create scales
    const xScale = d3.scaleLinear()
      .domain(d3.extent(filteredData, d => d.lap_number) as [number, number])
      .nice()
      .range([0, width]);

    const yScale = d3.scaleBand()
      .domain(displayDrivers.map(String))
      .range([0, height])
      .padding(0.2);

    // Duration scale for visualization
    const durationScale = d3.scaleLinear()
      .domain(d3.extent(filteredData, d => d.pit_duration) as [number, number])
      .range([10, 40]); // Circle radius range

    // Color scale based on pit stop duration
    const colorScale = d3.scaleSequential(d3.interpolateRdYlGn)
      .domain([d3.max(filteredData, d => d.pit_duration)!, d3.min(filteredData, d => d.pit_duration)!]);

    // Create driver info map
    const driverMap = new Map(drivers.map(d => [d.driver_number, d]));

    // Add background lanes for each driver
    displayDrivers.forEach(driverNumber => {
      const driver = driverMap.get(driverNumber);
      const y = yScale(driverNumber.toString())!;
      
      g.append('rect')
        .attr('class', 'driver-lane')
        .attr('x', 0)
        .attr('y', y)
        .attr('width', width)
        .attr('height', yScale.bandwidth())
        .attr('fill', driver?.team_colour || '#f0f0f0')
        .attr('opacity', 0.1)
        .attr('stroke', driver?.team_colour || '#ddd')
        .attr('stroke-width', 1);
    });

    // Add axes
    const xAxis = g.append('g')
      .attr('transform', `translate(0,${height})`)
      .call(d3.axisBottom(xScale).tickFormat(d => `Lap ${d}`));

    const yAxis = g.append('g')
      .call(d3.axisLeft(yScale).tickFormat(d => {
        const driver = driverMap.get(Number(d));
        return `${driver?.abbreviation || d} - ${driver?.name || `Driver ${d}`}`;
      }));

    // Add axis labels
    g.append('text')
      .attr('x', width / 2)
      .attr('y', height + 40)
      .attr('text-anchor', 'middle')
      .attr('class', 'axis-label')
      .text('Lap Number');

    g.append('text')
      .attr('transform', 'rotate(-90)')
      .attr('x', -height / 2)
      .attr('y', -60)
      .attr('text-anchor', 'middle')
      .attr('class', 'axis-label')
      .text('Drivers');

    // Add pit stops
    g.selectAll('.pit-stop')
      .data(filteredData)
      .enter()
      .append('circle')
      .attr('class', 'pit-stop')
      .attr('cx', d => xScale(d.lap_number))
      .attr('cy', d => yScale(d.driver_number.toString())! + yScale.bandwidth() / 2)
      .attr('r', d => durationScale(d.pit_duration))
      .attr('fill', d => colorScale(d.pit_duration))
      .attr('stroke', '#333')
      .attr('stroke-width', 2)
      .style('cursor', 'pointer')
      .on('mouseover', function(event, d) {
        const driver = driverMap.get(d.driver_number);
        
        // Highlight the pit stop
        d3.select(this)
          .attr('stroke-width', 4)
          .attr('stroke', '#000');

        // Create tooltip
        const tooltip = d3.select('body').append('div')
          .attr('class', 'pit-stop-tooltip')
          .style('opacity', 0)
          .style('position', 'absolute')
          .style('background', 'rgba(0, 0, 0, 0.9)')
          .style('color', 'white')
          .style('padding', '10px')
          .style('border-radius', '6px')
          .style('font-size', '12px')
          .style('pointer-events', 'none');

        tooltip.transition()
          .duration(200)
          .style('opacity', 1);

        const durationRank = filteredData
          .filter(ps => ps.lap_number === d.lap_number)
          .sort((a, b) => a.pit_duration - b.pit_duration)
          .findIndex(ps => ps.driver_number === d.driver_number) + 1;

        tooltip.html(`
          <strong>${driver?.name || `Driver ${d.driver_number}`}</strong><br/>
          <strong>Lap ${d.lap_number} Pit Stop</strong><br/>
          Duration: <strong>${d.pit_duration.toFixed(3)}s</strong><br/>
          ${durationRank ? `Rank: ${durationRank} of ${filteredData.filter(ps => ps.lap_number === d.lap_number).length}` : ''}
          <br/><span style="color: ${d.pit_duration < 3 ? '#00ff00' : d.pit_duration > 4 ? '#ff0000' : '#ffff00'}">
            ${d.pit_duration < 3 ? '🟢 Fast Stop' : d.pit_duration > 4 ? '🔴 Slow Stop' : '🟡 Average Stop'}
          </span>
        `)
          .style('left', (event.pageX + 10) + 'px')
          .style('top', (event.pageY - 10) + 'px');
      })
      .on('mouseout', function() {
        d3.select(this)
          .attr('stroke-width', 2)
          .attr('stroke', '#333');
        
        d3.selectAll('.pit-stop-tooltip').remove();
      });

    // Add connecting lines between pit stops for same driver
    const driverGroups = d3.group(filteredData, d => d.driver_number);
    
    driverGroups.forEach((driverPitStops, driverNumber) => {
      const sortedStops = Array.from(driverPitStops).sort((a, b) => a.lap_number - b.lap_number);
      
      if (sortedStops.length > 1) {
        const line = d3.line<PitStop>()
          .x(d => xScale(d.lap_number))
          .y(d => yScale(d.driver_number.toString())! + yScale.bandwidth() / 2)
          .curve(d3.curveMonotoneX);

        g.append('path')
          .datum(sortedStops)
          .attr('class', 'pit-stop-connection')
          .attr('fill', 'none')
          .attr('stroke', driverMap.get(driverNumber)?.team_colour || '#666')
          .attr('stroke-width', 2)
          .attr('stroke-dasharray', '5,5')
          .attr('opacity', 0.6)
          .attr('d', line);
      }
    });

    // Add legend
    const legend = g.append('g')
      .attr('class', 'pit-stop-legend')
      .attr('transform', `translate(${width + 10}, 20)`);

    // Duration legend
    legend.append('text')
      .attr('x', 0)
      .attr('y', 0)
      .attr('class', 'legend-title')
      .text('Pit Stop Duration');

    const legendData = [
      { duration: 2.5, label: 'Fast (< 3s)', color: colorScale(2.5) },
      { duration: 3.5, label: 'Average (3-4s)', color: colorScale(3.5) },
      { duration: 4.5, label: 'Slow (> 4s)', color: colorScale(4.5) }
    ];

    legendData.forEach((item, i) => {
      const legendItem = legend.append('g')
        .attr('transform', `translate(0, ${20 + i * 25})`);

      legendItem.append('circle')
        .attr('cx', 8)
        .attr('cy', 0)
        .attr('r', 8)
        .attr('fill', item.color)
        .attr('stroke', '#333')
        .attr('stroke-width', 1);

      legendItem.append('text')
        .attr('x', 20)
        .attr('y', 0)
        .attr('dy', '0.35em')
        .attr('class', 'legend-text')
        .text(item.label);
    });

    // Add grid lines
    const xGrid = g.append('g')
      .attr('class', 'grid')
      .attr('transform', `translate(0,${height})`)
      .call(d3.axisBottom(xScale)
        .tickSize(-height)
        .tickFormat(() => '')
      );

  }, [pitStops, drivers, selectedDrivers]);

  return (
    <div className="pit-stop-timeline-container" ref={containerRef}>
      <div className="chart-header">
        <h3>Pit Stop Timeline</h3>
        <p>Timeline showing when each driver made pit stops and their duration. Circle size represents pit stop duration.</p>
      </div>
      <svg ref={svgRef} className="pit-stop-timeline-svg"></svg>
    </div>
  );
};

export default PitStopTimeline;