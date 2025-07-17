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
        # 임시 더미 데이터 반환
        dummy_preferences = {
            "user_id": user_id,
            "favorite_drivers": [1, 16],  # Max Verstappen, Charles Leclerc
            "favorite_teams": [1, 3],     # Red Bull, Ferrari
            "notifications_enabled": True,
            "preferred_language": "ko",
            "theme": "dark",
            "timezone": "Asia/Seoul"
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