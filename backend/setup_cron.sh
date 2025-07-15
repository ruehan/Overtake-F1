#!/bin/bash
# Cron job 설정 스크립트

echo "Setting up weekly driver statistics scraping cron job..."

# 현재 디렉토리 확인
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WEEKLY_SCRAPER="${SCRIPT_DIR}/weekly_scraper.py"

echo "Script directory: ${SCRIPT_DIR}"
echo "Weekly scraper: ${WEEKLY_SCRAPER}"

# weekly_scraper.py 실행 권한 부여
chmod +x "${WEEKLY_SCRAPER}"

# 기존 cron job 백업
echo "Backing up existing crontab..."
crontab -l > "${SCRIPT_DIR}/crontab_backup_$(date +%Y%m%d_%H%M%S).txt" 2>/dev/null || echo "No existing crontab found"

# 새로운 cron job 추가
echo "Adding weekly scraping cron job..."

# 임시 cron 파일 생성
TEMP_CRON=$(mktemp)

# 기존 cron job 복사 (있다면)
crontab -l > "${TEMP_CRON}" 2>/dev/null || true

# 새로운 cron job 추가
# 매주 월요일 오전 9시에 실행
echo "0 9 * * 1 cd ${SCRIPT_DIR} && ${WEEKLY_SCRAPER} >> ${SCRIPT_DIR}/cron.log 2>&1" >> "${TEMP_CRON}"

# cron job 설치
crontab "${TEMP_CRON}"

# 임시 파일 삭제
rm "${TEMP_CRON}"

echo "✅ Cron job installed successfully!"
echo ""
echo "📋 Current crontab:"
crontab -l
echo ""
echo "📝 Cron job details:"
echo "  - Runs every Monday at 9:00 AM"
echo "  - Script: ${WEEKLY_SCRAPER}"
echo "  - Log file: ${SCRIPT_DIR}/cron.log"
echo "  - Scraper log: ${SCRIPT_DIR}/weekly_scraper.log"
echo ""
echo "🔧 To remove the cron job later:"
echo "  crontab -e"
echo "  # Delete the line containing 'weekly_scraper.py'"
echo ""
echo "📊 To test the scraper manually:"
echo "  cd ${SCRIPT_DIR}"
echo "  python3 weekly_scraper.py"