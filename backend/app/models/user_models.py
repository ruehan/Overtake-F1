from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class AlertType(str, Enum):
    OVERTAKES = "overtakes"
    PIT_STOPS = "pit_stops"
    LEAD_CHANGES = "lead_changes"
    FASTEST_LAPS = "fastest_laps"
    WEATHER_CHANGES = "weather_changes"
    INCIDENTS = "incidents"

class DashboardWidget(str, Enum):
    LIVE_MAP = "live_map"
    DRIVER_STANDINGS = "driver_standings"
    WEATHER = "weather"
    RECENT_RADIO = "recent_radio"
    LAP_TIMES = "lap_times"
    PIT_STOPS = "pit_stops"

class UserPreferences(BaseModel):
    user_id: str = Field(..., description="Unique user identifier")
    favorite_drivers: List[int] = Field(default_factory=list, description="List of favorite driver numbers")
    favorite_teams: List[str] = Field(default_factory=list, description="List of favorite team names")
    alert_settings: Dict[AlertType, bool] = Field(
        default_factory=lambda: {
            AlertType.OVERTAKES: True,
            AlertType.PIT_STOPS: True,
            AlertType.LEAD_CHANGES: True,
            AlertType.FASTEST_LAPS: False,
            AlertType.WEATHER_CHANGES: False,
            AlertType.INCIDENTS: True
        },
        description="Alert preferences"
    )
    dashboard_layout: Dict[DashboardWidget, bool] = Field(
        default_factory=lambda: {
            DashboardWidget.LIVE_MAP: True,
            DashboardWidget.DRIVER_STANDINGS: True,
            DashboardWidget.WEATHER: True,
            DashboardWidget.RECENT_RADIO: False,
            DashboardWidget.LAP_TIMES: True,
            DashboardWidget.PIT_STOPS: True
        },
        description="Dashboard widget visibility"
    )
    theme: str = Field(default="light", description="UI theme preference")
    timezone: str = Field(default="UTC", description="User timezone")
    language: str = Field(default="en", description="Language preference")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Created timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last updated timestamp")
    
    @field_validator('favorite_drivers')
    @classmethod
    def validate_favorite_drivers(cls, v):
        # Validate driver numbers are in valid range
        for driver_num in v:
            if not (1 <= driver_num <= 99):
                raise ValueError(f'Invalid driver number: {driver_num}')
        return list(set(v))  # Remove duplicates
    
    @field_validator('theme')
    @classmethod
    def validate_theme(cls, v):
        if v not in ['light', 'dark', 'auto']:
            raise ValueError('Theme must be light, dark, or auto')
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "user_123",
                "favorite_drivers": [44, 1, 16],
                "favorite_teams": ["Mercedes", "Red Bull Racing"],
                "alert_settings": {
                    "overtakes": True,
                    "pit_stops": True,
                    "lead_changes": True,
                    "fastest_laps": False,
                    "weather_changes": False,
                    "incidents": True
                },
                "dashboard_layout": {
                    "live_map": True,
                    "driver_standings": True,
                    "weather": True,
                    "recent_radio": False,
                    "lap_times": True,
                    "pit_stops": True
                },
                "theme": "dark",
                "timezone": "Europe/London",
                "language": "en"
            }
        }

class UserSession(BaseModel):
    session_id: str = Field(..., description="Session identifier")
    user_id: str = Field(..., description="User identifier")
    ip_address: str = Field(..., description="User IP address")
    user_agent: str = Field(..., description="User agent string")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Session created timestamp")
    last_activity: datetime = Field(default_factory=datetime.utcnow, description="Last activity timestamp")
    is_active: bool = Field(default=True, description="Session status")
    
    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "sess_123456789",
                "user_id": "user_123",
                "ip_address": "192.168.1.1",
                "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "is_active": True
            }
        }

class CacheEntry(BaseModel):
    key: str = Field(..., description="Cache key")
    data: Dict[str, Any] = Field(..., description="Cached data")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Cache created timestamp")
    expires_at: datetime = Field(..., description="Cache expiration timestamp")
    hit_count: int = Field(default=0, description="Number of cache hits")
    
    @property
    def is_expired(self) -> bool:
        return datetime.utcnow() > self.expires_at
    
    class Config:
        json_schema_extra = {
            "example": {
                "key": "drivers_session_9158",
                "data": {"drivers": []},
                "expires_at": "2024-03-02T16:00:00Z",
                "hit_count": 5
            }
        }

# Request/Response models for user preferences API
class UpdateUserPreferencesRequest(BaseModel):
    favorite_drivers: Optional[List[int]] = None
    favorite_teams: Optional[List[str]] = None
    alert_settings: Optional[Dict[AlertType, bool]] = None
    dashboard_layout: Optional[Dict[DashboardWidget, bool]] = None
    theme: Optional[str] = None
    timezone: Optional[str] = None
    language: Optional[str] = None

class UserPreferencesResponse(BaseModel):
    preferences: UserPreferences
    message: str = "User preferences retrieved successfully"