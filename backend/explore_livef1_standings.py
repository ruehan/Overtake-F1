"""
LiveF1에서 실제 순위 데이터 탐색
"""
import asyncio
import sys
import os
sys.path.insert(0, os.path.abspath('.'))

import livef1
from livef1 import get_season
from livef1.api import livetimingF1_request
import pandas as pd

async def explore_livef1_standings():
    print("=== LiveF1 순위 데이터 탐색 ===\n")
    
    try:
        # 1. LiveTiming API에서 순위 관련 엔드포인트 확인
        print("1. LiveTiming API 엔드포인트 테스트:")
        
        potential_endpoints = [
            "DriverStandings",
            "ConstructorStandings", 
            "Championship",
            "Standings",
            "SeasonStandings",
            "DriverList",
            "SessionInfo",
            "TrackStatus",
            "TimingData",
            "Position"
        ]
        
        for endpoint in potential_endpoints:
            try:
                print(f"  테스트: {endpoint}")
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(
                    None, 
                    lambda ep=endpoint: livetimingF1_request(ep)
                )
                if result:
                    print(f"    ✅ {endpoint}: 데이터 있음 ({type(result)})")
                    if isinstance(result, dict) and len(result) < 10:
                        print(f"       샘플: {list(result.keys())[:5]}")
                else:
                    print(f"    ❌ {endpoint}: 데이터 없음")
            except Exception as e:
                print(f"    ❌ {endpoint}: 오류 - {str(e)[:50]}")
        
        # 2. 시즌 객체에서 순위 관련 메서드 확인
        print(f"\n2. 시즌 객체 탐색:")
        season = get_season(2025)
        
        # 시즌 객체의 모든 속성과 메서드 확인
        season_methods = []
        for attr in dir(season):
            if not attr.startswith('_'):
                try:
                    value = getattr(season, attr)
                    if callable(value):
                        season_methods.append(f"  메서드: {attr}()")
                    else:
                        season_methods.append(f"  속성: {attr} ({type(value).__name__})")
                except:
                    season_methods.append(f"  {attr} (접근 불가)")
        
        print("\n시즌 객체 속성/메서드:")
        for method in season_methods[:15]:  # 처음 15개만 출력
            print(method)
        
        # 3. 미팅과 세션에서 결과 데이터 확인
        print(f"\n3. 미팅/세션 결과 데이터:")
        if hasattr(season, 'meetings') and season.meetings:
            print(f"미팅 수: {len(season.meetings)}")
            
            # 최근 미팅 확인
            for meeting in season.meetings[-3:]:  # 최근 3개 미팅
                meeting_name = getattr(meeting, 'circuit_short_name', 'Unknown')
                print(f"\n미팅: {meeting_name}")
                
                if hasattr(meeting, 'sessions'):
                    for session in meeting.sessions:
                        session_type = getattr(session, 'session_type', 'Unknown')
                        print(f"  세션: {session_type}")
                        
                        # 세션에서 순위 관련 속성 확인
                        result_attrs = ['results', 'final_results', 'classification', 'positions']
                        for attr in result_attrs:
                            if hasattr(session, attr):
                                try:
                                    data = getattr(session, attr)
                                    print(f"    ✅ {attr}: {type(data)}")
                                    if hasattr(data, 'shape'):
                                        print(f"       크기: {data.shape}")
                                    if hasattr(data, 'columns'):
                                        print(f"       컬럼: {list(data.columns)[:5]}")
                                except Exception as e:
                                    print(f"    ❌ {attr}: {e}")
        
        # 4. LiveF1의 다른 API 함수들 확인
        print(f"\n4. LiveF1 모듈 함수들:")
        livef1_functions = []
        for attr in dir(livef1):
            if not attr.startswith('_') and callable(getattr(livef1, attr)):
                livef1_functions.append(attr)
        
        print("LiveF1 함수들:")
        for func in livef1_functions:
            print(f"  - {func}")
            
    except Exception as e:
        print(f"오류 발생: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(explore_livef1_standings())