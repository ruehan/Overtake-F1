import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { updateMetaTags, getMetaData } from '../utils/metaUtils';

type Language = 'en' | 'ko';

interface LanguageContextType {
  language: Language;
  setLanguage: (lang: Language) => void;
  t: (key: string) => string;
  translateStatus: (status: string) => string;
  translateCountry: (country: string) => string;
  formatMessage: (key: string, values?: Record<string, string | number>) => string;
}

const LanguageContext = createContext<LanguageContextType | undefined>(undefined);

// 번역 데이터
const translations = {
  en: {
    // Navigation
    'nav.live': 'LIVE',
    'nav.standings': 'STANDINGS',
    'nav.progression': 'PROGRESSION',
    'nav.weekends': 'WEEKENDS',
    'nav.statistics': 'STATS',
    'nav.circuits': 'CIRCUITS',
    'nav.calendar': 'CALENDAR',
    'nav.results': 'RESULTS',
    
    // Dashboard
    'dashboard.title': '🔴 F1 Live Dashboard',
    'dashboard.connection': '📡 Live Connection',
    'dashboard.connected': 'CONNECTED',
    'dashboard.disconnected': 'DISCONNECTED',
    'dashboard.lastUpdate': 'Last update',
    'dashboard.currentRace': '🔴 Current Race Weekend',
    'dashboard.nextRace': '⏭️ Next Race',
    'dashboard.liveTiming': '⏱️ Live Timing',
    'dashboard.trackConditions': '🌤️ Track Conditions',
    'dashboard.noWeatherData': '🌤️ No Live Weather Data',
    'dashboard.weatherMessage': 'Weather data only available during active F1 sessions',
    'dashboard.drivers': '🏎️ Current Drivers',
    'dashboard.systemStatus': '🔧 System Status',
    'dashboard.noActiveSession': 'NO ACTIVE SESSION',
    
    // Standings
    'standings.title': '🏆 Championship Standings',
    'standings.drivers': '🏎️ DRIVERS',
    'standings.constructors': '🏭 CONSTRUCTORS',
    'standings.season': 'Season',
    'standings.position': 'POS',
    'standings.driver': 'DRIVER',
    'standings.team': 'TEAM',
    'standings.points': 'PTS',
    'standings.wins': 'WINS',
    'standings.battle': 'Championship Battle',
    'standings.driverChampionship': 'Driver Championship',
    'standings.constructorChampionship': 'Constructor Championship',
    'standings.leader': 'Leader',
    'standings.gapToSecond': 'Gap to 2nd',
    
    // Progression
    'progression.championshipPositionProgress': 'Championship Position Progress',
    'progression.championshipPointsProgress': 'Championship Points Progress', 
    'progression.positionOverTime': 'Championship Position Over Time',
    'progression.pointsAccumulation': 'Points Accumulation',
    'progression.selectDrivers': 'Select Drivers to Display',
    'progression.selectTeams': 'Select Teams to Display',
    'progression.available': 'available',
    
    // Statistics
    'statistics.title': '📊 Season Statistics',
    'statistics.drivers': '🏎️ DRIVERS',
    'statistics.constructors': '🏭 CONSTRUCTORS',
    'statistics.season': 'Season',
    'statistics.driverStats': '🏎️ Driver Statistics',
    'statistics.teamStats': '🏭 Constructor Statistics',
    'statistics.totalWins': 'Total Wins',
    'statistics.totalPodiums': 'Total Podiums',
    'statistics.fastestLaps': 'Fastest Laps',
    'statistics.dnfs': 'DNFs',
    'statistics.oneTwos': '1-2 Finishes',
    'statistics.legend': '📖 Legend',
    'statistics.legendPts': 'Championship points',
    'statistics.legendFl': 'Fastest laps',
    'statistics.legendDnf': 'Did not finish',
    'statistics.legendOneTwos': 'One-two finishes (teams only)',
    'statistics.goodPerformance': 'Good performance indicators',
    'statistics.reliabilityIssues': 'Reliability issues',
    
    // Circuits
    'circuits.title': '🏁 F1 Circuits',
    'circuits.season': 'Season',
    'circuits.clickDetails': 'Click for details',
    'circuits.info': '🔗 Info',
    'circuits.totalRaces': 'Total Races',
    'circuits.lapRecords': 'Lap Records',
    'circuits.differentWinners': 'Different Winners',
    'circuits.backToList': '← Back to List',
    'circuits.fastestLapRecords': '⚡ Fastest Lap Records',
    'circuits.mostSuccessfulDrivers': '🏆 Most Successful Drivers',
    'circuits.mostSuccessfulTeams': '🏭 Most Successful Teams',
    'circuits.recentRaceHistory': '📅 Recent Race History',
    'circuits.winner': 'Winner:',
    'circuits.rank': 'RANK',
    'circuits.time': 'TIME',
    'circuits.driver': 'DRIVER',
    'circuits.year': 'YEAR',
    'circuits.race': 'RACE',
    'circuits.win': 'win',
    'circuits.wins': 'wins',
    
    // Calendar
    'calendar.title': 'F1 Race Calendar',
    'calendar.nextRace': 'Next Race',
    'calendar.currentRace': 'Current Race Weekend',
    'calendar.seasonCalendar': 'Season Calendar',
    'calendar.race': 'Race',
    'calendar.qualifying': 'Qualifying',
    'calendar.live': 'LIVE',
    'calendar.upcoming': 'UPCOMING',
    'calendar.completed': 'COMPLETED',
    
    // Race Weekends
    'weekends.title': 'Race Weekends',
    'weekends.raceWeekend': 'Race Weekend',
    'weekends.sessionSchedule': 'Session Schedule & Results',
    'weekends.practice1': 'Practice 1',
    'weekends.practice2': 'Practice 2', 
    'weekends.practice3': 'Practice 3',
    'weekends.qualifying': 'Qualifying',
    'weekends.sprint': 'Sprint',
    'weekends.race': 'Race',
    'weekends.session': 'Session',
    'weekends.sessions': 'Sessions',
    'weekends.results': 'Results',
    'weekends.schedule': 'Schedule',
    
    // Results
    'results.title': 'Race Results',
    'results.latestRace': 'Latest Race Result',
    'results.seasonResults': 'Season Results',
    'results.position': 'Pos',
    'results.driver': 'Driver',
    'results.team': 'Team',
    'results.timeStatus': 'Time/Status',
    'results.finishers': 'finishers',
    'results.noResults': 'No results',
    'results.grid': 'Grid',
    'results.laps': 'Laps',
    'results.status': 'Status',
    'results.time': 'Time',
    'results.fastestLap': 'Fastest Lap',
    'results.points': 'pts',
    
    // Common
    'common.loading': 'Loading',
    'common.error': 'Error',
    'common.noData': 'No data available',
    'common.round': 'Round',
    'common.selectAll': 'Select All',
    'common.clearAll': 'Clear All',
    'common.races': 'races',
    'common.back': 'Back',
    'common.close': 'Close',
    
    // Driver Detail
    'driver.personalInfo': 'Personal Information',
    'driver.careerStats': 'Career Statistics',
    'driver.currentSeason': 'Current Season Performance',
    'driver.nationality': 'Nationality',
    'driver.dateOfBirth': 'Date of Birth',
    'driver.placeOfBirth': 'Place of Birth',
    'driver.f1Debut': 'F1 Debut',
    'driver.worldChampionships': 'World Championships',
    'driver.raceWins': 'Race Wins',
    'driver.podiums': 'Podiums',
    'driver.polePositions': 'Pole Positions',
    'driver.fastestLaps': 'Fastest Laps',
    'driver.careerPoints': 'Career Points',
    
    // Data translations
    'data.finished': 'Finished',
    'data.retired': 'Retired',
    'data.disqualified': 'Disqualified',
    'data.notClassified': 'Not Classified',
    'data.accident': 'Accident',
    'data.engine': 'Engine',
    'data.gearbox': 'Gearbox',
    'data.transmission': 'Transmission',
    'data.clutch': 'Clutch',
    'data.hydraulics': 'Hydraulics',
    'data.electrical': 'Electrical',
    'data.suspension': 'Suspension',
    'data.brakes': 'Brakes',
    'data.differential': 'Differential',
    'data.fuel': 'Fuel System',
    'data.wheel': 'Wheel',
    'data.driver': 'Driver',
    'data.withdrawn': 'Withdrawn',
    'data.spunOff': 'Spun off',
    'data.collision': 'Collision',
    'data.puncture': 'Puncture',
    'data.radiator': 'Radiator',
    'data.overheating': 'Overheating',
    'data.mechanical': 'Mechanical',
    'data.tyre': 'Tyre',
    'data.electronics': 'Electronics',
    'data.fire': 'Fire',
    'data.network': 'Connection problems',
    'data.weatherUnavailable': 'Weather data only available during active F1 sessions',
    'data.noActiveSession': 'No active F1 session',
    'data.timingDataActive': 'Active',
    'data.timingDataNoData': 'No Data',
    'data.raceWeekend': 'RACE WEEKEND',
    'data.noUpcomingRaces': 'No upcoming races found',
    'data.noRaceWeekend': 'No race weekend currently in progress',
    'data.driversCount': '{count} drivers',
    'data.circuitsCount': '{count} circuits',
    'data.racesCount': '{count} races',
    'data.completedRaces': '{completed} completed',
    'data.upcomingRaces': '{upcoming} upcoming',
    
    // Countries (주요 F1 개최국)
    'country.Australia': 'Australia',
    'country.Bahrain': 'Bahrain',
    'country.China': 'China',
    'country.Azerbaijan': 'Azerbaijan',
    'country.Spain': 'Spain',
    'country.Monaco': 'Monaco',
    'country.Canada': 'Canada',
    'country.France': 'France',
    'country.Austria': 'Austria',
    'country.UK': 'United Kingdom',
    'country.Hungary': 'Hungary',
    'country.Belgium': 'Belgium',
    'country.Netherlands': 'Netherlands',
    'country.Italy': 'Italy',
    'country.Singapore': 'Singapore',
    'country.Japan': 'Japan',
    'country.USA': 'United States',
    'country.Mexico': 'Mexico',
    'country.Brazil': 'Brazil',
    'country.UAE': 'United Arab Emirates',
    'country.Saudi Arabia': 'Saudi Arabia',
    'country.Qatar': 'Qatar'
  },
  ko: {
    // Navigation
    'nav.live': '라이브',
    'nav.standings': '순위',
    'nav.progression': '변화 추이',
    'nav.weekends': '레이스 주말',
    'nav.statistics': '통계',
    'nav.circuits': '서킷',
    'nav.calendar': '캘린더',
    'nav.results': '결과',
    
    // Dashboard
    'dashboard.title': '🔴 F1 라이브 대시보드',
    'dashboard.connection': '📡 라이브 연결',
    'dashboard.connected': '연결됨',
    'dashboard.disconnected': '연결 끊김',
    'dashboard.lastUpdate': '마지막 업데이트',
    'dashboard.currentRace': '🔴 현재 레이스 주말',
    'dashboard.nextRace': '⏭️ 다음 레이스',
    'dashboard.liveTiming': '⏱️ 라이브 타이밍',
    'dashboard.trackConditions': '🌤️ 트랙 상황',
    'dashboard.noWeatherData': '🌤️ 라이브 날씨 데이터 없음',
    'dashboard.weatherMessage': '날씨 데이터는 F1 세션 진행 중에만 이용 가능합니다',
    'dashboard.drivers': '🏎️ 현재 드라이버',
    'dashboard.systemStatus': '🔧 시스템 상태',
    'dashboard.noActiveSession': '활성 세션 없음',
    
    // Standings
    'standings.title': '🏆 챔피언십 순위',
    'standings.drivers': '🏎️ 드라이버',
    'standings.constructors': '🏭 컨스트럭터',
    'standings.season': '시즌',
    'standings.position': '순위',
    'standings.driver': '드라이버',
    'standings.team': '팀',
    'standings.points': '포인트',
    'standings.wins': '우승',
    'standings.battle': '챔피언십 경쟁',
    'standings.driverChampionship': '드라이버 챔피언십',
    'standings.constructorChampionship': '컨스트럭터 챔피언십',
    'standings.leader': '리더',
    'standings.gapToSecond': '2위와의 격차',
    
    // Progression
    'progression.championshipPositionProgress': '챔피언십 순위 변화',
    'progression.championshipPointsProgress': '챔피언십 포인트 변화',
    'progression.positionOverTime': '시간에 따른 챔피언십 순위',
    'progression.pointsAccumulation': '포인트 누적',
    'progression.selectDrivers': '표시할 드라이버 선택',
    'progression.selectTeams': '표시할 팀 선택',
    'progression.available': '사용 가능',
    
    // Statistics
    'statistics.title': '📊 시즌 통계',
    'statistics.drivers': '🏎️ 드라이버',
    'statistics.constructors': '🏭 컨스트럭터',
    'statistics.season': '시즌',
    'statistics.driverStats': '🏎️ 드라이버 통계',
    'statistics.teamStats': '🏭 컨스트럭터 통계',
    'statistics.totalWins': '총 우승 수',
    'statistics.totalPodiums': '총 포디움 수',
    'statistics.fastestLaps': '최고 기록',
    'statistics.dnfs': '리타이어',
    'statistics.oneTwos': '1-2 피니시',
    'statistics.legend': '📖 범례',
    'statistics.legendPts': '챔피언십 포인트',
    'statistics.legendFl': '최고 랩타임',
    'statistics.legendDnf': '완주 실패',
    'statistics.legendOneTwos': '1-2 피니시 (팀만 해당)',
    'statistics.goodPerformance': '좋은 성과 지표',
    'statistics.reliabilityIssues': '신뢰성 문제',
    
    // Circuits
    'circuits.title': '🏁 F1 서킷',
    'circuits.season': '시즌',
    'circuits.clickDetails': '자세히 보기',
    'circuits.info': '🔗 정보',
    'circuits.totalRaces': '총 레이스 수',
    'circuits.lapRecords': '랩 기록',
    'circuits.differentWinners': '다른 우승자',
    'circuits.backToList': '← 목록으로',
    'circuits.fastestLapRecords': '⚡ 최고 랩타임 기록',
    'circuits.mostSuccessfulDrivers': '🏆 가장 성공한 드라이버',
    'circuits.mostSuccessfulTeams': '🏭 가장 성공한 팀',
    'circuits.recentRaceHistory': '📅 최근 레이스 기록',
    'circuits.winner': '우승자:',
    'circuits.rank': '순위',
    'circuits.time': '시간',
    'circuits.driver': '드라이버',
    'circuits.year': '연도',
    'circuits.race': '레이스',
    'circuits.win': '승',
    'circuits.wins': '승',
    
    // Calendar
    'calendar.title': 'F1 레이스 캘린더',
    'calendar.nextRace': '다음 레이스',
    'calendar.currentRace': '현재 레이스 주말',
    'calendar.seasonCalendar': '시즌 캘린더',
    'calendar.race': '레이스',
    'calendar.qualifying': '예선',
    'calendar.live': '라이브',
    'calendar.upcoming': '예정',
    'calendar.completed': '완료',
    
    // Race Weekends
    'weekends.title': '레이스 주말',
    'weekends.raceWeekend': '레이스 주말',
    'weekends.sessionSchedule': '세션 일정 및 결과',
    'weekends.practice1': '연습 1',
    'weekends.practice2': '연습 2',
    'weekends.practice3': '연습 3',
    'weekends.qualifying': '예선',
    'weekends.sprint': '스프린트',
    'weekends.race': '레이스',
    'weekends.session': '세션',
    'weekends.sessions': '세션',
    'weekends.results': '결과',
    'weekends.schedule': '일정',
    
    // Results
    'results.title': '레이스 결과',
    'results.latestRace': '최신 레이스 결과',
    'results.seasonResults': '시즌 결과',
    'results.position': '순위',
    'results.driver': '드라이버',
    'results.team': '팀',
    'results.timeStatus': '시간/상태',
    'results.finishers': '완주자',
    'results.noResults': '결과 없음',
    'results.grid': '그리드',
    'results.laps': '랩',
    'results.status': '상태',
    'results.time': '시간',
    'results.fastestLap': '최고 랩타임',
    'results.points': '포인트',
    
    // Common
    'common.loading': '로딩 중',
    'common.error': '오류',
    'common.noData': '데이터가 없습니다',
    'common.round': '라운드',
    'common.selectAll': '전체 선택',
    'common.clearAll': '전체 해제',
    'common.races': '레이스',
    'common.back': '뒤로',
    'common.close': '닫기',
    
    // Driver Detail
    'driver.personalInfo': '개인 정보',
    'driver.careerStats': '경력 통계',
    'driver.currentSeason': '현재 시즌 성과',
    'driver.nationality': '국적',
    'driver.dateOfBirth': '생년월일',
    'driver.placeOfBirth': '출생지',
    'driver.f1Debut': 'F1 데뷔',
    'driver.worldChampionships': '월드 챔피언십',
    'driver.raceWins': '레이스 승리',
    'driver.podiums': '포디움',
    'driver.polePositions': '폴 포지션',
    'driver.fastestLaps': '최고 랩타임',
    'driver.careerPoints': '통산 포인트',
    
    // Data translations
    'data.finished': '완주',
    'data.retired': '리타이어',
    'data.disqualified': '실격',
    'data.notClassified': '미분류',
    'data.accident': '사고',
    'data.engine': '엔진',
    'data.gearbox': '기어박스',
    'data.transmission': '변속기',
    'data.clutch': '클러치',
    'data.hydraulics': '유압계통',
    'data.electrical': '전기계통',
    'data.suspension': '서스펜션',
    'data.brakes': '브레이크',
    'data.differential': '디퍼렌셜',
    'data.fuel': '연료계통',
    'data.wheel': '휠',
    'data.driver': '드라이버',
    'data.withdrawn': '철수',
    'data.spunOff': '스핀',
    'data.collision': '충돌',
    'data.puncture': '펑크',
    'data.radiator': '라디에이터',
    'data.overheating': '과열',
    'data.mechanical': '기계적 문제',
    'data.tyre': '타이어',
    'data.electronics': '전자장치',
    'data.fire': '화재',
    'data.network': '연결 문제',
    'data.weatherUnavailable': '날씨 데이터는 F1 세션 진행 중에만 이용 가능합니다',
    'data.noActiveSession': '활성 F1 세션 없음',
    'data.timingDataActive': '활성',
    'data.timingDataNoData': '데이터 없음',
    'data.raceWeekend': '레이스 주말',
    'data.noUpcomingRaces': '예정된 레이스가 없습니다',
    'data.noRaceWeekend': '현재 진행 중인 레이스 주말이 없습니다',
    'data.driversCount': '드라이버 {count}명',
    'data.circuitsCount': '서킷 {count}개',
    'data.racesCount': '레이스 {count}개',
    'data.completedRaces': '완료 {completed}개',
    'data.upcomingRaces': '예정 {upcoming}개',
    
    // Countries (주요 F1 개최국)
    'country.Australia': '호주',
    'country.Bahrain': '바레인',
    'country.China': '중국',
    'country.Azerbaijan': '아제르바이잔',
    'country.Spain': '스페인',
    'country.Monaco': '모나코',
    'country.Canada': '캐나다',
    'country.France': '프랑스',
    'country.Austria': '오스트리아',
    'country.UK': '영국',
    'country.Hungary': '헝가리',
    'country.Belgium': '벨기에',
    'country.Netherlands': '네덜란드',
    'country.Italy': '이탈리아',
    'country.Singapore': '싱가포르',
    'country.Japan': '일본',
    'country.USA': '미국',
    'country.Mexico': '멕시코',
    'country.Brazil': '브라질',
    'country.UAE': '아랍에미리트',
    'country.Saudi Arabia': '사우디아라비아',
    'country.Qatar': '카타르'
  }
};

