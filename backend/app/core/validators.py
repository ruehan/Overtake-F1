from typing import Any, Dict, List, Optional, Union, Callable
from datetime import datetime
import re
from functools import wraps
import logging

from pydantic import ValidationError
from app.models.f1_models import Driver, Position, Weather, LapTime, Session, TeamRadio, PitStop
from app.models.user_models import UserPreferences

logger = logging.getLogger(__name__)

class ValidationResult:
    """Result of a validation operation"""
    
    def __init__(self, is_valid: bool = True, errors: List[str] = None, warnings: List[str] = None):
        self.is_valid = is_valid
        self.errors = errors or []
        self.warnings = warnings or []
    
    def add_error(self, error: str):
        """Add an error to the result"""
        self.errors.append(error)
        self.is_valid = False
    
    def add_warning(self, warning: str):
        """Add a warning to the result"""
        self.warnings.append(warning)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "is_valid": self.is_valid,
            "errors": self.errors,
            "warnings": self.warnings
        }

class F1DataValidator:
    """Validator for F1 data"""
    
    # Valid F1 driver number ranges
    VALID_DRIVER_NUMBERS = list(range(1, 100))
    
    # Valid team colors (basic color validation)
    COLOR_PATTERN = re.compile(r'^#[0-9A-Fa-f]{6}$')
    
    # Valid session types
    VALID_SESSION_TYPES = [
        "Practice 1", "Practice 2", "Practice 3", 
        "Qualifying", "Sprint Qualifying", "Sprint", "Race"
    ]
    
    @staticmethod
    def validate_driver_data(data: Dict[str, Any]) -> ValidationResult:
        """Validate driver data"""
        result = ValidationResult()
        
        try:
            # Try to create Pydantic model (this will catch basic validation errors)
            Driver(**data)
        except ValidationError as e:
            for error in e.errors():
                result.add_error(f"Driver validation: {error['msg']} for field '{error['loc'][0]}'")
            return result
        
        # Additional business logic validation
        driver_number = data.get('driver_number')
        if driver_number and driver_number not in F1DataValidator.VALID_DRIVER_NUMBERS:
            result.add_error(f"Invalid driver number: {driver_number}")
        
        # Check team color format
        team_colour = data.get('team_colour')
        if team_colour and not F1DataValidator.COLOR_PATTERN.match(team_colour):
            result.add_error(f"Invalid team color format: {team_colour}")
        
        # Check abbreviation format
        abbreviation = data.get('abbreviation', '')
        if len(abbreviation) != 3:
            result.add_error(f"Driver abbreviation must be exactly 3 characters: {abbreviation}")
        elif not abbreviation.isupper():
            result.add_warning(f"Driver abbreviation should be uppercase: {abbreviation}")
        
        return result
    
    @staticmethod
    def validate_position_data(data: Dict[str, Any]) -> ValidationResult:
        """Validate position data"""
        result = ValidationResult()
        
        try:
            Position(**data)
        except ValidationError as e:
            for error in e.errors():
                result.add_error(f"Position validation: {error['msg']} for field '{error['loc'][0]}'")
            return result
        
        # Additional validation
        speed = data.get('speed')
        if speed is not None:
            if speed < 0:
                result.add_error("Speed cannot be negative")
            elif speed > 400:  # F1 cars don't go over 400 km/h typically
                result.add_warning(f"Unusually high speed: {speed} km/h")
        
        # Check position reasonableness
        position = data.get('position')
        if position is not None and (position < 1 or position > 20):
            result.add_warning(f"Unusual race position: {position}")
        
        return result
    
    @staticmethod
    def validate_weather_data(data: Dict[str, Any]) -> ValidationResult:
        """Validate weather data"""
        result = ValidationResult()
        
        try:
            Weather(**data)
        except ValidationError as e:
            for error in e.errors():
                result.add_error(f"Weather validation: {error['msg']} for field '{error['loc'][0]}'")
            return result
        
        # Additional validation
        air_temp = data.get('air_temperature')
        if air_temp is not None:
            if air_temp < -30 or air_temp > 60:
                result.add_warning(f"Unusual air temperature: {air_temp}°C")
        
        track_temp = data.get('track_temperature')
        if track_temp is not None:
            if track_temp < -30 or track_temp > 80:
                result.add_warning(f"Unusual track temperature: {track_temp}°C")
        
        humidity = data.get('humidity')
        if humidity is not None and (humidity < 0 or humidity > 100):
            result.add_error(f"Humidity must be between 0 and 100: {humidity}")
        
        return result
    
    @staticmethod
    def validate_lap_time_data(data: Dict[str, Any]) -> ValidationResult:
        """Validate lap time data"""
        result = ValidationResult()
        
        try:
            LapTime(**data)
        except ValidationError as e:
            for error in e.errors():
                result.add_error(f"Lap time validation: {error['msg']} for field '{error['loc'][0]}'")
            return result
        
        # Additional validation
        lap_time = data.get('lap_time')
        if lap_time is not None:
            if lap_time < 60:  # Fastest F1 lap is around 60 seconds
                result.add_warning(f"Unusually fast lap time: {lap_time} seconds")
            elif lap_time > 300:  # 5 minutes is very slow
                result.add_warning(f"Unusually slow lap time: {lap_time} seconds")
        
        # Validate sector times add up to lap time
        sectors = [data.get('sector_1'), data.get('sector_2'), data.get('sector_3')]
        if all(s is not None for s in sectors) and lap_time is not None:
            sector_sum = sum(sectors)
            if abs(sector_sum - lap_time) > 1.0:  # Allow 1 second tolerance
                result.add_warning(f"Sector times ({sector_sum:.3f}s) don't match lap time ({lap_time:.3f}s)")
        
        return result
    
    @staticmethod
    def validate_session_data(data: Dict[str, Any]) -> ValidationResult:
        """Validate session data"""
        result = ValidationResult()
        
        try:
            Session(**data)
        except ValidationError as e:
            for error in e.errors():
                result.add_error(f"Session validation: {error['msg']} for field '{error['loc'][0]}'")
            return result
        
        # Additional validation
        session_type = data.get('session_type')
        if session_type and session_type not in F1DataValidator.VALID_SESSION_TYPES:
            result.add_warning(f"Unusual session type: {session_type}")
        
        year = data.get('year')
        current_year = datetime.now().year
        if year is not None and (year < 1950 or year > current_year + 1):
            result.add_error(f"Invalid year: {year}")
        
        return result
    
    @staticmethod
    def validate_user_preferences(data: Dict[str, Any]) -> ValidationResult:
        """Validate user preferences data"""
        result = ValidationResult()
        
        try:
            UserPreferences(**data)
        except ValidationError as e:
            for error in e.errors():
                result.add_error(f"User preferences validation: {error['msg']} for field '{error['loc'][0]}'")
            return result
        
        # Additional validation
        favorite_drivers = data.get('favorite_drivers', [])
        if len(favorite_drivers) > 10:
            result.add_warning("More than 10 favorite drivers selected")
        
        favorite_teams = data.get('favorite_teams', [])
        if len(favorite_teams) > 5:
            result.add_warning("More than 5 favorite teams selected")
        
        return result

