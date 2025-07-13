#!/bin/bash

# macOS용 Overtake F1 배포 스크립트

echo "🍎 macOS에서 Overtake F1 배포 시작..."

# 로그 디렉토리 생성
mkdir -p logs

# 1. 프론트엔드 빌드
echo "📦 프론트엔드 빌드 중..."
cd frontend

# 환경 변수 설정 (본인의 맥 IP 또는 도메인)
echo "REACT_APP_API_URL=https://overtake-f1.com/api" > .env.production
echo "REACT_APP_WS_URL=wss://overtake-f1.com/ws" >> .env.production

# 의존성 설치 및 빌드
npm install
npm run build

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
CORS_ORIGINS=["https://overtake-f1.com", "http://localhost:3000"]
EOL

cd ..

# 3. Nginx 설정 확인
echo "🌐 Nginx 설정 확인..."
if ! command -v nginx &> /dev/null; then
    echo "❌ Nginx가 설치되어 있지 않습니다."
    echo "다음 명령어로 설치하세요: brew install nginx"
    exit 1
fi

# 4. PM2 설정 및 시작
echo "🚀 PM2로 애플리케이션 시작..."

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
pm2 stop all 2>/dev/null || true
pm2 delete all 2>/dev/null || true

# 새로운 프로세스 시작
pm2 start ecosystem.config.js

# PM2 startup 설정
pm2 startup
pm2 save

echo ""
echo "✅ macOS 배포 완료!"
echo ""
echo "📋 다음 단계:"
echo "1. 라우터에서 포트포워딩 설정:"
echo "   - 포트 80 → 맥 IP:80"
echo "   - 포트 443 → 맥 IP:443"
echo ""
echo "2. Nginx 설정:"
echo "   sudo cp nginx-mac.conf /usr/local/etc/nginx/nginx.conf"
echo "   brew services restart nginx"
echo ""
echo "3. SSL 인증서 발급:"
echo "   sudo certbot --nginx -d overtake-f1.com -d www.overtake-f1.com"
echo ""
echo "📊 PM2 상태 확인: pm2 status"
echo "📜 로그 확인: pm2 logs"