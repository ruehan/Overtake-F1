from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class SessionType(str, Enum):
    PRACTICE_1 = "Practice 1"
    PRACTICE_2 = "Practice 2"
    PRACTICE_3 = "Practice 3"
    QUALIFYING = "Qualifying"
    SPRINT_QUALIFYING = "Sprint Qualifying"
    SPRINT = "Sprint"
    RACE = "Race"

class Driver(BaseModel):
    driver_number: int = Field(..., ge=1, le=99, description="Driver number")
    name: str = Field(..., min_length=1, description="Full name of the driver")
    abbreviation: str = Field(..., min_length=3, max_length=3, description="3-letter abbreviation")
    team_name: str = Field(..., description="Current team name")
    team_colour: str = Field(..., description="Team color in hex format")
    headshot_url: Optional[str] = Field(None, description="URL to driver headshot image")
    country_code: Optional[str] = Field(None, min_length=2, max_length=3, description="Country code")
    
    @field_validator('abbreviation')
    @classmethod
    def validate_abbreviation(cls, v):
        return v.upper()
    
    @field_validator('team_colour')
    @classmethod
    def validate_team_colour(cls, v):
        # Add # prefix if not present
        if v and not v.startswith('#'):
            return f'#{v}'
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "driver_number": 44,
                "name": "Lewis Hamilton",
                "abbreviation": "HAM",
                "team_name": "Mercedes",
                "team_colour": "#00D2BE",
                "headshot_url": "https://example.com/hamilton.jpg",
                "country_code": "GBR"
            }
        }

class Team(BaseModel):
    team_name: str = Field(..., description="Team name")
    team_colour: str = Field(..., description="Team color in hex format")
    drivers: List[Dict[str, Any]] = Field(default_factory=list, description="List of drivers in the team")
    logo_url: Optional[str] = Field(None, description="URL to team logo image")
    
    @field_validator('team_colour')
    @classmethod
    def validate_team_colour(cls, v):
        # Add # prefix if not present
        if v and not v.startswith('#'):
            return f'#{v}'
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "team_name": "Mercedes",
                "team_colour": "#00D2BE",
                "drivers": [
                    {"driver_number": 44, "name": "Lewis Hamilton", "abbreviation": "HAM"},
                    {"driver_number": 63, "name": "George Russell", "abbreviation": "RUS"}
                ]
            }
        }

class Position(BaseModel):
    timestamp: int = Field(..., description="Unix timestamp")
    session_key: int = Field(..., description="Session identifier")
    driver_number: int = Field(..., ge=1, le=99, description="Driver number")
    position: Optional[int] = Field(None, ge=1, le=20, description="Race position")
    x_position: float = Field(..., description="X coordinate on track")
    y_position: float = Field(..., description="Y coordinate on track")
    z_position: float = Field(..., description="Z coordinate on track")
    speed: Optional[float] = Field(None, ge=0, description="Speed in km/h")
    drs: Optional[bool] = Field(None, description="DRS status")
    
    class Config:
        json_schema_extra = {
            "example": {
                "timestamp": 1672531200,
                "session_key": 9158,
                "driver_number": 44,
                "position": 1,
                "x_position": 1500.5,
                "y_position": 800.2,
                "z_position": 10.1,
                "speed": 285.5,
                "drs": True
            }
        }

class Session(BaseModel):
    session_key: int = Field(..., description="Unique session identifier")
    session_name: str = Field(..., description="Session name")
    session_type: SessionType = Field(..., description="Type of session")
    country: str = Field(..., description="Country where session takes place")
    circuit: str = Field(..., description="Circuit name")
    date: str = Field(..., description="Session date in ISO format")
    status: Optional[str] = Field(None, description="Session status")
    year: Optional[int] = Field(None, ge=1950, le=2030, description="Season year")
    
    class Config:
        json_schema_extra = {
            "example": {
                "session_key": 9158,
                "session_name": "Race",
                "session_type": "Race",
                "country": "Bahrain",
                "circuit": "Bahrain International Circuit",
                "date": "2024-03-02T15:00:00Z",
                "status": "Finished",
                "year": 2024
            }
        }

