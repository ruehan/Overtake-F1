from fastapi import APIRouter

from app.api.endpoints import drivers, teams, positions, sessions, weather, users, team_radio, standings, standings_cached
from app.routers import alerts

api_router = APIRouter()

api_router.include_router(drivers.router, prefix="/drivers", tags=["drivers"])
api_router.include_router(teams.router, prefix="/teams", tags=["teams"])
api_router.include_router(positions.router, prefix="/positions", tags=["positions"])
api_router.include_router(sessions.router, prefix="/sessions", tags=["sessions"])
api_router.include_router(weather.router, prefix="/weather", tags=["weather"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(alerts.router, prefix="/alerts", tags=["alerts"])
api_router.include_router(team_radio.router, prefix="/team-radio", tags=["team-radio"])
api_router.include_router(standings.router, prefix="/standings", tags=["standings"])
api_router.include_router(standings_cached.router, prefix="/standings-cached", tags=["standings-cached"])