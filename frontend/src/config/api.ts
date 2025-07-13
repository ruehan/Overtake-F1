// API 설정
const getBaseUrls = () => {
  const isHttps = window.location.protocol === 'https:';
  const host = window.location.host;
  
  // 로컬 개발환경인지 확인
  const isLocal = host.includes('localhost') || host.includes('127.0.0.1');
  
  if (isLocal) {
    return {
      apiUrl: 'http://localhost:8000',
      wsUrl: 'ws://localhost:8000'
    };
  } else {
    // 프로덕션 환경에서는 Nginx를 통해 프록시되므로 상대 경로 사용
    return {
      apiUrl: '',  // 상대 경로로 설정하여 현재 도메인 사용
      wsUrl: `${isHttps ? 'wss:' : 'ws:'}//${host}`
    };
  }
};

const { apiUrl, wsUrl } = getBaseUrls();

export const API_BASE_URL = process.env.REACT_APP_API_URL || apiUrl;
export const WS_BASE_URL = process.env.REACT_APP_WS_URL || wsUrl;

export const API_ENDPOINTS = {
  // Driver endpoints
  drivers: `${API_BASE_URL}/api/v1/drivers`,
  driverStandings: (year: number) => `${API_BASE_URL}/api/v1/driver-standings?year=${year}`,
  
  // Constructor endpoints
  constructorStandings: (year: number) => `${API_BASE_URL}/api/v1/constructor-standings?year=${year}`,
  
  // Calendar endpoints
  calendar: (year: number) => `${API_BASE_URL}/api/v1/calendar?year=${year}`,
  nextRace: `${API_BASE_URL}/api/v1/calendar/next`,
  currentRace: `${API_BASE_URL}/api/v1/calendar/current`,
  
  // Race results
  raceResults: (year: number) => `${API_BASE_URL}/api/v1/race-results?year=${year}`,
  latestResult: `${API_BASE_URL}/api/v1/race-results/latest`,
  
  // Statistics
  statistics: (year: number, type: string) => `${API_BASE_URL}/api/v1/statistics?year=${year}&type=${type}`,
  standingsProgression: (year: number) => `${API_BASE_URL}/api/v1/standings-progression?year=${year}`,
  
  // Race weekends
  raceWeekends: (year: number) => `${API_BASE_URL}/api/v1/race-weekends?year=${year}`,
  
  // Live data
  liveTiming: `${API_BASE_URL}/api/v1/live-timing`,
  weather: `${API_BASE_URL}/api/v1/weather`,
  
  // WebSocket
  websocket: `${WS_BASE_URL}/ws`
};