#!/usr/bin/env python3
"""
JSON 파일에서 선수별 커리어 통계 데이터를 보여주는 스크립트
"""

import json
import os
from datetime import datetime
from pathlib import Path

def load_career_stats():
    """JSON 파일에서 커리어 통계 로드"""
    json_file = Path(__file__).parent / "driver_career_stats.json"
    
    if not json_file.exists():
        print("❌ driver_career_stats.json 파일을 찾을 수 없습니다.")
        return None
    
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"❌ JSON 파일 로드 실패: {e}")
        return None

def format_career_stats_for_api(driver_data):
    """API 형식으로 커리어 통계 포맷팅"""
    stats = driver_data.get('stats', {})
    
    return {
        "race_wins": stats.get('wins', 0),
        "podiums": stats.get('podiums', 0),
        "pole_positions": stats.get('poles', 0),
        "fastest_laps": stats.get('fastest_laps', 0),
        "career_points": stats.get('points', 0),
        "world_championships": stats.get('championships', 0),
        "first_entry": stats.get('years', None),  # 년수는 있지만 첫 진입 년도는 별도 계산 필요
        "total_starts": stats.get('starts', 0),
        "entries": stats.get('entries', 0),
        "best_finish": stats.get('best_finish', None),
        "best_championship_position": stats.get('best_championship_position', None),
        "sprint_wins": stats.get('sprint_wins', 0),
        "years_active": stats.get('years', 0)
    }

def display_all_drivers():
    """모든 드라이버의 커리어 통계 출력"""
    data = load_career_stats()
    if not data:
        return
    
    print("🏎️  F1 드라이버 커리어 통계")
    print("=" * 80)
    print(f"📅 데이터 수집: {data.get('scraped_at', 'Unknown')}")
    print(f"👥 총 드라이버: {data.get('total_drivers', 0)}명")
    print(f"✅ 성공: {data.get('successful_scrapes', 0)}명")
    print(f"❌ 실패: {data.get('failed_scrapes', 0)}명")
    print()
    
    # 드라이버별 상세 정보
    drivers = data.get('drivers', {})
    
    # 성공한 드라이버들을 승수 순으로 정렬
    successful_drivers = [(slug, info) for slug, info in drivers.items() if info.get('success')]
    successful_drivers.sort(key=lambda x: x[1]['stats'].get('wins', 0), reverse=True)
    
    for slug, driver_info in successful_drivers:
        print(f"🏁 {driver_info['name']} (#{driver_info['number']})")
        print(f"   📊 API 형식 데이터:")
        
        api_data = format_career_stats_for_api(driver_info)
        for key, value in api_data.items():
            print(f"      {key}: {value}")
        
        print(f"   🔗 URL: {driver_info['url']}")
        print(f"   🕒 수집시간: {driver_info['scraped_at']}")
        print()

def get_driver_by_number(driver_number):
    """드라이버 번호로 특정 드라이버 정보 조회"""
    data = load_career_stats()
    if not data:
        return None
    
    drivers = data.get('drivers', {})
    
    for slug, driver_info in drivers.items():
        if driver_info['number'] == driver_number:
            return {
                'slug': slug,
                'info': driver_info,
                'api_data': format_career_stats_for_api(driver_info)
            }
    
    return None

def get_driver_by_slug(driver_slug):
    """드라이버 slug로 특정 드라이버 정보 조회"""
    data = load_career_stats()
    if not data:
        return None
    
    drivers = data.get('drivers', {})
    
    if driver_slug in drivers:
        driver_info = drivers[driver_slug]
        return {
            'slug': driver_slug,
            'info': driver_info,
            'api_data': format_career_stats_for_api(driver_info)
        }
    
    return None

def create_driver_mapping():
    """드라이버 번호 → slug 매핑 생성"""
    data = load_career_stats()
    if not data:
        return {}
    
    mapping = {}
    drivers = data.get('drivers', {})
    
    for slug, driver_info in drivers.items():
        if driver_info.get('success'):
            mapping[driver_info['number']] = slug
    
    return mapping

def show_top_performers():
    """각 부문별 톱 퍼포머 표시"""
    data = load_career_stats()
    if not data:
        return
    
    drivers = data.get('drivers', {})
    successful_drivers = [(slug, info) for slug, info in drivers.items() if info.get('success')]
    
    categories = {
        'wins': '🏆 최다 승리',
        'podiums': '🥇 최다 포디움',
        'poles': '🏁 최다 폴 포지션',
        'fastest_laps': '⚡ 최다 최고 랩타임',
        'points': '💎 최다 포인트',
        'championships': '👑 최다 챔피언십',
        'starts': '🎯 최다 출전'
    }
    
    print("🏆 부문별 톱 퍼포머")
    print("=" * 50)
    
    for stat_key, title in categories.items():
        top_drivers = sorted(successful_drivers, 
                           key=lambda x: x[1]['stats'].get(stat_key, 0), 
                           reverse=True)[:3]
        
        print(f"\n{title}:")
        for i, (slug, driver_info) in enumerate(top_drivers, 1):
            value = driver_info['stats'].get(stat_key, 0)
            print(f"  {i}. {driver_info['name']}: {value}")

def main():
    """메인 함수"""
    import sys
    
    if len(sys.argv) > 1:
        arg = sys.argv[1]
        
        if arg == "top":
            show_top_performers()
        elif arg == "mapping":
            mapping = create_driver_mapping()
            print("드라이버 번호 → slug 매핑:")
            for number, slug in sorted(mapping.items()):
                print(f"  {number}: {slug}")
        elif arg.isdigit():
            # 드라이버 번호로 조회
            driver = get_driver_by_number(int(arg))
            if driver:
                print(f"🏁 {driver['info']['name']} (#{driver['info']['number']})")
                print("📊 API 형식 데이터:")
                for key, value in driver['api_data'].items():
                    print(f"  {key}: {value}")
            else:
                print(f"❌ 드라이버 번호 {arg}를 찾을 수 없습니다.")
        else:
            # 드라이버 slug로 조회
            driver = get_driver_by_slug(arg)
            if driver:
                print(f"🏁 {driver['info']['name']} (#{driver['info']['number']})")
                print("📊 API 형식 데이터:")
                for key, value in driver['api_data'].items():
                    print(f"  {key}: {value}")
            else:
                print(f"❌ 드라이버 '{arg}'를 찾을 수 없습니다.")
    else:
        display_all_drivers()

if __name__ == "__main__":
    main()