class Weather(BaseModel):
    timestamp: int = Field(..., description="Unix timestamp")
    session_key: int = Field(..., description="Session identifier")
    air_temperature: float = Field(..., description="Air temperature in Celsius")
    track_temperature: float = Field(..., description="Track temperature in Celsius")
    humidity: float = Field(..., ge=0, le=100, description="Humidity percentage")
    wind_speed: float = Field(..., ge=0, description="Wind speed in km/h")
    wind_direction: Optional[float] = Field(None, ge=0, le=360, description="Wind direction in degrees")
    pressure: float = Field(..., ge=800, le=1200, description="Atmospheric pressure in hPa")
    rainfall: Optional[float] = Field(None, ge=0, description="Rainfall in mm")
    
    class Config:
        json_schema_extra = {
            "example": {
                "timestamp": 1672531200,
                "session_key": 9158,
                "air_temperature": 28.5,
                "track_temperature": 45.2,
                "humidity": 65.0,
                "wind_speed": 12.5,
                "wind_direction": 180.0,
                "pressure": 1013.25,
                "rainfall": 0.0
            }
        }

class LapTime(BaseModel):
    driver_number: int = Field(..., ge=1, le=99, description="Driver number")
    session_key: int = Field(..., description="Session identifier")
    lap_number: int = Field(..., ge=1, description="Lap number")
    lap_time: float = Field(..., gt=0, description="Lap time in seconds")
    sector_1: Optional[float] = Field(None, gt=0, description="Sector 1 time in seconds")
    sector_2: Optional[float] = Field(None, gt=0, description="Sector 2 time in seconds")
    sector_3: Optional[float] = Field(None, gt=0, description="Sector 3 time in seconds")
    is_personal_best: Optional[bool] = Field(False, description="Is this a personal best lap")
    timestamp: int = Field(..., description="Unix timestamp")
    
    @field_validator('lap_time')
    @classmethod
    def validate_lap_time(cls, v):
        # Reasonable lap time validation (between 1 minute and 5 minutes)
        if not (60 <= v <= 300):
            raise ValueError('Lap time must be between 60 and 300 seconds')
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "driver_number": 44,
                "session_key": 9158,
                "lap_number": 15,
                "lap_time": 89.567,
                "sector_1": 28.234,
                "sector_2": 31.567,
                "sector_3": 29.766,
                "is_personal_best": True,
                "timestamp": 1672531200
            }
        }

class PitStop(BaseModel):
    driver_number: int = Field(..., ge=1, le=99, description="Driver number")
    session_key: int = Field(..., description="Session identifier")
    pit_duration: float = Field(..., gt=0, description="Pit stop duration in seconds")
    lap_number: int = Field(..., ge=1, description="Lap number when pit stop occurred")
    timestamp: int = Field(..., description="Unix timestamp")
    
    @field_validator('pit_duration')
    @classmethod
    def validate_pit_duration(cls, v):
        # Reasonable pit stop duration (2-60 seconds)
        if not (2 <= v <= 60):
            raise ValueError('Pit stop duration must be between 2 and 60 seconds')
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "driver_number": 44,
                "session_key": 9158,
                "pit_duration": 2.456,
                "lap_number": 25,
                "timestamp": 1672531200
            }
        }

class TeamRadio(BaseModel):
    id: str = Field(..., description="Unique identifier for the radio message")
    driver_number: int = Field(..., ge=1, le=99, description="Driver number")
    driver_name: str = Field(..., description="Driver name")
    team_name: str = Field(..., description="Team name")
    timestamp: int = Field(..., description="Unix timestamp")
    audio_url: str = Field(..., description="URL to audio file")
    transcript: Optional[str] = Field(None, description="Transcript of the radio message")
    duration: Optional[float] = Field(None, gt=0, description="Duration in seconds")
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "radio_44_1672531200",
                "driver_number": 44,
                "driver_name": "Lewis Hamilton",
                "team_name": "Mercedes",
                "timestamp": 1672531200,
                "audio_url": "https://example.com/radio/44_1672531200.mp3",
                "transcript": "Box, box, box this lap",
                "duration": 3.2
            }
        }

# Response models for API endpoints
class DriversResponse(BaseModel):
    drivers: List[Driver]
    total: int
    session_key: Optional[int] = None

class PositionsResponse(BaseModel):
    positions: List[Position]
    total: int
    session_key: int

class WeatherResponse(BaseModel):
    weather_data: List[Weather]
    latest: Optional[Weather] = None
    session_key: int

class LapTimesResponse(BaseModel):
    lap_times: List[LapTime]
    total: int
    session_key: int
    driver_number: Optional[int] = None