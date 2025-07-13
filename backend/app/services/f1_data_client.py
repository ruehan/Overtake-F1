import logging
from typing import Optional, Dict, Any, List
from datetime import datetime

from app.config import settings
from app.core.exceptions import OpenF1APIException
from app.services.openf1_client import openf1_client
from app.services.livef1_client import livef1_client

logger = logging.getLogger(__name__)

class F1DataClient:
    """
    하이브리드 F1 데이터 클라이언트
    LiveF1을 우선 사용하고, 실패 시 OpenF1으로 fallback
    """
    
    def __init__(self):
        self.use_livef1 = settings.use_livef1
        self.fallback_to_openf1 = settings.fallback_to_openf1
        self.livef1_client = livef1_client
        self.openf1_client = openf1_client
    
    async def _try_both_clients(self, method_name: str, *args, **kwargs) -> Any:
        """
        LiveF1을 먼저 시도하고 실패하면 OpenF1으로 fallback
        """
        if self.use_livef1:
            try:
                livef1_method = getattr(self.livef1_client, method_name)
                result = await livef1_method(*args, **kwargs)
                if result:  # 결과가 있으면 LiveF1 결과 반환
                    logger.debug(f"{method_name}: Using LiveF1 data")
                    return result
            except Exception as e:
                logger.warning(f"{method_name}: LiveF1 failed: {e}")
        
        if self.fallback_to_openf1:
            try:
                openf1_method = getattr(self.openf1_client, method_name)
                result = await openf1_method(*args, **kwargs)
                logger.debug(f"{method_name}: Using OpenF1 fallback data")
                return result
            except Exception as e:
                logger.error(f"{method_name}: OpenF1 fallback also failed: {e}")
                raise e
        
        logger.error(f"{method_name}: No data source available")
        raise OpenF1APIException(f"Failed to get data from {method_name}")
    
    async def get_drivers(self, session_key: Optional[int] = None) -> List[Dict[str, Any]]:
        """드라이버 정보 조회"""
        return await self._try_both_clients("get_drivers", session_key=session_key)
    
    async def get_teams(self, session_key: Optional[int] = None) -> List[Dict[str, Any]]:
        """팀 정보 조회"""
        return await self._try_both_clients("get_teams", session_key=session_key)
    
    async def get_positions(
        self,
        session_key: Optional[int] = None,
        driver_number: Optional[int] = None,
        date: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """위치 데이터 조회"""
        return await self._try_both_clients(
            "get_positions", 
            session_key=session_key, 
            driver_number=driver_number, 
            date=date
        )
    
    async def get_sessions(
        self,
        year: Optional[int] = None,
        country: Optional[str] = None,
        session_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """세션 정보 조회"""
        return await self._try_both_clients(
            "get_sessions", 
            year=year, 
            country=country, 
            session_type=session_type
        )
    
    async def get_weather(
        self,
        session_key: Optional[int] = None,
        date: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """날씨 데이터 조회"""
        return await self._try_both_clients(
            "get_weather", 
            session_key=session_key, 
            date=date
        )
    
    async def get_lap_times(
        self,
        session_key: Optional[int] = None,
        driver_number: Optional[int] = None,
        lap_number: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """랩타임 데이터 조회"""
        return await self._try_both_clients(
            "get_lap_times", 
            session_key=session_key, 
            driver_number=driver_number, 
            lap_number=lap_number
        )
    
    async def get_pit_stops(
        self,
        session_key: Optional[int] = None,
        driver_number: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """피트스톱 데이터 조회"""
        return await self._try_both_clients(
            "get_pit_stops", 
            session_key=session_key, 
            driver_number=driver_number
        )
    
    async def get_team_radio(
        self,
        session_key: Optional[int] = None,
        driver_number: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """팀 라디오 메시지 조회"""
        return await self._try_both_clients(
            "get_team_radio", 
            session_key=session_key, 
            driver_number=driver_number
        )
    
    async def close(self):
        """클라이언트 정리"""
        if self.livef1_client:
            await self.livef1_client.close()
        if self.openf1_client:
            await self.openf1_client.close()
    
    async def get_data_source_status(self) -> Dict[str, Any]:
        """현재 데이터 소스 상태 반환"""
        status = {
            "use_livef1": self.use_livef1,
            "fallback_to_openf1": self.fallback_to_openf1,
            "livef1_available": False,
            "openf1_available": False
        }
        
        # LiveF1 상태 확인
        if self.use_livef1:
            try:
                await self.livef1_client.get_drivers()
                status["livef1_available"] = True
            except:
                pass
        
        # OpenF1 상태 확인
        if self.fallback_to_openf1:
            try:
                await self.openf1_client.get_drivers()
                status["openf1_available"] = True
            except:
                pass
        
        return status

f1_data_client = F1DataClient()