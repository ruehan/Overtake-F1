from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import socketio
from contextlib import asynccontextmanager
import uvicorn
import logging

from app.config import settings
from app.api import api_router
from app.websocket import sio_app
from app.core.middleware import ErrorHandlingMiddleware, RateLimitMiddleware, LoggingMiddleware
from app.services.openf1_client import openf1_client
from app.core.database import init_database, close_database
from app.services.cache_service import cache_service

# Configure logging
logging.basicConfig(
    level=logging.INFO if settings.debug else logging.WARNING,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    print(f"Starting OpenF1 Dashboard API...")
    
    # Initialize database
    await init_database()
    
    # Initialize cache service
    await cache_service.connect()
    
    yield
    
    print("Shutting down...")
    # Close services
    await openf1_client.close()
    await cache_service.close()
    await close_database()

app = FastAPI(
    title="OpenF1 Dashboard API",
    version="1.0.0",
    description="API for F1 race data visualization",
    lifespan=lifespan
)

# Add middleware in order (bottom to top execution)
app.add_middleware(ErrorHandlingMiddleware)
app.add_middleware(
    RateLimitMiddleware,
    calls=settings.rate_limit_per_minute,
    period=60
)
app.add_middleware(LoggingMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")
app.mount("/socket.io", sio_app)

@app.get("/")
async def root():
    return {"message": "OpenF1 Dashboard API", "version": "1.0.0"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )