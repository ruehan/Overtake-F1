from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from sqlalchemy.exc import IntegrityError
from typing import Optional, List, Dict, Any
from datetime import datetime
import uuid

from app.core.database import UserPreferencesDB, UserSessionDB, get_db
from app.models.user_models import (
    UserPreferences, UserSession, UpdateUserPreferencesRequest,
    AlertType, DashboardWidget
)

class UserService:
    
    @staticmethod
    async def get_user_preferences(db: AsyncSession, user_id: str) -> Optional[UserPreferences]:
        """Get user preferences by user ID"""
        result = await db.execute(
            select(UserPreferencesDB).where(UserPreferencesDB.user_id == user_id)
        )
        user_prefs_db = result.scalar_one_or_none()
        
        if not user_prefs_db:
            return None
        
        return UserPreferences(
            user_id=user_prefs_db.user_id,
            favorite_drivers=user_prefs_db.favorite_drivers or [],
            favorite_teams=user_prefs_db.favorite_teams or [],
            alert_settings=user_prefs_db.alert_settings or {},
            dashboard_layout=user_prefs_db.dashboard_layout or {},
            theme=user_prefs_db.theme,
            timezone=user_prefs_db.timezone,
            language=user_prefs_db.language,
            created_at=user_prefs_db.created_at,
            updated_at=user_prefs_db.updated_at
        )
    
    @staticmethod
    async def create_user_preferences(
        db: AsyncSession, 
        user_preferences: UserPreferences
    ) -> UserPreferences:
        """Create new user preferences"""
        
        # Set default values if not provided
        default_alert_settings = {
            AlertType.OVERTAKES: True,
            AlertType.PIT_STOPS: True,
            AlertType.LEAD_CHANGES: True,
            AlertType.FASTEST_LAPS: False,
            AlertType.WEATHER_CHANGES: False,
            AlertType.INCIDENTS: True
        }
        
        default_dashboard_layout = {
            DashboardWidget.LIVE_MAP: True,
            DashboardWidget.DRIVER_STANDINGS: True,
            DashboardWidget.WEATHER: True,
            DashboardWidget.RECENT_RADIO: False,
            DashboardWidget.LAP_TIMES: True,
            DashboardWidget.PIT_STOPS: True
        }
        
        user_prefs_db = UserPreferencesDB(
            user_id=user_preferences.user_id,
            favorite_drivers=user_preferences.favorite_drivers,
            favorite_teams=user_preferences.favorite_teams,
            alert_settings=user_preferences.alert_settings or default_alert_settings,
            dashboard_layout=user_preferences.dashboard_layout or default_dashboard_layout,
            theme=user_preferences.theme,
            timezone=user_preferences.timezone,
            language=user_preferences.language
        )
        
        try:
            db.add(user_prefs_db)
            await db.commit()
            await db.refresh(user_prefs_db)
            
            return await UserService.get_user_preferences(db, user_preferences.user_id)
        except IntegrityError:
            await db.rollback()
            raise ValueError(f"User preferences for user_id {user_preferences.user_id} already exist")
    
    @staticmethod
    async def update_user_preferences(
        db: AsyncSession,
        user_id: str,
        update_data: UpdateUserPreferencesRequest
    ) -> Optional[UserPreferences]:
        """Update user preferences"""
        
        # Build update dictionary with only provided fields
        update_dict = {}
        for field, value in update_data.dict(exclude_unset=True).items():
            if value is not None:
                update_dict[field] = value
        
        if not update_dict:
            return await UserService.get_user_preferences(db, user_id)
        
        # Add updated timestamp
        update_dict['updated_at'] = datetime.utcnow()
        
        result = await db.execute(
            update(UserPreferencesDB)
            .where(UserPreferencesDB.user_id == user_id)
            .values(**update_dict)
        )
        
        if result.rowcount == 0:
            return None
        
        await db.commit()
        return await UserService.get_user_preferences(db, user_id)
    
    @staticmethod
    async def delete_user_preferences(db: AsyncSession, user_id: str) -> bool:
        """Delete user preferences"""
        result = await db.execute(
            delete(UserPreferencesDB).where(UserPreferencesDB.user_id == user_id)
        )
        
        if result.rowcount > 0:
            await db.commit()
            return True
        return False
    
    @staticmethod
    async def get_or_create_user_preferences(
        db: AsyncSession, 
        user_id: str
    ) -> UserPreferences:
        """Get user preferences or create with defaults if not exists"""
        user_prefs = await UserService.get_user_preferences(db, user_id)
        
        if not user_prefs:
            # Create with defaults
            default_prefs = UserPreferences(user_id=user_id)
            user_prefs = await UserService.create_user_preferences(db, default_prefs)
        
        return user_prefs
    
    # Session management
    @staticmethod
    async def create_user_session(
        db: AsyncSession,
        user_id: str,
        ip_address: str,
        user_agent: str
    ) -> UserSession:
        """Create a new user session"""
        session_id = str(uuid.uuid4())
        
        session_db = UserSessionDB(
            session_id=session_id,
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        db.add(session_db)
        await db.commit()
        await db.refresh(session_db)
        
        return UserSession(
            session_id=session_db.session_id,
            user_id=session_db.user_id,
            ip_address=session_db.ip_address,
            user_agent=session_db.user_agent,
            created_at=session_db.created_at,
            last_activity=session_db.last_activity,
            is_active=session_db.is_active
        )
    
    @staticmethod
    async def get_user_session(db: AsyncSession, session_id: str) -> Optional[UserSession]:
        """Get user session by session ID"""
        result = await db.execute(
            select(UserSessionDB).where(UserSessionDB.session_id == session_id)
        )
        session_db = result.scalar_one_or_none()
        
        if not session_db:
            return None
        
        return UserSession(
            session_id=session_db.session_id,
            user_id=session_db.user_id,
            ip_address=session_db.ip_address,
            user_agent=session_db.user_agent,
            created_at=session_db.created_at,
            last_activity=session_db.last_activity,
            is_active=session_db.is_active
        )
    
    @staticmethod
    async def update_session_activity(db: AsyncSession, session_id: str) -> bool:
        """Update last activity for a session"""
        result = await db.execute(
            update(UserSessionDB)
            .where(UserSessionDB.session_id == session_id)
            .values(last_activity=datetime.utcnow())
        )
        
        if result.rowcount > 0:
            await db.commit()
            return True
        return False
    
    @staticmethod
    async def deactivate_session(db: AsyncSession, session_id: str) -> bool:
        """Deactivate a user session"""
        result = await db.execute(
            update(UserSessionDB)
            .where(UserSessionDB.session_id == session_id)
            .values(is_active=False)
        )
        
        if result.rowcount > 0:
            await db.commit()
            return True
        return False
    
    @staticmethod
    async def get_active_sessions(db: AsyncSession, user_id: str) -> List[UserSession]:
        """Get all active sessions for a user"""
        result = await db.execute(
            select(UserSessionDB)
            .where(UserSessionDB.user_id == user_id)
            .where(UserSessionDB.is_active == True)
            .order_by(UserSessionDB.last_activity.desc())
        )
        sessions_db = result.scalars().all()
        
        return [
            UserSession(
                session_id=session.session_id,
                user_id=session.user_id,
                ip_address=session.ip_address,
                user_agent=session.user_agent,
                created_at=session.created_at,
                last_activity=session.last_activity,
                is_active=session.is_active
            )
            for session in sessions_db
        ]