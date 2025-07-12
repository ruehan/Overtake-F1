from pydantic_settings import BaseSettings
from typing import Optional
import os

class Settings(BaseSettings):
    # API Settings
    api_v1_str: str = "/api/v1"
    project_name: str = "OpenF1 Dashboard"
    
    # OpenF1 API
    openf1_api_base_url: str = "https://api.openf1.org/v1"
    openf1_api_key: Optional[str] = None
    
    # Database
    database_url: str = "sqlite+aiosqlite:///./openf1_dashboard.db"
    
    # Redis
    redis_url: str = "redis://localhost:6379"
    
    # Cache settings
    cache_default_ttl: int = 300  # 5 minutes
    cache_drivers_ttl: int = 600  # 10 minutes
    cache_sessions_ttl: int = 3600  # 1 hour
    cache_positions_ttl: int = 10  # 10 seconds for real-time data
    
    # Rate limiting
    rate_limit_per_minute: int = 60
    rate_limit_burst: int = 10
    
    # WebSocket
    websocket_ping_interval: int = 25
    websocket_ping_timeout: int = 60
    
    # Data validation
    enable_data_validation: bool = True
    strict_validation: bool = False  # If True, reject invalid data; if False, log warnings
    
    # Environment
    environment: str = "development"
    debug: bool = True
    
    class Config:
        env_file = ".env"
        case_sensitive = False

settings = Settings()