from fastapi import APIRouter, Query, HTTPException
from typing import Optional, List, Dict, Any
import logging

router = APIRouter(prefix="/api/v1/teams", tags=["teams"])
logger = logging.getLogger(__name__)

# 서비스 초기화를 위한 변수
livef1_service = None

def init_service(service):
    global livef1_service
    livef1_service = service

@router.get("", response_model=List[Dict[str, Any]])
async def get_teams(
    year: Optional[int] = Query(2025, description="Year to get teams for")
):
    """Get teams for a specific year"""
    try:
        # 정적 팀 데이터 반환 (2025년 기준)
        teams_data = [
            {"id": 1, "name": "Red Bull Racing", "constructor": "Red Bull", "color": "#3671C6"},
            {"id": 2, "name": "Mercedes", "constructor": "Mercedes", "color": "#27F4D2"},
            {"id": 3, "name": "Ferrari", "constructor": "Ferrari", "color": "#E8002D"},
            {"id": 4, "name": "McLaren", "constructor": "McLaren", "color": "#FF8000"},
            {"id": 5, "name": "Aston Martin", "constructor": "Aston Martin", "color": "#229971"},
            {"id": 6, "name": "Alpine", "constructor": "Alpine", "color": "#0093CC"},
            {"id": 7, "name": "Williams", "constructor": "Williams", "color": "#64C4FF"},
            {"id": 8, "name": "RB", "constructor": "RB", "color": "#6692FF"},
            {"id": 9, "name": "Kick Sauber", "constructor": "Sauber", "color": "#52E252"},
            {"id": 10, "name": "Haas", "constructor": "Haas", "color": "#B6BABD"}
        ]
        
        logger.info(f"📊 Returning {len(teams_data)} teams for year {year}")
        return teams_data
        
    except Exception as e:
        logger.error(f"❌ Error getting teams: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) 