from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional, Dict
from pydantic import BaseModel

from app.models.user_models import AlertType, UserPreferences, UpdateUserPreferencesRequest
from app.services.race_event_detector import race_event_detector, RaceEvent, EventType

router = APIRouter(prefix="/alerts", tags=["alerts"])

# Request/Response models
class AlertSettingsResponse(BaseModel):
    alert_settings: Dict[AlertType, bool]
    notification_enabled: bool = True

class AlertHistoryItem(BaseModel):
    id: str
    event: Dict
    timestamp: str
    read: bool = False

class AlertHistoryResponse(BaseModel):
    history: List[AlertHistoryItem]
    total: int
    unread_count: int

# In-memory storage for demo (in production, use database)
user_preferences_store: Dict[str, UserPreferences] = {}
alert_history_store: Dict[str, List[Dict]] = {}

def get_current_user_id() -> str:
    """Get current user ID (mock implementation)"""
    return "demo_user"

@router.get("/settings", response_model=AlertSettingsResponse)
async def get_alert_settings(user_id: str = Depends(get_current_user_id)):
    """Get user's alert settings"""
    if user_id not in user_preferences_store:
        # Create default preferences
        user_preferences_store[user_id] = UserPreferences(
            user_id=user_id,
            alert_settings={
                AlertType.OVERTAKES: True,
                AlertType.PIT_STOPS: True,
                AlertType.LEAD_CHANGES: True,
                AlertType.FASTEST_LAPS: False,
                AlertType.WEATHER_CHANGES: False,
                AlertType.INCIDENTS: True
            }
        )
    
    preferences = user_preferences_store[user_id]
    return AlertSettingsResponse(
        alert_settings=preferences.alert_settings,
        notification_enabled=True
    )

@router.put("/settings", response_model=AlertSettingsResponse)
async def update_alert_settings(
    settings: Dict[AlertType, bool],
    user_id: str = Depends(get_current_user_id)
):
    """Update user's alert settings"""
    if user_id not in user_preferences_store:
        user_preferences_store[user_id] = UserPreferences(
            user_id=user_id,
            alert_settings=settings
        )
    else:
        user_preferences_store[user_id].alert_settings.update(settings)
    
    preferences = user_preferences_store[user_id]
    return AlertSettingsResponse(
        alert_settings=preferences.alert_settings,
        notification_enabled=True
    )

@router.get("/history", response_model=AlertHistoryResponse)
async def get_alert_history(
    limit: int = 50,
    offset: int = 0,
    event_type: Optional[str] = None,
    unread_only: bool = False,
    user_id: str = Depends(get_current_user_id)
):
    """Get user's alert history"""
    if user_id not in alert_history_store:
        alert_history_store[user_id] = []
    
    history = alert_history_store[user_id]
    
    # Apply filters
    filtered_history = history
    
    if event_type:
        filtered_history = [item for item in filtered_history 
                          if item.get('event', {}).get('event_type') == event_type]
    
    if unread_only:
        filtered_history = [item for item in filtered_history if not item.get('read', False)]
    
    # Apply pagination
    total = len(filtered_history)
    paginated_history = filtered_history[offset:offset + limit]
    
    # Calculate unread count
    unread_count = len([item for item in history if not item.get('read', False)])
    
    return AlertHistoryResponse(
        history=[AlertHistoryItem(**item) for item in paginated_history],
        total=total,
        unread_count=unread_count
    )

@router.post("/history/{alert_id}/read")
async def mark_alert_as_read(
    alert_id: str,
    user_id: str = Depends(get_current_user_id)
):
    """Mark a specific alert as read"""
    if user_id not in alert_history_store:
        raise HTTPException(status_code=404, detail="Alert history not found")
    
    history = alert_history_store[user_id]
    
    for item in history:
        if item.get('id') == alert_id:
            item['read'] = True
            return {"message": "Alert marked as read"}
    
    raise HTTPException(status_code=404, detail="Alert not found")

@router.post("/history/read-all")
async def mark_all_alerts_as_read(user_id: str = Depends(get_current_user_id)):
    """Mark all alerts as read"""
    if user_id not in alert_history_store:
        alert_history_store[user_id] = []
    
    history = alert_history_store[user_id]
    
    for item in history:
        item['read'] = True
    
    return {"message": "All alerts marked as read"}

@router.delete("/history")
async def clear_alert_history(user_id: str = Depends(get_current_user_id)):
    """Clear all alert history"""
    alert_history_store[user_id] = []
    return {"message": "Alert history cleared"}

@router.get("/test-events")
async def trigger_test_events():
    """Trigger test events for development (remove in production)"""
    import asyncio
    from datetime import datetime
    
    # Simulate some test events
    test_events = [
        RaceEvent(
            event_type=EventType.OVERTAKE,
            timestamp=datetime.utcnow(),
            session_key=9222,
            driver_number=44,
            target_driver_number=1,
            position_gained=1,
            data={
                'overtaking_driver': 'Lewis Hamilton',
                'overtaken_driver': 'Max Verstappen',
                'new_position': 2,
                'previous_position': 3
            },
            message="Lewis Hamilton overtakes Max Verstappen! Now P2"
        ),
        RaceEvent(
            event_type=EventType.FASTEST_LAP,
            timestamp=datetime.utcnow(),
            session_key=9222,
            driver_number=16,
            lap_number=15,
            data={
                'driver_name': 'Charles Leclerc',
                'lap_time': 89.567,
                'lap_number': 15
            },
            message="⚡ Charles Leclerc sets fastest lap: 89.567s (Lap 15)"
        ),
        RaceEvent(
            event_type=EventType.PIT_STOP,
            timestamp=datetime.utcnow(),
            session_key=9222,
            driver_number=63,
            lap_number=20,
            data={
                'driver_name': 'George Russell',
                'pit_duration': 2.456,
                'lap_number': 20
            },
            message="🔧 George Russell pits! Duration: 2.456s (Lap 20)"
        )
    ]
    
    # Emit events
    for event in test_events:
        await race_event_detector.emit_event(event)
        await asyncio.sleep(0.5)  # Small delay between events
    
    return {"message": f"Triggered {len(test_events)} test events"}

# Function to store alert in history (called by event handlers)
async def store_alert_in_history(user_id: str, event: RaceEvent):
    """Store an alert in user's history"""
    if user_id not in alert_history_store:
        alert_history_store[user_id] = []
    
    alert_item = {
        'id': f"{event.session_key}-{event.timestamp.isoformat()}-{event.driver_number}",
        'event': {
            'event_type': event.event_type.value,
            'timestamp': event.timestamp.isoformat(),
            'session_key': event.session_key,
            'driver_number': event.driver_number,
            'target_driver_number': event.target_driver_number,
            'position_gained': event.position_gained,
            'lap_number': event.lap_number,
            'data': event.data,
            'message': event.message
        },
        'timestamp': event.timestamp.isoformat(),
        'read': False
    }
    
    # Add to the beginning of the list (most recent first)
    alert_history_store[user_id].insert(0, alert_item)
    
    # Keep only the most recent 100 alerts
    if len(alert_history_store[user_id]) > 100:
        alert_history_store[user_id] = alert_history_store[user_id][:100]