class DataIntegrityValidator:
    """Validator for data integrity and consistency"""
    
    @staticmethod
    def validate_data_consistency(
        drivers: List[Dict[str, Any]], 
        positions: List[Dict[str, Any]]
    ) -> ValidationResult:
        """Validate consistency between drivers and positions data"""
        result = ValidationResult()
        
        driver_numbers = {d.get('driver_number') for d in drivers}
        position_driver_numbers = {p.get('driver_number') for p in positions}
        
        # Check if all position data has corresponding driver data
        missing_drivers = position_driver_numbers - driver_numbers
        if missing_drivers:
            result.add_warning(f"Position data exists for drivers not in driver list: {missing_drivers}")
        
        # Check for duplicate driver numbers
        driver_number_list = [d.get('driver_number') for d in drivers]
        duplicates = set([x for x in driver_number_list if driver_number_list.count(x) > 1])
        if duplicates:
            result.add_error(f"Duplicate driver numbers found: {duplicates}")
        
        return result
    
    @staticmethod
    def validate_temporal_consistency(
        positions: List[Dict[str, Any]], 
        max_time_gap: int = 300  # 5 minutes
    ) -> ValidationResult:
        """Validate temporal consistency in position data"""
        result = ValidationResult()
        
        if len(positions) < 2:
            return result
        
        # Sort by timestamp
        sorted_positions = sorted(positions, key=lambda x: x.get('timestamp', 0))
        
        for i in range(1, len(sorted_positions)):
            prev_time = sorted_positions[i-1].get('timestamp', 0)
            curr_time = sorted_positions[i].get('timestamp', 0)
            
            if curr_time < prev_time:
                result.add_error(f"Timestamps out of order: {prev_time} -> {curr_time}")
            elif curr_time - prev_time > max_time_gap:
                result.add_warning(f"Large time gap: {curr_time - prev_time} seconds")
        
        return result

# Validation decorators
def validate_input(validator_func: Callable):
    """Decorator to validate input data"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Find data in kwargs
            data = kwargs.get('data') or (args[1] if len(args) > 1 else None)
            
            if data:
                validation_result = validator_func(data)
                if not validation_result.is_valid:
                    logger.error(f"Validation failed for {func.__name__}: {validation_result.errors}")
                    raise ValueError(f"Validation errors: {', '.join(validation_result.errors)}")
                
                if validation_result.warnings:
                    logger.warning(f"Validation warnings for {func.__name__}: {validation_result.warnings}")
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator

def validate_response(validator_func: Callable):
    """Decorator to validate response data"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            result = await func(*args, **kwargs)
            
            if isinstance(result, list):
                for item in result:
                    validation_result = validator_func(item)
                    if not validation_result.is_valid:
                        logger.error(f"Response validation failed: {validation_result.errors}")
            elif isinstance(result, dict):
                validation_result = validator_func(result)
                if not validation_result.is_valid:
                    logger.error(f"Response validation failed: {validation_result.errors}")
            
            return result
        return wrapper
    return decorator

# Specific validation decorators
validate_driver_input = validate_input(F1DataValidator.validate_driver_data)
validate_position_input = validate_input(F1DataValidator.validate_position_data)
validate_weather_input = validate_input(F1DataValidator.validate_weather_data)
validate_lap_time_input = validate_input(F1DataValidator.validate_lap_time_data)

validate_driver_response = validate_response(F1DataValidator.validate_driver_data)
validate_position_response = validate_response(F1DataValidator.validate_position_data)
validate_weather_response = validate_response(F1DataValidator.validate_weather_data)