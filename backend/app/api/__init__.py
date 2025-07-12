from fastapi import APIRouter

from app.api.endpoints import drivers, teams, positions, sessions, weather

api_router = APIRouter()

api_router.include_router(drivers.router, prefix="/drivers", tags=["drivers"])
api_router.include_router(teams.router, prefix="/teams", tags=["teams"])
api_router.include_router(positions.router, prefix="/positions", tags=["positions"])
api_router.include_router(sessions.router, prefix="/sessions", tags=["sessions"])
api_router.include_router(weather.router, prefix="/weather", tags=["weather"])