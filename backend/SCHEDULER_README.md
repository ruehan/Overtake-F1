# OpenF1 데이터 자동 업데이트 스케줄러

매주 월요일에 자동으로 OpenF1 API에서 2025년 F1 시즌 데이터를 가져와서 JSON 파일로 저장하는 스케줄러입니다.

## 파일 구성

- `scheduler.py`: 메인 스케줄러 스크립트
- `fetch_openf1_data.py`: OpenF1 API 데이터 수집 스크립트
- `com.overtake.openf1scheduler.plist`: macOS launchd 설정 파일
- `openf1-scheduler.service`: Linux systemd 서비스 파일
- `Dockerfile.scheduler`: Docker 컨테이너 설정
- `docker-compose.scheduler.yml`: Docker Compose 설정

## 설정 방법

### 1. macOS에서 launchd 사용

```bash
# plist 파일을 LaunchAgents 디렉토리에 복사
cp com.overtake.openf1scheduler.plist ~/Library/LaunchAgents/

# 서비스 로드
launchctl load ~/Library/LaunchAgents/com.overtake.openf1scheduler.plist

# 서비스 상태 확인
launchctl list | grep openf1scheduler

# 서비스 언로드 (필요시)
launchctl unload ~/Library/LaunchAgents/com.overtake.openf1scheduler.plist
```

### 2. Linux에서 systemd 사용

```bash
# 서비스 파일을 시스템 디렉토리에 복사
sudo cp openf1-scheduler.service /etc/systemd/system/

# systemd 재로드
sudo systemctl daemon-reload

# 서비스 활성화 및 시작
sudo systemctl enable openf1-scheduler.service
sudo systemctl start openf1-scheduler.service

# 서비스 상태 확인
sudo systemctl status openf1-scheduler.service

# 로그 확인
sudo journalctl -u openf1-scheduler.service -f
```

### 3. Docker 사용

```bash
# Docker Compose로 실행
docker-compose -f docker-compose.scheduler.yml up -d

# 컨테이너 상태 확인
docker-compose -f docker-compose.scheduler.yml ps

# 로그 확인
docker-compose -f docker-compose.scheduler.yml logs -f

# 중지
docker-compose -f docker-compose.scheduler.yml down
```

### 4. 수동 실행 (개발/테스트용)

```bash
# Python 의존성 설치
pip install requests schedule

# 스케줄러 실행
python scheduler.py

# 또는 데이터 수집만 실행
python fetch_openf1_data.py
```

## 스케줄 설정

현재 설정: **매주 월요일 오전 9시**

스케줄을 변경하려면:

1. **scheduler.py**: `schedule.every().monday.at("09:00")` 부분 수정
2. **launchd (macOS)**: plist 파일의 `StartCalendarInterval` 수정
3. **systemd (Linux)**: 서비스 파일에 `OnCalendar` 옵션 추가

## 로그 확인

- **일반 실행**: `scheduler.log` 파일
- **launchd**: `~/Library/Logs/com.overtake.openf1scheduler/`
- **systemd**: `journalctl -u openf1-scheduler.service`
- **Docker**: `docker-compose logs`

## 데이터 백업

스케줄러는 새 데이터를 가져오기 전에 기존 데이터를 자동으로 백업합니다:
- 백업 파일: `openf1_2025_results_backup_YYYYMMDD_HHMMSS.json`

## 트러블슈팅

1. **권한 문제**: 스크립트 실행 권한 확인
   ```bash
   chmod +x scheduler.py fetch_openf1_data.py
   ```

2. **Python 경로 문제**: 시스템의 Python 경로 확인
   ```bash
   which python3
   ```

3. **의존성 문제**: 필요한 패키지 설치 확인
   ```bash
   pip install requests schedule
   ```

4. **네트워크 문제**: OpenF1 API 접근 가능 여부 확인
   ```bash
   curl -s "https://api.openf1.org/v1/sessions?year=2025&session_type=Race"
   ```

## 수동 업데이트

긴급하게 데이터를 업데이트해야 하는 경우:

```bash
cd /Users/hangyu/Desktop/Overtake/backend
python fetch_openf1_data.py
```