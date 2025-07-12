from fastapi import APIRouter, Query, HTTPException
from typing import Optional, List, Dict, Any
from datetime import datetime

from app.services.openf1_client import openf1_client
from app.core.exceptions import OpenF1APIException

router = APIRouter()

@router.get("", response_model=List[Dict[str, Any]])
async def get_weather(
    session_key: Optional[int] = Query(None, description="Session key"),
    date: Optional[datetime] = Query(None, description="Date filter")
):
    try:
        weather = await openf1_client.get_weather(
            session_key=session_key,
            date=date
        )
        return weather
    except OpenF1APIException as e:
        raise HTTPException(
            status_code=e.status_code or 500,
            detail=e.message
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/current", response_model=Dict[str, Any])
async def get_current_weather(
    session_key: int = Query(..., description="Session key")
):
    try:
        weather_data = await openf1_client.get_weather(session_key=session_key)
        if not weather_data:
            raise HTTPException(status_code=404, detail="No weather data found")
        
        # Return the most recent weather data
        latest_weather = max(
            weather_data,
            key=lambda x: x.get("timestamp", 0)
        )
        return latest_weather
    except OpenF1APIException as e:
        raise HTTPException(
            status_code=e.status_code or 500,
            detail=e.message
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))