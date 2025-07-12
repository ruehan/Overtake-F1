import axios, { AxiosInstance } from 'axios';
import { Driver, Team, Position, Session, Weather, LapTime, PitStop, TeamRadio } from '../types/f1Types';

class API {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: process.env.REACT_APP_API_URL || 'http://localhost:8000/api/v1',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Request interceptor
    this.client.interceptors.request.use(
      (config) => {
        // Add auth token if available
        const token = localStorage.getItem('authToken');
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error) => {
        return Promise.reject(error);
      }
    );

    // Response interceptor
    this.client.interceptors.response.use(
      (response) => response,
      (error) => {
        if (error.response?.status === 429) {
          console.error('Rate limit exceeded');
        }
        return Promise.reject(error);
      }
    );
  }

  // Drivers
  async getDrivers(sessionKey?: number): Promise<Driver[]> {
    const params = sessionKey ? { session_key: sessionKey } : {};
    const response = await this.client.get('/drivers', { params });
    return response.data;
  }

  async getDriver(driverNumber: number, sessionKey?: number): Promise<Driver> {
    const params = sessionKey ? { session_key: sessionKey } : {};
    const response = await this.client.get(`/drivers/${driverNumber}`, { params });
    return response.data;
  }

  // Teams
  async getTeams(sessionKey?: number): Promise<Team[]> {
    const params = sessionKey ? { session_key: sessionKey } : {};
    const response = await this.client.get('/teams', { params });
    return response.data;
  }

  // Positions
  async getPositions(sessionKey?: number, driverNumber?: number): Promise<Position[]> {
    const params: any = {};
    if (sessionKey) params.session_key = sessionKey;
    if (driverNumber) params.driver_number = driverNumber;
    const response = await this.client.get('/positions', { params });
    return response.data;
  }

  async getLatestPositions(sessionKey: number): Promise<Position[]> {
    const response = await this.client.get('/positions/latest', {
      params: { session_key: sessionKey },
    });
    return response.data;
  }

  // Sessions
  async getSessions(year?: number, country?: string, sessionType?: string): Promise<Session[]> {
    const params: any = {};
    if (year) params.year = year;
    if (country) params.country = country;
    if (sessionType) params.session_type = sessionType;
    const response = await this.client.get('/sessions', { params });
    return response.data;
  }

  async getCurrentSession(): Promise<Session> {
    const response = await this.client.get('/sessions/current');
    return response.data;
  }

  // Weather
  async getWeather(sessionKey?: number): Promise<Weather[]> {
    const params = sessionKey ? { session_key: sessionKey } : {};
    const response = await this.client.get('/weather', { params });
    return response.data;
  }

  async getCurrentWeather(sessionKey: number): Promise<Weather> {
    const response = await this.client.get('/weather/current', {
      params: { session_key: sessionKey },
    });
    return response.data;
  }
}

export default new API();