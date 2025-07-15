#!/usr/bin/env python3
"""
주간 F1 통계 스크래핑 스케줄러
매주 월요일 실행되어 드라이버 및 팀 통계를 업데이트
"""

import os
import sys
import subprocess
import logging
from datetime import datetime, timedelta
from pathlib import Path

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/Users/hangyu/Desktop/Overtake/backend/weekly_scraper.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def run_weekly_scraper():
    """주간 스크래핑 실행"""
    try:
        # 현재 스크립트의 디렉토리로 이동
        script_dir = Path(__file__).parent
        os.chdir(script_dir)
        
        logger.info("=== Weekly F1 Statistics Scraping Started ===")
        logger.info(f"Working directory: {os.getcwd()}")
        logger.info(f"Execution time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # 가상환경 Python 경로
        venv_python = script_dir / "venv" / "bin" / "python3"
        
        # 스크래핑 스크립트들
        driver_scraper = script_dir / "bulk_driver_scraper.py"
        team_scraper = script_dir / "team_season_scraper.py"
        
        # 가상환경 Python 경로 확인
        if not venv_python.exists():
            logger.error(f"Virtual environment Python not found at: {venv_python}")
            return False
        
        # 드라이버 스크래핑 실행
        logger.info("1. Starting driver statistics scraping...")
        if not driver_scraper.exists():
            logger.error(f"Driver scraper script not found at: {driver_scraper}")
            return False
        
        driver_result = subprocess.run(
            [str(venv_python), str(driver_scraper)],
            capture_output=True,
            text=True,
            timeout=3600  # 1시간 타임아웃
        )
        
        # 팀 스크래핑 실행
        logger.info("2. Starting team statistics scraping...")
        if not team_scraper.exists():
            logger.error(f"Team scraper script not found at: {team_scraper}")
            return False
        
        team_result = subprocess.run(
            [str(venv_python), str(team_scraper)],
            capture_output=True,
            text=True,
            timeout=1800  # 30분 타임아웃
        )
        
        # 결과 확인
        driver_success = driver_result.returncode == 0
        team_success = team_result.returncode == 0
        
        if driver_success:
            logger.info("✅ Driver scraping completed successfully!")
            logger.info(f"Driver output: {driver_result.stdout}")
        else:
            logger.error(f"❌ Driver scraping failed with return code: {driver_result.returncode}")
            logger.error(f"Driver error: {driver_result.stderr}")
        
        if team_success:
            logger.info("✅ Team scraping completed successfully!")
            logger.info(f"Team output: {team_result.stdout}")
        else:
            logger.error(f"❌ Team scraping failed with return code: {team_result.returncode}")
            logger.error(f"Team error: {team_result.stderr}")
        
        if driver_success and team_success:
            # JSON 파일들 생성 확인 및 백업
            files_to_check = [
                ("driver_career_stats.json", "driver_career_stats_backup"),
                ("team_2025_season_stats.json", "team_2025_season_backup")
            ]
            
            success_count = 0
            import shutil
            
            for json_file, backup_prefix in files_to_check:
                json_path = script_dir / json_file
                
                if json_path.exists():
                    file_size = json_path.stat().st_size
                    logger.info(f"📄 {json_file} updated (size: {file_size} bytes)")
                    
                    # 파일 백업 생성
                    backup_name = f"{backup_prefix}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                    backup_path = script_dir / "backups" / backup_name
                    
                    # 백업 디렉토리 생성
                    backup_path.parent.mkdir(exist_ok=True)
                    
                    # 백업 파일 복사
                    shutil.copy2(json_path, backup_path)
                    logger.info(f"📁 Backup created: {backup_path}")
                    
                    success_count += 1
                else:
                    logger.error(f"❌ {json_file} was not created")
            
            # 오래된 백업 파일 정리 (30일 이상)
            cleanup_old_backups(script_dir / "backups", days=30)
            
            return success_count == 2  # 두 파일 모두 성공해야 True
        else:
            logger.error("❌ One or both scraping tasks failed")
            return False
            
    except subprocess.TimeoutExpired:
        logger.error("❌ Scraping timed out after 1 hour")
        return False
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
        return False

def cleanup_old_backups(backup_dir, days=30):
    """오래된 백업 파일 정리"""
    try:
        cutoff_date = datetime.now() - timedelta(days=days)
        
        # 드라이버 백업 파일 정리
        for backup_file in backup_dir.glob("driver_career_stats_backup_*.json"):
            file_mtime = datetime.fromtimestamp(backup_file.stat().st_mtime)
            if file_mtime < cutoff_date:
                backup_file.unlink()
                logger.info(f"🗑️ Deleted old driver backup: {backup_file}")
        
        # 팀 백업 파일 정리
        for backup_file in backup_dir.glob("team_2025_season_backup_*.json"):
            file_mtime = datetime.fromtimestamp(backup_file.stat().st_mtime)
            if file_mtime < cutoff_date:
                backup_file.unlink()
                logger.info(f"🗑️ Deleted old team backup: {backup_file}")
                
    except Exception as e:
        logger.warning(f"Failed to cleanup old backups: {e}")

def send_notification(success, message=""):
    """알림 전송 (선택사항)"""
    try:
        # 슬랙, 이메일, 또는 기타 알림 서비스 통합 가능
        status = "✅ SUCCESS" if success else "❌ FAILED"
        notification_message = f"[OVERTAKE] Weekly F1 Statistics Scraping {status}\n{message}"
        
        # 예시: 로그 파일에 알림 기록
        logger.info(f"📢 Notification: {notification_message}")
        
        # TODO: 실제 알림 서비스 연동 (Slack, Email 등)
        
    except Exception as e:
        logger.warning(f"Failed to send notification: {e}")

def main():
    """메인 함수"""
    try:
        # 월요일인지 확인 (0=월요일, 6=일요일)
        today = datetime.now()
        if today.weekday() == 0:  # 월요일
            logger.info("🗓️ Today is Monday - Running weekly scraping")
            success = run_weekly_scraper()
            
            if success:
                message = f"Driver and team statistics updated successfully on {today.strftime('%Y-%m-%d')}"
                send_notification(True, message)
                logger.info("=== Weekly F1 statistics scraping completed successfully ===")
            else:
                message = f"F1 statistics scraping failed on {today.strftime('%Y-%m-%d')}"
                send_notification(False, message)
                logger.error("=== Weekly F1 statistics scraping failed ===")
                sys.exit(1)
        else:
            logger.info(f"🗓️ Today is {today.strftime('%A')} - Weekly scraping runs on Monday only")
            
    except Exception as e:
        logger.error(f"❌ Main execution failed: {e}")
        send_notification(False, f"Main execution failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()