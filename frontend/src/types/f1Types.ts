export interface Driver {
  driver_number: number;
  name: string;
  abbreviation: string;
  team_name: string;
  team_colour: string;
  headshot_url?: string;
  country_code?: string;
}

export interface Team {
  team_name: string;
  team_colour: string;
  drivers: Array<{
    driver_number: number;
    name: string;
    abbreviation: string;
  }>;
  logo_url?: string;
}

export interface Position {
  timestamp: number;
  session_key: number;
  driver_number: number;
  position?: number;
  x_position: number;
  y_position: number;
  z_position: number;
  speed?: number;
  drs?: boolean;
}

export interface Session {
  session_key: number;
  session_name: string;
  session_type: SessionType;
  country: string;
  circuit: string;
  date: string;
  status?: string;
  year?: number;
}

export enum SessionType {
  PRACTICE_1 = "Practice 1",
  PRACTICE_2 = "Practice 2", 
  PRACTICE_3 = "Practice 3",
  QUALIFYING = "Qualifying",
  SPRINT_QUALIFYING = "Sprint Qualifying",
  SPRINT = "Sprint",
  RACE = "Race"
}

export interface Weather {
  timestamp: number;
  session_key: number;
  air_temperature: number;
  track_temperature: number;
  humidity: number;
  wind_speed: number;
  wind_direction?: number;
  pressure: number;
  rainfall?: number;
}

export interface LapTime {
  driver_number: number;
  session_key: number;
  lap_number: number;
  lap_time: number;
  sector_1?: number;
  sector_2?: number;
  sector_3?: number;
  is_personal_best?: boolean;
  timestamp: number;
}

export interface PitStop {
  driver_number: number;
  session_key: number;
  pit_duration: number;
  lap_number: number;
  timestamp: number;
}

export interface TeamRadio {
  id: string;
  driver_number: number;
  driver_name: string;
  team_name: string;
  timestamp: number;
  audio_url: string;
  transcript?: string;
  duration?: number;
}

// Response types
export interface DriversResponse {
  drivers: Driver[];
  total: number;
  session_key?: number;
}

export interface PositionsResponse {
  positions: Position[];
  total: number;
  session_key: number;
}

export interface WeatherResponse {
  weather_data: Weather[];
  latest?: Weather;
  session_key: number;
}

export interface LapTimesResponse {
  lap_times: LapTime[];
  total: number;
  session_key: number;
  driver_number?: number;
}