from typing import Dict, List, Any, Optional
from datetime import datetime
from dataclasses import dataclass
from collections import defaultdict
import asyncio

from app.services.openf1_client import openf1_client
from app.core.exceptions import OpenF1APIException

@dataclass
class DriverStanding:
    driver_number: int
    driver_name: str
    team_name: str
    points: int
    position: int
    wins: int
    podiums: int
    fastest_laps: int
    races_completed: int
    team_color: str

@dataclass
class ConstructorStanding:
    team_name: str
    points: int
    position: int
    wins: int
    podiums: int
    drivers: List[Dict[str, Any]]
    team_color: str

@dataclass
class RaceResult:
    session_key: int
    location: str
    date: datetime
    driver_results: List[Dict[str, Any]]

class StandingsService:
    def __init__(self):
        # F1 2024 points system
        self.points_system = {
            1: 25, 2: 18, 3: 15, 4: 12, 5: 10,
            6: 8, 7: 6, 8: 4, 9: 2, 10: 1
        }
        
        # Driver and team info (Updated for 2024-2025 seasons)
        self.driver_info = {
            # Red Bull Racing
            1: {"name": "Max Verstappen", "team": "Red Bull Racing", "color": "#0600ef"},
            11: {"name": "Sergio Perez", "team": "Red Bull Racing", "color": "#0600ef"},
            
            # Mercedes
            44: {"name": "Lewis Hamilton", "team": "Mercedes", "color": "#00d2be"},
            63: {"name": "George Russell", "team": "Mercedes", "color": "#00d2be"},
            
            # Ferrari
            16: {"name": "Charles Leclerc", "team": "Ferrari", "color": "#dc0000"},
            55: {"name": "Carlos Sainz", "team": "Ferrari", "color": "#dc0000"},
            
            # McLaren
            4: {"name": "Lando Norris", "team": "McLaren", "color": "#ff8700"},
            81: {"name": "Oscar Piastri", "team": "McLaren", "color": "#ff8700"},
            
            # Aston Martin
            14: {"name": "Fernando Alonso", "team": "Aston Martin", "color": "#006f62"},
            18: {"name": "Lance Stroll", "team": "Aston Martin", "color": "#006f62"},
            
            # Alpine
            10: {"name": "Pierre Gasly", "team": "Alpine", "color": "#0090ff"},
            31: {"name": "Esteban Ocon", "team": "Alpine", "color": "#0090ff"},
            
            # Williams
            23: {"name": "Alexander Albon", "team": "Williams", "color": "#005aff"},
            2: {"name": "Logan Sargeant", "team": "Williams", "color": "#005aff"},
            
            # Alfa Romeo/Kick Sauber
            77: {"name": "Valtteri Bottas", "team": "Kick Sauber", "color": "#52c41a"},
            24: {"name": "Zhou Guanyu", "team": "Kick Sauber", "color": "#52c41a"},
            
            # AlphaTauri/RB
            22: {"name": "Yuki Tsunoda", "team": "RB", "color": "#2b4562"},
            3: {"name": "Daniel Ricciardo", "team": "RB", "color": "#2b4562"},
            
            # Haas
            27: {"name": "Nico Hulkenberg", "team": "Haas", "color": "#ffffff"},
            20: {"name": "Kevin Magnussen", "team": "Haas", "color": "#ffffff"},
            
            # Additional drivers that might appear
            40: {"name": "Liam Lawson", "team": "RB", "color": "#2b4562"},
            38: {"name": "Oliver Bearman", "team": "Ferrari", "color": "#dc0000"},
            39: {"name": "Franco Colapinto", "team": "Williams", "color": "#005aff"},
            50: {"name": "Nyck de Vries", "team": "AlphaTauri", "color": "#2b4562"},
            21: {"name": "Nyck de Vries", "team": "AlphaTauri", "color": "#2b4562"},
            
            # 2025 season new drivers
            30: {"name": "Isack Hadjar", "team": "RB", "color": "#2b4562"},
            87: {"name": "Andrea Kimi Antonelli", "team": "Mercedes", "color": "#00d2be"},
            5: {"name": "Sebastian Vettel", "team": "Aston Martin", "color": "#006f62"},
            7: {"name": "Kimi Raikkonen", "team": "Kick Sauber", "color": "#52c41a"},
            43: {"name": "Gabriel Bortoleto", "team": "Kick Sauber", "color": "#52c41a"},
            
            # Reserve/Test drivers
            6: {"name": "Nicholas Latifi", "team": "Williams", "color": "#005aff"},
            45: {"name": "Jack Doohan", "team": "Alpine", "color": "#0090ff"},
            12: {"name": "Felipe Drugovich", "team": "Aston Martin", "color": "#006f62"},
            
            # Additional possible numbers
            15: {"name": "Patricio O'Ward", "team": "McLaren", "color": "#ff8700"},
            25: {"name": "Theo Pourchaire", "team": "Kick Sauber", "color": "#52c41a"}
        }
        
        self.team_colors = {
            "Red Bull Racing": "#0600ef",
            "Mercedes": "#00d2be", 
            "Ferrari": "#dc0000",
            "McLaren": "#ff8700",
            "Aston Martin": "#006f62",
            "Kick Sauber": "#52c41a",
            "RB": "#2b4562",
            "AlphaTauri": "#2b4562",
            "Haas": "#ffffff",
            "Williams": "#005aff",
            "Alpine": "#0090ff",
            # Legacy team names that might still appear in data
            "Alfa Romeo": "#900000",
            "Alpha Tauri": "#2b4562"
        }

    async def get_race_sessions(self, year: int = 2024) -> List[Dict[str, Any]]:
        """Get all race sessions for a given year"""
        try:
            sessions = await openf1_client.get_sessions(
                year=year,
                session_type="Race"
            )
            
            # Sort by date
            return sorted(sessions, key=lambda x: x.get("date_start", ""))
            
        except Exception as e:
            print(f"Error getting race sessions: {e}")
            return []

    async def get_race_results(self, session_key: int) -> Optional[RaceResult]:
        """Get race results for a specific session"""
        try:
            # Get session info
            sessions = await openf1_client.get_sessions()
            session_info = next((s for s in sessions if s.get("session_key") == session_key), None)
            
            if not session_info:
                return None
            
            # Get final positions for this race
            positions = await openf1_client.get_positions(session_key=session_key)
            
            if not positions:
                return None
            
            # Get the final positions (latest timestamp)
            final_positions = {}
            for pos in positions:
                driver_num = pos.get("driver_number")
                timestamp = pos.get("date", "")
                
                if driver_num and timestamp:
                    if driver_num not in final_positions or timestamp > final_positions[driver_num]["timestamp"]:
                        final_positions[driver_num] = {
                            "position": pos.get("position"),
                            "timestamp": timestamp
                        }
            
            # Convert to driver results
            driver_results = []
            for driver_num, pos_data in final_positions.items():
                driver_info = self.driver_info.get(driver_num)
                if not driver_info:
                    # Log unknown driver for debugging
                    print(f"Warning: Unknown driver number {driver_num} found in race results")
                    driver_info = {
                        "name": f"Driver #{driver_num}",
                        "team": "Unknown Team",
                        "color": "#666666"
                    }
                
                position = pos_data["position"]
                points = self.points_system.get(position, 0)
                
                driver_results.append({
                    "driver_number": driver_num,
                    "driver_name": driver_info["name"],
                    "team_name": driver_info["team"],
                    "position": position,
                    "points": points,
                    "team_color": driver_info["color"]
                })
            
            # Sort by final position
            driver_results.sort(key=lambda x: x["position"] if x["position"] else 999)
            
            return RaceResult(
                session_key=session_key,
                location=session_info.get("location", "Unknown"),
                date=datetime.fromisoformat(session_info.get("date_start", "").replace("Z", "+00:00")),
                driver_results=driver_results
            )
            
        except Exception as e:
            print(f"Error getting race results for session {session_key}: {e}")
            return None

    async def calculate_driver_standings(self, year: int = 2024) -> List[DriverStanding]:
        """Calculate current driver championship standings"""
        try:
            # Get all race sessions for the year
            race_sessions = await self.get_race_sessions(year)
            
            # Accumulate points and stats for each driver
            driver_stats = defaultdict(lambda: {
                "points": 0,
                "wins": 0,
                "podiums": 0,
                "fastest_laps": 0,
                "races_completed": 0
            })
            
            # Process each race
            for session in race_sessions[:10]:  # Limit to first 10 races to avoid timeout
                session_key = session.get("session_key")
                if not session_key:
                    continue
                    
                race_result = await self.get_race_results(session_key)
                if not race_result:
                    continue
                
                for result in race_result.driver_results:
                    driver_num = result["driver_number"]
                    position = result["position"]
                    points = result["points"]
                    
                    if driver_num and position:
                        driver_stats[driver_num]["points"] += points
                        driver_stats[driver_num]["races_completed"] += 1
                        
                        if position == 1:
                            driver_stats[driver_num]["wins"] += 1
                        if position <= 3:
                            driver_stats[driver_num]["podiums"] += 1
            
            # Create standings
            standings = []
            for driver_num, stats in driver_stats.items():
                driver_info = self.driver_info.get(driver_num)
                if not driver_info:
                    # Log unknown driver for debugging
                    print(f"Warning: Unknown driver number {driver_num} found in standings data")
                    driver_info = {
                        "name": f"Driver #{driver_num}",
                        "team": "Unknown Team",
                        "color": "#666666"
                    }
                
                standings.append(DriverStanding(
                    driver_number=driver_num,
                    driver_name=driver_info["name"],
                    team_name=driver_info["team"],
                    points=stats["points"],
                    position=0,  # Will be set after sorting
                    wins=stats["wins"],
                    podiums=stats["podiums"],
                    fastest_laps=stats["fastest_laps"],
                    races_completed=stats["races_completed"],
                    team_color=driver_info["color"]
                ))
            
            # Sort by points and assign positions
            standings.sort(key=lambda x: x.points, reverse=True)
            for i, standing in enumerate(standings):
                standing.position = i + 1
            
            return standings
            
        except Exception as e:
            print(f"Error calculating driver standings: {e}")
            return []

    async def calculate_constructor_standings(self, year: int = 2024) -> List[ConstructorStanding]:
        """Calculate current constructor championship standings"""
        try:
            driver_standings = await self.calculate_driver_standings(year)
            
            # Group by team
            team_stats = defaultdict(lambda: {
                "points": 0,
                "wins": 0,
                "podiums": 0,
                "drivers": []
            })
            
            for driver in driver_standings:
                team = driver.team_name
                team_stats[team]["points"] += driver.points
                team_stats[team]["wins"] += driver.wins
                team_stats[team]["podiums"] += driver.podiums
                team_stats[team]["drivers"].append({
                    "driver_number": driver.driver_number,
                    "driver_name": driver.driver_name,
                    "points": driver.points,
                    "position": driver.position
                })
            
            # Create constructor standings
            standings = []
            for team_name, stats in team_stats.items():
                team_color = self.team_colors.get(team_name, "#666666")
                
                standings.append(ConstructorStanding(
                    team_name=team_name,
                    points=stats["points"],
                    position=0,  # Will be set after sorting
                    wins=stats["wins"],
                    podiums=stats["podiums"],
                    drivers=stats["drivers"],
                    team_color=team_color
                ))
            
            # Sort by points and assign positions
            standings.sort(key=lambda x: x.points, reverse=True)
            for i, standing in enumerate(standings):
                standing.position = i + 1
            
            return standings
            
        except Exception as e:
            print(f"Error calculating constructor standings: {e}")
            return []

    async def get_standings_analysis(self, year: int = 2024) -> Dict[str, Any]:
        """Get comprehensive standings analysis"""
        try:
            driver_standings = await self.calculate_driver_standings(year)
            constructor_standings = await self.calculate_constructor_standings(year)
            
            # Calculate analysis metrics
            total_races = max([d.races_completed for d in driver_standings], default=0)
            
            # Championship battle analysis
            championship_gap = 0
            if len(driver_standings) >= 2:
                championship_gap = driver_standings[0].points - driver_standings[1].points
            
            constructor_gap = 0
            if len(constructor_standings) >= 2:
                constructor_gap = constructor_standings[0].points - constructor_standings[1].points
            
            return {
                "timestamp": datetime.utcnow().isoformat(),
                "year": year,
                "total_races_completed": total_races,
                "driver_standings": [
                    {
                        "position": d.position,
                        "driver_number": d.driver_number,
                        "driver_name": d.driver_name,
                        "team_name": d.team_name,
                        "points": d.points,
                        "wins": d.wins,
                        "podiums": d.podiums,
                        "races_completed": d.races_completed,
                        "team_color": d.team_color
                    }
                    for d in driver_standings[:15]  # Top 15 drivers
                ],
                "constructor_standings": [
                    {
                        "position": c.position,
                        "team_name": c.team_name,
                        "points": c.points,
                        "wins": c.wins,
                        "podiums": c.podiums,
                        "drivers": c.drivers,
                        "team_color": c.team_color
                    }
                    for c in constructor_standings[:10]  # Top 10 teams
                ],
                "championship_analysis": {
                    "driver_championship_leader": driver_standings[0].driver_name if driver_standings else None,
                    "driver_championship_gap": championship_gap,
                    "constructor_championship_leader": constructor_standings[0].team_name if constructor_standings else None,
                    "constructor_championship_gap": constructor_gap,
                    "races_remaining": max(0, 24 - total_races),  # F1 season typically has ~24 races
                    "points_available": max(0, 24 - total_races) * 25  # Max points per race
                }
            }
            
        except Exception as e:
            print(f"Error in standings analysis: {e}")
            return {"error": f"Failed to analyze standings: {str(e)}"}

# Global instance
standings_service = StandingsService()