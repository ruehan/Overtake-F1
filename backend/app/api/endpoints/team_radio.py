from fastapi import APIRouter, Query, HTTPException
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta

from app.services.openf1_client import openf1_client
from app.core.exceptions import OpenF1APIException

router = APIRouter()

@router.get("", response_model=List[Dict[str, Any]])
async def get_team_radio_messages(
    session_key: Optional[int] = Query(None, description="Session key"),
    driver_number: Optional[int] = Query(None, description="Driver number"),
    limit: Optional[int] = Query(50, description="Maximum number of messages", ge=1, le=200)
):
    """Get team radio messages"""
    try:
        messages = await openf1_client.get_team_radio(
            session_key=session_key,
            driver_number=driver_number
        )
        
        if not messages:
            return []
        
        # Sort by timestamp (most recent first) and limit results
        sorted_messages = sorted(
            messages, 
            key=lambda x: x.get("date", ""), 
            reverse=True
        )
        
        return sorted_messages[:limit]
        
    except OpenF1APIException as e:
        raise HTTPException(
            status_code=e.status_code or 500,
            detail=e.message
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/drivers/{driver_number}", response_model=List[Dict[str, Any]])
async def get_driver_radio_messages(
    driver_number: int,
    session_key: Optional[int] = Query(None, description="Session key"),
    limit: Optional[int] = Query(20, description="Maximum number of messages", ge=1, le=100)
):
    """Get team radio messages for a specific driver"""
    try:
        messages = await openf1_client.get_team_radio(
            session_key=session_key,
            driver_number=driver_number
        )
        
        if not messages:
            return []
        
        # Sort by timestamp (most recent first) and limit results
        sorted_messages = sorted(
            messages, 
            key=lambda x: x.get("date", ""), 
            reverse=True
        )
        
        return sorted_messages[:limit]
        
    except OpenF1APIException as e:
        raise HTTPException(
            status_code=e.status_code or 500,
            detail=e.message
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/latest", response_model=List[Dict[str, Any]])
async def get_latest_radio_messages(
    session_key: int = Query(..., description="Session key"),
    minutes: int = Query(10, description="Minutes to look back", ge=1, le=60),
    limit: int = Query(20, description="Maximum number of messages", ge=1, le=50)
):
    """Get latest team radio messages within specified time window"""
    try:
        # Calculate time window
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(minutes=minutes)
        
        messages = await openf1_client.get_team_radio(
            session_key=session_key
        )
        
        if not messages:
            return []
        
        # Filter messages within time window
        filtered_messages = []
        for msg in messages:
            try:
                msg_time = datetime.fromisoformat(msg.get("date", "").replace("Z", "+00:00"))
                if start_time <= msg_time <= end_time:
                    filtered_messages.append(msg)
            except (ValueError, TypeError):
                continue  # Skip messages with invalid timestamps
        
        # Sort by timestamp (most recent first) and limit results
        sorted_messages = sorted(
            filtered_messages, 
            key=lambda x: x.get("date", ""), 
            reverse=True
        )
        
        return sorted_messages[:limit]
        
    except OpenF1APIException as e:
        raise HTTPException(
            status_code=e.status_code or 500,
            detail=e.message
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/search", response_model=List[Dict[str, Any]])
async def search_radio_messages(
    session_key: int = Query(..., description="Session key"),
    query: Optional[str] = Query(None, description="Search query"),
    driver_number: Optional[int] = Query(None, description="Filter by driver number"),
    limit: int = Query(30, description="Maximum number of messages", ge=1, le=100)
):
    """Search team radio messages"""
    try:
        messages = await openf1_client.get_team_radio(
            session_key=session_key,
            driver_number=driver_number
        )
        
        if not messages:
            return []
        
        # Apply text search if query provided
        if query:
            query_lower = query.lower()
            filtered_messages = []
            for msg in messages:
                # Search in message content if available
                if any(query_lower in str(msg.get(field, "")).lower() 
                      for field in ["recording_url", "date"]):
                    filtered_messages.append(msg)
            messages = filtered_messages
        
        # Sort by timestamp (most recent first) and limit results
        sorted_messages = sorted(
            messages, 
            key=lambda x: x.get("date", ""), 
            reverse=True
        )
        
        return sorted_messages[:limit]
        
    except OpenF1APIException as e:
        raise HTTPException(
            status_code=e.status_code or 500,
            detail=e.message
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats", response_model=Dict[str, Any])
async def get_radio_statistics(
    session_key: int = Query(..., description="Session key")
):
    """Get team radio statistics for a session"""
    try:
        messages = await openf1_client.get_team_radio(session_key=session_key)
        
        if not messages:
            return {
                "total_messages": 0,
                "drivers_with_radio": [],
                "message_timeline": [],
                "most_active_driver": None
            }
        
        # Count messages per driver
        driver_counts = {}
        driver_names = {}
        timeline_data = []
        
        for msg in messages:
            driver_num = msg.get("driver_number")
            if driver_num:
                driver_counts[driver_num] = driver_counts.get(driver_num, 0) + 1
                
                # Add to timeline
                try:
                    msg_time = datetime.fromisoformat(msg.get("date", "").replace("Z", "+00:00"))
                    timeline_data.append({
                        "timestamp": msg.get("date"),
                        "driver_number": driver_num,
                        "hour": msg_time.hour
                    })
                except (ValueError, TypeError):
                    continue
        
        # Find most active driver
        most_active_driver = None
        if driver_counts:
            most_active_num = max(driver_counts, key=driver_counts.get)
            most_active_driver = {
                "driver_number": most_active_num,
                "message_count": driver_counts[most_active_num]
            }
        
        # Sort timeline by timestamp
        timeline_data.sort(key=lambda x: x.get("timestamp", ""))
        
        return {
            "total_messages": len(messages),
            "drivers_with_radio": [
                {"driver_number": num, "message_count": count}
                for num, count in sorted(driver_counts.items())
            ],
            "message_timeline": timeline_data,
            "most_active_driver": most_active_driver,
            "session_key": session_key,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except OpenF1APIException as e:
        raise HTTPException(
            status_code=e.status_code or 500,
            detail=e.message
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))