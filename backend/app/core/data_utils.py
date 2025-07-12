from typing import List, Dict, Any, Optional, Union, Tuple
from datetime import datetime, timezone
import math
from functools import wraps

from app.models.f1_models import Driver, Position, LapTime, Weather

class DataTransformationUtils:
    """Utility class for transforming F1 data"""
    
    @staticmethod
    def normalize_driver_data(raw_driver: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize driver data from OpenF1 API"""
        return {
            "driver_number": raw_driver.get("driver_number"),
            "name": raw_driver.get("full_name") or raw_driver.get("name", "Unknown"),
            "abbreviation": (raw_driver.get("name_acronym") or raw_driver.get("abbreviation", "UNK")).upper(),
            "team_name": raw_driver.get("team_name", "Unknown Team"),
            "team_colour": raw_driver.get("team_colour", "#000000"),
            "headshot_url": raw_driver.get("headshot_url"),
            "country_code": raw_driver.get("country_code")
        }
    
    @staticmethod
    def normalize_position_data(raw_position: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize position data from OpenF1 API"""
        return {
            "timestamp": int(raw_position.get("date", 0)) if raw_position.get("date") else int(datetime.utcnow().timestamp()),
            "session_key": raw_position.get("session_key"),
            "driver_number": raw_position.get("driver_number"),
            "position": raw_position.get("position"),
            "x_position": float(raw_position.get("x", 0)),
            "y_position": float(raw_position.get("y", 0)),
            "z_position": float(raw_position.get("z", 0)),
            "speed": float(raw_position.get("speed", 0)) if raw_position.get("speed") else None,
            "drs": raw_position.get("drs")
        }
    
    @staticmethod
    def normalize_weather_data(raw_weather: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize weather data from OpenF1 API"""
        return {
            "timestamp": int(raw_weather.get("date", 0)) if raw_weather.get("date") else int(datetime.utcnow().timestamp()),
            "session_key": raw_weather.get("session_key"),
            "air_temperature": float(raw_weather.get("air_temperature", 0)),
            "track_temperature": float(raw_weather.get("track_temperature", 0)),
            "humidity": float(raw_weather.get("humidity", 0)),
            "wind_speed": float(raw_weather.get("wind_speed", 0)),
            "wind_direction": float(raw_weather.get("wind_direction", 0)) if raw_weather.get("wind_direction") else None,
            "pressure": float(raw_weather.get("pressure", 1013.25)),
            "rainfall": float(raw_weather.get("rainfall", 0)) if raw_weather.get("rainfall") else None
        }
    
    @staticmethod
    def normalize_lap_time_data(raw_lap: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize lap time data from OpenF1 API"""
        lap_time = raw_lap.get("lap_duration")
        if isinstance(lap_time, str):
            # Convert time string to seconds if needed
            lap_time = DataTransformationUtils.time_string_to_seconds(lap_time)
        
        return {
            "driver_number": raw_lap.get("driver_number"),
            "session_key": raw_lap.get("session_key"),
            "lap_number": raw_lap.get("lap_number"),
            "lap_time": float(lap_time) if lap_time else 0,
            "sector_1": float(raw_lap.get("duration_sector_1", 0)) if raw_lap.get("duration_sector_1") else None,
            "sector_2": float(raw_lap.get("duration_sector_2", 0)) if raw_lap.get("duration_sector_2") else None,
            "sector_3": float(raw_lap.get("duration_sector_3", 0)) if raw_lap.get("duration_sector_3") else None,
            "is_personal_best": raw_lap.get("is_personal_best", False),
            "timestamp": int(raw_lap.get("date", 0)) if raw_lap.get("date") else int(datetime.utcnow().timestamp())
        }
    
    @staticmethod
    def time_string_to_seconds(time_str: str) -> float:
        """Convert time string (e.g., '1:23.456') to seconds"""
        if not time_str:
            return 0.0
        
        try:
            # Handle different time formats
            if ':' in time_str:
                parts = time_str.split(':')
                minutes = float(parts[0])
                seconds = float(parts[1])
                return minutes * 60 + seconds
            else:
                return float(time_str)
        except (ValueError, IndexError):
            return 0.0
    
    @staticmethod
    def seconds_to_time_string(seconds: float) -> str:
        """Convert seconds to time string (e.g., 83.456 -> '1:23.456')"""
        if seconds <= 0:
            return "0:00.000"
        
        minutes = int(seconds // 60)
        remaining_seconds = seconds % 60
        return f"{minutes}:{remaining_seconds:06.3f}"
    
    @staticmethod
    def calculate_distance(pos1: Position, pos2: Position) -> float:
        """Calculate distance between two positions in meters"""
        dx = pos2.x_position - pos1.x_position
        dy = pos2.y_position - pos1.y_position
        dz = pos2.z_position - pos1.z_position
        return math.sqrt(dx*dx + dy*dy + dz*dz)
    
    @staticmethod
    def calculate_speed_kmh(pos1: Position, pos2: Position) -> float:
        """Calculate speed in km/h between two positions"""
        if pos1.timestamp >= pos2.timestamp:
            return 0.0
        
        distance_m = DataTransformationUtils.calculate_distance(pos1, pos2)
        time_s = pos2.timestamp - pos1.timestamp
        
        if time_s <= 0:
            return 0.0
        
        speed_ms = distance_m / time_s
        speed_kmh = speed_ms * 3.6
        return speed_kmh
    
    @staticmethod
    def group_positions_by_driver(positions: List[Position]) -> Dict[int, List[Position]]:
        """Group positions by driver number"""
        grouped = {}
        for position in positions:
            driver_num = position.driver_number
            if driver_num not in grouped:
                grouped[driver_num] = []
            grouped[driver_num].append(position)
        
        # Sort positions by timestamp for each driver
        for driver_num in grouped:
            grouped[driver_num].sort(key=lambda p: p.timestamp)
        
        return grouped
    
    @staticmethod
    def get_latest_positions(positions: List[Position]) -> Dict[int, Position]:
        """Get the latest position for each driver"""
        latest = {}
        for position in positions:
            driver_num = position.driver_number
            if (driver_num not in latest or 
                position.timestamp > latest[driver_num].timestamp):
                latest[driver_num] = position
        
        return latest
    
    @staticmethod
    def calculate_lap_time_statistics(lap_times: List[LapTime]) -> Dict[str, Any]:
        """Calculate lap time statistics"""
        if not lap_times:
            return {}
        
        times = [lt.lap_time for lt in lap_times if lt.lap_time > 0]
        if not times:
            return {}
        
        times.sort()
        
        return {
            "count": len(times),
            "fastest": min(times),
            "slowest": max(times),
            "average": sum(times) / len(times),
            "median": times[len(times) // 2],
            "std_deviation": DataTransformationUtils._calculate_std_dev(times)
        }
    
    @staticmethod
    def _calculate_std_dev(values: List[float]) -> float:
        """Calculate standard deviation"""
        if len(values) < 2:
            return 0.0
        
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / (len(values) - 1)
        return math.sqrt(variance)
    
    @staticmethod
    def detect_overtakes(
        previous_positions: Dict[int, Position], 
        current_positions: Dict[int, Position]
    ) -> List[Dict[str, Any]]:
        """Detect overtakes between two position snapshots"""
        overtakes = []
        
        # Create position mappings
        prev_order = {pos.driver_number: pos.position for pos in previous_positions.values() if pos.position}
        curr_order = {pos.driver_number: pos.position for pos in current_positions.values() if pos.position}
        
        for driver_num, curr_pos in curr_order.items():
            prev_pos = prev_order.get(driver_num)
            
            if prev_pos and prev_pos > curr_pos:
                # This driver gained position(s)
                positions_gained = prev_pos - curr_pos
                
                # Find who was overtaken
                overtaken_drivers = [
                    other_driver for other_driver, other_curr_pos in curr_order.items()
                    if (other_driver != driver_num and 
                        other_curr_pos > curr_pos and 
                        other_curr_pos <= prev_pos and
                        prev_order.get(other_driver, 999) < prev_pos)
                ]
                
                for overtaken_driver in overtaken_drivers:
                    overtakes.append({
                        "overtaking_driver": driver_num,
                        "overtaken_driver": overtaken_driver,
                        "new_position": curr_pos,
                        "positions_gained": positions_gained,
                        "timestamp": max(pos.timestamp for pos in current_positions.values())
                    })
        
        return overtakes
    
    @staticmethod
    def convert_timezone_timestamp(timestamp: int, from_tz: str = "UTC", to_tz: str = "UTC") -> int:
        """Convert timestamp from one timezone to another"""
        # For now, just return the timestamp as-is
        # In a full implementation, you'd use pytz or zoneinfo
        return timestamp
    
    @staticmethod
    def validate_and_clean_data(data: Dict[str, Any], required_fields: List[str]) -> Dict[str, Any]:
        """Validate and clean data dictionary"""
        cleaned = {}
        
        for field in required_fields:
            if field in data and data[field] is not None:
                cleaned[field] = data[field]
            else:
                # Set default values based on field type expectations
                if field.endswith('_number') or field.endswith('_key'):
                    cleaned[field] = 0
                elif field.endswith('_position') or field.endswith('_time'):
                    cleaned[field] = 0.0
                elif field.endswith('_name'):
                    cleaned[field] = "Unknown"
                else:
                    cleaned[field] = None
        
        return cleaned

# Decorator for data transformation
def transform_response(transformer_func):
    """Decorator to transform API response data"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            result = await func(*args, **kwargs)
            
            if isinstance(result, list):
                return [transformer_func(item) for item in result]
            elif isinstance(result, dict):
                return transformer_func(result)
            else:
                return result
        
        return wrapper
    return decorator

# Specific transformers
normalize_drivers_response = transform_response(DataTransformationUtils.normalize_driver_data)
normalize_positions_response = transform_response(DataTransformationUtils.normalize_position_data)
normalize_weather_response = transform_response(DataTransformationUtils.normalize_weather_data)
normalize_lap_times_response = transform_response(DataTransformationUtils.normalize_lap_time_data)