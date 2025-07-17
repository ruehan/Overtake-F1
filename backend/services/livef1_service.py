"""
LiveF1 서비스 클래스
F1 실시간 데이터 및 통계 정보를 처리하는 서비스
"""
from typing import List, Optional, Dict, Any
import asyncio
import json
import logging
from datetime import datetime
import requests
from fastapi import WebSocket

import livef1
from livef1 import get_season, get_session, get_meeting
from livef1.api import livetimingF1_request

# 로깅 설정
logger = logging.getLogger(__name__)


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
    
    async def _get_meeting_key_for_round(self, round_number: int, year: int = 2025) -> Optional[int]:
        """공식 캘린더에서 round_number에 해당하는 meeting_key를 추출"""
        try:
            # OpenF1 세션 정보에서 meeting_key 추출
            url = f"https://api.openf1.org/v1/sessions?year={year}"
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                sessions = response.json()
                # 라운드별로 첫 번째 Race 세션의 meeting_key를 기준으로 매핑
                round_meeting_map = {}
                for session in sessions:
                    if session.get('session_type', '').lower() == 'race':
                        meeting_key = session.get('meeting_key')
                        round_idx = len(round_meeting_map) + 1
                        round_meeting_map[round_idx] = meeting_key
                return round_meeting_map.get(round_number)
            return None
        except Exception as e:
            logger.warning(f"Failed to get meeting_key for round {round_number}: {e}")
            return None

    async def _get_openf1_session_results_from_json(self, round_number: int, session_type: str, year: int = 2025) -> List[Dict[str, Any]]:
        """meeting_key + session_type 기반으로 OpenF1 JSON에서 세션 결과를 추출"""
        try:
            import os
            json_file_path = os.path.join(os.path.dirname(__file__), "..", "openf1_2025_results.json")
            if not os.path.exists(json_file_path):
                logger.warning(f"OpenF1 JSON file not found: {json_file_path}")
                return []
            with open(json_file_path, 'r', encoding='utf-8') as f:
                openf1_data = json.load(f)
            sessions = openf1_data.get('sessions', {})
            # 1. round_number → meeting_key
            meeting_key = await self._get_meeting_key_for_round(round_number, year)
            if not meeting_key:
                logger.warning(f"No meeting_key found for round {round_number}")
                return []
            # 2. meeting_key + session_type으로 정확히 매칭
            target_session = None
            for session in sessions.values():
                if session.get('meeting_key') == meeting_key and session.get('session_type', '').lower() == session_type.lower():
                    target_session = session
                    break
            if not target_session:
                logger.warning(f"No session found for meeting_key {meeting_key}, session_type {session_type}")
                return []
            raw_results = target_session.get('results', [])
            # position이 None, 'None', '', 'null' 등 이상치이거나 숫자가 아닌 경우 제외
            valid_results = [
                result for result in raw_results
                if result.get('position') not in [None, 'None', '', 'null'] and str(result.get('position')).isdigit()
            ]
            sorted_results = sorted(valid_results, key=lambda x: int(x.get('position')))
            
            # 라운드 번호에 맞는 세션 찾기
            sessions = openf1_data.get('sessions', {})
            
            # 세션들을 날짜 순으로 정렬하여 라운드 번호에 맞는 세션 찾기
            session_list = []
            for session_key, session_data in sessions.items():
                if session_data.get('session_type') == session_type:
                    session_list.append(session_data)
            
            # 날짜 순으로 정렬
            session_list.sort(key=lambda x: x.get('date_start', ''))
            
            # 라운드 번호에 해당하는 세션 선택
            if round_number <= len(session_list):
                target_session = session_list[round_number - 1]
                raw_results = target_session.get('results', [])
                
                # OpenF1 원본 데이터를 Ergast 형식으로 변환
                formatted_results = []
                
                # 드라이버 이름 매핑
                driver_name_map = {
                    1: {"givenName": "Max", "familyName": "Verstappen", "code": "VER"},
                    4: {"givenName": "Lando", "familyName": "Norris", "code": "NOR"},
                    5: {"givenName": "Gabriel", "familyName": "Bortoleto", "code": "BOR"},
                    6: {"givenName": "Isack", "familyName": "Hadjar", "code": "HAD"},
                    7: {"givenName": "Jack", "familyName": "Doohan", "code": "DOO"},
                    10: {"givenName": "Pierre", "familyName": "Gasly", "code": "GAS"},
                    12: {"givenName": "Andrea Kimi", "familyName": "Antonelli", "code": "ANT"},
                    14: {"givenName": "Fernando", "familyName": "Alonso", "code": "ALO"},
                    16: {"givenName": "Charles", "familyName": "Leclerc", "code": "LEC"},
                    18: {"givenName": "Lance", "familyName": "Stroll", "code": "STR"},
                    22: {"givenName": "Yuki", "familyName": "Tsunoda", "code": "TSU"},
                    23: {"givenName": "Alexander", "familyName": "Albon", "code": "ALB"},
                    27: {"givenName": "Nico", "familyName": "Hülkenberg", "code": "HUL"},
                    30: {"givenName": "Liam", "familyName": "Lawson", "code": "LAW"},
                    31: {"givenName": "Esteban", "familyName": "Ocon", "code": "OCO"},
                    44: {"givenName": "Lewis", "familyName": "Hamilton", "code": "HAM"},
                    55: {"givenName": "Carlos", "familyName": "Sainz", "code": "SAI"},
                    63: {"givenName": "George", "familyName": "Russell", "code": "RUS"},
                    81: {"givenName": "Oscar", "familyName": "Piastri", "code": "PIA"},
                    87: {"givenName": "Oliver", "familyName": "Bearman", "code": "BEA"},
                }
                
                # 팀 매핑
                team_map = {
                    1: "Red Bull Racing", 4: "McLaren", 5: "Sauber", 6: "RB F1 Team", 7: "Alpine F1 Team",
                    10: "Alpine F1 Team", 12: "Mercedes", 14: "Aston Martin", 16: "Ferrari", 18: "Aston Martin",
                    22: "RB F1 Team", 23: "Williams", 27: "Sauber", 30: "Red Bull Racing", 31: "Haas F1 Team",
                    44: "Ferrari", 55: "Williams", 63: "Mercedes", 81: "McLaren", 87: "Haas F1 Team",
                }
                
                for result in sorted_results:
                    driver_number = result.get('driver_number', 0)
                    driver_info = driver_name_map.get(driver_number, {
                        "givenName": "Driver",
                        "familyName": f"#{driver_number}",
                        "code": f"D{driver_number:02d}"
                    })
                    
                    formatted_result = {
                        'position': str(result.get('position')),
                        'Driver': {
                            'givenName': driver_info["givenName"],
                            'familyName': driver_info["familyName"],
                            'permanentNumber': str(driver_number),
                            'code': driver_info["code"]
                        },
                        'Constructor': {
                            'name': team_map.get(driver_number, 'Unknown Team')
                        },
                        'points': str(result.get('points', 0)),
                        'laps': str(result.get('number_of_laps', 0))
                    }
                    
                    # 레이스 세션인 경우 시간 정보 추가
                    if session_type.lower() == 'race':
                        if result.get('duration'):
                            minutes = int(result['duration'] // 60)
                            seconds = result['duration'] % 60
                            formatted_result['Time'] = {
                                'time': f"{minutes}:{seconds:06.3f}"
                            }
                        if result.get('gap_to_leader') and result.get('gap_to_leader') > 0:
                            formatted_result['gap'] = f"+{result['gap_to_leader']:.3f}s"
                    
                    formatted_results.append(formatted_result)
                
                logger.info(f"OpenF1 JSON returned {len(formatted_results)} valid results for round {round_number} {session_type}")
                return formatted_results
            
            return []
            
        except Exception as e:
            logger.warning(f"Failed to get OpenF1 session results from JSON for round {round_number}: {e}")
            return []

    async def _get_openf1_race_weekend_details(self, round_number: Optional[int] = None) -> Dict[str, Any]:
        """2025년: motorsportstats_2025_race_results.json만 사용, 없으면 빈 데이터 반환"""
        import os
        import json
        base_dir = os.path.dirname(__file__)
        msstats_path = os.path.join(base_dir, "..", "motorsportstats_2025_race_results.json")
        # motorsportstats만 사용
        if os.path.exists(msstats_path):
            with open(msstats_path, 'r', encoding='utf-8') as f:
                msstats_data = json.load(f)
            weekends = []
            for idx, (slug, results) in enumerate(msstats_data.items(), 1):
                if round_number and idx != round_number:
                    continue
                weekends.append({
                    'round': idx,
                    'race_name': slug.replace('-', ' ').title(),
                    'sessions': [
                        {
                            'session_type': 'Race',
                            'results': results
                        }
                    ],
                    'weekend_status': 'completed' if results else 'upcoming',
                    'date': None  # 날짜 정보는 motorsportstats 데이터에 없으므로 None 처리
                })
            if round_number:
                return {'race_weekends': [weekends[0]] if weekends else []}
            return {'race_weekends': weekends, 'total_weekends': len(weekends), 'year': 2025}
        # 파일 없으면 빈 데이터 반환
        return {'race_weekends': [], 'total_weekends': 0, 'year': 2025}

    def _convert_openf1_results_to_ergast(self, openf1_results: List[Dict], session_type: str) -> List[Dict]:
        """OpenF1 결과를 Ergast 형식으로 변환"""
        try:
            if not openf1_results:
                return []
            
            # 드라이버 정보 매핑
            driver_name_map = {
                1: {"givenName": "Max", "familyName": "Verstappen", "code": "VER", "permanentNumber": "1"},
                4: {"givenName": "Lando", "familyName": "Norris", "code": "NOR", "permanentNumber": "4"},
                5: {"givenName": "Gabriel", "familyName": "Bortoleto", "code": "BOR", "permanentNumber": "5"},
                6: {"givenName": "Isack", "familyName": "Hadjar", "code": "HAD", "permanentNumber": "6"},
                7: {"givenName": "Jack", "familyName": "Doohan", "code": "DOO", "permanentNumber": "7"},
                10: {"givenName": "Pierre", "familyName": "Gasly", "code": "GAS", "permanentNumber": "10"},
                12: {"givenName": "Andrea Kimi", "familyName": "Antonelli", "code": "ANT", "permanentNumber": "12"},
                14: {"givenName": "Fernando", "familyName": "Alonso", "code": "ALO", "permanentNumber": "14"},
                16: {"givenName": "Charles", "familyName": "Leclerc", "code": "LEC", "permanentNumber": "16"},
                18: {"givenName": "Lance", "familyName": "Stroll", "code": "STR", "permanentNumber": "18"},
                22: {"givenName": "Yuki", "familyName": "Tsunoda", "code": "TSU", "permanentNumber": "22"},
                23: {"givenName": "Alexander", "familyName": "Albon", "code": "ALB", "permanentNumber": "23"},
                27: {"givenName": "Nico", "familyName": "Hülkenberg", "code": "HUL", "permanentNumber": "27"},
                30: {"givenName": "Liam", "familyName": "Lawson", "code": "LAW", "permanentNumber": "30"},
                31: {"givenName": "Esteban", "familyName": "Ocon", "code": "OCO", "permanentNumber": "31"},
                43: {"givenName": "Franco", "familyName": "Colapinto", "code": "COL", "permanentNumber": "43"},
                44: {"givenName": "Lewis", "familyName": "Hamilton", "code": "HAM", "permanentNumber": "44"},
                55: {"givenName": "Carlos", "familyName": "Sainz", "code": "SAI", "permanentNumber": "55"},
                63: {"givenName": "George", "familyName": "Russell", "code": "RUS", "permanentNumber": "63"},
                81: {"givenName": "Oscar", "familyName": "Piastri", "code": "PIA", "permanentNumber": "81"},
                87: {"givenName": "Oliver", "familyName": "Bearman", "code": "BEA", "permanentNumber": "87"}
            }
            
            # 팀 정보 매핑
            team_map = {
                1: {"name": "Red Bull Racing", "constructorId": "red_bull"},
                4: {"name": "McLaren", "constructorId": "mclaren"},
                5: {"name": "Sauber", "constructorId": "sauber"},
                6: {"name": "Red Bull Racing", "constructorId": "red_bull"},
                7: {"name": "Alpine", "constructorId": "alpine"},
                10: {"name": "Alpine", "constructorId": "alpine"},
                12: {"name": "Mercedes", "constructorId": "mercedes"},
                14: {"name": "Aston Martin", "constructorId": "aston_martin"},
                16: {"name": "Ferrari", "constructorId": "ferrari"},
                18: {"name": "Aston Martin", "constructorId": "aston_martin"},
                22: {"name": "RB", "constructorId": "alphatauri"},
                23: {"name": "Williams", "constructorId": "williams"},
                27: {"name": "Haas F1 Team", "constructorId": "haas"},
                30: {"name": "RB", "constructorId": "alphatauri"},
                31: {"name": "Haas F1 Team", "constructorId": "haas"},
                43: {"name": "Williams", "constructorId": "williams"},
                44: {"name": "Ferrari", "constructorId": "ferrari"},
                55: {"name": "Williams", "constructorId": "williams"},
                63: {"name": "Mercedes", "constructorId": "mercedes"},
                81: {"name": "McLaren", "constructorId": "mclaren"},
                87: {"name": "Sauber", "constructorId": "sauber"}
            }
            
            ergast_results = []
            
            for result in openf1_results:
                driver_number = result.get('driver_number')
                if not driver_number or driver_number not in driver_name_map:
                    continue
                
                driver_info = driver_name_map[driver_number]
                team_info = team_map.get(driver_number, {"name": "Unknown", "constructorId": "unknown"})
                
                ergast_result = {
                    "position": str(result.get('position', 0)),
                    "Driver": {
                        "driverId": driver_info['code'].lower(),
                        "permanentNumber": driver_info['permanentNumber'],
                        "code": driver_info['code'],
                        "givenName": driver_info['givenName'],
                        "familyName": driver_info['familyName']
                    },
                    "Constructor": {
                        "constructorId": team_info['constructorId'],
                        "name": team_info['name']
                    },
                    "points": str(result.get('points', 0))
                }
                
                # 세션 타입에 따라 추가 정보
                if session_type.lower() == 'race':
                    ergast_result.update({
                        "grid": str(result.get('grid', 0)),
                        "laps": str(result.get('number_of_laps', 0)),
                        "status": "Finished" if not result.get('dnf') else "DNF"
                    })
                    
                    # 시간 정보 추가
                    if result.get('duration'):
                        duration = result.get('duration')
                        minutes = int(duration // 60)
                        seconds = duration % 60
                        ergast_result["Time"] = {"time": f"{minutes}:{seconds:.3f}"}
                        
                elif session_type.lower() == 'qualifying':
                    # 퀄리파잉 시간 (임시로 Q1 시간만 설정)
                    ergast_result["Q1"] = "1:20.000"  # 실제 데이터 있으면 사용
                
                ergast_results.append(ergast_result)
            
            return ergast_results
            
        except Exception as e:
            logger.error(f"Failed to convert OpenF1 results to Ergast format: {e}")
            return []

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
                    results_url = f"https://api.openf1.org/v1/session_result?session_key={session_key}&driver_number={driver_number}"
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
    
    async def get_seasons(self) -> List[int]:
        """시즌 목록 가져오기 (get_available_seasons의 별칭)"""
        return await self.get_available_seasons()
    
    async def get_calendar(self, year: Optional[int] = None) -> List[Dict[str, Any]]:
        """레이스 캘린더 가져오기 (get_race_calendar의 별칭)"""
        return await self.get_race_calendar(year)
    
    async def get_race_calendar(self, year: Optional[int] = None) -> List[Dict[str, Any]]:
        """레이스 캘린더 가져오기"""
        try:
            if year is None:
                year = datetime.now().year
            
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
            # 2025년 데이터의 경우 motorsportstats_2025_race_results.json만 사용
            if year == 2025:
                msstats_result = await self._get_openf1_race_weekend_details(round_number)
                return msstats_result
            # 이하 기존 로직(Ergast API)
            # ... (기존 코드 유지) ...
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
                    logger.info(f"Fetching race results from: {results_url}")
                    results_response = requests.get(results_url, timeout=10)
                    if results_response.status_code == 200:
                        results_json = results_response.json()
                        races_with_results = results_json['MRData']['RaceTable']['Races']
                        logger.info(f"Found {len(races_with_results)} races with results")
                        for race in races_with_results:
                            race_round = int(race['round'])
                            race_results = race.get('Results', [])
                            results_data[race_round] = race_results
                            logger.info(f"Race {race_round}: {len(race_results)} results")
                    else:
                        logger.warning(f"Failed to fetch results: {results_response.status_code}")
                except Exception as e:
                    logger.error(f"Error fetching race results: {e}")
                
                try:
                    logger.info(f"Fetching qualifying results from: {qualifying_url}")
                    qualifying_response = requests.get(qualifying_url, timeout=10)
                    if qualifying_response.status_code == 200:
                        qualifying_json = qualifying_response.json()
                        races_with_qualifying = qualifying_json['MRData']['RaceTable']['Races']
                        logger.info(f"Found {len(races_with_qualifying)} races with qualifying")
                        for race in races_with_qualifying:
                            race_round = int(race['round'])
                            qualifying_results = race.get('QualifyingResults', [])
                            qualifying_data[race_round] = qualifying_results
                            logger.info(f"Qualifying {race_round}: {len(qualifying_results)} results")
                    else:
                        logger.warning(f"Failed to fetch qualifying: {qualifying_response.status_code}")
                except Exception as e:
                    logger.error(f"Error fetching qualifying results: {e}")
                
                # 각 레이스 주말 정보 구성
                for race in races:
                    if round_number and int(race['round']) != round_number:
                        continue
                    
                    race_round = int(race['round'])
                    
                    # 세션 일정 정리
                    sessions = []
                    
                    # 세션 상태 결정을 위한 날짜 비교 함수
                    def get_session_status(session_date, session_type='race', race_round=None):
                        from datetime import datetime
                        today = datetime.now().date()
                        try:
                            session_date_obj = datetime.strptime(session_date, '%Y-%m-%d').date()
                            if session_date_obj < today:
                                # 과거 세션인 경우 실제 결과 데이터 여부 확인
                                if session_type.lower() == 'qualifying':
                                    return 'completed' if race_round in qualifying_data else 'completed'
                                elif session_type.lower() == 'race':
                                    return 'completed' if race_round in results_data else 'completed'
                                else:
                                    return 'completed'
                            else:
                                return 'scheduled'
                        except:
                            return 'scheduled'
                    
                    # 연습 세션들
                    if race.get('FirstPractice'):
                        sessions.append({
                            'session_type': 'Practice 1',
                            'date': race['FirstPractice']['date'],
                            'time': race['FirstPractice'].get('time'),
                            'status': get_session_status(race['FirstPractice']['date'], 'practice', race_round)
                        })
                    
                    if race.get('SecondPractice'):
                        sessions.append({
                            'session_type': 'Practice 2',
                            'date': race['SecondPractice']['date'],
                            'time': race['SecondPractice'].get('time'),
                            'status': get_session_status(race['SecondPractice']['date'], 'practice', race_round)
                        })
                    
                    if race.get('ThirdPractice'):
                        sessions.append({
                            'session_type': 'Practice 3',
                            'date': race['ThirdPractice']['date'],
                            'time': race['ThirdPractice'].get('time'),
                            'status': get_session_status(race['ThirdPractice']['date'], 'practice', race_round)
                        })
                    
                    # 스프린트 (있는 경우)
                    if race.get('Sprint'):
                        sessions.append({
                            'session_type': 'Sprint',
                            'date': race['Sprint']['date'],
                            'time': race['Sprint'].get('time'),
                            'status': get_session_status(race['Sprint']['date'], 'sprint', race_round)
                        })
                    
                    # 예선
                    if race.get('Qualifying'):
                        qualifying_results = qualifying_data.get(race_round, [])
                        sessions.append({
                            'session_type': 'Qualifying',
                            'date': race['Qualifying']['date'],
                            'time': race['Qualifying'].get('time'),
                            'status': get_session_status(race['Qualifying']['date'], 'qualifying', race_round),
                            'results': qualifying_results
                        })
                    
                    # 레이스
                    race_results = results_data.get(race_round, [])
                    sessions.append({
                        'session_type': 'Race',
                        'date': race['date'],
                        'time': race.get('time'),
                        'status': get_session_status(race['date'], 'race', race_round),
                        'results': race_results
                    })
                    
                    # 레이스 날짜 기반으로 상태 결정
                    from datetime import datetime
                    today = datetime.now().date()
                    race_date = datetime.strptime(race['date'], '%Y-%m-%d').date()
                    
                    # 레이스 날짜가 지났으면 completed, 아니면 upcoming
                    if race_date < today:
                        weekend_status = 'completed'
                    else:
                        weekend_status = 'upcoming'
                    
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
                        'weekend_status': weekend_status
                    }
                    
                    race_weekends.append(weekend_info)
            
            if round_number:
                return race_weekends[0] if race_weekends else {}
            return {'race_weekends': race_weekends, 'total_weekends': len(race_weekends), 'year': year}
        except Exception as e:
            logger.error(f"Failed to get race weekend details: {e}")
            return {'race_weekends': [], 'total_weekends': 0, 'year': year}
    
    async def get_race_weekends(self, year: Optional[int] = None) -> List[Dict[str, Any]]:
        """레이스 주말 일정 가져오기 (get_race_weekend_details의 별칭)"""
        try:
            result = await self.get_race_weekend_details(year)
            if isinstance(result, dict) and 'race_weekends' in result:
                return result['race_weekends']
            return []
        except Exception as e:
            logger.error(f"Failed to get race weekends: {e}")
            return []

    async def get_race_results(self, year: Optional[int] = None, round_number: Optional[int] = None) -> List[Dict[str, Any]]:
        """레이스 결과 가져오기 (페이지네이션 사용)"""
        try:
            if year is None:
                year = datetime.now().year
            
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
    
    async def get_latest_race_result(self) -> Optional[Dict[str, Any]]:
        """최근 레이스 결과 가져오기"""
        try:
            # 현재 시즌 결과 가져오기
            results = await self.get_race_results()
            if not results:
                return None
            
            # 결과가 있는 완료된 레이스 찾기
            completed_races = [race for race in results if race.get('results')]
            
            if not completed_races:
                return None
            
            # 가장 최근 완료된 레이스 반환
            latest_race = completed_races[-1]
            return latest_race
            
        except Exception as e:
            logger.error(f"Failed to get latest race result: {e}")
            return None
    
    async def get_driver_statistics(self, year: Optional[int] = None, driver_id: Optional[str] = None) -> Dict[str, Any]:
        """드라이버 통계 데이터 가져오기"""
        try:
            if year is None:
                year = datetime.now().year
            
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

    async def get_circuits(self, year: Optional[int] = None) -> List[Dict[str, Any]]:
        """서킷 목록 가져오기 (routers/live_timing.py 호환성을 위한 메서드)"""
        try:
            circuit_info = await self.get_circuit_information(year)
            if 'circuits' in circuit_info:
                return circuit_info['circuits']
            return []
        except Exception as e:
            logger.error(f"Failed to get circuits: {e}")
            return []

    async def get_circuit_information(self, year: Optional[int] = None, circuit_id: Optional[str] = None) -> Dict[str, Any]:
        """서킷 정보 가져오기"""
        try:
            if year is None:
                year = datetime.now().year
                
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
    
    async def get_sessions_with_radio(self, limit: int = 20) -> List[Dict[str, Any]]:
        """라디오가 있는 세션 목록 가져오기"""
        try:
            # 현재는 임시로 일반 세션 목록을 반환
            # 실제로는 OpenF1 API의 team_radio 엔드포인트에서 세션 정보를 가져와야 함
            sessions = await self.get_sessions()
            return sessions[:limit]
        except Exception as e:
            logger.error(f"Failed to get sessions with radio: {e}")
            return []

    async def get_sessions_with_weather(self, limit: int = 20) -> List[Dict[str, Any]]:
        """날씨 정보가 있는 세션 목록 가져오기"""
        try:
            # 현재는 임시로 일반 세션 목록을 반환
            # 실제로는 OpenF1 API의 weather 엔드포인트에서 세션 정보를 가져와야 함
            sessions = await self.get_sessions()
            return sessions[:limit]
        except Exception as e:
            logger.error(f"Failed to get sessions with weather: {e}")
            return []

    async def get_team_radio(self, session_key: int, limit: int = 50) -> List[Dict[str, Any]]:
        """팀 라디오 데이터 가져오기"""
        try:
            # OpenF1 API를 사용하여 팀 라디오 데이터 가져오기
            url = f"https://api.openf1.org/v1/team_radio?session_key={session_key}&limit={limit}"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                radio_data = response.json()
                return radio_data
            else:
                logger.warning(f"Failed to fetch team radio data: HTTP {response.status_code}")
                return []
        except Exception as e:
            logger.error(f"Failed to get team radio: {e}")
            return []

    async def get_team_radio_stats(self, session_key: int) -> Dict[str, Any]:
        """팀 라디오 통계 가져오기"""
        try:
            radio_data = await self.get_team_radio(session_key, limit=1000)
            
            if not radio_data:
                return {
                    "total_messages": 0,
                    "drivers_count": 0,
                    "driver_stats": {},
                    "session_key": session_key
                }
            
            # 통계 계산
            driver_stats = {}
            for message in radio_data:
                driver_number = message.get("driver_number")
                if driver_number:
                    if driver_number not in driver_stats:
                        driver_stats[driver_number] = {
                            "message_count": 0,
                            "total_duration": 0
                        }
                    driver_stats[driver_number]["message_count"] += 1
                    
                    # 메시지 길이를 duration으로 추정 (임시)
                    if "recording_url" in message:
                        driver_stats[driver_number]["total_duration"] += 5  # 평균 5초로 추정
            
            return {
                "total_messages": len(radio_data),
                "drivers_count": len(driver_stats),
                "driver_stats": driver_stats,
                "session_key": session_key
            }
        except Exception as e:
            logger.error(f"Failed to get team radio stats: {e}")
            return {
                "total_messages": 0,
                "drivers_count": 0,
                "driver_stats": {},
                "session_key": session_key
            }

    async def get_weather_by_session(self, session_key: int) -> List[Dict[str, Any]]:
        """세션별 날씨 데이터 가져오기"""
        try:
            # OpenF1 API를 사용하여 날씨 데이터 가져오기
            url = f"https://api.openf1.org/v1/weather?session_key={session_key}"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                weather_data = response.json()
                return weather_data
            else:
                logger.warning(f"Failed to fetch weather data: HTTP {response.status_code}")
                return []
        except Exception as e:
            logger.error(f"Failed to get weather by session: {e}")
            return []

    async def get_weather_analysis(self, session_key: int) -> Dict[str, Any]:
        """날씨 분석 데이터 가져오기"""
        try:
            weather_data = await self.get_weather_by_session(session_key)
            
            if not weather_data:
                return {
                    "average_temperature": None,
                    "temperature_range": {"min": None, "max": None},
                    "average_humidity": None,
                    "humidity_range": {"min": None, "max": None},
                    "pressure_range": {"min": None, "max": None},
                    "wind_speed_range": {"min": None, "max": None},
                    "rainfall": False,
                    "track_temperature_range": {"min": None, "max": None},
                    "session_key": session_key
                }
            
            # 날씨 분석 계산
            temperatures = [w.get("air_temperature") for w in weather_data if w.get("air_temperature") is not None]
            humidity = [w.get("humidity") for w in weather_data if w.get("humidity") is not None]
            pressure = [w.get("pressure") for w in weather_data if w.get("pressure") is not None]
            wind_speed = [w.get("wind_speed") for w in weather_data if w.get("wind_speed") is not None]
            track_temp = [w.get("track_temperature") for w in weather_data if w.get("track_temperature") is not None]
            rainfall = any(w.get("rainfall", False) for w in weather_data)
            
            return {
                "average_temperature": sum(temperatures) / len(temperatures) if temperatures else None,
                "temperature_range": {"min": min(temperatures), "max": max(temperatures)} if temperatures else {"min": None, "max": None},
                "average_humidity": sum(humidity) / len(humidity) if humidity else None,
                "humidity_range": {"min": min(humidity), "max": max(humidity)} if humidity else {"min": None, "max": None},
                "pressure_range": {"min": min(pressure), "max": max(pressure)} if pressure else {"min": None, "max": None},
                "wind_speed_range": {"min": min(wind_speed), "max": max(wind_speed)} if wind_speed else {"min": None, "max": None},
                "rainfall": rainfall,
                "track_temperature_range": {"min": min(track_temp), "max": max(track_temp)} if track_temp else {"min": None, "max": None},
                "session_key": session_key
            }
        except Exception as e:
            logger.error(f"Failed to get weather analysis: {e}")
            return {
                "average_temperature": None,
                "temperature_range": {"min": None, "max": None},
                "average_humidity": None,
                "humidity_range": {"min": None, "max": None},
                "pressure_range": {"min": None, "max": None},
                "wind_speed_range": {"min": None, "max": None},
                "rainfall": False,
                "track_temperature_range": {"min": None, "max": None},
                "session_key": session_key
            }

    async def get_tire_strategy(self, session_key: int) -> Dict[str, Any]:
        """타이어 전략 분석 가져오기"""
        try:
            # OpenF1 API를 사용하여 스틴트 데이터 가져오기
            url = f"https://api.openf1.org/v1/stints?session_key={session_key}"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                stints_data = response.json()
                
                # 타이어 컴파운드별 사용 통계 계산
                compound_stats = {}
                driver_strategies = {}
                
                for stint in stints_data:
                    compound = stint.get("compound")
                    driver_number = stint.get("driver_number")
                    lap_start = stint.get("lap_start", 0)
                    lap_end = stint.get("lap_end", 0)
                    stint_length = lap_end - lap_start + 1 if lap_end > lap_start else 0
                    
                    if compound:
                        if compound not in compound_stats:
                            compound_stats[compound] = {
                                "usage_count": 0,
                                "total_laps": 0,
                                "average_stint_length": 0
                            }
                        compound_stats[compound]["usage_count"] += 1
                        compound_stats[compound]["total_laps"] += stint_length
                        
                    if driver_number:
                        if driver_number not in driver_strategies:
                            driver_strategies[driver_number] = []
                        driver_strategies[driver_number].append({
                            "compound": compound,
                            "lap_start": lap_start,
                            "lap_end": lap_end,
                            "stint_length": stint_length
                        })
                
                # 평균 스틴트 길이 계산
                for compound, stats in compound_stats.items():
                    if stats["usage_count"] > 0:
                        stats["average_stint_length"] = stats["total_laps"] / stats["usage_count"]
                
                return {
                    "compound_statistics": compound_stats,
                    "driver_strategies": driver_strategies,
                    "total_stints": len(stints_data),
                    "session_key": session_key
                }
            else:
                logger.warning(f"Failed to fetch tire strategy data: HTTP {response.status_code}")
                return {
                    "compound_statistics": {},
                    "driver_strategies": {},
                    "total_stints": 0,
                    "session_key": session_key
                }
        except Exception as e:
            logger.error(f"Failed to get tire strategy: {e}")
            return {
                "compound_statistics": {},
                "driver_strategies": {},
                "total_stints": 0,
                "session_key": session_key
            }

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

    async def calculate_season_driver_stats(self, year: int = 2025) -> List[Dict[str, Any]]:
        """motorsportstats_2025_race_results.json을 기반으로 드라이버별 시즌 통계 계산"""
        try:
            import os
            base_dir = os.path.dirname(__file__)
            msstats_path = os.path.join(base_dir, "..", "motorsportstats_2025_race_results.json")
            
            if not os.path.exists(msstats_path):
                logger.warning("motorsportstats_2025_race_results.json not found")
                return []
            
            with open(msstats_path, 'r', encoding='utf-8') as f:
                msstats_data = json.load(f)
            
            # 드라이버별 통계 초기화
            driver_stats = {}
            
            # F1 포인트 시스템 (1위부터 10위까지)
            points_system = {1: 25, 2: 18, 3: 15, 4: 12, 5: 10, 6: 8, 7: 6, 8: 4, 9: 2, 10: 1}
            
            for gp_slug, results in msstats_data.items():
                for result in results:
                    driver_name = result.get('DRIVER', '')
                    team_name = result.get('TEAM', '')
                    position_str = result.get('POS', '0')
                    
                    # 포지션을 숫자로 변환
                    try:
                        position = int(position_str)
                    except (ValueError, TypeError):
                        continue  # 유효하지 않은 포지션은 건너뛰기
                    
                    if driver_name not in driver_stats:
                        driver_stats[driver_name] = {
                            'name': driver_name,
                            'team': team_name,
                            'season_points': 0,
                            'season_wins': 0,
                            'season_podiums': 0,
                            'races_entered': 0,
                            'best_finish': float('inf'),
                            'finish_positions': [],
                            'poles': 0,  # 폴포지션 데이터가 없으므로 0으로 설정
                            'fastest_laps': 0,  # 최고속도랩 데이터가 없으므로 0으로 설정
                            'dnf': 0,  # DNF는 결과에 없으면 0
                            'championship_position': None
                        }
                    
                    # 통계 업데이트
                    driver_stats[driver_name]['races_entered'] += 1
                    driver_stats[driver_name]['finish_positions'].append(position)
                    
                    # 최고 피니시 업데이트
                    if position < driver_stats[driver_name]['best_finish']:
                        driver_stats[driver_name]['best_finish'] = position
                    
                    # 포인트 계산
                    if position in points_system:
                        driver_stats[driver_name]['season_points'] += points_system[position]
                    
                    # 승수 계산
                    if position == 1:
                        driver_stats[driver_name]['season_wins'] += 1
                    
                    # 포디움 계산
                    if position <= 3:
                        driver_stats[driver_name]['season_podiums'] += 1
            
            # 평균 피니시 계산 및 챔피언십 포지션 결정
            driver_list = []
            for driver_name, stats in driver_stats.items():
                if stats['finish_positions']:
                    stats['average_finish'] = round(sum(stats['finish_positions']) / len(stats['finish_positions']), 1)
                else:
                    stats['average_finish'] = 0.0
                
                if stats['best_finish'] == float('inf'):
                    stats['best_finish'] = None
                
                # driver_number 추출 (가능한 경우)
                stats['driver_number'] = hash(driver_name) % 100  # 임시 드라이버 번호
                stats['slug'] = driver_name.lower().replace(' ', '-')
                stats['data_source'] = 'motorsportstats'
                
                driver_list.append(stats)
            
            # 포인트순으로 정렬하여 챔피언십 포지션 결정
            driver_list.sort(key=lambda x: (-x['season_points'], -x['season_wins'], -x['season_podiums']))
            
            for i, driver in enumerate(driver_list, 1):
                driver['championship_position'] = str(i)
            
            return driver_list
            
        except Exception as e:
            logger.error(f"Failed to calculate driver season stats: {e}")
            return []

    async def calculate_season_team_stats(self, year: int = 2025) -> List[Dict[str, Any]]:
        """motorsportstats_2025_race_results.json을 기반으로 팀별 시즌 통계 계산"""
        try:
            import os
            base_dir = os.path.dirname(__file__)
            msstats_path = os.path.join(base_dir, "..", "motorsportstats_2025_race_results.json")
            
            if not os.path.exists(msstats_path):
                logger.warning("motorsportstats_2025_race_results.json not found")
                return []
            
            with open(msstats_path, 'r', encoding='utf-8') as f:
                msstats_data = json.load(f)
            
            # 팀별 통계 초기화
            team_stats = {}
            
            # F1 포인트 시스템
            points_system = {1: 25, 2: 18, 3: 15, 4: 12, 5: 10, 6: 8, 7: 6, 8: 4, 9: 2, 10: 1}
            
            for gp_slug, results in msstats_data.items():
                for result in results:
                    driver_name = result.get('DRIVER', '')
                    team_name = result.get('TEAM', '')
                    position_str = result.get('POS', '0')
                    
                    # 포지션을 숫자로 변환
                    try:
                        position = int(position_str)
                    except (ValueError, TypeError):
                        continue
                    
                    if team_name not in team_stats:
                        team_stats[team_name] = {
                            'name': team_name,
                            'full_name': team_name,
                            'season_points': 0,
                            'season_wins': 0,
                            'season_podiums': 0,
                            'season_races': 0,
                            'season_poles': 0,
                            'season_fastest_laps': 0,
                            'season_dnf': 0,
                            'drivers_count': set(),  # 드라이버 이름들을 저장할 set
                            'championship_position': None
                        }
                    
                    # 드라이버 추가
                    team_stats[team_name]['drivers_count'].add(driver_name)
                    team_stats[team_name]['season_races'] += 1
                    
                    # 포인트 계산
                    if position in points_system:
                        team_stats[team_name]['season_points'] += points_system[position]
                    
                    # 승수 계산
                    if position == 1:
                        team_stats[team_name]['season_wins'] += 1
                    
                    # 포디움 계산
                    if position <= 3:
                        team_stats[team_name]['season_podiums'] += 1
            
            # 팀 리스트 생성 및 정렬
            team_list = []
            for team_name, stats in team_stats.items():
                # drivers_count를 문자열로 변환
                stats['drivers_count'] = f"{len(stats['drivers_count'])} drivers"
                stats['team_slug'] = team_name.lower().replace(' ', '-').replace('formula', 'f1')
                stats['data_source'] = 'motorsportstats'
                
                team_list.append(stats)
            
            # 포인트순으로 정렬하여 챔피언십 포지션 결정
            team_list.sort(key=lambda x: (-x['season_points'], -x['season_wins'], -x['season_podiums']))
            
            for i, team in enumerate(team_list, 1):
                team['championship_position'] = str(i)
            
            return team_list
            
        except Exception as e:
            logger.error(f"Failed to calculate team season stats: {e}")
            return []

    async def get_season_driver_stats_2025(self) -> Dict[str, Any]:
        """2025년 드라이버 시즌 통계 반환"""
        try:
            driver_stats = await self.calculate_season_driver_stats(2025)
            return {
                'data': driver_stats,
                'total_drivers': len(driver_stats),
                'year': 2025,
                'data_source': 'motorsportstats'
            }
        except Exception as e:
            logger.error(f"Failed to get 2025 driver stats: {e}")
            return {'data': [], 'total_drivers': 0, 'year': 2025, 'data_source': 'motorsportstats'}

    async def get_season_team_stats_2025(self) -> Dict[str, Any]:
        """2025년 팀 시즌 통계 반환"""
        try:
            team_stats = await self.calculate_season_team_stats(2025)
            return {
                'data': team_stats,
                'total_teams': len(team_stats),
                'year': 2025,
                'data_source': 'motorsportstats'
            }
        except Exception as e:
            logger.error(f"Failed to get 2025 team stats: {e}")
            return {'data': [], 'total_teams': 0, 'year': 2025, 'data_source': 'motorsportstats'}