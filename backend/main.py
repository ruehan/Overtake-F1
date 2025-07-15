"""
LiveF1 전용 F1 대시보드 백엔드 - 리팩토링된 버전
"""
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import json
import logging
import os
from dotenv import load_dotenv
import socketio

# 환경 변수 로드
load_dotenv()

# 서비스 및 라우터 import
from services.livef1_service import LiveF1Service
from routers import drivers, statistics, races, live_timing

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Socket.IO 서버 생성
sio = socketio.AsyncServer(
    async_mode='asgi',
    cors_allowed_origins=[
        "http://localhost:3000", 
        "http://127.0.0.1:3000",
        "https://overtake-f1.com", 
        "https://www.overtake-f1.com",
        "http://overtake-f1.com", 
        "http://www.overtake-f1.com"
    ],
    ping_interval=25,
    ping_timeout=60
)

# FastAPI 앱 생성
app = FastAPI(
    title="F1 LiveTiming Dashboard",
    description="LiveF1 기반 실시간 F1 대시보드",
    version="2.0.0"
)

# Socket.IO ASGI 앱 마운트
sio_app = socketio.ASGIApp(sio, app)

# CORS 설정
origins = os.getenv("CORS_ORIGINS", '["*"]')
try:
    allowed_origins = json.loads(origins)
except:
    allowed_origins = ["*"]

# 도메인별 CORS 설정 추가
if allowed_origins == ["*"]:
    allowed_origins = [
        "http://localhost:3000",
        "http://127.0.0.1:3000", 
        "http://localhost",
        "http://127.0.0.1",
        "http://overtake-f1.com",
        "https://overtake-f1.com",
        "http://www.overtake-f1.com",
        "https://www.overtake-f1.com"
    ]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# LiveF1Service 인스턴스 생성
livef1_service = LiveF1Service()

# 라우터들에 서비스 전달
drivers.init_service(livef1_service)
statistics.init_service(livef1_service)
races.init_service(livef1_service)
live_timing.init_service(livef1_service)

# 라우터 등록
app.include_router(drivers.router)
app.include_router(statistics.router)
app.include_router(races.router)
app.include_router(live_timing.router)

# 기본 엔드포인트
@app.get("/")
async def read_root():
    return {"message": "F1 LiveTiming Dashboard API", "version": "2.0.0"}

# Socket.IO 이벤트 핸들러들
@sio.event
async def connect(sid, environ):
    logger.info(f"Client {sid} connected")
    await sio.emit('connected', {'status': 'connected'}, room=sid)

@sio.event
async def disconnect(sid):
    logger.info(f"Client {sid} disconnected")

@sio.event
async def request_live_timing(sid, data):
    try:
        # 라이브 타이밍 데이터 가져오기
        timing_data = await livef1_service.get_live_timing()
        await sio.emit('live_timing_data', timing_data, room=sid)
    except Exception as e:
        logger.error(f"Error sending live timing data: {e}")
        await sio.emit('error', {'message': str(e)}, room=sid)

@sio.event
async def request_weather(sid, data):
    try:
        weather_data = await livef1_service.get_weather()
        await sio.emit('weather_data', weather_data, room=sid)
    except Exception as e:
        logger.error(f"Error sending weather data: {e}")
        await sio.emit('error', {'message': str(e)}, room=sid)

@sio.event
async def request_driver_standings(sid, data):
    try:
        year = data.get('year') if data else None
        standings = await livef1_service.get_driver_standings(year)
        await sio.emit('driver_standings', standings, room=sid)
    except Exception as e:
        logger.error(f"Error sending driver standings: {e}")
        await sio.emit('error', {'message': str(e)}, room=sid)

@sio.event
async def request_constructor_standings(sid, data):
    try:
        year = data.get('year') if data else None
        standings = await livef1_service.get_constructor_standings(year)
        await sio.emit('constructor_standings', standings, room=sid)
    except Exception as e:
        logger.error(f"Error sending constructor standings: {e}")
        await sio.emit('error', {'message': str(e)}, room=sid)

# WebSocket 엔드포인트
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    livef1_service.websocket_connections.append(websocket)
    
    try:
        while True:
            # 클라이언트로부터 메시지 대기
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # 메시지 타입에 따라 처리
            if message.get('type') == 'live_timing':
                timing_data = await livef1_service.get_live_timing()
                await websocket.send_text(json.dumps({
                    'type': 'live_timing',
                    'data': timing_data
                }))
            elif message.get('type') == 'weather':
                weather_data = await livef1_service.get_weather()
                await websocket.send_text(json.dumps({
                    'type': 'weather',
                    'data': weather_data
                }))
            
    except WebSocketDisconnect:
        livef1_service.websocket_connections.remove(websocket)
        logger.info("WebSocket client disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        if websocket in livef1_service.websocket_connections:
            livef1_service.websocket_connections.remove(websocket)

# 메인 실행
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(sio_app, host="0.0.0.0", port=8000)