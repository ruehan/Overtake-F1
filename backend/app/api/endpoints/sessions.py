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
        # Get recent sessions from this year
        from datetime import datetime
        current_year = datetime.utcnow().year
        
        sessions = await openf1_client.get_sessions(year=current_year)
        if not sessions:
            raise HTTPException(status_code=404, detail="No current sessions available")
        
        # Sort by date and get the latest
        sorted_sessions = sorted(
            sessions,
            key=lambda x: x.get("date", ""),
            reverse=True
        )
        
        # Check if there are any recent sessions (within last 7 days)
        now = datetime.utcnow()
        recent_sessions = []
        
        for session in sorted_sessions[:10]:  # Check last 10 sessions
            session_date = session.get("date")
            if session_date:
                try:
                    session_dt = datetime.fromisoformat(session_date.replace("Z", "+00:00"))
                    time_diff = (now - session_dt).days
                    if time_diff <= 7:  # Within last 7 days
                        recent_sessions.append({
                            **session,
                            "is_active": time_diff <= 1,  # Active if within last day
                            "time_since": f"{time_diff} days ago" if time_diff > 0 else "Today"
                        })
                except:
                    continue
        
        if recent_sessions:
            return recent_sessions[0]
        else:
            # Return the latest session with inactive status
            latest_session = sorted_sessions[0]
            return {
                **latest_session,
                "is_active": False,
                "time_since": "No recent sessions"
            }
            
    except OpenF1APIException as e:
        raise HTTPException(
            status_code=e.status_code or 500,
            detail=e.message
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))