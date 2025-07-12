import socketio
import asyncio
from typing import Dict, Set, Optional
from datetime import datetime
import json

from app.services.openf1_client import openf1_client
from app.services.race_event_detector import race_event_detector, RaceEvent
from app.config import settings

# Create Socket.IO server
sio = socketio.AsyncServer(
    async_mode='asgi',
    cors_allowed_origins=["http://localhost:3000"],
    ping_interval=settings.websocket_ping_interval,
    ping_timeout=settings.websocket_ping_timeout
)

# Create ASGI app
sio_app = socketio.ASGIApp(sio)

# Store active subscriptions
subscriptions: Dict[str, Set[str]] = {
    "positions": set(),
    "weather": set(),
    "lap_times": set(),
    "pit_stops": set(),
    "team_radio": set(),
    "drivers": set(),
    "race_events": set()
}

# Background tasks
background_tasks = {}

@sio.event
async def connect(sid, environ):
    print(f"Client {sid} connected")
    
    # Register as race event listener
    await register_race_event_listener(sid)
    
    await sio.emit('connected', {'message': 'Connected to OpenF1 Dashboard'}, to=sid)

@sio.event
async def disconnect(sid):
    print(f"Client {sid} disconnected")
    # Remove from all subscriptions
    for topic in subscriptions:
        subscriptions[topic].discard(sid)

@sio.event
async def subscribe(sid, data):
    topic = data.get('topic')
    session_key = data.get('session_key')
    
    if topic not in subscriptions:
        await sio.emit('error', {'message': f'Invalid topic: {topic}'}, to=sid)
        return
    
    subscriptions[topic].add(sid)
    
    # Store session info for the client
    await sio.save_session(sid, {'session_key': session_key})
    
    # Start background task if not already running
    task_name = f"{topic}_{session_key}"
    if task_name not in background_tasks or background_tasks[task_name].done():
        background_tasks[task_name] = asyncio.create_task(
            stream_data(topic, session_key)
        )
    
    await sio.emit(
        'subscribed',
        {'topic': topic, 'session_key': session_key},
        to=sid
    )

@sio.event
async def unsubscribe(sid, data):
    topic = data.get('topic')
    
    if topic in subscriptions:
        subscriptions[topic].discard(sid)
        await sio.emit('unsubscribed', {'topic': topic}, to=sid)

