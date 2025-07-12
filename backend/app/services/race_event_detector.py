from typing import Dict, List, Optional, Callable, Set
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import asyncio
import logging
from collections import defaultdict

from app.models.f1_models import Position, Driver, LapTime, PitStop
from app.models.user_models import AlertType

logger = logging.getLogger(__name__)

class EventType(str, Enum):
    OVERTAKE = "overtake"
    PIT_STOP = "pit_stop"
    LEAD_CHANGE = "lead_change"
    FASTEST_LAP = "fastest_lap"
    WEATHER_CHANGE = "weather_change"
    INCIDENT = "incident"

@dataclass
class RaceEvent:
    event_type: EventType
    timestamp: datetime
    session_key: int
    driver_number: Optional[int] = None
    target_driver_number: Optional[int] = None
    position_gained: Optional[int] = None
    lap_number: Optional[int] = None
    data: Dict = None
    message: str = ""

class RaceEventDetector:
    def __init__(self):
        self.listeners: Dict[EventType, List[Callable]] = defaultdict(list)
        self.last_positions: Dict[int, Dict[int, int]] = {}  # session_key -> {driver_number: position}
        self.last_lap_times: Dict[int, Dict[int, float]] = {}  # session_key -> {driver_number: best_time}
        self.recent_pit_stops: Dict[int, Set[int]] = defaultdict(set)  # session_key -> {driver_numbers}
        self.position_history: Dict[int, List[Dict]] = defaultdict(list)  # session_key -> position_snapshots
        
    def add_listener(self, event_type: EventType, callback: Callable[[RaceEvent], None]):
        """Add a listener for specific event types"""
        self.listeners[event_type].append(callback)
        logger.info(f"Added listener for {event_type}")
    
    def remove_listener(self, event_type: EventType, callback: Callable):
        """Remove a listener for specific event types"""
        if callback in self.listeners[event_type]:
            self.listeners[event_type].remove(callback)
            logger.info(f"Removed listener for {event_type}")
    
    async def emit_event(self, event: RaceEvent):
        """Emit an event to all registered listeners"""
        logger.info(f"Emitting event: {event.event_type} - {event.message}")
        
        for callback in self.listeners[event.event_type]:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(event)
                else:
                    callback(event)
            except Exception as e:
                logger.error(f"Error in event listener: {e}")
    
    async def process_positions(self, positions: List, drivers: List):
        """Process position data and detect overtaking events"""
        if not positions:
            return
            
        session_key = positions[0].session_key
        current_positions = {}
        
        # Extract current positions
        for pos in positions:
            # Handle both Position objects and SimplePosition objects
            position = getattr(pos, 'position', None)
            driver_number = getattr(pos, 'driver_number', None)
            
            if position and driver_number:
                current_positions[driver_number] = position
        
        # Check for overtakes and lead changes
        if session_key in self.last_positions:
            await self._detect_overtakes(session_key, current_positions, drivers)
            await self._detect_lead_changes(session_key, current_positions, drivers)
        
        # Store current positions for next comparison
        self.last_positions[session_key] = current_positions.copy()
        
        # Store position snapshot for history
        self.position_history[session_key].append({
            'timestamp': datetime.utcnow(),
            'positions': current_positions.copy()
        })
        
        # Keep only last 100 snapshots to prevent memory issues
        if len(self.position_history[session_key]) > 100:
            self.position_history[session_key] = self.position_history[session_key][-100:]
    
    async def _detect_overtakes(self, session_key: int, current_positions: Dict[int, int], drivers: List):
        """Detect overtaking events between drivers"""
        if session_key not in self.last_positions:
            return
            
        last_positions = self.last_positions[session_key]
        # Create driver map (handle both Driver objects and SimpleDriver objects)
        driver_map = {}
        for d in drivers:
            driver_number = getattr(d, 'driver_number', None)
            if driver_number:
                driver_map[driver_number] = d
        
        for driver_num, current_pos in current_positions.items():
            if driver_num not in last_positions:
                continue
                
            last_pos = last_positions[driver_num]
            position_change = last_pos - current_pos  # Positive means gained positions
            
            if position_change > 0:  # Driver gained positions
                # Find who was overtaken
                overtaken_drivers = []
                for other_driver, other_current_pos in current_positions.items():
                    if other_driver == driver_num:
                        continue
                    if (other_driver in last_positions and 
                        last_positions[other_driver] < last_pos and 
                        other_current_pos > current_pos):
                        overtaken_drivers.append(other_driver)
                
                # Create overtake events
                for overtaken_driver in overtaken_drivers:
                    driver_obj = driver_map.get(driver_num)
                    overtaken_obj = driver_map.get(overtaken_driver)
                    driver_name = getattr(driver_obj, 'name', f"Driver {driver_num}") if driver_obj else f"Driver {driver_num}"
                    overtaken_name = getattr(overtaken_obj, 'name', f"Driver {overtaken_driver}") if overtaken_obj else f"Driver {overtaken_driver}"
                    
                    event = RaceEvent(
                        event_type=EventType.OVERTAKE,
                        timestamp=datetime.utcnow(),
                        session_key=session_key,
                        driver_number=driver_num,
                        target_driver_number=overtaken_driver,
                        position_gained=1,
                        data={
                            'overtaking_driver': driver_name,
                            'overtaken_driver': overtaken_name,
                            'new_position': current_pos,
                            'previous_position': last_pos
                        },
                        message=f"{driver_name} overtakes {overtaken_name}! Now P{current_pos}"
                    )
                    await self.emit_event(event)
    
    async def _detect_lead_changes(self, session_key: int, current_positions: Dict[int, int], drivers: List):
        """Detect changes in race leadership"""
        if session_key not in self.last_positions:
            return
            
        # Find current leader (position 1)
        current_leader = None
        for driver_num, pos in current_positions.items():
            if pos == 1:
                current_leader = driver_num
                break
        
        # Find previous leader
        last_positions = self.last_positions[session_key]
        previous_leader = None
        for driver_num, pos in last_positions.items():
            if pos == 1:
                previous_leader = driver_num
                break
        
        # Check if leadership changed
        if (current_leader and previous_leader and 
            current_leader != previous_leader):
            
            # Create driver map (handle both Driver objects and SimpleDriver objects)
            driver_map = {}
            for d in drivers:
                driver_number = getattr(d, 'driver_number', None)
                if driver_number:
                    driver_map[driver_number] = d
            
            new_leader_obj = driver_map.get(current_leader)
            previous_leader_obj = driver_map.get(previous_leader)
            new_leader_name = getattr(new_leader_obj, 'name', f"Driver {current_leader}") if new_leader_obj else f"Driver {current_leader}"
            previous_leader_name = getattr(previous_leader_obj, 'name', f"Driver {previous_leader}") if previous_leader_obj else f"Driver {previous_leader}"
            
            event = RaceEvent(
                event_type=EventType.LEAD_CHANGE,
                timestamp=datetime.utcnow(),
                session_key=session_key,
                driver_number=current_leader,
                target_driver_number=previous_leader,
                data={
                    'new_leader': new_leader_name,
                    'previous_leader': previous_leader_name
                },
                message=f"🏆 {new_leader_name} takes the lead!"
            )
            await self.emit_event(event)
    
    async def process_lap_times(self, lap_times: List[LapTime], drivers: List):
        """Process lap time data and detect fastest laps"""
        if not lap_times:
            return
            
        session_key = lap_times[0].session_key
        # Create driver map (handle both Driver objects and SimpleDriver objects)
        driver_map = {}
        for d in drivers:
            driver_number = getattr(d, 'driver_number', None)
            if driver_number:
                driver_map[driver_number] = d
        
        for lap_time in lap_times:
            driver_num = lap_time.driver_number
            current_time = lap_time.lap_time
            
            # Check if this is a new session best
            if session_key not in self.last_lap_times:
                self.last_lap_times[session_key] = {}
            
            session_best = min(self.last_lap_times[session_key].values()) if self.last_lap_times[session_key] else float('inf')
            
            if current_time < session_best:
                driver_obj = driver_map.get(driver_num)
                driver_name = getattr(driver_obj, 'name', f"Driver {driver_num}") if driver_obj else f"Driver {driver_num}"
                
                event = RaceEvent(
                    event_type=EventType.FASTEST_LAP,
                    timestamp=datetime.utcnow(),
                    session_key=session_key,
                    driver_number=driver_num,
                    lap_number=lap_time.lap_number,
                    data={
                        'driver_name': driver_name,
                        'lap_time': current_time,
                        'lap_number': lap_time.lap_number,
                        'previous_best': session_best if session_best != float('inf') else None
                    },
                    message=f"⚡ {driver_name} sets fastest lap: {current_time:.3f}s (Lap {lap_time.lap_number})"
                )
                await self.emit_event(event)
            
            # Update best time for this driver
            if driver_num not in self.last_lap_times[session_key] or current_time < self.last_lap_times[session_key][driver_num]:
                self.last_lap_times[session_key][driver_num] = current_time
    
    async def process_pit_stops(self, pit_stops: List[PitStop], drivers: List):
        """Process pit stop data and detect pit stop events"""
        # Create driver map (handle both Driver objects and SimpleDriver objects)
        driver_map = {}
        for d in drivers:
            driver_number = getattr(d, 'driver_number', None)
            if driver_number:
                driver_map[driver_number] = d
        
        for pit_stop in pit_stops:
            session_key = pit_stop.session_key
            driver_num = pit_stop.driver_number
            
            # Check if this is a new pit stop (not already processed)
            if driver_num not in self.recent_pit_stops[session_key]:
                self.recent_pit_stops[session_key].add(driver_num)
                
                driver_obj = driver_map.get(driver_num)
                driver_name = getattr(driver_obj, 'name', f"Driver {driver_num}") if driver_obj else f"Driver {driver_num}"
                
                event = RaceEvent(
                    event_type=EventType.PIT_STOP,
                    timestamp=datetime.utcnow(),
                    session_key=session_key,
                    driver_number=driver_num,
                    lap_number=pit_stop.lap_number,
                    data={
                        'driver_name': driver_name,
                        'pit_duration': pit_stop.pit_duration,
                        'lap_number': pit_stop.lap_number
                    },
                    message=f"🔧 {driver_name} pits! Duration: {pit_stop.pit_duration:.3f}s (Lap {pit_stop.lap_number})"
                )
                await self.emit_event(event)
    
    def clear_session_data(self, session_key: int):
        """Clear stored data for a specific session"""
        if session_key in self.last_positions:
            del self.last_positions[session_key]
        if session_key in self.last_lap_times:
            del self.last_lap_times[session_key]
        if session_key in self.recent_pit_stops:
            del self.recent_pit_stops[session_key]
        if session_key in self.position_history:
            del self.position_history[session_key]
        logger.info(f"Cleared data for session {session_key}")

# Global instance
race_event_detector = RaceEventDetector()