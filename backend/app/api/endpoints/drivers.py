from fastapi import APIRouter, Query, HTTPException
from typing import Optional, List, Dict, Any

from app.services.openf1_client import openf1_client
from app.core.exceptions import OpenF1APIException
from app.core.data_utils import DataTransformationUtils
from app.core.validators import validate_driver_response, F1DataValidator
from app.models.f1_models import DriversResponse

router = APIRouter()

@router.get("", response_model=List[Dict[str, Any]])
@validate_driver_response
async def get_drivers(
    session_key: Optional[int] = Query(None, description="Session key to filter drivers")
):
    try:
        raw_drivers = await openf1_client.get_drivers(session_key=session_key)
        
        # Transform and validate data
        normalized_drivers = []
        for raw_driver in raw_drivers:
            normalized = DataTransformationUtils.normalize_driver_data(raw_driver)
            validation_result = F1DataValidator.validate_driver_data(normalized)
            
            if validation_result.is_valid:
                normalized_drivers.append(normalized)
            else:
                # Log validation errors but don't fail the entire request
                print(f"Driver data validation failed: {validation_result.errors}")
        
        return normalized_drivers
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