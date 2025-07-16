"""
LiveF1 전용 F1 대시보드 백엔드
"""
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional, Dict, Any
import asyncio
import json
import logging
from datetime import datetime
import os
from dotenv import load_dotenv
import socketio
import requests

# 환경 변수 로드
load_dotenv()

import livef1
from livef1 import get_season, get_session, get_meeting
from livef1.api import livetimingF1_request

# LiveF1Service 임포트
from services.livef1_service import LiveF1Service

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Socket.IO 서버 생성
sio = socketio.AsyncServer(
    async_mode='asgi',
    cors_allowed_origins=[
        "http://localhost:3000", 
        "http://127.0.0.1:3000",
        "https://overtake-f1.com", 
        "https://www.overtake-f1.com",
        "http://overtake-f1.com", 
        "http://www.overtake-f1.com"
    ],
    ping_interval=25,
    ping_timeout=60
)

# FastAPI 앱 생성
app = FastAPI(
    title="F1 LiveTiming Dashboard",
    description="LiveF1 기반 실시간 F1 대시보드",
    version="2.0.0"
)

# Socket.IO ASGI 앱 마운트
sio_app = socketio.ASGIApp(sio, app)

# CORS 설정
origins = os.getenv("CORS_ORIGINS", '["*"]')
try:
    allowed_origins = json.loads(origins)
except:
    allowed_origins = ["*"]

