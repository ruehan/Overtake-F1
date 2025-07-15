// API 설정
const getBaseUrls = () => {
  const { hostname, protocol, port } = window.location;
  
  console.log('🌐 Current location:', { hostname, protocol, port, href: window.location.href });
  
  // 로컬 개발환경인지 확인
  const isLocal = hostname === 'localhost' || hostname === '127.0.0.1';
  
  if (isLocal) {
    return {
      apiUrl: 'http://localhost:8000',
      wsUrl: 'ws://localhost:8000'
    };
  } else if (hostname === 'www.overtake-f1.com' || hostname === 'overtake-f1.com') {
    // 프로덕션 환경 - API를 같은 도메인의 다른 경로로 프록시
    return {
      apiUrl: '/api',  // nginx에서 /api -> localhost:8000 프록시 설정 필요
      wsUrl: `https://${hostname}`  // Socket.IO 연결
    };
  } else {
    // 네트워크 IP나 다른 도메인으로 접근하는 경우
    // HTTPS로 접근 중이면 상대 경로 사용 (프록시를 통해)
    if (protocol === 'https:') {
      return {
        apiUrl: '/api',
        wsUrl: `https://${hostname}`
      };
    } else {
      // HTTP 로컬 개발 환경
      return {
        apiUrl: 'http://localhost:8000',
        wsUrl: 'ws://localhost:8000'
      };
    }
  }
};

const { apiUrl, wsUrl } = getBaseUrls();

console.log('🔧 API Config Debug:', {
  apiUrl,
  wsUrl,
  envApiUrl: process.env.REACT_APP_API_URL,
  envWsUrl: process.env.REACT_APP_WS_URL
});

export const API_BASE_URL = process.env.REACT_APP_API_URL || apiUrl;
export const WS_BASE_URL = process.env.REACT_APP_WS_URL || wsUrl;

export const API_ENDPOINTS = {
  // Driver endpoints
  drivers: `${API_BASE_URL}/v1/drivers`,
  driverDetail: (driverNumber: number) => `${API_BASE_URL}/v1/drivers/${driverNumber}`,
  driverSeasonStats: (driverNumber: number, year?: number) => `${API_BASE_URL}/v1/drivers/${driverNumber}/season-stats${year ? `?year=${year}` : ''}`,
  driverCareerStats: (driverNumber: number) => `${API_BASE_URL}/v1/drivers/${driverNumber}/career-stats`,
  driverStandings: (year: number) => `${API_BASE_URL}/v1/driver-standings?year=${year}`,
  
  // Constructor endpoints
  constructorStandings: (year: number) => `${API_BASE_URL}/v1/constructor-standings?year=${year}`,
  
  // Calendar endpoints
  calendar: (year: number) => `${API_BASE_URL}/v1/calendar?year=${year}`,
  nextRace: `${API_BASE_URL}/v1/calendar/next`,
  currentRace: `${API_BASE_URL}/v1/calendar/current`,
  
  // Race results
  raceResults: (year: number) => `${API_BASE_URL}/v1/race-results?year=${year}`,
  latestResult: `${API_BASE_URL}/v1/race-results/latest`,
  
  // Statistics
  statistics: (year: number, type: string) => `${API_BASE_URL}/v1/${type === 'drivers' ? 'driver-statistics' : 'team-statistics'}?year=${year}`,
  allDriversSeasonStats: (year: number) => `${API_BASE_URL}/v1/all-drivers/season-stats?year=${year}`,
  allTeamsSeasonStats: (year: number) => `${API_BASE_URL}/v1/all-teams/season-stats?year=${year}`,
  standingsProgression: (year: number) => `${API_BASE_URL}/v1/standings-progression?year=${year}`,
  
  // Race weekends
  raceWeekends: (year: number) => `${API_BASE_URL}/v1/race-weekends?year=${year}`,
  
  // Live data
  liveTiming: `${API_BASE_URL}/v1/live-timing`,
  weather: `${API_BASE_URL}/v1/weather`,
  
  // Additional endpoints
  circuits: (year: number) => `${API_BASE_URL}/v1/circuits?year=${year}`,
  sessionsWithRadio: (limit: number = 20) => `${API_BASE_URL}/v1/sessions/with-radio?limit=${limit}`,
  sessionsWithWeather: (limit: number = 20) => `${API_BASE_URL}/v1/sessions/with-weather?limit=${limit}`,
  teamRadio: (sessionKey: number, limit: number = 50) => `${API_BASE_URL}/v1/team-radio?session_key=${sessionKey}&limit=${limit}`,
  teamRadioStats: (sessionKey: number) => `${API_BASE_URL}/v1/team-radio/stats?session_key=${sessionKey}`,
  weatherBySession: (sessionKey: number) => `${API_BASE_URL}/v1/weather?session_key=${sessionKey}`,
  weatherAnalysis: (sessionKey: number) => `${API_BASE_URL}/v1/weather/analysis?session_key=${sessionKey}`,
  tireStrategy: (sessionKey: number) => `${API_BASE_URL}/v1/weather/tire-strategy?session_key=${sessionKey}`,
  
  // WebSocket (Socket.IO)
  websocket: WS_BASE_URL
};