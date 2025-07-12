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
}

export interface Position {
  timestamp: number;
  session_key: number;
  driver_number: number;
  position: number;
  x_position: number;
  y_position: number;
  z_position: number;
  speed: number;
  drs: boolean;
}

export interface Session {
  session_key: number;
  session_name: string;
  session_type: string;
  country: string;
  circuit: string;
  date: string;
  status?: string;
}

export interface Weather {
  timestamp: number;
  air_temperature: number;
  track_temperature: number;
  humidity: number;
  wind_speed: number;
  wind_direction: number;
  pressure: number;
  rainfall?: number;
}

export interface LapTime {
  driver_number: number;
  lap_number: number;
  lap_time: number;
  sector_1: number;
  sector_2: number;
  sector_3: number;
  is_personal_best?: boolean;
  timestamp: number;
}

export interface PitStop {
  driver_number: number;
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
}