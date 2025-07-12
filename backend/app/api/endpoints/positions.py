from fastapi import APIRouter, Query, HTTPException
from typing import Optional, List, Dict, Any
from datetime import datetime

from app.services.openf1_client import openf1_client
from app.core.exceptions import OpenF1APIException

router = APIRouter()

@router.get("", response_model=List[Dict[str, Any]])
async def get_positions(
    session_key: Optional[int] = Query(None, description="Session key"),
    driver_number: Optional[int] = Query(None, description="Driver number"),
    date: Optional[datetime] = Query(None, description="Date filter")
):
    try:
        positions = await openf1_client.get_positions(
            session_key=session_key,
            driver_number=driver_number,
            date=date
        )
        return positions
    except OpenF1APIException as e:
        raise HTTPException(
            status_code=e.status_code or 500,
            detail=e.message
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/latest", response_model=List[Dict[str, Any]])
async def get_latest_positions(
    session_key: int = Query(..., description="Session key")
):
    try:
        positions = await openf1_client.get_positions(session_key=session_key)
        if not positions:
            return []
        
        # Group by driver and get latest position for each
        latest_positions = {}
        for pos in positions:
            driver_num = pos.get("driver_number")
            if driver_num and (
                driver_num not in latest_positions or
                pos.get("timestamp", 0) > latest_positions[driver_num].get("timestamp", 0)
            ):
                latest_positions[driver_num] = pos
        
        return list(latest_positions.values())
    except OpenF1APIException as e:
        raise HTTPException(
            status_code=e.status_code or 500,
            detail=e.message
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))