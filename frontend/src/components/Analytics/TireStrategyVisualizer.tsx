import React, { useEffect, useRef } from 'react';
import * as d3 from 'd3';
import { LapTime, PitStop, Driver } from '../../types/f1Types';
import './TireStrategyVisualizer.css';

interface TireStrategyVisualizerProps {
  data: {
    lapTimes: LapTime[];
    pitStops: PitStop[];
  };
  drivers: Driver[];
  selectedDrivers: number[];
}

// Tire compound types
enum TireCompound {
  SOFT = 'Soft',
  MEDIUM = 'Medium', 
  HARD = 'Hard',
  INTERMEDIATE = 'Intermediate',
  WET = 'Wet'
}

interface TireStint {
  driver_number: number;
  start_lap: number;
  end_lap: number;
  compound: TireCompound;
  performance: number; // Average lap time for this stint
  degradation: number; // Performance drop over stint
}

const TireStrategyVisualizer: React.FC<TireStrategyVisualizerProps> = ({
  data,
  drivers,
  selectedDrivers
}) => {
  const svgRef = useRef<SVGSVGElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  // Generate tire strategy data based on pit stops and lap times
  const generateTireStints = (): TireStint[] => {
    const stints: TireStint[] = [];
    const displayDrivers = selectedDrivers.length > 0 ? selectedDrivers : drivers.slice(0, 5).map(d => d.driver_number);
    
    displayDrivers.forEach(driverNumber => {
      const driverPitStops = data.pitStops
        .filter(ps => ps.driver_number === driverNumber)
        .sort((a, b) => a.lap_number - b.lap_number);
      
      const driverLapTimes = data.lapTimes
        .filter(lt => lt.driver_number === driverNumber)
        .sort((a, b) => a.lap_number - b.lap_number);

      if (driverLapTimes.length === 0) return;

      let currentLap = 1;
      const maxLap = Math.max(...driverLapTimes.map(lt => lt.lap_number));

      // Generate tire compounds randomly for demo (in real data, this would come from API)
      const compounds = [TireCompound.SOFT, TireCompound.MEDIUM, TireCompound.HARD];
      
      driverPitStops.forEach((pitStop, index) => {
        const stintLaps = driverLapTimes.filter(lt => 
          lt.lap_number >= currentLap && lt.lap_number < pitStop.lap_number
        );
        
        if (stintLaps.length > 0) {
          const avgLapTime = stintLaps.reduce((sum, lt) => sum + lt.lap_time, 0) / stintLaps.length;
          const firstLap = stintLaps[0].lap_time;
          const lastLap = stintLaps[stintLaps.length - 1].lap_time;
          const degradation = lastLap - firstLap;

          stints.push({
            driver_number: driverNumber,
            start_lap: currentLap,
            end_lap: pitStop.lap_number - 1,
            compound: compounds[index % compounds.length],
            performance: avgLapTime,
            degradation: degradation
          });
        }
        
        currentLap = pitStop.lap_number;
      });

      // Final stint after last pit stop
      const finalStintLaps = driverLapTimes.filter(lt => lt.lap_number >= currentLap);
      if (finalStintLaps.length > 0) {
        const avgLapTime = finalStintLaps.reduce((sum, lt) => sum + lt.lap_time, 0) / finalStintLaps.length;
        const firstLap = finalStintLaps[0].lap_time;
        const lastLap = finalStintLaps[finalStintLaps.length - 1].lap_time;
        const degradation = lastLap - firstLap;

        stints.push({
          driver_number: driverNumber,
          start_lap: currentLap,
          end_lap: maxLap,
          compound: compounds[driverPitStops.length % compounds.length],
          performance: avgLapTime,
          degradation: degradation
        });
      }
    });

    return stints;
  };

  useEffect(() => {
    if (!svgRef.current || !data.lapTimes.length) return;

    const svg = d3.select(svgRef.current);
    svg.selectAll('*').remove();

    // Get container dimensions
    const container = containerRef.current;
    if (!container) return;

    const containerRect = container.getBoundingClientRect();
    const margin = { top: 60, right: 120, bottom: 60, left: 100 };
    const width = containerRect.width - margin.left - margin.right;
    const height = 400 - margin.top - margin.bottom;

    // Set SVG dimensions
    svg.attr('width', containerRect.width).attr('height', 400);

    const g = svg.append('g')
      .attr('transform', `translate(${margin.left},${margin.top})`);

    const tireStints = generateTireStints();

    if (!tireStints.length) {
      g.append('text')
        .attr('x', width / 2)
        .attr('y', height / 2)
        .attr('text-anchor', 'middle')
        .attr('class', 'no-data-text')
        .text('No tire strategy data available for selected drivers');
      return;
    }

    // Create scales
    const displayDrivers = selectedDrivers.length > 0 ? selectedDrivers : drivers.slice(0, 5).map(d => d.driver_number);
    
    const maxLap = Math.max(...tireStints.map(s => s.end_lap));
    const xScale = d3.scaleLinear()
      .domain([1, maxLap])
      .range([0, width]);

    const yScale = d3.scaleBand()
      .domain(displayDrivers.map(String))
      .range([0, height])
      .padding(0.1);

    // Tire compound colors
    const tireColors = {
      [TireCompound.SOFT]: '#FF3333',
      [TireCompound.MEDIUM]: '#FFD700', 
      [TireCompound.HARD]: '#FFFFFF',
      [TireCompound.INTERMEDIATE]: '#00FF00',
      [TireCompound.WET]: '#0066FF'
    };

    // Create driver info map
    const driverMap = new Map(drivers.map(d => [d.driver_number, d]));

    // Add axes
    const xAxis = g.append('g')
      .attr('transform', `translate(0,${height})`)
      .call(d3.axisBottom(xScale).tickFormat(d => `Lap ${d}`));

    const yAxis = g.append('g')
      .call(d3.axisLeft(yScale).tickFormat(d => {
        const driver = driverMap.get(Number(d));
        return `${driver?.abbreviation || d}`;
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

    // Add tire stint bars
    g.selectAll('.tire-stint')
      .data(tireStints)
      .enter()
      .append('rect')
      .attr('class', 'tire-stint')
      .attr('x', d => xScale(d.start_lap))
      .attr('y', d => yScale(d.driver_number.toString())!)
      .attr('width', d => xScale(d.end_lap) - xScale(d.start_lap))
      .attr('height', yScale.bandwidth())
      .attr('fill', d => tireColors[d.compound])
      .attr('stroke', '#333')
      .attr('stroke-width', 1)
      .style('cursor', 'pointer')
      .on('mouseover', function(event, d) {
        const driver = driverMap.get(d.driver_number);
        
        // Highlight the stint
        d3.select(this)
          .attr('stroke-width', 3)
          .attr('stroke', '#000');

        // Create tooltip
        const tooltip = d3.select('body').append('div')
          .attr('class', 'tire-strategy-tooltip')
          .style('opacity', 0)
          .style('position', 'absolute')
          .style('background', 'rgba(0, 0, 0, 0.9)')
          .style('color', 'white')
          .style('padding', '12px')
          .style('border-radius', '6px')
          .style('font-size', '12px')
          .style('pointer-events', 'none');

        tooltip.transition()
          .duration(200)
          .style('opacity', 1);

        const stintLength = d.end_lap - d.start_lap + 1;
        
        tooltip.html(`
          <strong>${driver?.name || `Driver ${d.driver_number}`}</strong><br/>
          <span style="color: ${tireColors[d.compound]};">● ${d.compound} Tires</span><br/>
          Laps ${d.start_lap}-${d.end_lap} (${stintLength} laps)<br/>
          Avg Lap Time: ${d.performance.toFixed(3)}s<br/>
          Degradation: ${d.degradation > 0 ? '+' : ''}${d.degradation.toFixed(3)}s<br/>
          ${d.degradation > 0.5 ? '🔴 High degradation' : 
            d.degradation < -0.5 ? '🟢 Improving pace' : '🟡 Stable performance'}
        `)
          .style('left', (event.pageX + 10) + 'px')
          .style('top', (event.pageY - 10) + 'px');
      })
      .on('mouseout', function() {
        d3.select(this)
          .attr('stroke-width', 1)
          .attr('stroke', '#333');
        
        d3.selectAll('.tire-strategy-tooltip').remove();
      });

    // Add compound labels on stints
    g.selectAll('.stint-label')
      .data(tireStints.filter(d => (d.end_lap - d.start_lap) >= 3)) // Only label longer stints
      .enter()
      .append('text')
      .attr('class', 'stint-label')
      .attr('x', d => xScale(d.start_lap) + (xScale(d.end_lap) - xScale(d.start_lap)) / 2)
      .attr('y', d => yScale(d.driver_number.toString())! + yScale.bandwidth() / 2)
      .attr('text-anchor', 'middle')
      .attr('dy', '0.35em')
      .style('font-size', '10px')
      .style('font-weight', 'bold')
      .style('fill', d => d.compound === TireCompound.HARD ? '#333' : '#fff')
      .style('pointer-events', 'none')
      .text(d => d.compound.charAt(0)); // First letter of compound

    // Add pit stop markers
    data.pitStops.forEach(pitStop => {
      if (displayDrivers.includes(pitStop.driver_number)) {
        g.append('line')
          .attr('class', 'pit-stop-marker')
          .attr('x1', xScale(pitStop.lap_number))
          .attr('x2', xScale(pitStop.lap_number))
          .attr('y1', yScale(pitStop.driver_number.toString())!)
          .attr('y2', yScale(pitStop.driver_number.toString())! + yScale.bandwidth())
          .attr('stroke', '#ff0000')
          .attr('stroke-width', 3)
          .attr('opacity', 0.8);

        g.append('text')
          .attr('class', 'pit-stop-label')
          .attr('x', xScale(pitStop.lap_number))
          .attr('y', yScale(pitStop.driver_number.toString())! - 5)
          .attr('text-anchor', 'middle')
          .style('font-size', '8px')
          .style('font-weight', 'bold')
          .style('fill', '#ff0000')
          .text('PIT');
      }
    });

    // Add legend
    const legend = g.append('g')
      .attr('class', 'tire-legend')
      .attr('transform', `translate(${width + 20}, 20)`);

    legend.append('text')
      .attr('x', 0)
      .attr('y', 0)
      .attr('class', 'legend-title')
      .text('Tire Compounds');

    Object.entries(tireColors).forEach(([compound, color], i) => {
      const legendItem = legend.append('g')
        .attr('transform', `translate(0, ${20 + i * 20})`);

      legendItem.append('rect')
        .attr('x', 0)
        .attr('y', -8)
        .attr('width', 15)
        .attr('height', 15)
        .attr('fill', color)
        .attr('stroke', '#333')
        .attr('stroke-width', 1);

      legendItem.append('text')
        .attr('x', 20)
        .attr('y', 0)
        .attr('dy', '0.35em')
        .attr('class', 'legend-text')
        .text(compound);
    });

    // Add pit stop legend
    const pitLegend = legend.append('g')
      .attr('transform', `translate(0, ${20 + Object.keys(tireColors).length * 20 + 20})`);

    pitLegend.append('text')
      .attr('x', 0)
      .attr('y', 0)
      .attr('class', 'legend-title')
      .text('Pit Stops');

    pitLegend.append('line')
      .attr('x1', 0)
      .attr('x2', 15)
      .attr('y1', 15)
      .attr('y2', 15)
      .attr('stroke', '#ff0000')
      .attr('stroke-width', 3);

    pitLegend.append('text')
      .attr('x', 20)
      .attr('y', 15)
      .attr('dy', '0.35em')
      .attr('class', 'legend-text')
      .text('Pit Stop');

    // Add grid lines
    const xGrid = g.append('g')
      .attr('class', 'grid')
      .attr('transform', `translate(0,${height})`)
      .call(d3.axisBottom(xScale)
        .tickSize(-height)
        .tickFormat(() => '')
      );

  }, [data, drivers, selectedDrivers]);

  return (
    <div className="tire-strategy-visualizer-container" ref={containerRef}>
      <div className="chart-header">
        <h3>Tire Strategy Analysis</h3>
        <p>Visual representation of tire compounds used throughout the race. Red lines indicate pit stops.</p>
      </div>
      <svg ref={svgRef} className="tire-strategy-svg"></svg>
    </div>
  );
};

export default TireStrategyVisualizer;