"""
LiveF1으로 순위 데이터 테스트
"""
import asyncio
import sys
import os
sys.path.insert(0, os.path.abspath('.'))

import livef1
from livef1 import get_season
import pandas as pd

async def test_standings_data():
    print("=== LiveF1 순위 데이터 탐색 ===\n")
    
    try:
        # 2024 시즌 로드
        season = get_season(2024)
        print(f"2024 시즌 로드 완료")
        print(f"시즌 타입: {type(season)}")
        
        # 시즌 객체의 속성들 확인
        print(f"\n시즌 객체 속성들:")
        for attr in dir(season):
            if not attr.startswith('_'):
                print(f"  - {attr}")
        
        # 미팅들 확인
        if hasattr(season, 'meetings') and season.meetings:
            print(f"\n미팅 수: {len(season.meetings)}")
            
            # 최근 완료된 레이스 찾기
            completed_meetings = []
            for meeting in season.meetings:
                if hasattr(meeting, 'sessions'):
                    for session in meeting.sessions:
                        if hasattr(session, 'session_type') and 'Race' in str(getattr(session, 'session_type', '')):
                            completed_meetings.append((meeting, session))
            
            print(f"레이스 세션 수: {len(completed_meetings)}")
            
            if completed_meetings:
                # 최근 레이스 세션
                recent_meeting, recent_race = completed_meetings[-1]
                print(f"\n최근 레이스: {getattr(recent_meeting, 'circuit_short_name', 'Unknown')}")
                print(f"레이스 세션: {getattr(recent_race, 'session_name', 'Unknown')}")
                
                # 세션 객체의 속성들 확인
                print(f"\n레이스 세션 속성들:")
                for attr in dir(recent_race):
                    if not attr.startswith('_'):
                        try:
                            value = getattr(recent_race, attr)
                            if not callable(value):
                                print(f"  - {attr}: {type(value)}")
                        except:
                            print(f"  - {attr}: (접근 불가)")
                
                # 가능한 순위 관련 속성들 확인
                potential_standings_attrs = ['results', 'standings', 'classification', 'positions', 'drivers', 'lap_times']
                for attr in potential_standings_attrs:
                    if hasattr(recent_race, attr):
                        try:
                            data = getattr(recent_race, attr)
                            print(f"\n{attr} 데이터:")
                            print(f"  - 타입: {type(data)}")
                            if hasattr(data, 'shape'):
                                print(f"  - 크기: {data.shape}")
                            if hasattr(data, 'columns'):
                                print(f"  - 컬럼: {list(data.columns)}")
                            if hasattr(data, 'head'):
                                print(f"  - 샘플 데이터:")
                                print(data.head(3))
                        except Exception as e:
                            print(f"  - {attr} 접근 오류: {e}")
        
        # 시즌 레벨에서 순위 데이터 확인
        season_attrs = ['standings', 'driver_standings', 'constructor_standings', 'championship']
        print(f"\n시즌 레벨 순위 데이터 확인:")
        for attr in season_attrs:
            if hasattr(season, attr):
                try:
                    data = getattr(season, attr)
                    print(f"  - {attr}: {type(data)}")
                    if hasattr(data, 'shape'):
                        print(f"    크기: {data.shape}")
                except Exception as e:
                    print(f"  - {attr} 오류: {e}")
                    
    except Exception as e:
        print(f"오류 발생: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_standings_data())