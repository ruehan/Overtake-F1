import socketio
import asyncio
from typing import Dict, Set, Optional
from datetime import datetime
import json

from app.services.openf1_client import openf1_client
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
    "team_radio": set()
}

# Background tasks
background_tasks = {}

@sio.event
async def connect(sid, environ):
    print(f"Client {sid} connected")
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
            
            if data:
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

# Utility function to broadcast to all connected clients
async def broadcast_event(event_type: str, data: Dict):
    await sio.emit(event_type, data)