"""
레이스 관련 API 엔드포인트
"""
from fastapi import APIRouter, HTTPException
from typing import Optional
import logging

# 로깅 설정
logger = logging.getLogger(__name__)

# 라우터 생성
router = APIRouter(prefix="/api/v1", tags=["races"])

# LiveF1Service는 main.py에서 전달받음
livef1_service = None

def init_service(service):
    """LiveF1Service 초기화"""
    global livef1_service
    livef1_service = service

@router.get("/calendar")
async def get_calendar(year: Optional[int] = None):
    """레이스 캘린더 가져오기"""
    try:
        calendar = await livef1_service.get_calendar(year)
        return {"calendar": calendar, "year": year}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/calendar/next")
async def get_next_race():
    """다음 레이스 일정"""
    try:
        next_race = await livef1_service.get_next_race()
        if not next_race:
            return {"next_race": None, "message": "No upcoming races found"}
        return {"next_race": next_race}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/calendar/current")
async def get_current_race():
    """현재 진행 중인 레이스"""
    try:
        current_race = await livef1_service.get_current_race()
        if not current_race:
            return {"current_race": None, "message": "No race currently in progress"}
        return {"current_race": current_race}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/race-results")
async def get_race_results(year: Optional[int] = None):
    """레이스 결과 가져오기"""
    try:
        results = await livef1_service.get_race_results(year)
        return {"results": results, "year": year}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/race-results/latest")
async def get_latest_race_result():
    """최근 레이스 결과"""
    try:
        latest_result = await livef1_service.get_latest_race_result()
        if not latest_result:
            return {"latest_result": None, "message": "No race results available"}
        return {"latest_result": latest_result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/race-weekends")
async def get_race_weekends(year: Optional[int] = None):
    """레이스 주말 일정"""
    try:
        weekends = await livef1_service.get_race_weekends(year)
        return {"weekends": weekends, "year": year}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/seasons")
async def get_seasons():
    """시즌 목록 가져오기"""
    try:
        seasons = await livef1_service.get_seasons()
        return {"seasons": seasons}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))