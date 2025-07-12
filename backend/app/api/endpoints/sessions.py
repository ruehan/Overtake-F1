from fastapi import APIRouter, Query, HTTPException
from typing import Optional, List, Dict, Any

from app.services.openf1_client import openf1_client
from app.core.exceptions import OpenF1APIException

router = APIRouter()

@router.get("", response_model=List[Dict[str, Any]])
async def get_sessions(
    year: Optional[int] = Query(None, description="Year filter"),
    country: Optional[str] = Query(None, description="Country filter"),
    session_type: Optional[str] = Query(None, description="Session type (Practice, Qualifying, Race)")
):
    try:
        sessions = await openf1_client.get_sessions(
            year=year,
            country=country,
            session_type=session_type
        )
        return sessions
    except OpenF1APIException as e:
        raise HTTPException(
            status_code=e.status_code or 500,
            detail=e.message
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/current", response_model=Dict[str, Any])
async def get_current_session():
    try:
        # Get sessions and find the most recent one
        sessions = await openf1_client.get_sessions()
        if not sessions:
            raise HTTPException(status_code=404, detail="No sessions found")
        
        # Sort by date and get the latest
        sorted_sessions = sorted(
            sessions,
            key=lambda x: x.get("date", ""),
            reverse=True
        )
        
        # Find the first session that's not in the future
        from datetime import datetime
        now = datetime.utcnow()
        
        for session in sorted_sessions:
            session_date = session.get("date")
            if session_date:
                try:
                    session_dt = datetime.fromisoformat(session_date.replace("Z", "+00:00"))
                    if session_dt <= now:
                        return session
                except:
                    continue
        
        return sorted_sessions[0]  # Return latest if none found
    except OpenF1APIException as e:
        raise HTTPException(
            status_code=e.status_code or 500,
            detail=e.message
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))