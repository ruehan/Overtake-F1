"""
라이브 타이밍 관련 API 엔드포인트
"""
from fastapi import APIRouter, HTTPException
from typing import Optional
import logging

# 로깅 설정
logger = logging.getLogger(__name__)

# 라우터 생성
router = APIRouter(prefix="/api/v1", tags=["live_timing"])

# LiveF1Service는 main.py에서 전달받음
livef1_service = None

def init_service(service):
    """LiveF1Service 초기화"""
    global livef1_service
    livef1_service = service

@router.get("/sessions")
async def get_sessions():
    """세션 목록 가져오기"""
    try:
        sessions = await livef1_service.get_sessions()
        return {"sessions": sessions}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/live-timing")
async def get_live_timing():
    """라이브 타이밍 데이터"""
    try:
        timing = await livef1_service.get_live_timing()
        return {"timing": timing}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/weather")
async def get_weather():
    """날씨 정보"""
    try:
        weather = await livef1_service.get_weather()
        return {"weather": weather}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/circuits")
async def get_circuits(year: Optional[int] = None):
    """서킷 정보"""
    try:
        circuits = await livef1_service.get_circuits(year)
        return {"circuits": circuits, "year": year}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/sessions/with-radio")
async def get_sessions_with_radio(limit: int = 20):
    """라디오가 있는 세션 목록"""
    try:
        sessions = await livef1_service.get_sessions_with_radio(limit)
        return {"sessions": sessions, "limit": limit}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/sessions/with-weather")
async def get_sessions_with_weather(limit: int = 20):
    """날씨 정보가 있는 세션 목록"""
    try:
        sessions = await livef1_service.get_sessions_with_weather(limit)
        return {"sessions": sessions, "limit": limit}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/team-radio")
async def get_team_radio(session_key: int, limit: int = 50):
    """팀 라디오 데이터"""
    try:
        radio = await livef1_service.get_team_radio(session_key, limit)
        return {"radio": radio, "session_key": session_key, "limit": limit}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/team-radio/stats")
async def get_team_radio_stats(session_key: int):
    """팀 라디오 통계"""
    try:
        stats = await livef1_service.get_team_radio_stats(session_key)
        return {"stats": stats, "session_key": session_key}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/weather/by-session")
async def get_weather_by_session(session_key: int):
    """세션별 날씨"""
    try:
        weather = await livef1_service.get_weather_by_session(session_key)
        return {"weather": weather, "session_key": session_key}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/weather/analysis")
async def get_weather_analysis(session_key: int):
    """날씨 분석"""
    try:
        analysis = await livef1_service.get_weather_analysis(session_key)
        return {"analysis": analysis, "session_key": session_key}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/weather/tire-strategy")
async def get_tire_strategy(session_key: int):
    """타이어 전략"""
    try:
        strategy = await livef1_service.get_tire_strategy(session_key)
        return {"strategy": strategy, "session_key": session_key}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))