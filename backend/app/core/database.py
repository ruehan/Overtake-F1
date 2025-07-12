from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import Column, Integer, String, DateTime, Boolean, JSON, Text, Float
from sqlalchemy.sql import func
from contextlib import asynccontextmanager
from typing import AsyncGenerator
import os

from app.config import settings

# Database URL
DATABASE_URL = f"sqlite+aiosqlite:///./{settings.environment}_openf1_dashboard.db"

# Create async engine
engine = create_async_engine(
    DATABASE_URL,
    echo=settings.debug,  # Log SQL queries in debug mode
    future=True
)

# Create session factory
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# Base class for all models
Base = declarative_base()

# Database models
class UserPreferencesDB(Base):
    __tablename__ = "user_preferences"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(100), unique=True, index=True, nullable=False)
    favorite_drivers = Column(JSON, default=list)
    favorite_teams = Column(JSON, default=list)
    alert_settings = Column(JSON, default=dict)
    dashboard_layout = Column(JSON, default=dict)
    theme = Column(String(20), default="light")
    timezone = Column(String(50), default="UTC")
    language = Column(String(10), default="en")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class UserSessionDB(Base):
    __tablename__ = "user_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(100), unique=True, index=True, nullable=False)
    user_id = Column(String(100), index=True, nullable=False)
    ip_address = Column(String(45))  # Support IPv6
    user_agent = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_activity = Column(DateTime(timezone=True), server_default=func.now())
    is_active = Column(Boolean, default=True)

class CacheMetricsDB(Base):
    __tablename__ = "cache_metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    namespace = Column(String(100), index=True, nullable=False)
    cache_key = Column(String(255), index=True, nullable=False)
    hit_count = Column(Integer, default=0)
    miss_count = Column(Integer, default=0)
    last_hit = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class APIMetricsDB(Base):
    __tablename__ = "api_metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    endpoint = Column(String(200), index=True, nullable=False)
    method = Column(String(10), nullable=False)
    status_code = Column(Integer, index=True)
    response_time = Column(Float)  # in seconds
    user_id = Column(String(100), index=True)
    ip_address = Column(String(45))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

# Database dependency
@asynccontextmanager
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency to get database session"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

# Database initialization
async def init_database():
    """Initialize database tables"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("✅ Database tables created successfully")

async def close_database():
    """Close database connection"""
    await engine.dispose()
    print("🔒 Database connection closed")

# Database health check
async def check_database_health() -> bool:
    """Check if database is accessible"""
    try:
        async with get_db() as db:
            # Try a simple query
            await db.execute("SELECT 1")
            return True
    except Exception as e:
        print(f"❌ Database health check failed: {e}")
        return False