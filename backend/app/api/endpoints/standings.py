from fastapi import APIRouter, Query, HTTPException, BackgroundTasks
from typing import Optional, List, Dict, Any

from app.services.standings_service import standings_service
from app.services.standings_calculator import standings_calculator
from app.core.exceptions import OpenF1APIException

router = APIRouter()

@router.get("/drivers", response_model=List[Dict[str, Any]])
async def get_driver_standings(
    year: int = Query(2024, description="Championship year", ge=2020, le=2030)
):
    """Get current driver championship standings"""
    try:
        standings = await standings_service.calculate_driver_standings(year)
        
        return [
            {
                "position": standing.position,
                "driver_number": standing.driver_number,
                "driver_name": standing.driver_name,
                "team_name": standing.team_name,
                "points": standing.points,
                "wins": standing.wins,
                "podiums": standing.podiums,
                "fastest_laps": standing.fastest_laps,
                "races_completed": standing.races_completed,
                "team_color": standing.team_color
            }
            for standing in standings
        ]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/constructors", response_model=List[Dict[str, Any]])
async def get_constructor_standings(
    year: int = Query(2024, description="Championship year", ge=2020, le=2030)
):
    """Get current constructor championship standings"""
    try:
        standings = await standings_service.calculate_constructor_standings(year)
        
        return [
            {
                "position": standing.position,
                "team_name": standing.team_name,
                "points": standing.points,
                "wins": standing.wins,
                "podiums": standing.podiums,
                "drivers": standing.drivers,
                "team_color": standing.team_color
            }
            for standing in standings
        ]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/analysis", response_model=Dict[str, Any])
async def get_standings_analysis(
    year: int = Query(2024, description="Championship year", ge=2020, le=2030)
):
    """Get comprehensive championship standings analysis"""
    try:
        analysis = await standings_service.get_standings_analysis(year)
        
        if "error" in analysis:
            raise HTTPException(status_code=500, detail=analysis["error"])
        
        return analysis
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/race-results/{session_key}", response_model=Dict[str, Any])
async def get_race_result(session_key: int):
    """Get detailed race results for a specific session"""
    try:
        result = await standings_service.get_race_results(session_key)
        
        if not result:
            raise HTTPException(status_code=404, detail="Race results not found")
        
        return {
            "session_key": result.session_key,
            "location": result.location,
            "date": result.date.isoformat(),
            "driver_results": result.driver_results
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/championship-battle", response_model=Dict[str, Any])
async def get_championship_battle(
    year: int = Query(2024, description="Championship year", ge=2020, le=2030),
    top_n: int = Query(5, description="Number of top drivers/teams to analyze", ge=2, le=10)
):
    """Get championship battle analysis between top drivers and constructors"""
    try:
        analysis = await standings_service.get_standings_analysis(year)
        
        if "error" in analysis:
            raise HTTPException(status_code=500, detail=analysis["error"])
        
        # Extract top N drivers and constructors
        top_drivers = analysis["driver_standings"][:top_n]
        top_constructors = analysis["constructor_standings"][:top_n]
        
        # Calculate gaps and battle metrics
        driver_gaps = []
        for i in range(1, len(top_drivers)):
            gap = top_drivers[0]["points"] - top_drivers[i]["points"]
            driver_gaps.append({
                "position": i + 1,
                "driver_name": top_drivers[i]["driver_name"],
                "gap_to_leader": gap,
                "mathematically_possible": gap <= analysis["championship_analysis"]["points_available"]
            })
        
        constructor_gaps = []
        for i in range(1, len(top_constructors)):
            gap = top_constructors[0]["points"] - top_constructors[i]["points"]
            constructor_gaps.append({
                "position": i + 1,
                "team_name": top_constructors[i]["team_name"],
                "gap_to_leader": gap,
                "mathematically_possible": gap <= analysis["championship_analysis"]["points_available"]
            })
        
        return {
            "championship_leader": {
                "driver": top_drivers[0] if top_drivers else None,
                "constructor": top_constructors[0] if top_constructors else None
            },
            "driver_battle": {
                "contenders": top_drivers,
                "gaps_to_leader": driver_gaps
            },
            "constructor_battle": {
                "contenders": top_constructors,
                "gaps_to_leader": constructor_gaps
            },
            "season_info": {
                "races_completed": analysis["total_races_completed"],
                "races_remaining": analysis["championship_analysis"]["races_remaining"],
                "max_points_available": analysis["championship_analysis"]["points_available"]
            },
            "timestamp": analysis["timestamp"]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))