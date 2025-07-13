from fastapi import APIRouter, Query, HTTPException, BackgroundTasks
from typing import Optional, List, Dict, Any

from app.services.standings_calculator import standings_calculator

router = APIRouter()

@router.get("/drivers", response_model=List[Dict[str, Any]])
async def get_cached_driver_standings(
    year: int = Query(2025, description="Championship year", ge=2020, le=2030)
):
    """Get driver standings from cached data (updated daily)"""
    try:
        data = await standings_calculator.update_year_if_needed(year)
        
        if not data:
            raise HTTPException(status_code=404, detail=f"No standings data available for {year}")
        
        return data.get("driver_standings", [])
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/constructors", response_model=List[Dict[str, Any]])
async def get_cached_constructor_standings(
    year: int = Query(2025, description="Championship year", ge=2020, le=2030)
):
    """Get constructor standings from cached data (updated daily)"""
    try:
        data = await standings_calculator.update_year_if_needed(year)
        
        if not data:
            raise HTTPException(status_code=404, detail=f"No standings data available for {year}")
        
        return data.get("constructor_standings", [])
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/analysis", response_model=Dict[str, Any])
async def get_cached_standings_analysis(
    year: int = Query(2025, description="Championship year", ge=2020, le=2030)
):
    """Get comprehensive standings analysis from cached data"""
    try:
        data = await standings_calculator.update_year_if_needed(year)
        
        if not data:
            raise HTTPException(status_code=404, detail=f"No standings data available for {year}")
        
        driver_standings = data.get("driver_standings", [])
        constructor_standings = data.get("constructor_standings", [])
        
        # Calculate championship gaps
        driver_gap = 0
        constructor_gap = 0
        
        if len(driver_standings) >= 2:
            driver_gap = driver_standings[0]["points"] - driver_standings[1]["points"]
        
        if len(constructor_standings) >= 2:
            constructor_gap = constructor_standings[0]["points"] - constructor_standings[1]["points"]
        
        # Estimate races remaining (rough calculation)
        total_races = data.get("total_races", 0)
        estimated_season_races = 24  # Typical F1 season
        races_remaining = max(0, estimated_season_races - total_races)
        
        return {
            "timestamp": data.get("last_updated"),
            "year": year,
            "total_races_completed": total_races,
            "driver_standings": driver_standings[:10],  # Top 10
            "constructor_standings": constructor_standings[:10],  # Top 10
            "championship_analysis": {
                "driver_championship_leader": driver_standings[0]["driver_name"] if driver_standings else None,
                "driver_championship_gap": driver_gap,
                "constructor_championship_leader": constructor_standings[0]["team_name"] if constructor_standings else None,
                "constructor_championship_gap": constructor_gap,
                "races_remaining": races_remaining,
                "points_available": races_remaining * 25  # Max points per race
            },
            "metadata": data.get("metadata", {}),
            "cache_info": {
                "last_updated": data.get("last_updated"),
                "sessions_processed": len(data.get("sessions_processed", [])),
                "data_freshness": "Updated daily",
                "total_drivers": len(driver_standings),
                "total_teams": len(constructor_standings)
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/race-results/{year}", response_model=List[Dict[str, Any]])
async def get_cached_race_results(
    year: int,
    limit: Optional[int] = Query(None, description="Limit number of races returned")
):
    """Get all race results for a year from cached data"""
    try:
        data = await standings_calculator.update_year_if_needed(year)
        
        if not data:
            raise HTTPException(status_code=404, detail=f"No race results available for {year}")
        
        race_results = data.get("race_results", [])
        
        if limit:
            race_results = race_results[:limit]
        
        return race_results
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/refresh/{year}")
async def refresh_standings_data(
    year: int,
    background_tasks: BackgroundTasks,
    force: bool = Query(False, description="Force refresh even if data is fresh")
):
    """Manually refresh standings data for a specific year"""
    try:
        # Add background task to refresh data
        background_tasks.add_task(
            standings_calculator.update_year_if_needed,
            year,
            force=force
        )
        
        return {
            "message": f"Refresh task started for {year}",
            "year": year,
            "force": force,
            "status": "processing"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/refresh/all")
async def refresh_all_standings_data(
    background_tasks: BackgroundTasks,
    years: Optional[str] = Query(None, description="Comma-separated years (e.g., '2024,2025')"),
    force: bool = Query(False, description="Force refresh even if data is fresh")
):
    """Manually refresh standings data for all years or specified years"""
    try:
        if years:
            year_list = [int(y.strip()) for y in years.split(",")]
        else:
            year_list = [2021, 2022, 2023, 2024, 2025]
        
        # Add background task to refresh all data
        background_tasks.add_task(
            standings_calculator.batch_update_all_years,
            years=year_list,
            force=force
        )
        
        return {
            "message": f"Batch refresh task started",
            "years": year_list,
            "force": force,
            "status": "processing"
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/cache-status")
async def get_cache_status():
    """Get cache status for all years"""
    try:
        status = {}
        years = [2021, 2022, 2023, 2024, 2025]
        
        for year in years:
            data = standings_calculator.load_standings_data(year)
            if data:
                status[year] = {
                    "cached": True,
                    "last_updated": data.get("last_updated"),
                    "total_races": data.get("total_races", 0),
                    "is_stale": standings_calculator.is_data_stale(year),
                    "drivers": len(data.get("driver_standings", [])),
                    "teams": len(data.get("constructor_standings", [])),
                    "sessions_processed": len(data.get("sessions_processed", []))
                }
            else:
                status[year] = {
                    "cached": False,
                    "last_updated": None,
                    "is_stale": True,
                    "total_races": 0,
                    "drivers": 0,
                    "teams": 0
                }
        
        return {
            "cache_status": status,
            "data_directory": str(standings_calculator.data_dir),
            "cache_max_age_hours": 24,
            "system_info": {
                "total_cached_years": len([y for y in status.values() if y["cached"]]),
                "stale_years": len([y for y in status.values() if y["is_stale"]])
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))