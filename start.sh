#!/bin/bash

echo "🏁 Overtake F1 시작 중..."

# PM2 설치 확인
if ! command -v pm2 &> /dev/null; then
    echo "PM2가 설치되어 있지 않습니다. 설치 중..."
    npm install -g pm2
fi

# serve 설치 확인
if ! command -v serve &> /dev/null; then
    echo "serve가 설치되어 있지 않습니다. 설치 중..."
    npm install -g serve
fi

# 기존 프로세스 정지
echo "🛑 기존 프로세스 정지 중..."
pm2 stop overtake-backend 2>/dev/null || true
pm2 stop overtake-frontend 2>/dev/null || true
pm2 delete overtake-backend 2>/dev/null || true
pm2 delete overtake-frontend 2>/dev/null || true

# 백엔드 시작 (기존 환경 사용)
echo "🔧 백엔드 시작 중..."
cd backend

# 가상환경이 있으면 사용, 없으면 시스템 Python 사용
if [ -d "venv" ]; then
    pm2 start --name "overtake-backend" --interpreter python3 "main.py" --cwd "/Users/hangyu/Desktop/Overtake/backend" -- --venv
else
    pm2 start --name "overtake-backend" --interpreter python3 "main.py" --cwd "/Users/hangyu/Desktop/Overtake/backend"
fi

cd ..

# 프론트엔드 빌드가 있는지 확인하고 없으면 빌드
echo "📦 프론트엔드 확인 중..."
cd frontend
if [ ! -d "build" ]; then
    echo "빌드 디렉토리가 없습니다. 빌드 중..."
    npm run build
fi

# 프론트엔드 시작
echo "🌐 프론트엔드 시작 중..."
pm2 start --name "overtake-frontend" "serve" -- "-s build -l 3000"

cd ..

# 상태 확인
sleep 2
echo ""
echo "✅ 시작 완료!"
echo ""
pm2 status

echo ""
echo "🌐 서비스 URL:"
echo "  - 프론트엔드: http://localhost:3000"
echo "  - 백엔드 API: http://localhost:8000"
echo "  - Nginx (80포트): http://localhost"
echo ""
echo "📊 명령어:"
echo "  - 상태 확인: pm2 status"
echo "  - 로그 확인: pm2 logs"
echo "  - 서비스 중지: ./stop.sh"