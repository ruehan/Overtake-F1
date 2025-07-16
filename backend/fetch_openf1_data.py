#!/usr/bin/env python3
"""
OpenF1 API에서 2025년 레이스 결과 데이터를 가져와서 JSON 파일로 저장하는 스크립트
"""

import requests
import json
import time
import logging
from datetime import datetime
from typing import Dict, List, Any

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def fetch_2025_sessions() -> List[Dict[str, Any]]:
    """2025년 모든 세션 정보 한 번에 가져오기"""
    try:
        logger.info("Fetching 2025 sessions from OpenF1 API (all types)...")
        url = "https://api.openf1.org/v1/sessions?year=2025"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            sessions = response.json()
            logger.info(f"Found {len(sessions)} sessions")
            return sessions
        else:
            logger.error(f"Failed to fetch sessions: {response.status_code}")
            return []
    except Exception as e:
        logger.error(f"Failed to fetch 2025 sessions: {e}")
        return []

def fetch_session_results(session_key: int, session_type: str) -> List[Dict[str, Any]]:
    """특정 세션의 결과 가져오기 (OpenF1 API 원본 응답 그대로 저장)"""
    try:
        logger.info(f"Fetching results for session {session_key} ({session_type})...")
        
        results_url = f"https://api.openf1.org/v1/session_result?session_key={session_key}"
        response = requests.get(results_url, timeout=10)
        
        if response.status_code == 200:
            results = response.json()
            
            if results:
                logger.info(f"Found {len(results)} raw results for session {session_key}")
                # OpenF1 API 응답을 그대로 반환
                return results
        
        return []
        
    except Exception as e:
        logger.error(f"Failed to fetch results for session {session_key}: {e}")
        return []

def main():
    """메인 함수"""
    logger.info("Starting OpenF1 data fetch...")
    
    # 세션 정보 가져오기
    sessions = fetch_2025_sessions()
    
    if not sessions:
        logger.error("No sessions found")
        return
    
    # 결과 저장할 데이터 구조
    openf1_data = {
        "year": 2025,
        "fetched_at": datetime.now().isoformat(),
        "sessions": {}
    }
    
    # 각 세션별로 결과 가져오기
    for session in sessions:
        session_key = session.get('session_key')
        session_type = session.get('session_type')
        location = session.get('location')
        date_start = session.get('date_start')
        
        if not session_key:
            continue
        
        logger.info(f"Processing session {session_key}: {session_type} at {location}")
        
        # 결과 가져오기
        results = fetch_session_results(session_key, session_type)
        
        # 세션 정보 저장
        openf1_data["sessions"][str(session_key)] = {
            "session_key": session_key,
            "meeting_key": session.get('meeting_key'),
            "session_type": session_type,
            "location": location,
            "date_start": date_start,
            "country_name": session.get('country_name'),
            "circuit_short_name": session.get('circuit_short_name'),
            "results": results
        }
        
        # API 호출 제한을 위해 잠시 대기
        time.sleep(0.5)
    
    # JSON 파일로 저장
    output_file = "openf1_2025_results.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(openf1_data, f, indent=2, ensure_ascii=False)
    
    logger.info(f"OpenF1 data saved to {output_file}")
    logger.info(f"Total sessions processed: {len(openf1_data['sessions'])}")

if __name__ == "__main__":
    main()