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

import livef1
from livef1 import get_season, get_session, get_meeting
from livef1.api import livetimingF1_request

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI 앱 생성
app = FastAPI(
    title="F1 LiveTiming Dashboard",
    description="LiveF1 기반 실시간 F1 대시보드",
    version="2.0.0"
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class LiveF1Service:
    def __init__(self):
        self.current_season = None
        self.current_session = None
        self.websocket_connections: List[WebSocket] = []
    
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
                    drivers.append({
                        "driver_number": standing.get("driver_number", 0),
                        "full_name": standing.get("name", ""),
                        "name": standing.get("name", "").split()[-1] if standing.get("name") else "",
                        "abbreviation": standing.get("code", ""),
                        "team_name": standing.get("team", ""),
                        "team_colour": "#ff6b35",  # 기본 색상
                        "country_code": "",
                        "headshot_url": ""
                    })
                return drivers
            
            return []
            
        except Exception as e:
            logger.error(f"Failed to get drivers: {e}")
            return []
    
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
                        formatted_standings.append({
                            "position": int(driver_data['position']),
                            "driver_number": int(driver_data['Driver'].get('permanentNumber', i + 1)),
                            "name": f"{driver_data['Driver']['givenName']} {driver_data['Driver']['familyName']}",
                            "code": driver_data['Driver'].get('code', ''),
                            "team": driver_data['Constructors'][0]['name'] if driver_data['Constructors'] else 'Unknown',
                            "points": int(driver_data['points']),
                            "wins": int(driver_data['wins'])
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

@app.get("/api/v1/status")
async def get_status():
    return {
        "status": "running",
        "data_source": "LiveF1",
        "websocket_connections": len(livef1_service.websocket_connections),
        "timestamp": datetime.now().isoformat()
    }

# WebSocket 엔드포인트
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    livef1_service.websocket_connections.append(websocket)
    logger.info(f"WebSocket connected. Total connections: {len(livef1_service.websocket_connections)}")
    
    try:
        while True:
            # 클라이언트에서 메시지 대기 (keep-alive)
            await websocket.receive_text()
    except WebSocketDisconnect:
        livef1_service.websocket_connections.remove(websocket)
        logger.info(f"WebSocket disconnected. Total connections: {len(livef1_service.websocket_connections)}")

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
    uvicorn.run(app, host="0.0.0.0", port=8000)