import json
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from pathlib import Path
import os

from app.services.openf1_client import openf1_client
from app.core.exceptions import OpenF1APIException

class StandingsCalculator:
    def __init__(self):
        # Data storage path
        self.data_dir = Path("data/standings")
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # F1 2024 points system
        self.points_system = {
            1: 25, 2: 18, 3: 15, 4: 12, 5: 10,
            6: 8, 7: 6, 8: 4, 9: 2, 10: 1
        }
        
        # Updated F1 driver database - Accurate as of 2024/2025 seasons
        # NOTE: OpenF1 API may contain test/simulation data - this affects accuracy
        self.driver_database = {
            # 2024 Actual F1 Grid
            1: {"name": "Max Verstappen", "team": "Red Bull Racing", "color": "#0600ef", "active_2024": True, "active_2025": True},
            11: {"name": "Sergio Perez", "team": "Red Bull Racing", "color": "#0600ef", "active_2024": True, "active_2025": False},  # Replaced mid-2024
            
            # Mercedes 2024/2025 - Hamilton to Ferrari in 2025
            44: {"name": "Lewis Hamilton", "team": "Mercedes", "color": "#00d2be", "active_2024": True, "active_2025": False},  # To Ferrari 2025
            63: {"name": "George Russell", "team": "Mercedes", "color": "#00d2be", "active_2024": True, "active_2025": True},
            
            # Ferrari 2024/2025 - Hamilton joins in 2025
            16: {"name": "Charles Leclerc", "team": "Ferrari", "color": "#dc0000", "active_2024": True, "active_2025": True},
            55: {"name": "Carlos Sainz Jr", "team": "Ferrari", "color": "#dc0000", "active_2024": True, "active_2025": False},  # To Williams 2025
            
            # McLaren - Stable lineup
            4: {"name": "Lando Norris", "team": "McLaren", "color": "#ff8700", "active_2024": True, "active_2025": True},
            81: {"name": "Oscar Piastri", "team": "McLaren", "color": "#ff8700", "active_2024": True, "active_2025": True},
            
            # Aston Martin - Stable lineup
            14: {"name": "Fernando Alonso", "team": "Aston Martin", "color": "#006f62", "active_2024": True, "active_2025": True},
            18: {"name": "Lance Stroll", "team": "Aston Martin", "color": "#006f62", "active_2024": True, "active_2025": True},
            
            # Alpine/Renault - Driver changes
            10: {"name": "Pierre Gasly", "team": "Alpine", "color": "#0090ff", "active_2024": True, "active_2025": True},
            31: {"name": "Esteban Ocon", "team": "Alpine", "color": "#0090ff", "active_2024": True, "active_2025": False},  # To Haas 2025
            
            # Williams - Multiple driver changes 2024
            23: {"name": "Alexander Albon", "team": "Williams", "color": "#005aff", "active_2024": True, "active_2025": True},
            2: {"name": "Logan Sargeant", "team": "Williams", "color": "#005aff", "active_2024": True, "active_2025": False},  # Dropped mid-2024
            39: {"name": "Franco Colapinto", "team": "Williams", "color": "#005aff", "active_2024": True, "active_2025": False},  # Mid-2024 replacement
            
            # Kick Sauber/Stake - Team changes
            77: {"name": "Valtteri Bottas", "team": "Kick Sauber", "color": "#52c41a", "active_2024": True, "active_2025": False},
            24: {"name": "Zhou Guanyu", "team": "Kick Sauber", "color": "#52c41a", "active_2024": True, "active_2025": False},
            
            # RB/VCARB - Driver rotations
            22: {"name": "Yuki Tsunoda", "team": "RB", "color": "#2b4562", "active_2024": True, "active_2025": True},
            3: {"name": "Daniel Ricciardo", "team": "RB", "color": "#2b4562", "active_2024": True, "active_2025": False},  # Dropped 2024
            40: {"name": "Liam Lawson", "team": "RB", "color": "#2b4562", "active_2024": True, "active_2025": True},  # Promoted 2024
            
            # Haas - Stable then changes
            27: {"name": "Nico Hulkenberg", "team": "Haas", "color": "#b6babd", "active_2024": True, "active_2025": False},  # To Kick Sauber 2025
            20: {"name": "Kevin Magnussen", "team": "Haas", "color": "#b6babd", "active_2024": True, "active_2025": True},
            
            # 2025 New Entries/Rookies
            87: {"name": "Andrea Kimi Antonelli", "team": "Mercedes", "color": "#00d2be", "active_2024": False, "active_2025": True},  # 2025 rookie
            43: {"name": "Gabriel Bortoleto", "team": "Kick Sauber", "color": "#52c41a", "active_2024": False, "active_2025": True},  # 2025 F2 graduate
            50: {"name": "Jack Doohan", "team": "Alpine", "color": "#0090ff", "active_2024": False, "active_2025": True},  # 2025 Alpine
            
            # Test/Reserve drivers that appear in data
            38: {"name": "Oliver Bearman", "team": "Ferrari", "color": "#dc0000", "active_2024": False, "active_2025": False},  # Reserve/F2
            30: {"name": "Isack Hadjar", "team": "RB", "color": "#2b4562", "active_2024": False, "active_2025": False},  # Reserve
            12: {"name": "Felipe Drugovich", "team": "Aston Martin", "color": "#006f62", "active_2024": False, "active_2025": False},  # Reserve
            
            # Historical/Former drivers (shouldn't be in current standings)
            5: {"name": "Sebastian Vettel", "team": "Retired", "color": "#666666", "active_2024": False, "active_2025": False},
            7: {"name": "Kimi Raikkonen", "team": "Retired", "color": "#666666", "active_2024": False, "active_2025": False},
            9: {"name": "Nikita Mazepin", "team": "Former Haas", "color": "#666666", "active_2024": False, "active_2025": False},
            6: {"name": "Nicholas Latifi", "team": "Former Williams", "color": "#666666", "active_2024": False, "active_2025": False},
        }
        
        self.team_colors = {
            "Red Bull Racing": "#0600ef",
            "Mercedes": "#00d2be", 
            "Ferrari": "#dc0000",
            "McLaren": "#ff8700",
            "Aston Martin": "#006f62",
            "Kick Sauber": "#52c41a",
            "RB": "#2b4562",
            "Alpine": "#0090ff",
            "Williams": "#005aff",
            "Haas": "#ffffff",
            # Legacy names for compatibility
            "Alfa Romeo": "#900000",
            "AlphaTauri": "#2b4562"
        }

    def get_driver_info(self, driver_number: int, year: int = None) -> Dict[str, Any]:
        """Get driver info with fallback for unknown drivers and year validation"""
        driver_info = self.driver_database.get(driver_number)
        if not driver_info:
            print(f"Warning: Unknown driver #{driver_number} in OpenF1 data")
            return {
                "name": f"Unknown Driver #{driver_number}",
                "team": "Unknown Team",
                "color": "#666666",
                "data_warning": f"Driver #{driver_number} not in official F1 database"
            }
        
        # Check if driver was active in the specified year
        if year:
            active_key = f"active_{year}"
            if active_key in driver_info and not driver_info[active_key]:
                print(f"Warning: Driver {driver_info['name']} was not active in {year}")
                driver_info = driver_info.copy()
                driver_info["data_warning"] = f"Driver was not active in official F1 {year} season"
        
        return driver_info
    
    def is_valid_race_session(self, session_info: Dict[str, Any]) -> bool:
        """Validate if session is likely a real F1 race (not test/practice)"""
        session_name = session_info.get("session_name", "").lower()
        location = session_info.get("location", "").lower()
        
        # Filter out test sessions, sprints, and practice
        invalid_sessions = [
            "test", "testing", "practice", "fp1", "fp2", "fp3", 
            "qualifying", "sprint", "pre-season"
        ]
        
        # Check if session name indicates it's not a main race
        for invalid in invalid_sessions:
            if invalid in session_name:
                return False
        
        # Allow only main race sessions
        valid_sessions = ["race", "grand prix", "gp"]
        return any(valid in session_name for valid in valid_sessions)
    
    def filter_suspicious_results(self, race_results: List[Dict[str, Any]], year: int) -> List[Dict[str, Any]]:
        """Filter out suspicious results that don't match real F1 patterns"""
        if not race_results:
            return race_results
        
        filtered_results = []
        warnings = []
        
        for result in race_results:
            driver_num = result.get("driver_number")
            driver_info = self.get_driver_info(driver_num, year)
            
            # Check if driver was supposed to be active in this year
            active_key = f"active_{year}"
            if active_key in self.driver_database.get(driver_num, {}) and not self.driver_database[driver_num][active_key]:
                warnings.append(f"Excluded {driver_info['name']} - not active in {year}")
                continue
            
            # Check for suspicious point totals (too high for realistic race)
            if result.get("points", 0) > 25:
                warnings.append(f"Suspicious points for {driver_info['name']}: {result.get('points')}")
                continue
                
            filtered_results.append(result)
        
        if warnings:
            print(f"Data filtering warnings: {warnings}")
        
        return filtered_results

    async def get_race_sessions_for_year(self, year: int) -> List[Dict[str, Any]]:
        """Get all race sessions for a specific year, filtered for valid F1 races"""
        try:
            sessions = await openf1_client.get_sessions(year=year, session_type="Race")
            
            # Filter for valid race sessions only
            valid_sessions = []
            for session in sessions:
                if self.is_valid_race_session(session):
                    valid_sessions.append(session)
                else:
                    print(f"Filtered out session: {session.get('session_name', 'Unknown')} at {session.get('location', 'Unknown')}")
            
            # Sort by date
            print(f"Found {len(valid_sessions)} valid race sessions out of {len(sessions)} total sessions for {year}")
            return sorted(valid_sessions, key=lambda x: x.get("date_start", ""))
        except Exception as e:
            print(f"Error getting sessions for {year}: {e}")
            return []

    async def calculate_race_results(self, session_key: int, year: int = None) -> Optional[Dict[str, Any]]:
        """Calculate results for a single race session with improved validation"""
        try:
            # Get session info
            sessions = await openf1_client.get_sessions()
            session_info = next((s for s in sessions if s.get("session_key") == session_key), None)
            
            if not session_info:
                return None

            # Validate if this is a real race session
            if not self.is_valid_race_session(session_info):
                print(f"Skipping non-race session: {session_info.get('session_name', 'Unknown')}")
                return None

            # Get positions for this race
            positions = await openf1_client.get_positions(session_key=session_key)
            
            if not positions:
                return None

            # Find final positions (latest timestamp for each driver)
            final_positions = {}
            for pos in positions:
                driver_num = pos.get("driver_number")
                timestamp = pos.get("date", "")
                position = pos.get("position")
                
                # Only include valid positions (1-20 typical F1 grid)
                if driver_num and timestamp and position and 1 <= position <= 25:
                    if driver_num not in final_positions or timestamp > final_positions[driver_num]["timestamp"]:
                        final_positions[driver_num] = {
                            "position": position,
                            "timestamp": timestamp
                        }

            # Create race results
            race_results = []
            for driver_num, pos_data in final_positions.items():
                driver_info = self.get_driver_info(driver_num, year)
                position = pos_data["position"]
                points = self.points_system.get(position, 0) if position else 0
                
                race_results.append({
                    "driver_number": driver_num,
                    "driver_name": driver_info["name"],
                    "team_name": driver_info["team"],
                    "position": position,
                    "points": points,
                    "team_color": driver_info["color"],
                    "data_warning": driver_info.get("data_warning")
                })

            # Filter suspicious results
            if year:
                race_results = self.filter_suspicious_results(race_results, year)

            # Sort by position
            race_results.sort(key=lambda x: x["position"] if x["position"] else 999)

            return {
                "session_key": session_key,
                "location": session_info.get("location", "Unknown"),
                "date": session_info.get("date_start", ""),
                "session_name": session_info.get("session_name", "Race"),
                "results": race_results,
                "validation_warnings": len([r for r in race_results if r.get("data_warning")])
            }

        except Exception as e:
            print(f"Error calculating race results for session {session_key}: {e}")
            return None

    async def calculate_year_standings(self, year: int) -> Dict[str, Any]:
        """Calculate complete standings for a year"""
        print(f"Calculating standings for {year}...")
        
        # Get all race sessions for the year
        race_sessions = await self.get_race_sessions_for_year(year)
        print(f"Found {len(race_sessions)} race sessions for {year}")
        
        # Calculate results for each race
        all_race_results = []
        driver_stats = {}
        sessions_processed = []
        
        for session in race_sessions[:15]:  # Limit to prevent timeout
            session_key = session.get("session_key")
            if not session_key:
                continue
                
            print(f"Processing session {session_key} - {session.get('location', 'Unknown')}")
            race_result = await self.calculate_race_results(session_key, year)
            
            if not race_result:
                continue
                
            all_race_results.append(race_result)
            sessions_processed.append(session_key)
            
            # Accumulate driver stats
            for result in race_result["results"]:
                driver_num = result["driver_number"]
                if driver_num not in driver_stats:
                    driver_stats[driver_num] = {
                        "driver_name": result["driver_name"],
                        "team_name": result["team_name"],
                        "team_color": result["team_color"],
                        "points": 0,
                        "wins": 0,
                        "podiums": 0,
                        "races_completed": 0
                    }
                
                stats = driver_stats[driver_num]
                stats["points"] += result["points"]
                stats["races_completed"] += 1
                
                if result["position"] == 1:
                    stats["wins"] += 1
                if result["position"] and result["position"] <= 3:
                    stats["podiums"] += 1

        # Create driver standings
        driver_standings = []
        for driver_num, stats in driver_stats.items():
            driver_standings.append({
                "position": 0,  # Will be set after sorting
                "driver_number": driver_num,
                "driver_name": stats["driver_name"],
                "team_name": stats["team_name"],
                "points": stats["points"],
                "wins": stats["wins"],
                "podiums": stats["podiums"],
                "races_completed": stats["races_completed"],
                "team_color": stats["team_color"]
            })

        # Sort by points and assign positions
        driver_standings.sort(key=lambda x: x["points"], reverse=True)
        for i, standing in enumerate(driver_standings):
            standing["position"] = i + 1

        # Create constructor standings
        team_stats = {}
        for driver in driver_standings:
            team = driver["team_name"]
            if team not in team_stats:
                team_stats[team] = {
                    "points": 0,
                    "wins": 0,
                    "podiums": 0,
                    "drivers": [],
                    "team_color": driver["team_color"]
                }
            
            team_stats[team]["points"] += driver["points"]
            team_stats[team]["wins"] += driver["wins"]
            team_stats[team]["podiums"] += driver["podiums"]
            team_stats[team]["drivers"].append({
                "driver_number": driver["driver_number"],
                "driver_name": driver["driver_name"],
                "points": driver["points"],
                "position": driver["position"]
            })

        constructor_standings = []
        for team, stats in team_stats.items():
            constructor_standings.append({
                "position": 0,  # Will be set after sorting
                "team_name": team,
                "points": stats["points"],
                "wins": stats["wins"],
                "podiums": stats["podiums"],
                "drivers": stats["drivers"],
                "team_color": stats["team_color"]
            })

        # Sort constructor standings by points
        constructor_standings.sort(key=lambda x: x["points"], reverse=True)
        for i, standing in enumerate(constructor_standings):
            standing["position"] = i + 1

        return {
            "year": year,
            "last_updated": datetime.utcnow().isoformat(),
            "total_races": len(all_race_results),
            "sessions_processed": sessions_processed,
            "driver_standings": driver_standings,
            "constructor_standings": constructor_standings,
            "race_results": all_race_results,
            "metadata": {
                "calculation_date": datetime.utcnow().isoformat(),
                "data_source": "OpenF1 API",
                "data_warning": "⚠️ IMPORTANT: This data may not reflect actual F1 championship standings. OpenF1 API may contain test/simulation data.",
                "accuracy_issues": [
                    "Some drivers may show incorrect team assignments",
                    "Points may not match official F1 standings",
                    "Data may include test sessions or simulations",
                    "Driver lineup changes during season may not be accurate",
                    "Historical data might be incomplete or incorrect"
                ],
                "validation_applied": {
                    "session_filtering": "Only Race sessions included",
                    "driver_validation": "Active drivers checked by year",
                    "position_validation": "Positions limited to 1-25",
                    "points_validation": "Points capped at 25 per race"
                },
                "points_system": self.points_system,
                "total_drivers": len(driver_standings),
                "total_teams": len(constructor_standings),
                "sessions_analyzed": len(all_race_results),
                "total_warnings": sum(r.get("validation_warnings", 0) for r in all_race_results),
                "data_accuracy": "🔍 For reference only - NOT official F1 championship data",
                "recommendation": "Use official F1 sources for accurate championship standings"
            }
        }

    def save_standings_data(self, year: int, data: Dict[str, Any]) -> None:
        """Save standings data to JSON file"""
        file_path = self.data_dir / f"standings_{year}.json"
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print(f"Saved standings data for {year} to {file_path}")
        except Exception as e:
            print(f"Error saving data for {year}: {e}")

    def load_standings_data(self, year: int) -> Optional[Dict[str, Any]]:
        """Load standings data from JSON file"""
        file_path = self.data_dir / f"standings_{year}.json"
        try:
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Error loading data for {year}: {e}")
        return None

    def is_data_stale(self, year: int, max_age_hours: int = 24) -> bool:
        """Check if cached data is older than max_age_hours"""
        data = self.load_standings_data(year)
        if not data:
            return True
            
        try:
            last_updated = datetime.fromisoformat(data["last_updated"].replace("Z", "+00:00"))
            age = datetime.utcnow() - last_updated.replace(tzinfo=None)
            return age > timedelta(hours=max_age_hours)
        except:
            return True

    async def update_year_if_needed(self, year: int, force: bool = False) -> Dict[str, Any]:
        """Update standings for a year if data is stale or force is True"""
        if not force and not self.is_data_stale(year):
            print(f"Data for {year} is fresh, loading from cache")
            return self.load_standings_data(year)
        
        print(f"Updating standings data for {year}")
        standings_data = await self.calculate_year_standings(year)
        self.save_standings_data(year, standings_data)
        return standings_data

    async def batch_update_all_years(self, years: List[int] = None, force: bool = False) -> Dict[str, Any]:
        """Update standings for multiple years"""
        if years is None:
            years = [2021, 2022, 2023, 2024, 2025]
        
        results = {}
        for year in years:
            try:
                print(f"\n=== Updating {year} ===")
                data = await self.update_year_if_needed(year, force=force)
                results[year] = {
                    "success": True,
                    "races": data.get("total_races", 0),
                    "last_updated": data.get("last_updated", ""),
                    "drivers": len(data.get("driver_standings", [])),
                    "teams": len(data.get("constructor_standings", []))
                }
            except Exception as e:
                print(f"Error updating {year}: {e}")
                results[year] = {
                    "success": False,
                    "error": str(e)
                }
        
        return results

# Global instance
standings_calculator = StandingsCalculator()