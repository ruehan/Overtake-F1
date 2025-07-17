from fastapi import APIRouter, HTTPException
from typing import Dict, Any
import logging

router = APIRouter(prefix="/api/v1/users", tags=["users"])
logger = logging.getLogger(__name__)

# 서비스 초기화를 위한 변수
livef1_service = None

def init_service(service):
    global livef1_service
    livef1_service = service

@router.get("/preferences/{user_id}")
async def get_user_preferences(user_id: str):
    """Get user preferences"""
    try:
        # 프론트엔드가 기대하는 형식에 맞춘 더미 데이터
        dummy_preferences = {
            "user_id": user_id,
            "favorite_drivers": [1, 16, 4],  # Max Verstappen, Charles Leclerc, Lando Norris
            "favorite_teams": ["Red Bull Racing", "Ferrari", "McLaren"],
            "alert_settings": {
                "race_start": True,
                "qualifying_start": True,
                "driver_podium": True,
                "team_victory": True,
                "championship_change": True
            },
            "dashboard_layout": {
                "show_driver_stats": True,
                "show_team_stats": True,
                "show_standings": True,
                "show_quick_actions": True
            },
            "theme": "monaco",
            "timezone": "Asia/Seoul",
            "language": "ko"
        }
        
        logger.info(f"📊 Returning preferences for user {user_id}")
        return {
            "preferences": dummy_preferences,
            "message": "User preferences retrieved successfully"
        }
        
    except Exception as e:
        logger.error(f"❌ Error getting user preferences: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/preferences/{user_id}")
async def update_user_preferences(user_id: str, preferences: Dict[str, Any]):
    """Update user preferences"""
    try:
        # 임시로 받은 데이터를 그대로 반환
        logger.info(f"📝 Updating preferences for user {user_id}: {preferences}")
        
        return {
            "preferences": preferences,
            "message": "User preferences updated successfully"
        }
        
    except Exception as e:
        logger.error(f"❌ Error updating user preferences: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats/{user_id}/dashboard")
async def get_user_dashboard_stats(user_id: str):
    """Get personalized dashboard statistics for user"""
    try:
        # 사용자 선호도 기반 대시보드 데이터
        dashboard_data = {
            "favorite_driver_stats": [
                {
                    "driver_name": "Max Verstappen",
                    "driver_number": 1,
                    "team_name": "Red Bull Racing",
                    "points": 575,
                    "wins": 19,
                    "podiums": 21,
                    "pole_positions": 8,
                    "fastest_laps": 5,
                    "races_entered": 22,
                    "championship_position": 1,
                    "last_result": "1st",
                    "avg_position": 1.2
                },
                {
                    "driver_name": "Charles Leclerc",
                    "driver_number": 16,
                    "team_name": "Ferrari",
                    "points": 356,
                    "wins": 3,
                    "podiums": 12,
                    "pole_positions": 7,
                    "fastest_laps": 3,
                    "races_entered": 22,
                    "championship_position": 3,
                    "last_result": "2nd",
                    "avg_position": 4.1
                },
                {
                    "driver_name": "Lando Norris",
                    "driver_number": 4,
                    "team_name": "McLaren",
                    "points": 374,
                    "wins": 4,
                    "podiums": 15,
                    "pole_positions": 5,
                    "fastest_laps": 2,
                    "races_entered": 22,
                    "championship_position": 2,
                    "last_result": "3rd",
                    "avg_position": 3.8
                }
            ],
            "favorite_team_stats": [
                {
                    "team_name": "Red Bull Racing",
                    "points": 589,
                    "wins": 19,
                    "podiums": 33,
                    "pole_positions": 9,
                    "fastest_laps": 7,
                    "drivers_count": 2,
                    "championship_position": 1,
                    "avg_position": 2.1
                },
                {
                    "team_name": "Ferrari",
                    "points": 407,
                    "wins": 5,
                    "podiums": 24,
                    "pole_positions": 9,
                    "fastest_laps": 5,
                    "drivers_count": 2,
                    "championship_position": 3,
                    "avg_position": 4.5
                },
                {
                    "team_name": "McLaren",
                    "points": 608,
                    "wins": 6,
                    "podiums": 27,
                    "pole_positions": 6,
                    "fastest_laps": 4,
                    "drivers_count": 2,
                    "championship_position": 2,
                    "avg_position": 3.2
                }
            ],
            "last_update": "2025-01-15T10:30:00Z"
        }
        
        logger.info(f"📊 Returning dashboard stats for user {user_id}")
        return dashboard_data
        
    except Exception as e:
        logger.error(f"❌ Error getting dashboard stats: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e)) 