"""
드라이버 관련 API 엔드포인트
"""
from fastapi import APIRouter, HTTPException
from typing import Optional
import json
import os
import logging
from datetime import datetime

# 로깅 설정
logger = logging.getLogger(__name__)

# 라우터 생성
router = APIRouter(prefix="/api/v1/drivers", tags=["drivers"])

# LiveF1Service는 main.py에서 전달받음
livef1_service = None

def init_service(service):
    """LiveF1Service 초기화"""
    global livef1_service
    livef1_service = service

@router.get("")
async def get_drivers():
    """모든 드라이버 목록 가져오기"""
    try:
        drivers = await livef1_service.get_drivers()
        return {"drivers": drivers}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{driver_number}")
async def get_driver_detail(driver_number: int):
    """특정 드라이버 상세 정보 (통합 - 기본 정보 + 시즌 통계 + 경력 통계)"""
    try:
        # 기본 드라이버 정보
        driver = await livef1_service.get_driver_detail(driver_number)
        if not driver:
            raise HTTPException(status_code=404, detail="Driver not found")
        
        # JSON 파일을 한 번만 읽어서 시즌 통계와 경력 통계 모두 가져오기
        season_stats = {}
        career_stats = {}
        
        try:
            career_json_file = os.path.join(os.path.dirname(__file__), "..", "driver_career_stats.json")
            
            if os.path.exists(career_json_file):
                with open(career_json_file, 'r', encoding='utf-8') as f:
                    scraped_data = json.load(f)
                
                # 드라이버 번호로 매핑 찾기
                drivers = scraped_data.get('drivers', {})
                for slug, driver_info in drivers.items():
                    if driver_info['number'] == driver_number and driver_info.get('success'):
                        # 시즌 통계 (2025년)
                        season_data = driver_info.get('season_2025_data', {})
                        if season_data:
                            season_stats = {
                                "season_wins": season_data.get('season_wins', 0),
                                "season_podiums": season_data.get('season_podiums', 0),
                                "season_points": season_data.get('season_points', 0),
                                "races_entered": season_data.get('season_races', 0),
                                "best_finish": season_data.get('season_best_finish', None),
                                "average_finish": round(season_data.get('season_avg_finish', 0), 2),
                                "fastest_laps": season_data.get('season_fastest_laps', 0),
                                "poles": season_data.get('season_poles', 0),
                                "dnf": season_data.get('season_dnf', 0),
                                "championship_position": season_data.get('season_championship_position', None),
                                "team": season_data.get('season_entrant', None),
                            }
                        
                        # 경력 통계
                        stats = driver_info.get('stats', {})
                        career_stats = {
                            "race_wins": stats.get('wins', 0),
                            "podiums": stats.get('podiums', 0),
                            "pole_positions": stats.get('poles', 0),
                            "fastest_laps": stats.get('fastest_laps', 0),
                            "career_points": stats.get('points', 0),
                            "world_championships": stats.get('championships', 0),
                            "first_entry": 2025 - stats.get('years', 0) if stats.get('years') else None,
                            "total_starts": stats.get('starts', 0),
                            "entries": stats.get('entries', 0),
                            "best_finish": stats.get('best_finish', None),
                            "best_championship_position": stats.get('best_championship_position', None),
                            "sprint_wins": stats.get('sprint_wins', 0),
                            "years_active": stats.get('years', 0),
                        }
                        break
        except Exception as e:
            logger.warning(f"Failed to load driver stats for driver {driver_number}: {e}")
        
        # 모든 데이터 병합
        combined_data = {
            **driver,
            **season_stats,
            **career_stats
        }
        
        return {"driver": combined_data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{driver_number}/season-stats")
async def get_driver_season_stats(driver_number: int, year: Optional[int] = None):
    """드라이버 시즌 통계"""
    try:
        if year is None:
            year = datetime.now().year
        
        # 2025년 시즌 데이터가 있으면 스크래핑된 데이터 사용, 없으면 기존 API 사용
        if year == 2025:
            try:
                # 커리어 통계 JSON 파일에서 2025 시즌 데이터 가져오기
                career_json_file = os.path.join(os.path.dirname(__file__), "..", "driver_career_stats.json")
                
                if os.path.exists(career_json_file):
                    with open(career_json_file, 'r', encoding='utf-8') as f:
                        career_data = json.load(f)
                    
                    # 드라이버 번호로 매핑 찾기
                    drivers = career_data.get('drivers', {})
                    for slug, driver_info in drivers.items():
                        if driver_info['number'] == driver_number and driver_info.get('success'):
                            season_data = driver_info.get('season_2025_data', {})
                            
                            if season_data:
                                season_stats = {
                                    "season_wins": season_data.get('season_wins', 0),
                                    "season_podiums": season_data.get('season_podiums', 0),
                                    "season_points": season_data.get('season_points', 0),
                                    "season_position": None,  # 별도로 standings에서 가져와야 함
                                    "races_entered": season_data.get('season_races', 0),
                                    "best_finish": season_data.get('season_best_finish', None),
                                    "average_finish": round(season_data.get('season_avg_finish', 0), 2),
                                    "fastest_laps": season_data.get('season_fastest_laps', 0),
                                    "poles": season_data.get('season_poles', 0),
                                    "dnf": season_data.get('season_dnf', 0),
                                    "championship_position": season_data.get('season_championship_position', None),
                                    "team": season_data.get('season_entrant', None),
                                    "data_source": "motorsportstats_2025_scraped",
                                    "scraped_at": driver_info.get('scraped_at')
                                }
                                
                                # 드라이버 순위는 기존 API에서 가져오기
                                try:
                                    standings = await livef1_service.get_driver_standings(year)
                                    for driver_standing in standings:
                                        if driver_standing["driver_number"] == driver_number:
                                            season_stats["season_position"] = driver_standing.get("position", None)
                                            break
                                except Exception as e:
                                    logger.warning(f"Failed to get standings for driver {driver_number}: {e}")
                                
                                logger.info(f"Using 2025 scraped data for driver {driver_number}: {season_stats}")
                                return {"data": season_stats, "year": year}
                    
                    logger.info(f"Driver {driver_number} not found in 2025 scraped data, falling back to fallback data")
                else:
                    logger.warning(f"Career stats file not found at {career_json_file}, using fallback data")
                    
            except Exception as e:
                logger.error(f"Error loading 2025 season data: {e}, falling back to fallback data")
        
        # 스크래핑된 데이터가 없으면 기본값 반환
        season_stats = {
            "season_wins": 0,
            "season_podiums": 0,
            "season_points": 0,
            "season_position": None,
            "races_entered": 0,
            "best_finish": None,
            "average_finish": 0,
            "fastest_laps": 0,
            "poles": 0,
            "dnf": 0,
            "championship_position": None,
            "team": None,
            "data_source": "fallback_default"
        }
        
        return {"data": season_stats, "year": year}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{driver_number}/career-stats")
async def get_driver_career_stats(driver_number: int):
    """드라이버 커리어 통계"""
    try:
        # JSON 파일에서 커리어 통계 로드 시도
        try:
            json_file_path = os.path.join(os.path.dirname(__file__), "..", "driver_career_stats.json")
            
            if os.path.exists(json_file_path):
                with open(json_file_path, 'r', encoding='utf-8') as f:
                    scraped_data = json.load(f)
                
                # 드라이버 번호로 매핑 찾기
                drivers = scraped_data.get('drivers', {})
                for slug, driver_info in drivers.items():
                    if driver_info['number'] == driver_number and driver_info.get('success'):
                        stats = driver_info.get('stats', {})
                        
                        # API 형식으로 변환
                        career_stats = {
                            "race_wins": stats.get('wins', 0),
                            "podiums": stats.get('podiums', 0),
                            "pole_positions": stats.get('poles', 0),
                            "fastest_laps": stats.get('fastest_laps', 0),
                            "career_points": stats.get('points', 0),
                            "world_championships": stats.get('championships', 0),
                            "first_entry": 2025 - stats.get('years', 0) if stats.get('years') else None,
                            "total_starts": stats.get('starts', 0),
                            "entries": stats.get('entries', 0),
                            "best_finish": stats.get('best_finish', None),
                            "best_championship_position": stats.get('best_championship_position', None),
                            "sprint_wins": stats.get('sprint_wins', 0),
                            "years_active": stats.get('years', 0),
                            "data_source": "motorsportstats_scraped",
                            "scraped_at": driver_info.get('scraped_at')
                        }
                        
                        logger.info(f"Using scraped data for driver {driver_number}: {career_stats}")
                        return {"data": career_stats}
                
                logger.info(f"Driver {driver_number} not found in scraped data, falling back to fallback data")
            else:
                logger.warning(f"Scraped data file not found at {json_file_path}, using fallback data")
                
        except Exception as e:
            logger.error(f"Error loading scraped data: {e}, using fallback data")
        
        # 스크래핑된 데이터가 없으면 기본값 반환
        career_stats = {
            "race_wins": 0,
            "podiums": 0,
            "pole_positions": 0,
            "fastest_laps": 0,
            "career_points": 0,
            "world_championships": 0,
            "first_entry": None,
            "total_starts": 0,
            "entries": 0,
            "best_finish": None,
            "best_championship_position": None,
            "sprint_wins": 0,
            "years_active": 0,
            "data_source": "fallback_default"
        }
        
        return {"data": career_stats}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))