import httpx
from typing import Optional, Dict, Any, List
from datetime import datetime
import asyncio
from asyncio_throttle import Throttler

from app.config import settings
from app.core.exceptions import OpenF1APIException
from app.services.cache_service import cache_service, cached

class OpenF1Client:
    def __init__(self):
        self.base_url = settings.openf1_api_base_url
        self.api_key = settings.openf1_api_key
        self.throttler = Throttler(
            rate_limit=settings.rate_limit_per_minute,
            period=60
        )
        self._client: Optional[httpx.AsyncClient] = None
    
    @property
    def client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            headers = {
                "Accept": "application/json",
                "User-Agent": "OpenF1-Dashboard/1.0.0"
            }
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"
            
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                headers=headers,
                timeout=30.0
            )
        return self._client
    
    async def close(self):
        if self._client:
            await self._client.aclose()
    
    async def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        async with self.throttler:
            try:
                response = await self.client.request(
                    method=method,
                    url=endpoint,
                    params=params,
                    json=data
                )
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                raise OpenF1APIException(
                    f"HTTP {e.response.status_code}: {e.response.text}",
                    status_code=e.response.status_code
                )
            except httpx.RequestError as e:
                raise OpenF1APIException(f"Request failed: {str(e)}")
            except Exception as e:
                raise OpenF1APIException(f"Unexpected error: {str(e)}")
    
    @cached(namespace="drivers", ttl_seconds=600)  # Cache for 10 minutes
    async def get_drivers(self, session_key: Optional[int] = None) -> List[Dict[str, Any]]:
        params = {}
        if session_key:
            params["session_key"] = session_key
        return await self._make_request("GET", "/drivers", params=params)
    
    @cached(namespace="teams", ttl_seconds=600)  # Cache for 10 minutes
    async def get_teams(self, session_key: Optional[int] = None) -> List[Dict[str, Any]]:
        params = {}
        if session_key:
            params["session_key"] = session_key
        # OpenF1 doesn't have a direct teams endpoint, we'll derive from drivers
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
    
    async def get_positions(
        self,
        session_key: Optional[int] = None,
        driver_number: Optional[int] = None,
        date: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        params = {}
        if session_key:
            params["session_key"] = session_key
        if driver_number:
            params["driver_number"] = driver_number
        if date:
            params["date"] = date.isoformat()
        return await self._make_request("GET", "/position", params=params)
    
    @cached(namespace="sessions", ttl_seconds=3600)  # Cache for 1 hour
    async def get_sessions(
        self,
        year: Optional[int] = None,
        country: Optional[str] = None,
        session_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        params = {}
        if year:
            params["year"] = year
        if country:
            params["country"] = country
        if session_type:
            params["session_type"] = session_type
        return await self._make_request("GET", "/sessions", params=params)
    
    async def get_weather(
        self,
        session_key: Optional[int] = None,
        date: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        params = {}
        if session_key:
            params["session_key"] = session_key
        if date:
            params["date"] = date.isoformat()
        return await self._make_request("GET", "/weather", params=params)
    
    async def get_lap_times(
        self,
        session_key: Optional[int] = None,
        driver_number: Optional[int] = None,
        lap_number: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        params = {}
        if session_key:
            params["session_key"] = session_key
        if driver_number:
            params["driver_number"] = driver_number
        if lap_number:
            params["lap_number"] = lap_number
        return await self._make_request("GET", "/laps", params=params)
    
    async def get_pit_stops(
        self,
        session_key: Optional[int] = None,
        driver_number: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        params = {}
        if session_key:
            params["session_key"] = session_key
        if driver_number:
            params["driver_number"] = driver_number
        return await self._make_request("GET", "/pit", params=params)
    
    async def get_team_radio(
        self,
        session_key: Optional[int] = None,
        driver_number: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        params = {}
        if session_key:
            params["session_key"] = session_key
        if driver_number:
            params["driver_number"] = driver_number
        return await self._make_request("GET", "/team_radio", params=params)

openf1_client = OpenF1Client()