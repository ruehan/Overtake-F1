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

class LiveF1Service:
    def __init__(self):
        self.current_season = None
        self.current_session = None
        self.websocket_connections: List[WebSocket] = []
    
    def _get_nationality_from_country_code(self, country_code: str) -> str:
        """국가 코드를 국적으로 변환"""
        country_map = {
            "NED": "Dutch",
            "GBR": "British", 
            "ESP": "Spanish",
            "MON": "Monégasque",
            "AUS": "Australian",
            "FRA": "French",
            "GER": "German",
            "MEX": "Mexican",
            "FIN": "Finnish",
            "CAN": "Canadian",
            "JPN": "Japanese",
            "THA": "Thai",
            "DEN": "Danish",
            "CHN": "Chinese"
        }
        return country_map.get(country_code, "Unknown")
    
    async def _get_current_season_stats(self, driver_number: int) -> dict:
        """2025 시즌 실제 통계 가져오기"""
        try:
            # 2025년 모든 레이스 세션 가져오기
            sessions_url = "https://api.openf1.org/v1/sessions?year=2025&session_type=Race"
            sessions_response = requests.get(sessions_url, timeout=10)
            
            season_stats = {
                "season_wins": 0,
                "season_podiums": 0,
                "season_points": 0
            }
            
            if sessions_response.status_code == 200:
                sessions = sessions_response.json()
                
                for session in sessions:
                    session_key = session["session_key"]
                    
                    # 각 세션의 결과 가져오기
                    results_url = f"https://api.openf1.org/v1/results?session_key={session_key}&driver_number={driver_number}"
                    results_response = requests.get(results_url, timeout=5)
                    
                    if results_response.status_code == 200:
                        results = results_response.json()
                        
                        if results:
                            result = results[0]
                            position = result.get("position")
                            points = result.get("points", 0)
                            
                            if position:
                                if position == 1:
                                    season_stats["season_wins"] += 1
                                if position <= 3:
                                    season_stats["season_podiums"] += 1
                                
                                season_stats["season_points"] += points
            
            return season_stats
            
        except Exception as e:
            logger.warning(f"Failed to get current season stats for driver {driver_number}: {e}")
            return {
                "season_wins": 0,
                "season_podiums": 0,
                "season_points": 0
            }
    
    async def get_current_season(self, year: Optional[int] = None):
        if year is None:
            year = datetime.now().year
        
        if self.current_season is None or getattr(self.current_season, 'year', None) != year:
            try:
                self.current_season = get_season(year)
                logger.info(f"Loaded season {year}")
            except Exception as e:
                logger.error(f"Failed to load season {year}: {e}")
                raise
        
        return self.current_season
    
    async def get_drivers(self, session_key: Optional[str] = None) -> List[Dict[str, Any]]:
        try:
            # LiveTiming API에서 드라이버 정보 가져오기 시도
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
                        "team_colour": f"#{driver_info.get('TeamColour', '000000')}",
                        "country_code": driver_info.get("CountryCode", ""),
                        "headshot_url": driver_info.get("HeadshotUrl", "")
                    })
                return drivers
            
            # Fallback: 현재 시즌 순위에서 드라이버 정보 생성
            logger.info("LiveF1 DriverList not available, using fallback driver data")
            current_standings = await self.get_driver_standings()
            if current_standings:
                drivers = []
                for standing in current_standings:
                    driver_name = standing.get("name", "")
                    original_team = standing.get("team", "")
                    
                    # 팀 소속 수정
                    if driver_name == "Yuki Tsunoda":
                        team_name = "Red Bull"
                        team_colour = "#0600EF"  # 레드불 색상
                    elif driver_name == "Liam Lawson":
                        team_name = "RB F1 Team"
                        team_colour = "#6692FF"  # RB F1 Team 색상
                    else:
                        team_name = original_team
                        # 팀별 색상 매핑
                        team_colour_map = {
                            "Mercedes": "#00D2BE",
                            "Red Bull Racing": "#0600EF",
                            "Red Bull": "#0600EF",
                            "Ferrari": "#DC143C",
                            "McLaren": "#FF8700",
                            "Alpine": "#0090FF",
                            "Aston Martin": "#006F62",
                            "Williams": "#005AFF",
                            "Alfa Romeo": "#900000",
                            "Haas": "#FFFFFF",
                            "RB F1 Team": "#6692FF"
                        }
                        team_colour = team_colour_map.get(team_name, "#ff6b35")
                    
                    drivers.append({
                        "driver_number": standing.get("driver_number", 0),
                        "full_name": driver_name,
                        "name": driver_name.split()[-1] if driver_name else "",
                        "abbreviation": standing.get("code", ""),
                        "team_name": team_name,
                        "team_colour": team_colour,
                        "country_code": "",
                        "headshot_url": f"/images/drivers/{driver_name}.webp" if driver_name else ""
                    })
                return drivers
            
            return []
            
        except Exception as e:
            logger.error(f"Failed to get drivers: {e}")
            return []
    
    async def get_driver_detail(self, driver_number: int) -> Optional[Dict[str, Any]]:
        try:
            # 먼저 드라이버 목록에서 기본 정보 찾기
            drivers = await self.get_drivers()
            driver = next((d for d in drivers if d["driver_number"] == driver_number), None)
            
            if not driver:
                return None
            
            # OpenF1 API에서 실제 데이터 가져오기
            try:
                # OpenF1 API에서 드라이버 정보 가져오기
                openf1_url = f"https://api.openf1.org/v1/drivers?driver_number={driver_number}"
                response = requests.get(openf1_url, timeout=10)
                
                ergast_data = {}
                if response.status_code == 200:
                    data = response.json()
                    if data:
                        # 최신 정보 가져오기
                        latest_data = data[0]
                        ergast_data = {
                            "nationality": self._get_nationality_from_country_code(latest_data.get('country_code', '')),
                            "date_of_birth": "",  # OpenF1에서는 제공하지 않음
                            "place_of_birth": ""  # OpenF1에서는 제공하지 않음
                        }
                
                # 2025 시즌 실제 결과 가져오기
                current_season_stats = await self._get_current_season_stats(driver_number)
                logger.info(f"Current season stats for driver {driver_number}: {current_season_stats}")
                
                # 드라이버별 상세 정보 (하드코딩)
                driver_stats = {
                    1: {  # Max Verstappen
                        "nationality": "Dutch",
                        "date_of_birth": "1997-09-30",
                        "place_of_birth": "Hasselt, Belgium",
                        "race_wins": 62,
                        "podiums": 107,
                        "pole_positions": 40,
                        "fastest_laps": 33,
                        "career_points": 2586,
                        "first_entry": 2015,
                        "world_championships": 3
                    },
                    4: {  # Lando Norris
                        "nationality": "British",
                        "date_of_birth": "1999-11-13",
                        "place_of_birth": "Bristol, England",
                        "race_wins": 4,
                        "podiums": 22,
                        "pole_positions": 8,
                        "fastest_laps": 7,
                        "career_points": 650,
                        "first_entry": 2019,
                        "world_championships": 0
                    },
                    81: {  # Oscar Piastri
                        "nationality": "Australian",
                        "date_of_birth": "2001-04-06",
                        "place_of_birth": "Melbourne, Australia",
                        "race_wins": 2,
                        "podiums": 12,
                        "pole_positions": 1,
                        "fastest_laps": 1,
                        "career_points": 292,
                        "first_entry": 2023,
                        "world_championships": 0
                    },
                    16: {  # Charles Leclerc
                        "nationality": "Monégasque",
                        "date_of_birth": "1997-10-16",
                        "place_of_birth": "Monte Carlo, Monaco",
                        "race_wins": 7,
                        "podiums": 39,
                        "pole_positions": 26,
                        "fastest_laps": 9,
                        "career_points": 1196,
                        "first_entry": 2018,
                        "world_championships": 0
                    },
                    55: {  # Carlos Sainz
                        "nationality": "Spanish",
                        "date_of_birth": "1994-09-01",
                        "place_of_birth": "Madrid, Spain",
                        "race_wins": 3,
                        "podiums": 25,
                        "pole_positions": 6,
                        "fastest_laps": 3,
                        "career_points": 1013,
                        "first_entry": 2015,
                        "world_championships": 0
                    },
                    44: {  # Lewis Hamilton
                        "nationality": "British",
                        "date_of_birth": "1985-01-07",
                        "place_of_birth": "Stevenage, England",
                        "race_wins": 103,
                        "podiums": 197,
                        "pole_positions": 104,
                        "fastest_laps": 67,
                        "career_points": 4526,
                        "first_entry": 2007,
                        "world_championships": 7,
                        # 2025 시즌 데이터
                        "season_wins": 0,
                        "season_podiums": 0,
                        "season_points": 0
                    },
                    63: {  # George Russell
                        "nationality": "British",
                        "date_of_birth": "1998-02-15",
                        "place_of_birth": "King's Lynn, England",
                        "race_wins": 1,
                        "podiums": 13,
                        "pole_positions": 3,
                        "fastest_laps": 7,
                        "career_points": 376,
                        "first_entry": 2019,
                        "world_championships": 0
                    },
                    33: {  # Max Verstappen (if using number 33 instead of 1)
                        "nationality": "Dutch",
                        "date_of_birth": "1997-09-30",
                        "place_of_birth": "Hasselt, Belgium",
                        "race_wins": 62,
                        "podiums": 107,
                        "pole_positions": 40,
                        "fastest_laps": 33,
                        "career_points": 2586,
                        "first_entry": 2015,
                        "world_championships": 3
                    }
                }
                
                if driver_number in driver_stats:
                    stats = driver_stats[driver_number]
                    ergast_data.update({
                        "nationality": stats["nationality"],
                        "date_of_birth": stats["date_of_birth"],
                        "place_of_birth": stats["place_of_birth"]
                    })
                    career_stats = {
                        "race_wins": stats["race_wins"],
                        "podiums": stats["podiums"],
                        "pole_positions": stats["pole_positions"],
                        "fastest_laps": stats["fastest_laps"],
                        "career_points": stats["career_points"],
                        "first_entry": stats["first_entry"],
                        "world_championships": stats["world_championships"],
                        # 현재 시즌 데이터는 실제 API에서 가져온 값 사용
                        "season_wins": current_season_stats["season_wins"],
                        "season_podiums": current_season_stats["season_podiums"],
                        "season_points": current_season_stats["season_points"]
                    }
                else:
                    # 기본값 설정
                    career_stats = {
                        "race_wins": 0,
                        "podiums": 0,
                        "pole_positions": 0,
                        "fastest_laps": 0,
                        "career_points": 0,
                        "first_entry": None,
                        "world_championships": 0,
                        # 현재 시즌 데이터는 실제 API에서 가져온 값 사용
                        "season_wins": current_season_stats["season_wins"],
                        "season_podiums": current_season_stats["season_podiums"],
                        "season_points": current_season_stats["season_points"]
                    }
                
            except Exception as e:
                logger.warning(f"Failed to fetch additional driver data for {driver_number}: {e}")
                # 실패 시에도 현재 시즌 데이터는 시도해보기
                current_season_stats = await self._get_current_season_stats(driver_number)
                
                ergast_data = {
                    "nationality": "Unknown",
                    "date_of_birth": "",
                    "place_of_birth": "Unknown"
                }
                career_stats = {
                    "race_wins": 0,
                    "podiums": 0,
                    "pole_positions": 0,
                    "fastest_laps": 0,
                    "career_points": 0,
                    "first_entry": None,
                    "world_championships": 0,
                    # 현재 시즌 데이터는 실제 API에서 가져온 값 사용
                    "season_wins": current_season_stats["season_wins"],
                    "season_podiums": current_season_stats["season_podiums"],
                    "season_points": current_season_stats["season_points"]
                }
            
            # 상세 정보 병합
            detailed_driver = {
                **driver,
                **ergast_data,
                **career_stats
            }
            
            return detailed_driver
            
        except Exception as e:
            logger.error(f"Failed to get driver detail for {driver_number}: {e}")
            return None
    
    async def get_sessions(self, year: Optional[int] = None) -> List[Dict[str, Any]]:
        try:
            season = await self.get_current_season(year)
            if not season or not hasattr(season, 'meetings'):
                return []
            
            sessions = []
            for meeting in season.meetings:
                if hasattr(meeting, 'sessions'):
                    for session in meeting.sessions:
                        sessions.append({
                            "session_key": getattr(session, 'session_key', None),
                            "session_name": getattr(session, 'session_name', ''),
                            "session_type": getattr(session, 'session_type', ''),
                            "date_start": str(getattr(session, 'date_start', '')),
                            "date_end": str(getattr(session, 'date_end', '')),
                            "circuit_short_name": getattr(meeting, 'circuit_short_name', ''),
                            "country_name": getattr(meeting, 'country_name', ''),
                            "meeting_key": getattr(meeting, 'meeting_key', None)
                        })
            
            return sessions
            
        except Exception as e:
            logger.error(f"Failed to get sessions: {e}")
            return []
    
    async def get_live_timing(self) -> Dict[str, Any]:
        try:
            # 실시간 타이밍 데이터 시도
            timing_data = await self._livef1_request("TimingData")
            position_data = await self._livef1_request("Position")
            
            if timing_data or position_data:
                return {
                    "timing": timing_data or {},
                    "positions": position_data or {},
                    "timestamp": datetime.now().isoformat()
                }
            
            # Fallback: 빈 데이터 반환 (세션이 없을 때)
            logger.info("LiveF1 timing data not available, returning empty data")
            return {
                "timing": {},
                "positions": {},
                "timestamp": datetime.now().isoformat(),
                "status": "no_active_session"
            }
            
        except Exception as e:
            logger.error(f"Failed to get live timing: {e}")
            return {
                "timing": {},
                "positions": {},
                "timestamp": datetime.now().isoformat(),
                "status": "error"
            }
    
    async def get_weather(self) -> Dict[str, Any]:
        try:
            weather_data = await self._livef1_request("WeatherData")
            if weather_data:
                return weather_data
            
            # Fallback: 기본 날씨 정보 반환
            logger.info("LiveF1 weather data not available, returning default data")
            return {
                "status": "no_active_session",
                "message": "Weather data only available during active F1 sessions",
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to get weather: {e}")
            return {
                "status": "error",
                "message": "Weather data unavailable",
                "timestamp": datetime.now().isoformat()
            }
    
    async def get_driver_standings(self, year: Optional[int] = None) -> List[Dict[str, Any]]:
        """드라이버 챔피언십 순위 가져오기"""
        try:
            if year is None:
                year = datetime.now().year
            
            # 실제 F1 API에서 데이터 가져오기
            import requests
            
            if year == datetime.now().year:
                # 현재 시즌은 current 사용
                url = "https://api.jolpi.ca/ergast/f1/current/driverStandings"
            else:
                # 특정 년도
                url = f"https://api.jolpi.ca/ergast/f1/{year}/driverStandings"
            
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                standings_list = data['MRData']['StandingsTable']['StandingsLists']
                
                if standings_list:
                    raw_standings = standings_list[0]['DriverStandings']
                    
                    # 데이터 포맷 변환
                    formatted_standings = []
                    for i, driver_data in enumerate(raw_standings):
                        driver_name = f"{driver_data['Driver']['givenName']} {driver_data['Driver']['familyName']}"
                        original_team = driver_data['Constructors'][0]['name'] if driver_data['Constructors'] else 'Unknown'
                        
                        # 팀 소속 수정
                        if driver_name == "Yuki Tsunoda":
                            team_name = "Red Bull"
                        elif driver_name == "Liam Lawson":
                            team_name = "RB F1 Team"
                        else:
                            team_name = original_team
                        
                        # 이미지 URL 추가 (파일이 있으면 자동 매핑)
                        headshot_url = f"/images/drivers/{driver_name}.webp"
                        
                        formatted_standings.append({
                            "position": int(driver_data['position']),
                            "driver_number": int(driver_data['Driver'].get('permanentNumber', i + 1)),
                            "name": driver_name,
                            "code": driver_data['Driver'].get('code', ''),
                            "team": team_name,
                            "points": int(driver_data['points']),
                            "wins": int(driver_data['wins']),
                            "headshot_url": headshot_url
                        })
                    
                    return formatted_standings
            
            # API 실패 시 빈 리스트 반환
            logger.warning(f"Failed to fetch driver standings from API for year {year}")
            return []
            
        except Exception as e:
            logger.error(f"Failed to get driver standings: {e}")
            return []
    
    async def get_constructor_standings(self, year: Optional[int] = None) -> List[Dict[str, Any]]:
        """컨스트럭터 챔피언십 순위 가져오기"""
        try:
            if year is None:
                year = datetime.now().year
            
            # 실제 F1 API에서 데이터 가져오기
            import requests
            
            if year == datetime.now().year:
                # 현재 시즌은 current 사용
                url = "https://api.jolpi.ca/ergast/f1/current/constructorStandings"
            else:
                # 특정 년도
                url = f"https://api.jolpi.ca/ergast/f1/{year}/constructorStandings"
            
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                standings_list = data['MRData']['StandingsTable']['StandingsLists']
                
                if standings_list:
                    raw_standings = standings_list[0]['ConstructorStandings']
                    
                    # 데이터 포맷 변환
                    formatted_standings = []
                    for constructor_data in raw_standings:
                        formatted_standings.append({
                            "position": int(constructor_data['position']),
                            "team": constructor_data['Constructor']['name'],
                            "nationality": constructor_data['Constructor'].get('nationality', ''),
                            "points": int(constructor_data['points']),
                            "wins": int(constructor_data['wins'])
                        })
                    
                    return formatted_standings
            
            # API 실패 시 빈 리스트 반환
            logger.warning(f"Failed to fetch constructor standings from API for year {year}")
            return []
            
        except Exception as e:
            logger.error(f"Failed to get constructor standings: {e}")
            return []
    
    async def get_available_seasons(self) -> List[int]:
        """사용 가능한 시즌 목록 반환"""
        return [2025, 2024, 2023]
    
    async def get_race_calendar(self, year: Optional[int] = None) -> List[Dict[str, Any]]:
        """레이스 캘린더 가져오기"""
        try:
            if year is None:
                year = datetime.now().year
            
            import requests
            
            if year == datetime.now().year:
                url = "https://api.jolpi.ca/ergast/f1/current.json"
            else:
                url = f"https://api.jolpi.ca/ergast/f1/{year}.json"
            
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                races = data['MRData']['RaceTable']['Races']
                
                # 데이터 포맷 변환
                formatted_races = []
                for race in races:
                    race_info = {
                        "round": int(race['round']),
                        "race_name": race['raceName'],
                        "circuit_name": race['Circuit']['circuitName'],
                        "circuit_id": race['Circuit']['circuitId'],
                        "country": race['Circuit']['Location']['country'],
                        "locality": race['Circuit']['Location']['locality'],
                        "date": race['date'],
                        "time": race.get('time'),
                        "url": race.get('url', ''),
                        "season": race['season'],
                        "circuit_url": race['Circuit'].get('url', ''),
                        "first_practice": race.get('FirstPractice', {}).get('date'),
                        "second_practice": race.get('SecondPractice', {}).get('date'),
                        "third_practice": race.get('ThirdPractice', {}).get('date'),
                        "qualifying": race.get('Qualifying', {}).get('date'),
                        "sprint": race.get('Sprint', {}).get('date'),
                    }
                    formatted_races.append(race_info)
                
                return formatted_races
            
            logger.warning(f"Failed to fetch race calendar from API for year {year}")
            return []
            
        except Exception as e:
            logger.error(f"Failed to get race calendar: {e}")
            return []
    
    async def get_next_race(self) -> Optional[Dict[str, Any]]:
        """다음 레이스 정보 가져오기"""
        try:
            races = await self.get_race_calendar()
            if not races:
                return None
            
            today = datetime.now().date()
            
            for race in races:
                race_date = datetime.strptime(race['date'], '%Y-%m-%d').date()
                if race_date >= today:
                    return race
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get next race: {e}")
            return None
    
    async def get_current_race(self) -> Optional[Dict[str, Any]]:
        """현재 진행 중인 레이스 확인"""
        try:
            races = await self.get_race_calendar()
            if not races:
                return None
            
            today = datetime.now().date()
            
            for race in races:
                race_date = datetime.strptime(race['date'], '%Y-%m-%d').date()
                
                # 레이스 주말 확인 (금요일부터 일요일)
                if race.get('first_practice'):
                    weekend_start = datetime.strptime(race['first_practice'], '%Y-%m-%d').date()
                else:
                    # 연습주행 정보가 없으면 레이스 날짜 기준으로 추정
                    from datetime import timedelta
                    weekend_start = race_date - timedelta(days=2)
                
                if weekend_start <= today <= race_date:
                    return race
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get current race: {e}")
            return None
    
    async def get_standings_progression(self, year: Optional[int] = None) -> Dict[str, Any]:
        """시즌 순위 변화 추적 데이터 생성"""
        try:
            if year is None:
                year = datetime.now().year
            
            import requests
            
            # 해당 시즌의 모든 레이스 결과 가져오기
            race_results = await self.get_race_results(year)
            
            if not race_results:
                return {"driver_progression": [], "constructor_progression": [], "race_labels": []}
            
            # 드라이버별 레이스별 순위 및 포인트 추적
            driver_progression = {}
            constructor_progression = {}
            race_labels = []
            
            # 각 레이스별로 순위 계산
            current_driver_points = {}
            current_constructor_points = {}
            
            for race in race_results:
                if not race.get('results'):
                    continue
                    
                race_label = f"R{race['round']}"
                race_labels.append(race_label)
                
                # 레이스 결과에서 포인트 누적
                for result in race['results']:
                    driver_name = result['driver_name']
                    team_name = result['team']
                    points = result['points']
                    
                    # 드라이버 포인트 누적
                    if driver_name not in current_driver_points:
                        current_driver_points[driver_name] = 0
                        driver_progression[driver_name] = []
                    current_driver_points[driver_name] += points
                    
                    # 컨스트럭터 포인트 누적
                    if team_name not in current_constructor_points:
                        current_constructor_points[team_name] = 0
                        constructor_progression[team_name] = []
                    current_constructor_points[team_name] += points
                
                # 현재 레이스 후 순위 계산
                sorted_drivers = sorted(current_driver_points.items(), key=lambda x: x[1], reverse=True)
                sorted_constructors = sorted(current_constructor_points.items(), key=lambda x: x[1], reverse=True)
                
                # 드라이버별 현재 순위 기록
                for position, (driver_name, points) in enumerate(sorted_drivers, 1):
                    if driver_name not in driver_progression:
                        driver_progression[driver_name] = []
                    driver_progression[driver_name].append({
                        "race": race_label,
                        "position": position,
                        "points": points,
                        "round": race['round']
                    })
                
                # 컨스트럭터별 현재 순위 기록
                for position, (team_name, points) in enumerate(sorted_constructors, 1):
                    if team_name not in constructor_progression:
                        constructor_progression[team_name] = []
                    constructor_progression[team_name].append({
                        "race": race_label,
                        "position": position,
                        "points": points,
                        "round": race['round']
                    })
            
            # 모든 드라이버와 컨스트럭터를 포함하되, 포인트 순으로 정렬
            sorted_drivers = sorted(current_driver_points.items(), key=lambda x: x[1], reverse=True)
            sorted_constructors = sorted(current_constructor_points.items(), key=lambda x: x[1], reverse=True)
            
            # 모든 드라이버/컨스트럭터 포함 (순서만 정렬)
            filtered_driver_progression = {name: driver_progression[name] for name, _ in sorted_drivers if name in driver_progression}
            filtered_constructor_progression = {name: constructor_progression[name] for name, _ in sorted_constructors if name in constructor_progression}
            
            return {
                "driver_progression": filtered_driver_progression,
                "constructor_progression": filtered_constructor_progression,
                "race_labels": race_labels,
                "total_races": len(race_labels),
                "year": year
            }
            
        except Exception as e:
            logger.error(f"Failed to get standings progression: {e}")
            return {"driver_progression": [], "constructor_progression": [], "race_labels": []}

    async def get_race_weekend_details(self, year: Optional[int] = None, round_number: Optional[int] = None) -> Dict[str, Any]:
        """특정 레이스 주말의 상세 정보 (일정, 결과 등)"""
        try:
            if year is None:
                year = datetime.now().year
            
            import requests
            
            # 레이스 캘린더 정보
            calendar_url = f"https://api.jolpi.ca/ergast/f1/{year}.json?limit=1000"
            calendar_response = requests.get(calendar_url, timeout=10)
            
            # 레이스 결과 정보
            if round_number:
                results_url = f"https://api.jolpi.ca/ergast/f1/{year}/{round_number}/results.json?limit=1000"
                qualifying_url = f"https://api.jolpi.ca/ergast/f1/{year}/{round_number}/qualifying.json?limit=1000"
            else:
                # 모든 라운드의 결과
                results_url = f"https://api.jolpi.ca/ergast/f1/{year}/results.json?limit=1000"
                qualifying_url = f"https://api.jolpi.ca/ergast/f1/{year}/qualifying.json?limit=1000"
            
            race_weekends = []
            
            if calendar_response.status_code == 200:
                calendar_data = calendar_response.json()
                races = calendar_data['MRData']['RaceTable']['Races']
                
                # 결과 데이터 가져오기
                results_data = {}
                qualifying_data = {}
                
                try:
                    results_response = requests.get(results_url, timeout=10)
                    if results_response.status_code == 200:
                        results_json = results_response.json()
                        for race in results_json['MRData']['RaceTable']['Races']:
                            results_data[int(race['round'])] = race.get('Results', [])
                except:
                    pass
                
                try:
                    qualifying_response = requests.get(qualifying_url, timeout=10)
                    if qualifying_response.status_code == 200:
                        qualifying_json = qualifying_response.json()
                        for race in qualifying_json['MRData']['RaceTable']['Races']:
                            qualifying_data[int(race['round'])] = race.get('QualifyingResults', [])
                except:
                    pass
                
                # 각 레이스 주말 정보 구성
                for race in races:
                    if round_number and int(race['round']) != round_number:
                        continue
                    
                    race_round = int(race['round'])
                    
                    # 세션 일정 정리
                    sessions = []
                    
                    # 연습 세션들
                    if race.get('FirstPractice'):
                        sessions.append({
                            'session_type': 'Practice 1',
                            'date': race['FirstPractice']['date'],
                            'time': race['FirstPractice'].get('time'),
                            'status': 'completed' if race_round in results_data else 'scheduled'
                        })
                    
                    if race.get('SecondPractice'):
                        sessions.append({
                            'session_type': 'Practice 2',
                            'date': race['SecondPractice']['date'],
                            'time': race['SecondPractice'].get('time'),
                            'status': 'completed' if race_round in results_data else 'scheduled'
                        })
                    
                    if race.get('ThirdPractice'):
                        sessions.append({
                            'session_type': 'Practice 3',
                            'date': race['ThirdPractice']['date'],
                            'time': race['ThirdPractice'].get('time'),
                            'status': 'completed' if race_round in results_data else 'scheduled'
                        })
                    
                    # 스프린트 (있는 경우)
                    if race.get('Sprint'):
                        sessions.append({
                            'session_type': 'Sprint',
                            'date': race['Sprint']['date'],
                            'time': race['Sprint'].get('time'),
                            'status': 'completed' if race_round in results_data else 'scheduled'
                        })
                    
                    # 예선
                    if race.get('Qualifying'):
                        sessions.append({
                            'session_type': 'Qualifying',
                            'date': race['Qualifying']['date'],
                            'time': race['Qualifying'].get('time'),
                            'status': 'completed' if race_round in qualifying_data else 'scheduled',
                            'results': qualifying_data.get(race_round, [])
                        })
                    
                    # 레이스
                    sessions.append({
                        'session_type': 'Race',
                        'date': race['date'],
                        'time': race.get('time'),
                        'status': 'completed' if race_round in results_data else 'scheduled',
                        'results': results_data.get(race_round, [])
                    })
                    
                    weekend_info = {
                        'round': race_round,
                        'race_name': race['raceName'],
                        'circuit_name': race['Circuit']['circuitName'],
                        'circuit_id': race['Circuit']['circuitId'],
                        'country': race['Circuit']['Location']['country'],
                        'locality': race['Circuit']['Location']['locality'],
                        'date': race['date'],
                        'url': race.get('url', ''),
                        'season': race['season'],
                        'sessions': sessions,
                        'weekend_status': 'completed' if race_round in results_data else 'upcoming'
                    }
                    
                    race_weekends.append(weekend_info)
            
            if round_number:
                return race_weekends[0] if race_weekends else {}
            
            return {
                'race_weekends': race_weekends,
                'total_weekends': len(race_weekends),
                'year': year
            }
            
        except Exception as e:
            logger.error(f"Failed to get race weekend details: {e}")
            return {}

    async def get_race_results(self, year: Optional[int] = None, round_number: Optional[int] = None) -> List[Dict[str, Any]]:
        """레이스 결과 가져오기 (페이지네이션 사용)"""
        try:
            if year is None:
                year = datetime.now().year
            
            import requests
            
            all_races = []
            offset = 0
            limit = 100
            
            while True:
                # 페이지네이션으로 모든 결과 가져오기
                if round_number:
                    url = f"https://api.jolpi.ca/ergast/f1/{year}/{round_number}/results.json?limit={limit}&offset={offset}"
                else:
                    if year == datetime.now().year:
                        url = f"https://api.jolpi.ca/ergast/f1/current/results.json?limit={limit}&offset={offset}"
                    else:
                        url = f"https://api.jolpi.ca/ergast/f1/{year}/results.json?limit={limit}&offset={offset}"
                
                response = requests.get(url, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    races = data['MRData']['RaceTable']['Races']
                    
                    if not races:  # 더 이상 데이터가 없으면 중단
                        break
                    
                    all_races.extend(races)
                    
                    # 총 레이스 수를 확인하여 모든 데이터를 가져왔는지 체크
                    total = int(data['MRData'].get('total', 0))
                    if len(all_races) >= total:
                        break
                    
                    offset += limit
                else:
                    break
            
            # 데이터 포맷팅
            formatted_results = []
            for race in all_races:
                race_info = {
                    "round": int(race['round']),
                    "race_name": race['raceName'],
                    "circuit_name": race['Circuit']['circuitName'],
                    "country": race['Circuit']['Location']['country'],
                    "date": race['date'],
                    "season": race['season'],
                    "results": []
                }
                
                # 결과 데이터 포맷팅
                if 'Results' in race:
                    for result in race['Results']:
                        driver_result = {
                            "position": int(result['position']),
                            "driver_number": int(result['Driver'].get('permanentNumber', 0)),
                            "driver_name": f"{result['Driver']['givenName']} {result['Driver']['familyName']}",
                            "driver_code": result['Driver'].get('code', ''),
                            "team": result['Constructor']['name'],
                            "grid": int(result.get('grid', 0)),
                            "laps": int(result.get('laps', 0)),
                            "status": result.get('status', ''),
                            "time": result.get('Time', {}).get('time'),
                            "points": float(result.get('points', 0)),
                            "fastest_lap": result.get('FastestLap', {}).get('Time', {}).get('time')
                        }
                        race_info["results"].append(driver_result)
                
                formatted_results.append(race_info)
            
            logger.info(f"Fetched {len(formatted_results)} race results for year {year}")
            return formatted_results
            
        except Exception as e:
            logger.error(f"Failed to get race results: {e}")
            return []
    
    async def get_driver_statistics(self, year: Optional[int] = None, driver_id: Optional[str] = None) -> Dict[str, Any]:
        """드라이버 통계 데이터 가져오기"""
        try:
            if year is None:
                year = datetime.now().year
            
            import requests
            
            # 특정 드라이버 통계 또는 전체 드라이버 통계
            if driver_id:
                # 특정 드라이버의 상세 통계
                driver_results = []
                
                # 해당 년도의 모든 레이스 결과에서 해당 드라이버 찾기
                if year == datetime.now().year:
                    url = f"https://api.jolpi.ca/ergast/f1/current/drivers/{driver_id}/results.json"
                else:
                    url = f"https://api.jolpi.ca/ergast/f1/{year}/drivers/{driver_id}/results.json"
                
                logger.info(f"DEBUG: Requesting URL: {url}")
                response = requests.get(url, timeout=10)
                logger.info(f"DEBUG: Response status: {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    races = data['MRData']['RaceTable']['Races']
                    
                    logger.info(f"DEBUG: Found {len(races)} races for {driver_id} in {year}")
                    logger.info(f"DEBUG: Sample race data: {races[:1] if races else 'No races'}")
                    
                    wins = podiums = points_finishes = dnfs = 0
                    total_points = 0
                    fastest_laps = 0
                    
                    for race in races:
                        if 'Results' in race and race['Results']:
                            result = race['Results'][0]  # 해당 드라이버의 결과
                            position = int(result['position'])
                            points = float(result.get('points', 0))
                            status = result.get('status', '')
                            
                            # 통계 계산
                            if position == 1:
                                wins += 1
                            if position <= 3:
                                podiums += 1
                            if points > 0:
                                points_finishes += 1
                            if 'DNF' in status or 'Accident' in status or 'Retired' in status:
                                dnfs += 1
                                
                            total_points += points
                            
                            # 패스티스트 랩 체크
                            if result.get('FastestLap', {}).get('rank') == '1':
                                fastest_laps += 1
                            
                            # 레이스별 결과 저장
                            driver_results.append({
                                'round': int(race['round']),
                                'race_name': race['raceName'],
                                'position': position,
                                'grid': int(result.get('grid', 0)),
                                'points': points,
                                'status': status,
                                'time': result.get('Time', {}).get('time'),
                                'fastest_lap': result.get('FastestLap', {}).get('Time', {}).get('time')
                            })
                    
                    # 드라이버 정보
                    driver_info = {}
                    if races and races[0]['Results']:
                        driver_data = races[0]['Results'][0]['Driver']
                        driver_info = {
                            'driver_id': driver_data['driverId'],
                            'full_name': f"{driver_data['givenName']} {driver_data['familyName']}",
                            'code': driver_data.get('code', ''),
                            'number': driver_data.get('permanentNumber', ''),
                            'nationality': driver_data.get('nationality', ''),
                            'date_of_birth': driver_data.get('dateOfBirth', ''),
                            'url': driver_data.get('url', '')
                        }
                    
                    return {
                        'driver_info': driver_info,
                        'season_stats': {
                            'wins': wins,
                            'podiums': podiums,
                            'points_finishes': points_finishes,
                            'dnfs': dnfs,
                            'total_points': total_points,
                            'fastest_laps': fastest_laps,
                            'races_entered': len(races)
                        },
                        'race_results': driver_results,
                        'year': year
                    }
            else:
                # 전체 드라이버 통계 (시즌 요약)
                standings = await self.get_driver_standings(year)
                race_results = await self.get_race_results(year)
                
                driver_stats = []
                for standing in standings:
                    driver_name = standing['name']
                    
                    # 각 드라이버의 레이스 결과 분석
                    wins = podiums = dnfs = 0
                    fastest_laps = 0
                    
                    for race in race_results:
                        for result in race.get('results', []):
                            if result['driver_name'] == driver_name:
                                position = result['position']
                                status = result['status']
                                
                                if position == 1:
                                    wins += 1
                                if position <= 3:
                                    podiums += 1
                                if 'DNF' in status or 'Accident' in status or 'Retired' in status:
                                    dnfs += 1
                                if result.get('fastest_lap'):
                                    fastest_laps += 1
                    
                    driver_stats.append({
                        'position': standing['position'],
                        'driver_name': driver_name,
                        'driver_code': standing['code'],
                        'team': standing['team'],
                        'points': standing['points'],
                        'wins': wins,
                        'podiums': podiums,
                        'dnfs': dnfs,
                        'fastest_laps': fastest_laps
                    })
                
                return {
                    'drivers': driver_stats,
                    'total_drivers': len(driver_stats),
                    'year': year
                }
                
        except Exception as e:
            logger.error(f"Failed to get driver statistics: {e}")
            return {}

    async def get_driver_career_statistics(self, driver_id: str) -> Dict[str, Any]:
        """드라이버의 전체 커리어 통계를 현재 시즌부터 역순으로 계산"""
        try:
            career_stats = {
                "race_wins": 0,
                "podiums": 0,
                "pole_positions": 0,
                "fastest_laps": 0,
                "career_points": 0,
                "world_championships": 0,
                "first_entry": None,
                "seasons_data": []
            }
            
            current_year = datetime.now().year
            year = current_year
            consecutive_empty_years = 0
            max_empty_years = 3  # 연속 3년 데이터 없으면 중단
            
            while consecutive_empty_years < max_empty_years and year >= 1950:  # F1 시작 연도
                try:
                    logger.info(f"Fetching career statistics for {driver_id} in {year}")
                    year_stats = await self.get_driver_statistics(year=year, driver_id=driver_id)
                    
                    if year_stats and 'season_stats' in year_stats:
                        stats = year_stats['season_stats']
                        races_entered = stats.get("races_entered", 0)
                        
                        if races_entered > 0:
                            # 데이터가 있는 경우
                            consecutive_empty_years = 0
                            
                            # 첫 참가 연도 업데이트
                            if career_stats["first_entry"] is None or year < career_stats["first_entry"]:
                                career_stats["first_entry"] = year
                            
                            # 통계 누적
                            career_stats["race_wins"] += stats.get("wins", 0)
                            career_stats["podiums"] += stats.get("podiums", 0)
                            career_stats["career_points"] += stats.get("total_points", 0)
                            career_stats["fastest_laps"] += stats.get("fastest_laps", 0)
                            
                            # 폴 포지션 추정 (승수의 80%)
                            career_stats["pole_positions"] += int(stats.get("wins", 0) * 0.8)
                            
                            # 월드 챔피언십 체크
                            try:
                                standings = await self.get_driver_standings(year)
                                for driver_standing in standings:
                                    if driver_standing.get("driver_number") == stats.get("driver_number"):
                                        if driver_standing.get("position") == 1:
                                            career_stats["world_championships"] += 1
                                        break
                            except Exception as e:
                                logger.warning(f"Failed to get standings for year {year}: {e}")
                            
                            # 연도별 데이터 저장
                            career_stats["seasons_data"].append({
                                "year": year,
                                "wins": stats.get("wins", 0),
                                "podiums": stats.get("podiums", 0),
                                "points": stats.get("total_points", 0),
                                "fastest_laps": stats.get("fastest_laps", 0),
                                "races_entered": races_entered
                            })
                            
                            logger.info(f"Added {year} data for {driver_id}: wins={stats.get('wins', 0)}, podiums={stats.get('podiums', 0)}")
                        else:
                            consecutive_empty_years += 1
                            logger.info(f"No race data for {driver_id} in {year}, empty count: {consecutive_empty_years}")
                    else:
                        consecutive_empty_years += 1
                        logger.info(f"No statistics found for {driver_id} in {year}, empty count: {consecutive_empty_years}")
                        
                except Exception as e:
                    consecutive_empty_years += 1
                    logger.warning(f"Error fetching statistics for {driver_id} in {year}: {e}")
                
                year -= 1
            
            # 시즌 데이터를 시간순으로 정렬 (오래된 것부터)
            career_stats["seasons_data"].sort(key=lambda x: x["year"])
            
            logger.info(f"Career statistics completed for {driver_id}: {career_stats}")
            return career_stats
            
        except Exception as e:
            logger.error(f"Failed to get career statistics for {driver_id}: {e}")
            return {}

    async def get_circuit_information(self, year: Optional[int] = None, circuit_id: Optional[str] = None) -> Dict[str, Any]:
        """서킷 정보 가져오기"""
        try:
            if year is None:
                year = datetime.now().year
                
            import requests
            
            if circuit_id:
                # 특정 서킷의 상세 정보
                if year == datetime.now().year:
                    url = f"https://api.jolpi.ca/ergast/f1/current/circuits/{circuit_id}.json"
                else:
                    url = f"https://api.jolpi.ca/ergast/f1/{year}/circuits/{circuit_id}.json"
                
                response = requests.get(url, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    circuits = data['MRData']['CircuitTable']['Circuits']
                    
                    if circuits:
                        circuit = circuits[0]
                        
                        # 해당 서킷에서의 레이스 결과 가져오기
                        if year == datetime.now().year:
                            races_url = f"https://api.jolpi.ca/ergast/f1/current/circuits/{circuit_id}/results.json"
                        else:
                            races_url = f"https://api.jolpi.ca/ergast/f1/{year}/circuits/{circuit_id}/results.json"
                        
                        circuit_races = []
                        try:
                            races_response = requests.get(races_url, timeout=10)
                            if races_response.status_code == 200:
                                races_data = races_response.json()
                                circuit_races = races_data['MRData']['RaceTable']['Races']
                        except:
                            pass
                        
                        # 랩 기록 정보 (qualifying 결과에서 추출)
                        lap_records = []
                        if circuit_races:
                            for race in circuit_races:
                                if 'Results' in race and race['Results']:
                                    fastest_lap = None
                                    for result in race['Results']:
                                        if result.get('FastestLap'):
                                            if not fastest_lap or result['FastestLap']['Time']['time'] < fastest_lap['time']:
                                                fastest_lap = {
                                                    'time': result['FastestLap']['Time']['time'],
                                                    'driver': f"{result['Driver']['givenName']} {result['Driver']['familyName']}",
                                                    'year': race['season'],
                                                    'race': race['raceName']
                                                }
                                    
                                    if fastest_lap:
                                        lap_records.append(fastest_lap)
                        
                        # 승리 통계
                        winner_stats = {}
                        constructor_stats = {}
                        
                        for race in circuit_races:
                            if 'Results' in race and race['Results']:
                                winner = race['Results'][0]
                                driver_name = f"{winner['Driver']['givenName']} {winner['Driver']['familyName']}"
                                constructor_name = winner['Constructor']['name']
                                
                                winner_stats[driver_name] = winner_stats.get(driver_name, 0) + 1
                                constructor_stats[constructor_name] = constructor_stats.get(constructor_name, 0) + 1
                        
                        return {
                            'circuit_info': {
                                'circuit_id': circuit['circuitId'],
                                'name': circuit['circuitName'],
                                'location': {
                                    'locality': circuit['Location']['locality'],
                                    'country': circuit['Location']['country'],
                                    'lat': circuit['Location'].get('lat'),
                                    'lng': circuit['Location'].get('long')
                                },
                                'url': circuit.get('url', '')
                            },
                            'race_history': circuit_races,
                            'lap_records': sorted(lap_records, key=lambda x: x['time'])[:10],  # Top 10 fastest laps
                            'winner_statistics': {
                                'drivers': dict(sorted(winner_stats.items(), key=lambda x: x[1], reverse=True)[:10]),
                                'constructors': dict(sorted(constructor_stats.items(), key=lambda x: x[1], reverse=True)[:10])
                            },
                            'total_races': len(circuit_races),
                            'year': year
                        }
            else:
                # 모든 서킷 목록
                if year == datetime.now().year:
                    url = "https://api.jolpi.ca/ergast/f1/current/circuits.json"
                else:
                    url = f"https://api.jolpi.ca/ergast/f1/{year}/circuits.json"
                
                response = requests.get(url, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    circuits = data['MRData']['CircuitTable']['Circuits']
                    
                    circuit_list = []
                    for circuit in circuits:
                        circuit_list.append({
                            'circuit_id': circuit['circuitId'],
                            'name': circuit['circuitName'],
                            'location': {
                                'locality': circuit['Location']['locality'],
                                'country': circuit['Location']['country'],
                                'lat': circuit['Location'].get('lat'),
                                'lng': circuit['Location'].get('long')
                            },
                            'url': circuit.get('url', '')
                        })
                    
                    return {
                        'circuits': circuit_list,
                        'total_circuits': len(circuit_list),
                        'year': year
                    }
                    
        except Exception as e:
            logger.error(f"Failed to get circuit information: {e}")
            return {}

    async def get_team_statistics(self, year: Optional[int] = None, team_id: Optional[str] = None) -> Dict[str, Any]:
        """팀 통계 데이터 가져오기"""
        try:
            if year is None:
                year = datetime.now().year
            
            import requests
            
            if team_id:
                # 특정 팀의 상세 통계
                if year == datetime.now().year:
                    url = f"https://api.jolpi.ca/ergast/f1/current/constructors/{team_id}/results.json"
                else:
                    url = f"https://api.jolpi.ca/ergast/f1/{year}/constructors/{team_id}/results.json"
                
                response = requests.get(url, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    races = data['MRData']['RaceTable']['Races']
                    
                    # 팀 통계 계산
                    wins = podiums = points_finishes = dnfs = 0
                    total_points = 0
                    fastest_laps = 0
                    one_twos = 0  # 1-2 피니시
                    
                    team_results = []
                    
                    for race in races:
                        if 'Results' in race:
                            race_data = {
                                'round': int(race['round']),
                                'race_name': race['raceName'],
                                'driver_results': []
                            }
                            
                            positions = []
                            for result in race['Results']:
                                position = int(result['position'])
                                points = float(result.get('points', 0))
                                status = result.get('status', '')
                                
                                positions.append(position)
                                
                                # 통계 업데이트
                                if position == 1:
                                    wins += 1
                                if position <= 3:
                                    podiums += 1
                                if points > 0:
                                    points_finishes += 1
                                if 'DNF' in status or 'Accident' in status or 'Retired' in status:
                                    dnfs += 1
                                if result.get('FastestLap', {}).get('rank') == '1':
                                    fastest_laps += 1
                                
                                total_points += points
                                
                                # 드라이버별 결과
                                race_data['driver_results'].append({
                                    'driver_name': f"{result['Driver']['givenName']} {result['Driver']['familyName']}",
                                    'position': position,
                                    'grid': int(result.get('grid', 0)),
                                    'points': points,
                                    'status': status,
                                    'time': result.get('Time', {}).get('time')
                                })
                            
                            # 1-2 피니시 체크
                            if len(positions) >= 2 and 1 in positions and 2 in positions:
                                one_twos += 1
                            
                            team_results.append(race_data)
                    
                    # 팀 정보
                    team_info = {}
                    if races and races[0]['Results']:
                        constructor_data = races[0]['Results'][0]['Constructor']
                        team_info = {
                            'team_id': constructor_data['constructorId'],
                            'name': constructor_data['name'],
                            'nationality': constructor_data.get('nationality', ''),
                            'url': constructor_data.get('url', '')
                        }
                    
                    return {
                        'team_info': team_info,
                        'season_stats': {
                            'wins': wins,
                            'podiums': podiums,
                            'points_finishes': points_finishes,
                            'dnfs': dnfs,
                            'total_points': total_points,
                            'fastest_laps': fastest_laps,
                            'one_twos': one_twos,
                            'races_entered': len(races)
                        },
                        'race_results': team_results,
                        'year': year
                    }
            else:
                # 전체 팀 통계
                standings = await self.get_constructor_standings(year)
                race_results = await self.get_race_results(year)
                
                team_stats = []
                for standing in standings:
                    team_name = standing['team']
                    
                    # 각 팀의 레이스 결과 분석
                    wins = podiums = dnfs = 0
                    fastest_laps = 0
                    one_twos = 0
                    
                    for race in race_results:
                        race_positions = []
                        for result in race.get('results', []):
                            if result['team'] == team_name:
                                position = result['position']
                                status = result['status']
                                
                                race_positions.append(position)
                                
                                if position == 1:
                                    wins += 1
                                if position <= 3:
                                    podiums += 1
                                if 'DNF' in status or 'Accident' in status or 'Retired' in status:
                                    dnfs += 1
                                if result.get('fastest_lap'):
                                    fastest_laps += 1
                        
                        # 1-2 피니시 체크
                        if len(race_positions) >= 2 and 1 in race_positions and 2 in race_positions:
                            one_twos += 1
                    
                    team_stats.append({
                        'position': standing['position'],
                        'team_name': team_name,
                        'nationality': standing.get('nationality', ''),
                        'points': standing['points'],
                        'wins': wins,
                        'podiums': podiums,
                        'dnfs': dnfs,
                        'fastest_laps': fastest_laps,
                        'one_twos': one_twos
                    })
                
                return {
                    'teams': team_stats,
                    'total_teams': len(team_stats),
                    'year': year
                }
                
        except Exception as e:
            logger.error(f"Failed to get team statistics: {e}")
            return {}

    async def _livef1_request(self, endpoint: str) -> Any:
        try:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None, 
                lambda: livetimingF1_request(endpoint)
            )
            return result
        except Exception as e:
            # 403 Forbidden은 정상적인 상황 (활성 세션이 없을 때)
            if "403" in str(e) or "Forbidden" in str(e):
                logger.debug(f"LiveF1 endpoint {endpoint} not available (no active session)")
            else:
                logger.warning(f"LiveF1 API request failed for {endpoint}: {e}")
            return None
    
    async def broadcast_to_websockets(self, data: Dict[str, Any]):
        if not self.websocket_connections:
            return
        
        message = json.dumps(data)
        disconnected = []
        
        for websocket in self.websocket_connections:
            try:
                await websocket.send_text(message)
            except:
                disconnected.append(websocket)
        
        # 연결이 끊어진 WebSocket 제거
        for ws in disconnected:
            self.websocket_connections.remove(ws)

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