# 도메인별 CORS 설정 추가
if allowed_origins == ["*"]:
    allowed_origins = [
        "http://localhost:3000",
        "http://127.0.0.1:3000", 
        "http://localhost",
        "http://127.0.0.1",
        "http://overtake-f1.com",
        "https://overtake-f1.com",
        "http://www.overtake-f1.com",
        "https://www.overtake-f1.com"
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 서비스 인스턴스
livef1_service = LiveF1Service()

# API 엔드포인트들
@app.get("/")
async def root():
    return {"message": "F1 LiveTiming Dashboard API", "version": "2.0.0"}

@app.get("/api/v1/drivers")
async def get_drivers(session_key: Optional[str] = None):
    try:
        drivers = await livef1_service.get_drivers(session_key)
        return {"data": drivers, "count": len(drivers)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/drivers/{driver_number}")
async def get_driver_detail(driver_number: int):
    try:
        driver = await livef1_service.get_driver_detail(driver_number)
        if not driver:
            raise HTTPException(status_code=404, detail="Driver not found")
        return {"data": driver}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/drivers/{driver_number}/season-stats")
async def get_driver_season_stats(driver_number: int, year: Optional[int] = None):
    try:
        if year is None:
            year = datetime.now().year
        
        # 드라이버 번호를 드라이버 ID로 매핑
        driver_number_to_id = {
            23: "albon",
            14: "alonso", 
            12: "antonelli",
            87: "bearman",
            5: "bortoleto",
            43: "colapinto",
            7: "doohan",
            10: "gasly",
            6: "hadjar",
            44: "hamilton",
            27: "hulkenberg",
            30: "lawson",
            16: "leclerc",
            4: "norris",
            31: "ocon",
            81: "piastri",
            63: "russell",
            55: "sainz",
            18: "stroll",
            22: "tsunoda",
            33: "verstappen"
        }
        
        # 드라이버 ID가 없으면 에러 반환
        driver_id = driver_number_to_id.get(driver_number)
        if not driver_id:
            raise HTTPException(status_code=404, detail=f"Driver with number {driver_number} not found")
        
        # 2025년 시즌 데이터가 있으면 스크래핑된 데이터 사용, 없으면 기존 API 사용
        if year == 2025:
            try:
                # 커리어 통계 JSON 파일에서 2025 시즌 데이터 가져오기
                career_json_file = os.path.join(os.path.dirname(__file__), "driver_career_stats.json")
                
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
                    
                    logger.info(f"Driver {driver_number} not found in 2025 scraped data, falling back to API")
                else:
                    logger.warning(f"Career stats file not found at {career_json_file}, using API")
                    
            except Exception as e:
                logger.error(f"Error loading 2025 season data: {e}, falling back to API")
        
        # 기존 API 방식 사용
        year_stats = await livef1_service.get_driver_statistics(year=year, driver_id=driver_id)
        
        season_stats = {
            "season_wins": 0,
            "season_podiums": 0,
            "season_points": 0,
            "season_position": None,
            "data_source": "api_calculated"
        }
        
        if year_stats and 'season_stats' in year_stats:
            stats = year_stats['season_stats']
            season_stats["season_wins"] = stats.get("wins", 0)
            season_stats["season_podiums"] = stats.get("podiums", 0)
            season_stats["season_points"] = stats.get("total_points", 0)
        
        # 드라이버 순위에서 현재 시즌 순위 가져오기
        standings = await livef1_service.get_driver_standings(year)
        for driver_standing in standings:
            if driver_standing["driver_number"] == driver_number:
                season_stats["season_position"] = driver_standing.get("position", None)
                break
        
        return {"data": season_stats, "year": year}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/all-drivers/season-stats")
async def get_all_drivers_season_stats(year: Optional[int] = None):
    """모든 드라이버의 시즌 통계를 한번에 가져오기"""
    try:
        if year is None:
            year = datetime.now().year
        
        # 2025년 데이터는 JSON 파일에서 가져오기
        if year == 2025:
            try:
                career_json_file = os.path.join(os.path.dirname(__file__), "driver_career_stats.json")
                
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

@app.get("/api/v1/all-teams/season-stats")
async def get_all_teams_season_stats(year: Optional[int] = None):
    """모든 팀의 시즌 통계를 한번에 가져오기"""
    try:
        if year is None:
            year = datetime.now().year
        
        # 2025년 데이터는 JSON 파일에서 가져오기
        if year == 2025:
            try:
                team_json_file = os.path.join(os.path.dirname(__file__), "team_2025_season_stats.json")
                
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

@app.get("/api/v1/drivers/{driver_number}/career-stats")
async def get_driver_career_stats(driver_number: int):
    try:
        logger.info(f"DEBUG: Getting career stats for driver_number={driver_number}")
        # 드라이버 번호를 드라이버 ID로 매핑
        driver_number_to_id = {
            1: "max_verstappen",   # Max Verstappen (champion's number)
            23: "albon",
            14: "alonso", 
            12: "antonelli",
            87: "bearman",
            5: "bortoleto",
            43: "colapinto",
            7: "doohan",
            10: "gasly",
            6: "hadjar",
            44: "hamilton",
            27: "hulkenberg",
            30: "lawson",
            16: "leclerc",
            4: "norris",
            31: "ocon",
            81: "piastri",
            63: "russell",
            55: "sainz",
            18: "stroll",
            22: "tsunoda",
            33: "verstappen"   # Max Verstappen (permanent number)
        }
        
        # 드라이버별 실제 데뷔 연도
        driver_debut_years = {
            1: 2015,   # Max Verstappen (champion's number)
            23: 2019,  # Alexander Albon
            14: 2005,  # Fernando Alonso
            12: 2025,  # Antonelli
            87: 2024,  # Bearman
            5: 2025,   # Bortoleto
            43: 2024,  # Colapinto
            7: 2025,   # Doohan
            10: 2017,  # Pierre Gasly
            6: 2025,   # Hadjar
            44: 2007,  # Lewis Hamilton
            27: 2010,  # Nico Hulkenberg
            30: 2023,  # Lawson
            16: 2018,  # Charles Leclerc
            4: 2019,   # Lando Norris
            31: 2020,  # Esteban Ocon
            81: 2023,  # Oscar Piastri
            63: 2019,  # George Russell
            55: 2015,  # Carlos Sainz
            18: 2017,  # Lance Stroll
            22: 2021,  # Yuki Tsunoda
            33: 2015,  # Max Verstappen (permanent number)
        }
        
        # 드라이버 ID가 없으면 에러 반환
        driver_id = driver_number_to_id.get(driver_number)
        logger.info(f"DEBUG: Mapped driver_number={driver_number} to driver_id={driver_id}")
        if not driver_id:
            raise HTTPException(status_code=404, detail=f"Driver with number {driver_number} not found")
        
        # JSON 파일에서 커리어 통계 로드 시도
        try:
            json_file_path = os.path.join(os.path.dirname(__file__), "driver_career_stats.json")
            
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
                
                logger.info(f"Driver {driver_number} not found in scraped data, falling back to API")
            else:
                logger.warning(f"Scraped data file not found at {json_file_path}, using API")
                
        except Exception as e:
            logger.error(f"Error loading scraped data: {e}, falling back to API")
        
        # 스크래핑된 데이터가 없으면 기존 API 방식 사용
        career_stats = await livef1_service.get_driver_career_statistics(driver_id)
        career_stats["data_source"] = "api_calculated"
        
        return {"data": career_stats}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/sessions")
async def get_sessions(year: Optional[int] = None):
    try:
        sessions = await livef1_service.get_sessions(year)
        return {"data": sessions, "count": len(sessions)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/live-timing")
async def get_live_timing():
    try:
        timing = await livef1_service.get_live_timing()
        return {"data": timing}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/weather")
async def get_weather():
    try:
        weather = await livef1_service.get_weather()
        return {"data": weather}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/driver-standings")
async def get_driver_standings(year: Optional[int] = None):
    try:
        standings = await livef1_service.get_driver_standings(year)
        return {"data": standings, "count": len(standings), "year": year or datetime.now().year}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/constructor-standings")
async def get_constructor_standings(year: Optional[int] = None):
    try:
        standings = await livef1_service.get_constructor_standings(year)
        return {"data": standings, "count": len(standings), "year": year or datetime.now().year}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/seasons")
async def get_available_seasons():
    try:
        seasons = await livef1_service.get_available_seasons()
        return {"data": seasons, "count": len(seasons)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/calendar")
async def get_race_calendar(year: Optional[int] = None):
    try:
        calendar = await livef1_service.get_race_calendar(year)
        return {"data": calendar, "count": len(calendar), "year": year or datetime.now().year}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/calendar/next")
async def get_next_race():
    try:
        next_race = await livef1_service.get_next_race()
        if next_race:
            return {"data": next_race}
        else:
            return {"data": None, "message": "No upcoming races found"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/calendar/current")
async def get_current_race():
    try:
        current_race = await livef1_service.get_current_race()
        if current_race:
            return {"data": current_race}
        else:
            return {"data": None, "message": "No race weekend currently in progress"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/race-results")
async def get_race_results(
    year: Optional[int] = None,
    round_number: Optional[int] = None
):
    try:
        results = await livef1_service.get_race_results(year, round_number)
        return {
            "data": results, 
            "count": len(results), 
            "year": year or datetime.now().year,
            "round": round_number
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/race-results/latest")
async def get_latest_race_result():
    try:
        # Get current year results and find the latest completed race
        results = await livef1_service.get_race_results()
        if not results:
            return {"data": None, "message": "No race results found"}
        
        # Filter races that have results (completed races)
        completed_races = [race for race in results if race.get('results')]
        
        if not completed_races:
            return {"data": None, "message": "No completed races found"}
        
        # Return the most recent completed race
        latest_race = completed_races[-1]
        return {"data": latest_race}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/standings-progression")
async def get_standings_progression(year: Optional[int] = None):
    try:
        progression = await livef1_service.get_standings_progression(year)
        return {
            "data": progression,
            "year": year or datetime.now().year
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/race-weekends")
async def get_race_weekends(year: Optional[int] = None):
    try:
        weekends = await livef1_service.get_race_weekend_details(year)
        return {
            "data": weekends,
            "year": year or datetime.now().year
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/race-weekends/{round_number}")
async def get_race_weekend_detail(round_number: int, year: Optional[int] = None):
    try:
        weekend = await livef1_service.get_race_weekend_details(year, round_number)
        if not weekend:
            raise HTTPException(status_code=404, detail="Race weekend not found")
        return {
            "data": weekend,
            "year": year or datetime.now().year
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/driver-statistics")
async def get_driver_statistics(year: Optional[int] = None, driver_id: Optional[str] = None):
    try:
        stats = await livef1_service.get_driver_statistics(year, driver_id)
        return {
            "data": stats,
            "year": year or datetime.now().year
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/team-statistics")
async def get_team_statistics(year: Optional[int] = None, team_id: Optional[str] = None):
    try:
        stats = await livef1_service.get_team_statistics(year, team_id)
        return {
            "data": stats,
            "year": year or datetime.now().year
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/circuits")
async def get_circuits(year: Optional[int] = None, circuit_id: Optional[str] = None):
    try:
        circuits = await livef1_service.get_circuit_information(year, circuit_id)
        return {
            "data": circuits,
            "year": year or datetime.now().year
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/status")
async def get_status():
    return {
        "status": "running",
        "data_source": "LiveF1",
        "websocket_connections": len(livef1_service.websocket_connections),
        "timestamp": datetime.now().isoformat()
    }

# Socket.IO 이벤트 핸들러
@sio.event
async def connect(sid, environ):
    logger.info(f"Socket.IO client {sid} connected")
    await sio.emit('connected', {'message': 'Connected to F1 Dashboard'}, to=sid)

@sio.event
async def disconnect(sid):
    logger.info(f"Socket.IO client {sid} disconnected")

@sio.event
async def subscribe(sid, data):
    topic = data.get('topic')
    logger.info(f"Client {sid} subscribed to {topic}")
    await sio.emit('subscribed', {'topic': topic}, to=sid)

@sio.event
async def unsubscribe(sid, data):
    topic = data.get('topic')
    logger.info(f"Client {sid} unsubscribed from {topic}")
    await sio.emit('unsubscribed', {'topic': topic}, to=sid)

# 실시간 데이터 브로드캐스트 태스크
async def broadcast_live_data():
    while True:
        try:
            if livef1_service.websocket_connections:
                # 실시간 타이밍 데이터 가져오기
                timing_data = await livef1_service.get_live_timing()
                if timing_data:
                    await livef1_service.broadcast_to_websockets({
                        "type": "live_timing",
                        "data": timing_data
                    })
            
            await asyncio.sleep(1)  # 1초마다 업데이트
            
        except Exception as e:
            logger.error(f"Broadcast error: {e}")
            await asyncio.sleep(5)

# 앱 시작 시 백그라운드 태스크 실행
@app.on_event("startup")
async def startup_event():
    logger.info("Starting F1 LiveTiming Dashboard...")
    asyncio.create_task(broadcast_live_data())

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(sio_app, host="0.0.0.0", port=8000)