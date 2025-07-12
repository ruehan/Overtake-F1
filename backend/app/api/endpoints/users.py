from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any

from app.core.database import get_db
from app.services.user_service import UserService
from app.models.user_models import (
    UserPreferences, UserPreferencesResponse, UpdateUserPreferencesRequest,
    UserSession
)

router = APIRouter()

@router.get("/preferences/{user_id}", response_model=UserPreferencesResponse)
async def get_user_preferences(
    user_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get user preferences"""
    try:
        preferences = await UserService.get_or_create_user_preferences(db, user_id)
        return UserPreferencesResponse(
            preferences=preferences,
            message="User preferences retrieved successfully"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/preferences/{user_id}", response_model=UserPreferencesResponse)
async def update_user_preferences(
    user_id: str,
    update_data: UpdateUserPreferencesRequest,
    db: AsyncSession = Depends(get_db)
):
    """Update user preferences"""
    try:
        # Ensure user preferences exist
        await UserService.get_or_create_user_preferences(db, user_id)
        
        # Update preferences
        updated_preferences = await UserService.update_user_preferences(db, user_id, update_data)
        
        if not updated_preferences:
            raise HTTPException(status_code=404, detail="User preferences not found")
        
        return UserPreferencesResponse(
            preferences=updated_preferences,
            message="User preferences updated successfully"
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/preferences/{user_id}")
async def delete_user_preferences(
    user_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Delete user preferences"""
    try:
        deleted = await UserService.delete_user_preferences(db, user_id)
        
        if not deleted:
            raise HTTPException(status_code=404, detail="User preferences not found")
        
        return {"message": "User preferences deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/sessions", response_model=Dict[str, Any])
async def create_user_session(
    request: Request,
    user_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Create a new user session"""
    try:
        ip_address = request.client.host
        user_agent = request.headers.get("user-agent", "")
        
        session = await UserService.create_user_session(
            db, user_id, ip_address, user_agent
        )
        
        return {
            "session_id": session.session_id,
            "user_id": session.user_id,
            "message": "Session created successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/sessions/{session_id}")
async def get_user_session(
    session_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get user session information"""
    try:
        session = await UserService.get_user_session(db, session_id)
        
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        return {
            "session": session,
            "message": "Session retrieved successfully"
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/sessions/{session_id}/activity")
async def update_session_activity(
    session_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Update session last activity"""
    try:
        updated = await UserService.update_session_activity(db, session_id)
        
        if not updated:
            raise HTTPException(status_code=404, detail="Session not found")
        
        return {"message": "Session activity updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/sessions/{session_id}")
async def deactivate_session(
    session_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Deactivate a user session"""
    try:
        deactivated = await UserService.deactivate_session(db, session_id)
        
        if not deactivated:
            raise HTTPException(status_code=404, detail="Session not found")
        
        return {"message": "Session deactivated successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/sessions/user/{user_id}")
async def get_user_active_sessions(
    user_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get all active sessions for a user"""
    try:
        sessions = await UserService.get_active_sessions(db, user_id)
        
        return {
            "sessions": sessions,
            "total": len(sessions),
            "message": "Active sessions retrieved successfully"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))