from fastapi import APIRouter, Query, HTTPException
from typing import Optional, List, Dict, Any

from app.services.openf1_client import openf1_client
from app.core.exceptions import OpenF1APIException

router = APIRouter()

@router.get("", response_model=List[Dict[str, Any]])
async def get_teams(
    session_key: Optional[int] = Query(None, description="Session key to filter teams")
):
    try:
        teams = await openf1_client.get_teams(session_key=session_key)
        return teams
    except OpenF1APIException as e:
        raise HTTPException(
            status_code=e.status_code or 500,
            detail=e.message
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))