export const LanguageProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [language, setLanguage] = useState<Language>('ko'); // 기본값을 한글로 설정

  // 언어 변경 시 메타데이터 업데이트
  useEffect(() => {
    const metaData = getMetaData(language);
    updateMetaTags(metaData);
    
    // HTML lang 속성도 업데이트
    document.documentElement.lang = language;
  }, [language]);

  const t = (key: string): string => {
    return translations[language][key as keyof typeof translations[typeof language]] || key;
  };

  // 레이스 상태를 번역하는 함수
  const translateStatus = (status: string): string => {
    const statusLower = status.toLowerCase();
    
    // 상태별 매핑
    const statusMappings: Record<string, string> = {
      'finished': 'data.finished',
      'retired': 'data.retired',
      'disqualified': 'data.disqualified',
      'not classified': 'data.notClassified',
      'accident': 'data.accident',
      'engine': 'data.engine',
      'gearbox': 'data.gearbox',
      'transmission': 'data.transmission',
      'clutch': 'data.clutch',
      'hydraulics': 'data.hydraulics',
      'electrical': 'data.electrical',
      'suspension': 'data.suspension',
      'brakes': 'data.brakes',
      'differential': 'data.differential',
      'fuel': 'data.fuel',
      'wheel': 'data.wheel',
      'driver': 'data.driver',
      'withdrawn': 'data.withdrawn',
      'spun off': 'data.spunOff',
      'collision': 'data.collision',
      'puncture': 'data.puncture',
      'radiator': 'data.radiator',
      'overheating': 'data.overheating',
      'mechanical': 'data.mechanical',
      'tyre': 'data.tyre',
      'electronics': 'data.electronics',
      'fire': 'data.fire'
    };

    // 부분 매칭도 지원
    for (const [key, translationKey] of Object.entries(statusMappings)) {
      if (statusLower.includes(key)) {
        return t(translationKey);
      }
    }

    return status; // 매핑되지 않은 경우 원본 반환
  };

  // 국가명을 번역하는 함수
  const translateCountry = (country: string): string => {
    const countryKey = `country.${country}`;
    const translated = t(countryKey);
    return translated !== countryKey ? translated : country;
  };

  // 메시지 포맷팅 함수 (변수 치환 지원)
  const formatMessage = (key: string, values?: Record<string, string | number>): string => {
    let message = t(key);
    
    if (values) {
      Object.entries(values).forEach(([placeholder, value]) => {
        message = message.replace(new RegExp(`{${placeholder}}`, 'g'), String(value));
      });
    }
    
    return message;
  };

  return (
    <LanguageContext.Provider value={{ 
      language, 
      setLanguage, 
      t, 
      translateStatus, 
      translateCountry, 
      formatMessage 
    }}>
      {children}
    </LanguageContext.Provider>
  );
};

export const useLanguage = (): LanguageContextType => {
  const context = useContext(LanguageContext);
  if (!context) {
    throw new Error('useLanguage must be used within a LanguageProvider');
  }
  return context;
};