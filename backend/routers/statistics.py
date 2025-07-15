"""
통계 관련 API 엔드포인트
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
router = APIRouter(prefix="/api/v1", tags=["statistics"])

# LiveF1Service는 main.py에서 전달받음
livef1_service = None

def init_service(service):
    """LiveF1Service 초기화"""
    global livef1_service
    livef1_service = service

@router.get("/all-drivers/season-stats")
async def get_all_drivers_season_stats(year: Optional[int] = None):
    """모든 드라이버의 시즌 통계를 한번에 가져오기"""
    try:
        if year is None:
            year = datetime.now().year
        
        # 2025년 데이터는 JSON 파일에서 가져오기
        if year == 2025:
            try:
                career_json_file = os.path.join(os.path.dirname(__file__), "..", "driver_career_stats.json")
                
                if os.path.exists(career_json_file):
                    with open(career_json_file, 'r', encoding='utf-8') as f:
                        career_data = json.load(f)
                    
                    all_drivers_stats = []
                    drivers = career_data.get('drivers', {})
                    
                    for slug, driver_info in drivers.items():
                        if driver_info.get('success'):
                            season_data = driver_info.get('season_2025_data', {})
                            
                            if season_data:
                                driver_stats = {
                                    "driver_number": driver_info['number'],
                                    "name": driver_info['name'],
                                    "slug": slug,
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
                                    "data_source": "motorsportstats_2025_scraped"
                                }
                                all_drivers_stats.append(driver_stats)
                    
                    # 포인트 순으로 정렬
                    all_drivers_stats.sort(key=lambda x: x['season_points'], reverse=True)
                    
                    return {
                        "data": all_drivers_stats,
                        "year": year,
                        "total_drivers": len(all_drivers_stats),
                        "data_source": "motorsportstats_2025_scraped"
                    }
                else:
                    logger.warning(f"Career stats file not found, falling back to API")
                    
            except Exception as e:
                logger.error(f"Error loading 2025 season data: {e}, falling back to API")
        
        # 다른 연도는 기존 API 방식 사용
        # 기존 standings API를 사용해서 모든 드라이버 데이터 가져오기
        standings = await livef1_service.get_driver_standings(year)
        
        all_drivers_stats = []
        for standing in standings:
            driver_stats = {
                "driver_number": standing.get("driver_number"),
                "name": standing.get("name"),
                "season_wins": standing.get("wins", 0),
                "season_podiums": 0,  # API에서 제공하지 않음
                "season_points": standing.get("points", 0),
                "races_entered": 0,  # API에서 제공하지 않음
                "best_finish": None,  # API에서 제공하지 않음
                "average_finish": 0,  # API에서 제공하지 않음
                "fastest_laps": 0,  # API에서 제공하지 않음
                "poles": 0,  # API에서 제공하지 않음
                "dnf": 0,  # API에서 제공하지 않음
                "championship_position": standing.get("position"),
                "team": standing.get("team"),
                "data_source": "api_calculated"
            }
            all_drivers_stats.append(driver_stats)
        
        return {
            "data": all_drivers_stats,
            "year": year,
            "total_drivers": len(all_drivers_stats),
            "data_source": "api_calculated"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/all-teams/season-stats")
async def get_all_teams_season_stats(year: Optional[int] = None):
    """모든 팀의 시즌 통계를 한번에 가져오기"""
    try:
        if year is None:
            year = datetime.now().year
        
        # 2025년 데이터는 JSON 파일에서 가져오기
        if year == 2025:
            try:
                team_json_file = os.path.join(os.path.dirname(__file__), "..", "team_2025_season_stats.json")
                
                if os.path.exists(team_json_file):
                    with open(team_json_file, 'r', encoding='utf-8') as f:
                        team_data = json.load(f)
                    
                    all_teams_stats = []
                    teams = team_data.get('teams', {})
                    
                    for slug, team_info in teams.items():
                        if team_info.get('success'):
                            season_data = team_info.get('season_data', {})
                            
                            if season_data:
                                team_stats = {
                                    "team_slug": slug,
                                    "name": team_info['name'],
                                    "full_name": team_info['full_name'],
                                    "season_wins": season_data.get('season_wins', 0),
                                    "season_podiums": season_data.get('season_podiums', 0),
                                    "season_poles": season_data.get('season_poles', 0),
                                    "season_fastest_laps": season_data.get('season_fastest_laps', 0),
                                    "season_points": season_data.get('season_points', 0),
                                    "season_races": season_data.get('season_races', 0),
                                    "season_dnf": season_data.get('season_dnf', 0),
                                    "championship_position": season_data.get('season_championship_position', None),
                                    "drivers_count": season_data.get('season_drivers', None),
                                    "data_source": "motorsportstats_2025_scraped"
                                }
                                all_teams_stats.append(team_stats)
                    
                    # 포인트 순으로 정렬
                    all_teams_stats.sort(key=lambda x: x['season_points'], reverse=True)
                    
                    return {
                        "data": all_teams_stats,
                        "year": year,
                        "total_teams": len(all_teams_stats),
                        "data_source": "motorsportstats_2025_scraped"
                    }
                else:
                    logger.warning(f"Team stats file not found, falling back to API")
                    
            except Exception as e:
                logger.error(f"Error loading 2025 team data: {e}, falling back to API")
        
        # 다른 연도는 기존 API 방식 사용
        # 기존 constructor standings API를 사용해서 모든 팀 데이터 가져오기
        standings = await livef1_service.get_constructor_standings(year)
        
        all_teams_stats = []
        for standing in standings:
            team_stats = {
                "team_slug": standing.get("team", "").lower().replace(" ", "-"),
                "name": standing.get("team"),
                "full_name": standing.get("team"),
                "season_wins": standing.get("wins", 0),
                "season_podiums": 0,  # API에서 제공하지 않음
                "season_poles": 0,  # API에서 제공하지 않음
                "season_fastest_laps": 0,  # API에서 제공하지 않음
                "season_points": standing.get("points", 0),
                "season_races": 0,  # API에서 제공하지 않음
                "season_dnf": 0,  # API에서 제공하지 않음
                "championship_position": standing.get("position"),
                "drivers_count": None,  # API에서 제공하지 않음
                "data_source": "api_calculated"
            }
            all_teams_stats.append(team_stats)
        
        return {
            "data": all_teams_stats,
            "year": year,
            "total_teams": len(all_teams_stats),
            "data_source": "api_calculated"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/driver-standings")
async def get_driver_standings(year: Optional[int] = None):
    """드라이버 순위 가져오기"""
    try:
        if year is None:
            year = datetime.now().year
        
        standings = await livef1_service.get_driver_standings(year)
        return {"standings": standings, "year": year}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/constructor-standings")
async def get_constructor_standings(year: Optional[int] = None):
    """컨스트럭터 순위 가져오기"""
    try:
        if year is None:
            year = datetime.now().year
        
        standings = await livef1_service.get_constructor_standings(year)
        return {"standings": standings, "year": year}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/standings-progression")
async def get_standings_progression(year: Optional[int] = None):
    """순위 진행 상황"""
    try:
        if year is None:
            year = datetime.now().year
        
        progression = await livef1_service.get_standings_progression(year)
        return {"progression": progression, "year": year}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))