async def stream_data(topic: str, session_key: int):
    print(f"Starting stream for {topic} (session {session_key})")
    
    while subscriptions[topic]:  # While there are subscribers
        try:
            data = None
            
            if topic == "positions":
                positions = await openf1_client.get_positions(session_key=session_key)
                # Get latest position for each driver
                latest_positions = {}
                for pos in positions:
                    driver_num = pos.get("driver_number")
                    if driver_num and (
                        driver_num not in latest_positions or
                        pos.get("timestamp", 0) > latest_positions[driver_num].get("timestamp", 0)
                    ):
                        latest_positions[driver_num] = pos
                data = list(latest_positions.values())
            
            elif topic == "weather":
                weather_data = await openf1_client.get_weather(session_key=session_key)
                if weather_data:
                    data = max(weather_data, key=lambda x: x.get("timestamp", 0))
            
            elif topic == "lap_times":
                # Get latest lap times
                data = await openf1_client.get_lap_times(session_key=session_key)
            
            elif topic == "pit_stops":
                data = await openf1_client.get_pit_stops(session_key=session_key)
            
            elif topic == "team_radio":
                data = await openf1_client.get_team_radio(session_key=session_key)
            
            elif topic == "drivers":
                data = await openf1_client.get_drivers(session_key=session_key)
            
            if data:
                # Process data through race event detector for relevant topics
                if topic == "positions":
                    drivers = await openf1_client.get_drivers(session_key=session_key)
                    positions = [pos for pos in data if pos.get("driver_number") and pos.get("position")]
                    if positions and drivers:
                        # Convert to simplified position objects for event detection
                        from app.models.f1_models import Driver
                        driver_objects = []
                        
                        try:
                            # Create simplified position objects that only need driver_number and position
                            class SimplePosition:
                                def __init__(self, driver_number, position, session_key):
                                    self.driver_number = driver_number
                                    self.position = position
                                    self.session_key = session_key
                            
                            position_objects = []
                            for pos in positions:
                                # Only create position if we have the required fields
                                if pos.get("driver_number") and pos.get("position"):
                                    position_objects.append(SimplePosition(
                                        driver_number=pos["driver_number"],
                                        position=pos["position"],
                                        session_key=session_key
                                    ))
                            
                            # Create simplified driver objects for event detection
                            class SimpleDriver:
                                def __init__(self, driver_number, name, abbreviation, team_name=None, team_colour=None):
                                    self.driver_number = driver_number
                                    self.name = name
                                    self.abbreviation = abbreviation
                                    self.team_name = team_name or "Unknown Team"
                                    self.team_colour = team_colour or "#666666"
                            
                            for driver in drivers:
                                try:
                                    # Extract data from OpenF1 API format
                                    driver_number = driver.get("driver_number")
                                    first_name = driver.get("first_name", "")
                                    last_name = driver.get("last_name", "")
                                    name_acronym = driver.get("name_acronym", "")
                                    team_name = driver.get("team_name", "Unknown Team")
                                    team_colour = driver.get("team_colour", "#666666")
                                    
                                    # Construct full name
                                    if first_name and last_name:
                                        full_name = f"{first_name} {last_name}"
                                    elif driver.get("full_name"):
                                        full_name = driver.get("full_name")
                                    else:
                                        full_name = f"Driver {driver_number}"
                                    
                                    # Use acronym or generate abbreviation
                                    abbreviation = name_acronym or (last_name[:3].upper() if last_name else f"D{driver_number}")
                                    
                                    if driver_number:
                                        driver_objects.append(SimpleDriver(
                                            driver_number=driver_number,
                                            name=full_name,
                                            abbreviation=abbreviation,
                                            team_name=team_name,
                                            team_colour=team_colour if team_colour.startswith('#') else f"#{team_colour}"
                                        ))
                                except Exception as e:
                                    print(f"Error creating driver object: {e}")
                                    continue
                            
                            if position_objects and driver_objects:
                                await race_event_detector.process_positions(position_objects, driver_objects)
                        except Exception as e:
                            print(f"Error processing positions for event detection: {e}")
                
                # Emit to all subscribers of this topic
                for client_sid in list(subscriptions[topic]):
                    session = await sio.get_session(client_sid)
                    if session and session.get('session_key') == session_key:
                        await sio.emit(
                            topic,
                            {
                                'data': data,
                                'timestamp': datetime.utcnow().isoformat()
                            },
                            to=client_sid
                        )
            
            # Wait before next update (adjust based on topic)
            if topic == "positions":
                await asyncio.sleep(1)  # Update positions every second
            elif topic == "weather":
                await asyncio.sleep(30)  # Update weather every 30 seconds
            else:
                await asyncio.sleep(5)  # Update other data every 5 seconds
                
        except Exception as e:
            print(f"Error streaming {topic}: {str(e)}")
            # Notify clients of error
            for client_sid in list(subscriptions[topic]):
                await sio.emit(
                    'stream_error',
                    {'topic': topic, 'error': str(e)},
                    to=client_sid
                )
            await asyncio.sleep(5)  # Wait before retrying
    
    print(f"Stopping stream for {topic} (session {session_key})")

# Race event handling
async def handle_race_event(event: RaceEvent):
    """Handle race events and broadcast to subscribed clients"""
    event_data = {
        'event_type': event.event_type.value,
        'timestamp': event.timestamp.isoformat(),
        'session_key': event.session_key,
        'driver_number': event.driver_number,
        'target_driver_number': event.target_driver_number,
        'position_gained': event.position_gained,
        'lap_number': event.lap_number,
        'data': event.data,
        'message': event.message
    }
    
    # Emit to all clients subscribed to race events
    for client_sid in list(subscriptions["race_events"]):
        await sio.emit('race_event', event_data, to=client_sid)

async def register_race_event_listener(sid: str):
    """Register a new client for race event notifications"""
    from app.services.race_event_detector import EventType
    
    # Add event listeners for this client
    for event_type in EventType:
        if not any(listener.__name__ == 'handle_race_event' 
                  for listener in race_event_detector.listeners[event_type]):
            race_event_detector.add_listener(event_type, handle_race_event)

# Utility function to broadcast to all connected clients
async def broadcast_event(event_type: str, data: Dict):
    await sio.emit(event_type, data)