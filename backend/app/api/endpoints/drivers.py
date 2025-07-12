from fastapi import APIRouter, Query, HTTPException
from typing import Optional, List, Dict, Any

from app.services.openf1_client import openf1_client
from app.core.exceptions import OpenF1APIException

router = APIRouter()

@router.get("", response_model=List[Dict[str, Any]])
async def get_drivers(
    session_key: Optional[int] = Query(None, description="Session key to filter drivers")
):
    try:
        drivers = await openf1_client.get_drivers(session_key=session_key)
        return drivers
    except OpenF1APIException as e:
        raise HTTPException(
            status_code=e.status_code or 500,
            detail=e.message
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{driver_number}", response_model=Dict[str, Any])
async def get_driver(
    driver_number: int,
    session_key: Optional[int] = Query(None, description="Session key to filter driver")
):
    try:
        drivers = await openf1_client.get_drivers(session_key=session_key)
        for driver in drivers:
            if driver.get("driver_number") == driver_number:
                return driver
        raise HTTPException(status_code=404, detail="Driver not found")
    except OpenF1APIException as e:
        raise HTTPException(
            status_code=e.status_code or 500,
            detail=e.message
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))