#!/bin/bash

# Overtake F1 배포 스크립트

echo "🏁 Overtake F1 배포 시작..."

# 로그 디렉토리 생성
mkdir -p logs

# 1. 프론트엔드 빌드
echo "📦 프론트엔드 빌드 중..."
cd frontend

# 환경 변수 설정
echo "REACT_APP_API_URL=https://overtake-f1.com/api" > .env.production
echo "REACT_APP_WS_URL=wss://overtake-f1.com/ws" >> .env.production

# 의존성 설치 및 빌드
npm install
npm run build

# serve 패키지 설치 (정적 파일 서빙용)
npm install -g serve

cd ..

# 2. 백엔드 설정
echo "🔧 백엔드 설정 중..."
cd backend

# Python 가상환경 생성 및 활성화
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

source venv/bin/activate

# 의존성 설치
pip install -r requirements.txt

# 환경 변수 설정
cat > .env << EOL
HOST=0.0.0.0
PORT=8000
ENVIRONMENT=production
CORS_ORIGINS=["https://overtake-f1.com"]
EOL

cd ..

# 3. PM2 시작
echo "🚀 PM2로 애플리케이션 시작..."

# PM2 설치 확인
if ! command -v pm2 &> /dev/null; then
    echo "PM2가 설치되어 있지 않습니다. 설치 중..."
    npm install -g pm2
fi

# 기존 프로세스 정지
pm2 stop all
pm2 delete all

# 새로운 프로세스 시작
pm2 start ecosystem.config.js

# PM2 startup 설정 (재부팅 시 자동 시작)
pm2 startup
pm2 save

echo "✅ 배포 완료!"
echo "📊 PM2 상태 확인: pm2 status"
echo "📜 로그 확인: pm2 logs"