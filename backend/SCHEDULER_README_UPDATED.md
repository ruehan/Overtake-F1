# F1 Statistics Auto-Scraping Scheduler

매주 월요일에 자동으로 F1 통계 데이터를 업데이트하는 완전한 스크래핑 시스템입니다.

## 🎯 시스템 개요

이 스케줄러는 다음 데이터를 자동으로 수집합니다:

1. **MotorsportStats 레이스 결과** (우선순위 1) - 2025년 현재 시즌 데이터
2. **드라이버 커리어 통계** - motorsportstats.com에서 수집
3. **팀 시즌 통계** - 2025년 팀별 성과 데이터
4. **OpenF1 데이터** (백업용) - API 기반 데이터

## 📁 파일 구성

### 핵심 스크래핑 파일
- `weekly_scraper.py` - 메인 스케줄러 스크립트 (통합 관리)
- `motorsportstats_race_batch_scraper.py` - 2025년 레이스 결과 스크래핑
- `bulk_driver_scraper.py` - 드라이버 커리어 통계 스크래핑
- `team_season_scraper.py` - 팀 시즌 통계 스크래핑
- `fetch_openf1_data.py` - OpenF1 API 데이터 수집

### 설정 파일
- `com.overtake.f1scheduler.plist` - macOS launchd 설정
- `setup_scheduler_macos.sh` - macOS 자동 설정 스크립트
- `setup_cron.sh` - Linux cron 설정 스크립트

### 생성되는 데이터 파일
- `motorsportstats_2025_race_results.json` - 현재 시즌 레이스 결과
- `driver_career_stats.json` - 드라이버 커리어 데이터
- `team_2025_season_stats.json` - 2025년 팀 통계
- `openf1_2025_results.json` - OpenF1 백업 데이터

## 🚀 설정 방법

### 1. macOS 자동 설정 (추천)

```bash
cd /Users/hangyu/Desktop/Overtake/backend
./setup_scheduler_macos.sh
```

이 스크립트는 자동으로:
- 가상환경 확인
- 파일 권한 설정
- launchd 서비스 등록
- 백업 디렉토리 생성

### 2. 수동 macOS 설정

```bash
# plist 파일을 LaunchAgents 디렉토리에 복사
cp com.overtake.f1scheduler.plist ~/Library/LaunchAgents/

# 서비스 로드
launchctl load ~/Library/LaunchAgents/com.overtake.f1scheduler.plist

# 서비스 상태 확인
launchctl list | grep f1scheduler
```

### 3. Linux cron 설정

```bash
# cron 자동 설정
./setup_cron.sh

# 또는 수동 설정
crontab -e
# 다음 라인 추가:
# 0 10 * * 1 cd /path/to/backend && python3 weekly_scraper.py >> /path/to/logs/cron.log 2>&1
```

## 📅 스케줄 정보

- **실행 시간**: 매주 월요일 오전 10시
- **작업 순서**:
  1. MotorsportStats 레이스 결과 (30분 타임아웃)
  2. 드라이버 통계 (1시간 타임아웃)
  3. 팀 통계 (30분 타임아웃)
  4. OpenF1 데이터 (30분 타임아웃)

## 🔍 관리 명령어

### macOS launchd
```bash
# 서비스 상태 확인
launchctl list | grep f1scheduler

# 서비스 중지
launchctl unload ~/Library/LaunchAgents/com.overtake.f1scheduler.plist

# 서비스 시작
launchctl load ~/Library/LaunchAgents/com.overtake.f1scheduler.plist

# 로그 확인
tail -f /Users/hangyu/Desktop/Overtake/backend/weekly_scraper.log
```

### Linux cron
```bash
# cron 상태 확인
crontab -l

# cron 편집
crontab -e

# 로그 확인
tail -f /path/to/backend/weekly_scraper.log
```

## 📊 로그 및 백업

### 로그 파일
- `weekly_scraper.log` - 메인 스케줄러 로그
- `scheduler.log` - 기존 스케줄러 로그 (참고용)

### 자동 백업
스크래핑 완료 후 자동으로 백업 파일 생성:
- `motorsportstats_race_backup_YYYYMMDD_HHMMSS.json`
- `driver_career_stats_backup_YYYYMMDD_HHMMSS.json`
- `team_2025_season_backup_YYYYMMDD_HHMMSS.json`
- `openf1_2025_results_backup_YYYYMMDD_HHMMSS.json`

30일 이상된 백업 파일은 자동 삭제됩니다.

## 🧪 테스트 및 수동 실행

### 전체 스크래핑 테스트
```bash
cd /Users/hangyu/Desktop/Overtake/backend
python3 weekly_scraper.py
```

### 개별 스크래핑 테스트
```bash
# MotorsportStats 레이스 결과
python3 motorsportstats_race_batch_scraper.py

# 드라이버 통계
python3 bulk_driver_scraper.py

# 팀 통계
python3 team_season_scraper.py

# OpenF1 데이터
python3 fetch_openf1_data.py
```

### 즉시 실행 (요일 체크 무시)
`weekly_scraper.py`의 메인 함수에서 요일 체크를 임시로 비활성화:
```python
# 기존 코드
if today.weekday() == 0:  # 월요일

# 테스트용으로 변경
if True:  # 항상 실행
```

## 🔧 문제 해결

### 1. 권한 문제
```bash
chmod +x weekly_scraper.py
chmod +x setup_scheduler_macos.sh
```

### 2. 가상환경 문제
```bash
cd /Users/hangyu/Desktop/Overtake/backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. 네트워크 문제
```bash
# MotorsportStats 접근 테스트
curl -s "https://motorsportstats.com/results/fia-formula-one-world-championship/2025/bahrain-grand-prix/classification"

# OpenF1 API 접근 테스트
curl -s "https://api.openf1.org/v1/sessions?year=2025&session_type=Race"
```

### 4. 로그 확인
```bash
# 실시간 로그 확인
tail -f weekly_scraper.log

# 에러 로그만 확인
grep "ERROR\|❌" weekly_scraper.log

# 성공 로그만 확인
grep "✅" weekly_scraper.log
```

## 📈 성능 모니터링

### 데이터 파일 크기 확인
```bash
ls -lh *.json
```

### 스크래핑 성공률 확인
```bash
grep -c "✅" weekly_scraper.log
grep -c "❌" weekly_scraper.log
```

### 백업 파일 정리
```bash
# 수동으로 오래된 백업 삭제 (30일 이상)
find backups/ -name "*_backup_*.json" -mtime +30 -delete
```

## 🔔 알림 설정 (선택사항)

`weekly_scraper.py`의 `send_notification()` 함수에서:
- Slack 웹훅 추가
- 이메일 전송 설정
- Discord 알림 설정 등

## 📋 체크리스트

설정 완료 후 확인사항:
- [ ] 가상환경 생성 및 패키지 설치
- [ ] 스크립트 실행 권한 설정
- [ ] 스케줄러 서비스 등록
- [ ] 백업 디렉토리 생성
- [ ] 수동 테스트 실행 성공
- [ ] 로그 파일 생성 확인
- [ ] 서비스 상태 정상 확인

이제 매주 월요일마다 자동으로 최신 F1 통계 데이터가 업데이트됩니다! 🏎️✨ 