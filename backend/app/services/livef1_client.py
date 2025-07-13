import asyncio
from typing import Optional, Dict, Any, List
from datetime import datetime
import logging

import livef1
from livef1 import get_season, get_session, get_meeting
from livef1.api import livetimingF1_request

from app.config import settings
from app.core.exceptions import OpenF1APIException
from app.services.cache_service import cache_service, cached

logger = logging.getLogger(__name__)

class LiveF1Client:
    def __init__(self):
        self.current_season = None
        self.current_session = None
        self._cache = {}
    
    async def _get_current_season(self, year: Optional[int] = None) -> Any:
        if year is None:
            year = datetime.now().year
        
        if self.current_season is None or getattr(self.current_season, 'year', None) != year:
            try:
                self.current_season = get_season(year)
                logger.info(f"Loaded season {year} with {len(self.current_season.meetings)} meetings")
            except Exception as e:
                logger.error(f"Failed to load season {year}: {e}")
                raise OpenF1APIException(f"Failed to load season {year}: {str(e)}")
        
        return self.current_season
    
    async def _livef1_request(self, endpoint: str, **kwargs) -> Any:
        try:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None, 
                lambda: livetimingF1_request(endpoint, **kwargs)
            )
            return result
        except Exception as e:
            logger.warning(f"LiveF1 API request failed for {endpoint}: {e}")
            return None
    
    @cached(namespace="livef1_drivers", ttl_seconds=600)
    async def get_drivers(self, session_key: Optional[int] = None) -> List[Dict[str, Any]]:
        try:
            if session_key:
                session = await self._get_session_by_key(session_key)
                if session and hasattr(session, 'drivers'):
                    drivers_data = session.drivers
                    if drivers_data is not None and not drivers_data.empty:
                        return drivers_data.to_dict('records')
            
            data = await self._livef1_request("DriverList")
            if data:
                drivers = []
                for driver_num, driver_info in data.items():
                    drivers.append({
                        "driver_number": int(driver_num),
                        "full_name": driver_info.get("FullName", ""),
                        "name": driver_info.get("LastName", ""),
                        "abbreviation": driver_info.get("Tla", ""),
                        "team_name": driver_info.get("TeamName", ""),
                        "team_colour": driver_info.get("TeamColour", "#000000"),
                        "country_code": driver_info.get("CountryCode", ""),
                        "headshot_url": driver_info.get("HeadshotUrl", "")
                    })
                return drivers
            
            season = await self._get_current_season()
            if season and hasattr(season, 'meetings') and season.meetings:
                latest_meeting = season.meetings[-1]
                if hasattr(latest_meeting, 'sessions') and latest_meeting.sessions:
                    latest_session = latest_meeting.sessions[-1]
                    if hasattr(latest_session, 'drivers'):
                        drivers_data = latest_session.drivers
                        if drivers_data is not None and not drivers_data.empty:
                            return drivers_data.to_dict('records')
            
            return []
            
        except Exception as e:
            logger.error(f"Failed to get drivers: {e}")
            raise OpenF1APIException(f"Failed to get drivers: {str(e)}")
    
    @cached(namespace="livef1_teams", ttl_seconds=600)
    async def get_teams(self, session_key: Optional[int] = None) -> List[Dict[str, Any]]:
        try:
            drivers = await self.get_drivers(session_key)
            teams = {}
            
            for driver in drivers:
                team_name = driver.get("team_name")
                if team_name and team_name not in teams:
                    teams[team_name] = {
                        "team_name": team_name,
                        "team_colour": driver.get("team_colour", "#000000"),
                        "drivers": []
                    }
                if team_name:
                    teams[team_name]["drivers"].append({
                        "driver_number": driver.get("driver_number"),
                        "name": driver.get("name"),
                        "abbreviation": driver.get("abbreviation")
                    })
            
            return list(teams.values())
            
        except Exception as e:
            logger.error(f"Failed to get teams: {e}")
            raise OpenF1APIException(f"Failed to get teams: {str(e)}")
    
    async def get_positions(
        self,
        session_key: Optional[int] = None,
        driver_number: Optional[int] = None,
        date: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        try:
            data = await self._livef1_request("Position")
            if data:
                positions = []
                for timestamp, pos_data in data.items():
                    for driver_num, position in pos_data.items():
                        if driver_number and int(driver_num) != driver_number:
                            continue
                        
                        positions.append({
                            "driver_number": int(driver_num),
                            "date": timestamp,
                            "position": position.get("Status", 0),
                            "x": position.get("X", 0),
                            "y": position.get("Y", 0),
                            "z": position.get("Z", 0)
                        })
                return positions
            
            return []
            
        except Exception as e:
            logger.error(f"Failed to get positions: {e}")
            return []
    
    @cached(namespace="livef1_sessions", ttl_seconds=3600)
    async def get_sessions(
        self,
        year: Optional[int] = None,
        country: Optional[str] = None,
        session_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        try:
            season = await self._get_current_season(year)
            if not season or not hasattr(season, 'meetings'):
                return []
            
            sessions = []
            for meeting in season.meetings:
                if hasattr(meeting, 'sessions'):
                    for session in meeting.sessions:
                        session_info = {
                            "session_key": getattr(session, 'session_key', None),
                            "session_name": getattr(session, 'session_name', ''),
                            "session_type": getattr(session, 'session_type', ''),
                            "date_start": getattr(session, 'date_start', None),
                            "date_end": getattr(session, 'date_end', None),
                            "circuit_short_name": getattr(meeting, 'circuit_short_name', ''),
                            "country_name": getattr(meeting, 'country_name', ''),
                            "meeting_key": getattr(meeting, 'meeting_key', None)
                        }
                        
                        if country and country.lower() not in session_info.get("country_name", "").lower():
                            continue
                        if session_type and session_type.lower() not in session_info.get("session_type", "").lower():
                            continue
                        
                        sessions.append(session_info)
            
            return sessions
            
        except Exception as e:
            logger.error(f"Failed to get sessions: {e}")
            raise OpenF1APIException(f"Failed to get sessions: {str(e)}")
    
    async def _get_session_by_key(self, session_key: int) -> Any:
        try:
            if self.current_session and getattr(self.current_session, 'session_key', None) == session_key:
                return self.current_session
            
            season = await self._get_current_season()
            if season and hasattr(season, 'meetings'):
                for meeting in season.meetings:
                    if hasattr(meeting, 'sessions'):
                        for session in meeting.sessions:
                            if getattr(session, 'session_key', None) == session_key:
                                self.current_session = session
                                return session
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get session by key {session_key}: {e}")
            return None
    
    async def get_weather(
        self,
        session_key: Optional[int] = None,
        date: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        try:
            data = await self._livef1_request("WeatherData")
            if data:
                weather_list = []
                for timestamp, weather_info in data.items():
                    weather_list.append({
                        "date": timestamp,
                        "air_temperature": weather_info.get("AirTemp", 0),
                        "track_temperature": weather_info.get("TrackTemp", 0),
                        "humidity": weather_info.get("Humidity", 0),
                        "pressure": weather_info.get("Pressure", 0),
                        "wind_direction": weather_info.get("WindDirection", 0),
                        "wind_speed": weather_info.get("WindSpeed", 0),
                        "rainfall": weather_info.get("Rainfall", 0)
                    })
                return weather_list
            
            return []
            
        except Exception as e:
            logger.error(f"Failed to get weather: {e}")
            return []
    
    async def get_lap_times(
        self,
        session_key: Optional[int] = None,
        driver_number: Optional[int] = None,
        lap_number: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        try:
            data = await self._livef1_request("TimingData")
            if data:
                lap_times = []
                for driver_num, timing_info in data.get("Lines", {}).items():
                    if driver_number and int(driver_num) != driver_number:
                        continue
                    
                    lap_times.append({
                        "driver_number": int(driver_num),
                        "lap_number": timing_info.get("NumberOfLaps", 0),
                        "lap_time": timing_info.get("LastLapTime", {}).get("Value", None),
                        "sector_1_time": timing_info.get("Sectors", [{}])[0].get("Value", None) if timing_info.get("Sectors") else None,
                        "sector_2_time": timing_info.get("Sectors", [{}, {}])[1].get("Value", None) if len(timing_info.get("Sectors", [])) > 1 else None,
                        "sector_3_time": timing_info.get("Sectors", [{}, {}, {}])[2].get("Value", None) if len(timing_info.get("Sectors", [])) > 2 else None,
                        "position": timing_info.get("Position", 0)
                    })
                
                return lap_times
            
            return []
            
        except Exception as e:
            logger.error(f"Failed to get lap times: {e}")
            return []
    
    async def get_pit_stops(
        self,
        session_key: Optional[int] = None,
        driver_number: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        try:
            return []
            
        except Exception as e:
            logger.error(f"Failed to get pit stops: {e}")
            return []
    
    async def get_team_radio(
        self,
        session_key: Optional[int] = None,
        driver_number: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        try:
            data = await self._livef1_request("TeamRadio")
            if data:
                radio_messages = []
                for message in data.get("Captures", []):
                    if driver_number and message.get("RacingNumber") != driver_number:
                        continue
                    
                    radio_messages.append({
                        "driver_number": message.get("RacingNumber"),
                        "date": message.get("Utc"),
                        "recording_url": message.get("Path", "")
                    })
                
                return radio_messages
            
            return []
            
        except Exception as e:
            logger.error(f"Failed to get team radio: {e}")
            return []
    
    async def close(self):
        pass

livef1_client = LiveF1Client()