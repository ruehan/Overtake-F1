# 🏁 Overtake F1 배포 가이드

## 📋 사전 준비사항

### 1. 서버 요구사항
- Ubuntu 20.04 LTS 이상
- RAM: 최소 2GB (권장 4GB)
- 디스크: 최소 20GB
- Python 3.8 이상
- Node.js 16 이상
- Nginx
- SSL 인증서 (Let's Encrypt 권장)

### 2. 도메인 설정
- 가비아에서 구매한 `overtake-f1.com` 도메인의 DNS 설정
- A 레코드: `@` → 서버 IP 주소
- A 레코드: `www` → 서버 IP 주소

## 🚀 배포 단계

### 1. 서버 초기 설정

```bash
# 시스템 업데이트
sudo apt update && sudo apt upgrade -y

# 필수 패키지 설치
sudo apt install -y python3-pip python3-venv nodejs npm nginx certbot python3-certbot-nginx git

# Node.js 최신 버전 설치 (선택사항)
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs
```

### 2. 프로젝트 클론

```bash
cd /home/ubuntu
git clone https://github.com/your-username/overtake.git
cd overtake
```

### 3. SSL 인증서 발급

```bash
# Let's Encrypt SSL 인증서 발급
sudo certbot --nginx -d overtake-f1.com -d www.overtake-f1.com
```

### 4. Nginx 설정

```bash
# Nginx 설정 파일 복사
sudo cp nginx.conf /etc/nginx/sites-available/overtake-f1
sudo ln -s /etc/nginx/sites-available/overtake-f1 /etc/nginx/sites-enabled/
sudo rm /etc/nginx/sites-enabled/default

# Nginx 설정 테스트 및 재시작
sudo nginx -t
sudo systemctl restart nginx
```

### 5. 애플리케이션 배포

```bash
# 배포 스크립트 실행
./deploy.sh
```

## 📊 PM2 명령어

### 상태 확인
```bash
pm2 status              # 프로세스 상태 확인
pm2 logs               # 전체 로그 확인
pm2 logs overtake-backend   # 백엔드 로그만 확인
pm2 logs overtake-frontend  # 프론트엔드 로그만 확인
```

### 프로세스 관리
```bash
pm2 restart all        # 모든 프로세스 재시작
pm2 reload all         # 무중단 재시작
pm2 stop all          # 모든 프로세스 중지
pm2 delete all        # 모든 프로세스 삭제
```

### 모니터링
```bash
pm2 monit             # 실시간 모니터링
pm2 web               # 웹 대시보드 (별도 설정 필요)
```

## 🔧 환경 변수 설정

### 백엔드 (.env)
```env
HOST=0.0.0.0
PORT=8000
ENVIRONMENT=production
CORS_ORIGINS=["https://overtake-f1.com"]
```

### 프론트엔드 (.env.production)
```env
REACT_APP_API_URL=https://overtake-f1.com/api
REACT_APP_WS_URL=wss://overtake-f1.com/ws
```

## 🐛 문제 해결

### 1. 포트 충돌
```bash
# 사용 중인 포트 확인
sudo lsof -i :8000
sudo lsof -i :3000

# 프로세스 종료
sudo kill -9 <PID>
```

### 2. 권한 문제
```bash
# 로그 디렉토리 권한 설정
sudo chown -R ubuntu:ubuntu /home/ubuntu/overtake
chmod -R 755 /home/ubuntu/overtake/logs
```

### 3. Python 패키지 문제
```bash
cd backend
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt --force-reinstall
```

### 4. WebSocket 연결 문제
- Nginx 설정에서 WebSocket 프록시 설정 확인
- 방화벽에서 WebSocket 포트 허용 확인

## 🔐 보안 설정

### 1. 방화벽 설정
```bash
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw enable
```

### 2. 자동 SSL 갱신
```bash
# Crontab에 추가
sudo crontab -e
# 다음 줄 추가:
0 0 * * * certbot renew --quiet
```

## 📈 성능 최적화

### 1. PM2 클러스터 모드
```javascript
// ecosystem.config.js에서 instances 설정
instances: 'max',  // CPU 코어 수만큼 프로세스 생성
```

### 2. Nginx 캐싱
- 정적 파일에 대한 캐싱 헤더 설정
- Gzip 압축 활성화

### 3. 데이터베이스 연결 풀링
- 필요시 백엔드에서 연결 풀 설정

## 🔄 업데이트 절차

```bash
# 1. 코드 업데이트
cd /home/ubuntu/overtake
git pull origin main

# 2. 프론트엔드 재빌드
cd frontend
npm install
npm run build

# 3. 백엔드 의존성 업데이트
cd ../backend
source venv/bin/activate
pip install -r requirements.txt

# 4. PM2 재시작
cd ..
pm2 reload all
```

## 📞 지원

문제가 발생하면 다음을 확인하세요:
- PM2 로그: `pm2 logs`
- Nginx 로그: `/var/log/nginx/overtake-f1.error.log`
- 시스템 로그: `sudo journalctl -xe`