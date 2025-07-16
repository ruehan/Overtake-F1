#!/usr/bin/env python3
"""
OpenF1 데이터 자동 업데이트 스케줄러
매주 월요일에 실행되어 2025년 F1 시즌 데이터를 업데이트합니다.
"""

import schedule
import time
import subprocess
import logging
import os
from datetime import datetime

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scheduler.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def update_openf1_data():
    """OpenF1 데이터 업데이트 작업"""
    try:
        logger.info("Starting OpenF1 data update job...")
        
        # 현재 스크립트 디렉토리로 이동
        script_dir = os.path.dirname(os.path.abspath(__file__))
        
        # fetch_openf1_data.py 실행
        result = subprocess.run(
            ['/usr/bin/python3', 'fetch_openf1_data.py'],
            cwd=script_dir,
            capture_output=True,
            text=True,
            timeout=300  # 5분 타임아웃
        )
        
        if result.returncode == 0:
            logger.info("OpenF1 data update completed successfully")
            logger.info(f"Output: {result.stdout}")
        else:
            logger.error(f"OpenF1 data update failed with return code {result.returncode}")
            logger.error(f"Error: {result.stderr}")
            
    except subprocess.TimeoutExpired:
        logger.error("OpenF1 data update timed out after 5 minutes")
    except Exception as e:
        logger.error(f"Error during OpenF1 data update: {e}")

def backup_existing_data():
    """기존 데이터 백업"""
    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        json_file = os.path.join(script_dir, 'openf1_2025_results.json')
        
        if os.path.exists(json_file):
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_file = os.path.join(script_dir, f'openf1_2025_results_backup_{timestamp}.json')
            
            os.rename(json_file, backup_file)
            logger.info(f"Existing data backed up to {backup_file}")
            
    except Exception as e:
        logger.error(f"Error during data backup: {e}")

def scheduled_update():
    """스케줄된 업데이트 작업 (백업 + 업데이트)"""
    logger.info("=== Weekly OpenF1 Data Update Started ===")
    
    # 기존 데이터 백업
    backup_existing_data()
    
    # 새 데이터 업데이트
    update_openf1_data()
    
    logger.info("=== Weekly OpenF1 Data Update Completed ===")

def run_scheduler():
    """스케줄러 실행"""
    logger.info("OpenF1 Data Scheduler started")
    logger.info("Scheduled to run every Monday at 09:00")
    
    # 매주 월요일 오전 9시에 실행
    schedule.every().monday.at("09:00").do(scheduled_update)
    
    # 테스트용: 즉시 실행 (개발/테스트 시에만 사용)
    # scheduled_update()
    
    while True:
        try:
            schedule.run_pending()
            time.sleep(60)  # 1분마다 체크
        except KeyboardInterrupt:
            logger.info("Scheduler stopped by user")
            break
        except Exception as e:
            logger.error(f"Scheduler error: {e}")
            time.sleep(60)

if __name__ == "__main__":
    run_scheduler()