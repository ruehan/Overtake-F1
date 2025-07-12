import React, { useEffect, useRef } from 'react';
import * as d3 from 'd3';
import { LapTime, Driver } from '../../types/f1Types';
import './LapTimeChart.css';

interface LapTimeChartProps {
  lapTimes: LapTime[];
  drivers: Driver[];
  selectedDrivers: number[];
}

const LapTimeChart: React.FC<LapTimeChartProps> = ({ 
  lapTimes, 
  drivers, 
  selectedDrivers 
}) => {
  const svgRef = useRef<SVGSVGElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!svgRef.current || !lapTimes.length) return;

    const svg = d3.select(svgRef.current);
    svg.selectAll('*').remove();

    // Get container dimensions
    const container = containerRef.current;
    if (!container) return;

    const containerRect = container.getBoundingClientRect();
    const margin = { top: 20, right: 80, bottom: 60, left: 60 };
    const width = containerRect.width - margin.left - margin.right;
    const height = 400 - margin.top - margin.bottom;

    // Set SVG dimensions
    svg.attr('width', containerRect.width).attr('height', 400);

    const g = svg.append('g')
      .attr('transform', `translate(${margin.left},${margin.top})`);

    // Filter data for selected drivers
    const displayDrivers = selectedDrivers.length > 0 ? selectedDrivers : drivers.slice(0, 5).map(d => d.driver_number);
    const filteredData = lapTimes.filter(lt => displayDrivers.includes(lt.driver_number));

    if (!filteredData.length) {
      g.append('text')
        .attr('x', width / 2)
        .attr('y', height / 2)
        .attr('text-anchor', 'middle')
        .attr('class', 'no-data-text')
        .text('No lap time data available for selected drivers');
      return;
    }

    // Create scales
    const xScale = d3.scaleLinear()
      .domain(d3.extent(filteredData, d => d.lap_number) as [number, number])
      .range([0, width]);

    const yScale = d3.scaleLinear()
      .domain(d3.extent(filteredData, d => d.lap_time) as [number, number])
      .nice()
      .range([height, 0]);

    // Create color scale
    const driverMap = new Map(drivers.map(d => [d.driver_number, d]));
    const colorScale = d3.scaleOrdinal<string>()
      .domain(displayDrivers.map(String))
      .range(displayDrivers.map(driverNum => {
        const driver = driverMap.get(driverNum);
        return driver?.team_colour || '#666';
      }));

    // Add axes
    const xAxis = g.append('g')
      .attr('transform', `translate(0,${height})`)
      .call(d3.axisBottom(xScale).tickFormat(d => `Lap ${d}`));

    const yAxis = g.append('g')
      .call(d3.axisLeft(yScale).tickFormat(d => `${Number(d).toFixed(1)}s`));

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
      .attr('y', -40)
      .attr('text-anchor', 'middle')
      .attr('class', 'axis-label')
      .text('Lap Time (seconds)');

    // Group data by driver
    const driverData = d3.group(filteredData, d => d.driver_number);

    // Create line generator
    const line = d3.line<LapTime>()
      .x(d => xScale(d.lap_number))
      .y(d => yScale(d.lap_time))
      .curve(d3.curveMonotoneX);

    // Add lines for each driver
    driverData.forEach((driverLaps, driverNumber) => {
      const driver = driverMap.get(driverNumber);
      const color = colorScale(driverNumber.toString());
      
      // Sort laps by lap number
      const sortedLaps = Array.from(driverLaps).sort((a, b) => a.lap_number - b.lap_number);

      // Add line
      g.append('path')
        .datum(sortedLaps)
        .attr('class', 'lap-time-line')
        .attr('fill', 'none')
        .attr('stroke', color)
        .attr('stroke-width', 2)
        .attr('d', line);

      // Add dots for each lap
      g.selectAll(`.dot-${driverNumber}`)
        .data(sortedLaps)
        .enter().append('circle')
        .attr('class', `lap-time-dot dot-${driverNumber}`)
        .attr('cx', d => xScale(d.lap_number))
        .attr('cy', d => yScale(d.lap_time))
        .attr('r', d => d.is_personal_best ? 6 : 3)
        .attr('fill', color)
        .attr('stroke', d => d.is_personal_best ? '#fff' : 'none')
        .attr('stroke-width', d => d.is_personal_best ? 2 : 0)
        .style('cursor', 'pointer');

      // Add tooltips
      g.selectAll(`.dot-${driverNumber}`)
        .on('mouseover', function(event, d) {
          const lapData = d as LapTime;
          const tooltip = d3.select('body').append('div')
            .attr('class', 'lap-time-tooltip')
            .style('opacity', 0)
            .style('position', 'absolute')
            .style('background', 'rgba(0, 0, 0, 0.8)')
            .style('color', 'white')
            .style('padding', '8px')
            .style('border-radius', '4px')
            .style('font-size', '12px')
            .style('pointer-events', 'none');

          tooltip.transition()
            .duration(200)
            .style('opacity', 1);

          tooltip.html(`
            <strong>${driver?.name || `Driver ${driverNumber}`}</strong><br/>
            Lap ${lapData.lap_number}: ${lapData.lap_time.toFixed(3)}s<br/>
            ${lapData.is_personal_best ? '<span style="color: #ffd700;">⭐ Personal Best</span>' : ''}
            ${lapData.sector_1 ? `<br/>S1: ${lapData.sector_1.toFixed(3)}s` : ''}
            ${lapData.sector_2 ? `<br/>S2: ${lapData.sector_2.toFixed(3)}s` : ''}
            ${lapData.sector_3 ? `<br/>S3: ${lapData.sector_3.toFixed(3)}s` : ''}
          `)
            .style('left', (event.pageX + 10) + 'px')
            .style('top', (event.pageY - 10) + 'px');
        })
        .on('mouseout', function() {
          d3.selectAll('.lap-time-tooltip').remove();
        });
    });

    // Add legend
    const legend = g.append('g')
      .attr('class', 'legend')
      .attr('transform', `translate(${width + 10}, 20)`);

    displayDrivers.forEach((driverNumber, i) => {
      const driver = driverMap.get(driverNumber);
      const color = colorScale(driverNumber.toString());
      
      const legendItem = legend.append('g')
        .attr('transform', `translate(0, ${i * 25})`);

      legendItem.append('line')
        .attr('x1', 0)
        .attr('x2', 15)
        .attr('y1', 0)
        .attr('y2', 0)
        .attr('stroke', color)
        .attr('stroke-width', 3);

      legendItem.append('circle')
        .attr('cx', 7.5)
        .attr('cy', 0)
        .attr('r', 3)
        .attr('fill', color);

      legendItem.append('text')
        .attr('x', 20)
        .attr('y', 0)
        .attr('dy', '0.35em')
        .attr('class', 'legend-text')
        .text(`${driver?.abbreviation || driverNumber} - ${driver?.name || `Driver ${driverNumber}`}`);
    });

    // Add grid lines
    const xGrid = g.append('g')
      .attr('class', 'grid')
      .attr('transform', `translate(0,${height})`)
      .call(d3.axisBottom(xScale)
        .tickSize(-height)
        .tickFormat(() => '')
      );

    const yGrid = g.append('g')
      .attr('class', 'grid')
      .call(d3.axisLeft(yScale)
        .tickSize(-width)
        .tickFormat(() => '')
      );

  }, [lapTimes, drivers, selectedDrivers]);

  return (
    <div className="lap-time-chart-container" ref={containerRef}>
      <div className="chart-header">
        <h3>Lap Time Comparison</h3>
        <p>Compare lap times across selected drivers. ⭐ indicates personal best laps.</p>
      </div>
      <svg ref={svgRef} className="lap-time-chart-svg"></svg>
    </div>
  );
};

export default LapTimeChart;