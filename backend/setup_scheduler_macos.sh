#!/bin/bash
# macOS launchd를 사용한 자동 스크래핑 스케줄러 설정

echo "🍎 Setting up F1 Statistics Scraping Scheduler for macOS..."
echo ""

# 현재 디렉토리 확인
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLIST_FILE="${SCRIPT_DIR}/com.overtake.f1scheduler.plist"
WEEKLY_SCRAPER="${SCRIPT_DIR}/weekly_scraper.py"
TARGET_PLIST="$HOME/Library/LaunchAgents/com.overtake.f1scheduler.plist"

echo "📁 Script directory: ${SCRIPT_DIR}"
echo "📄 Plist file: ${PLIST_FILE}"
echo "🐍 Weekly scraper: ${WEEKLY_SCRAPER}"
echo "🎯 Target location: ${TARGET_PLIST}"
echo ""

# 파일 존재 확인
if [ ! -f "${PLIST_FILE}" ]; then
    echo "❌ Error: Plist file not found at ${PLIST_FILE}"
    exit 1
fi

if [ ! -f "${WEEKLY_SCRAPER}" ]; then
    echo "❌ Error: Weekly scraper not found at ${WEEKLY_SCRAPER}"
    exit 1
fi

# 가상환경 Python 확인
VENV_PYTHON="${SCRIPT_DIR}/venv/bin/python3"
if [ ! -f "${VENV_PYTHON}" ]; then
    echo "⚠️  Warning: Virtual environment Python not found at ${VENV_PYTHON}"
    echo "🔧 Make sure to create a virtual environment first:"
    echo "   cd ${SCRIPT_DIR}"
    echo "   python3 -m venv venv"
    echo "   source venv/bin/activate"
    echo "   pip install -r requirements.txt"
    echo ""
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# weekly_scraper.py 실행 권한 부여
chmod +x "${WEEKLY_SCRAPER}"

# LaunchAgents 디렉토리 생성 (없다면)
mkdir -p "$HOME/Library/LaunchAgents"

# 기존 서비스 언로드 (에러 무시)
echo "🔄 Stopping existing service (if any)..."
launchctl unload "${TARGET_PLIST}" 2>/dev/null || true

# plist 파일 복사
echo "📋 Installing scheduler configuration..."
cp "${PLIST_FILE}" "${TARGET_PLIST}"

# 서비스 로드
echo "🚀 Starting scheduler service..."
launchctl load "${TARGET_PLIST}"

# 서비스 상태 확인
echo ""
echo "✅ Scheduler setup completed!"
echo ""
echo "📊 Service Status:"
launchctl list | grep f1scheduler || echo "Service may not be loaded yet"
echo ""
echo "📅 Schedule Details:"
echo "  - Runs every Monday at 10:00 AM"
echo "  - Scrapes MotorsportStats race results"
echo "  - Scrapes driver career statistics"
echo "  - Scrapes team season statistics"
echo "  - Scrapes OpenF1 data (backup)"
echo ""
echo "📂 File Locations:"
echo "  - Configuration: ${TARGET_PLIST}"
echo "  - Script: ${WEEKLY_SCRAPER}"
echo "  - Log file: ${SCRIPT_DIR}/weekly_scraper.log"
echo ""
echo "🔧 Management Commands:"
echo "  Check status:    launchctl list | grep f1scheduler"
echo "  Stop service:    launchctl unload ${TARGET_PLIST}"
echo "  Start service:   launchctl load ${TARGET_PLIST}"
echo "  View logs:       tail -f ${SCRIPT_DIR}/weekly_scraper.log"
echo ""
echo "🧪 Test Commands:"
echo "  Test manually:   cd ${SCRIPT_DIR} && python3 weekly_scraper.py"
echo "  Test today:      (edit weekly_scraper.py to disable weekday check)"
echo ""

# 백업 디렉토리 생성
BACKUP_DIR="${SCRIPT_DIR}/backups"
mkdir -p "${BACKUP_DIR}"
echo "📁 Created backup directory: ${BACKUP_DIR}"

echo "🎉 Setup complete! The scheduler will run automatically every Monday at 10:00 AM." 