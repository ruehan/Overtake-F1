from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import asyncio
from dataclasses import dataclass
from enum import Enum

from app.services.openf1_client import openf1_client
from app.core.exceptions import OpenF1APIException

class MessageCategory(Enum):
    STRATEGY = "strategy"
    TECHNICAL = "technical"
    MOTIVATIONAL = "motivational"
    WARNING = "warning"
    GENERAL = "general"

@dataclass
class RadioMessage:
    session_key: int
    driver_number: int
    date: datetime
    recording_url: Optional[str]
    duration: Optional[float]
    category: MessageCategory
    importance: int  # 1-5 scale
    driver_name: Optional[str] = None
    team_name: Optional[str] = None
    transcript: Optional[str] = None

@dataclass
class RadioStats:
    total_messages: int
    active_drivers: List[int]
    messages_per_hour: Dict[int, int]
    most_active_driver: Optional[Dict[str, Any]]
    category_distribution: Dict[str, int]
    average_duration: float

class TeamRadioService:
    def __init__(self):
        self.cache = {}
        self.cache_duration = 30  # seconds
        
    async def get_radio_messages(
        self, 
        session_key: int, 
        driver_number: Optional[int] = None,
        limit: int = 50
    ) -> List[RadioMessage]:
        """Get team radio messages for a session"""
        try:
            raw_messages = await openf1_client.get_team_radio(
                session_key=session_key,
                driver_number=driver_number
            )
            
            if not raw_messages:
                return []
            
            # Convert to RadioMessage objects
            messages = []
            for msg in raw_messages:
                try:
                    radio_msg = self._parse_radio_message(msg, session_key)
                    if radio_msg:
                        messages.append(radio_msg)
                except Exception as e:
                    print(f"Error parsing radio message: {e}")
                    continue
            
            # Sort by timestamp (most recent first) and limit
            messages.sort(key=lambda x: x.date, reverse=True)
            return messages[:limit]
            
        except Exception as e:
            print(f"Error getting radio messages: {e}")
            return []
    
    async def get_latest_messages(
        self, 
        session_key: int, 
        minutes: int = 10, 
        limit: int = 20
    ) -> List[RadioMessage]:
        """Get latest radio messages within time window"""
        try:
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(minutes=minutes)
            
            all_messages = await self.get_radio_messages(session_key, limit=200)
            
            # Filter by time window
            recent_messages = [
                msg for msg in all_messages 
                if start_time <= msg.date <= end_time
            ]
            
            return recent_messages[:limit]
            
        except Exception as e:
            print(f"Error getting latest messages: {e}")
            return []
    
    async def search_messages(
        self, 
        session_key: int, 
        query: Optional[str] = None,
        driver_number: Optional[int] = None,
        category: Optional[MessageCategory] = None,
        limit: int = 30
    ) -> List[RadioMessage]:
        """Search radio messages with filters"""
        try:
            messages = await self.get_radio_messages(session_key, driver_number, limit=100)
            
            filtered_messages = messages
            
            # Apply text search
            if query:
                query_lower = query.lower()
                filtered_messages = [
                    msg for msg in filtered_messages
                    if (msg.transcript and query_lower in msg.transcript.lower()) or
                       (msg.driver_name and query_lower in msg.driver_name.lower()) or
                       (msg.team_name and query_lower in msg.team_name.lower())
                ]
            
            # Apply category filter
            if category:
                filtered_messages = [
                    msg for msg in filtered_messages
                    if msg.category == category
                ]
            
            return filtered_messages[:limit]
            
        except Exception as e:
            print(f"Error searching messages: {e}")
            return []
    
    async def get_driver_messages(
        self, 
        session_key: int, 
        driver_number: int, 
        limit: int = 20
    ) -> List[RadioMessage]:
        """Get all messages for a specific driver"""
        return await self.get_radio_messages(session_key, driver_number, limit)
    
    async def get_radio_statistics(self, session_key: int) -> RadioStats:
        """Get comprehensive statistics for team radio"""
        try:
            messages = await self.get_radio_messages(session_key, limit=500)
            
            if not messages:
                return RadioStats(
                    total_messages=0,
                    active_drivers=[],
                    messages_per_hour={},
                    most_active_driver=None,
                    category_distribution={},
                    average_duration=0.0
                )
            
            # Calculate statistics
            driver_counts = {}
            category_counts = {}
            hourly_counts = {}
            total_duration = 0
            duration_count = 0
            
            for msg in messages:
                # Driver activity
                driver_counts[msg.driver_number] = driver_counts.get(msg.driver_number, 0) + 1
                
                # Category distribution
                category_counts[msg.category.value] = category_counts.get(msg.category.value, 0) + 1
                
                # Hourly distribution
                hour = msg.date.hour
                hourly_counts[hour] = hourly_counts.get(hour, 0) + 1
                
                # Duration calculation
                if msg.duration:
                    total_duration += msg.duration
                    duration_count += 1
            
            # Find most active driver
            most_active_driver = None
            if driver_counts:
                most_active_num = max(driver_counts, key=driver_counts.get)
                most_active_driver = {
                    "driver_number": most_active_num,
                    "message_count": driver_counts[most_active_num],
                    "driver_name": next(
                        (msg.driver_name for msg in messages if msg.driver_number == most_active_num),
                        f"Driver {most_active_num}"
                    )
                }
            
            return RadioStats(
                total_messages=len(messages),
                active_drivers=list(driver_counts.keys()),
                messages_per_hour=hourly_counts,
                most_active_driver=most_active_driver,
                category_distribution=category_counts,
                average_duration=total_duration / duration_count if duration_count > 0 else 0.0
            )
            
        except Exception as e:
            print(f"Error getting radio statistics: {e}")
            return RadioStats(
                total_messages=0,
                active_drivers=[],
                messages_per_hour={},
                most_active_driver=None,
                category_distribution={},
                average_duration=0.0
            )
    
    def _parse_radio_message(self, raw_msg: Dict[str, Any], session_key: int) -> Optional[RadioMessage]:
        """Parse raw API message into RadioMessage object"""
        try:
            # Parse timestamp
            date_str = raw_msg.get("date", "")
            if not date_str:
                return None
            
            try:
                date = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
            except ValueError:
                return None
            
            driver_number = raw_msg.get("driver_number")
            if not driver_number:
                return None
            
            # Categorize message (simplified heuristic)
            category = self._categorize_message(raw_msg)
            
            # Calculate importance (1-5 scale)
            importance = self._calculate_importance(raw_msg, category)
            
            return RadioMessage(
                session_key=session_key,
                driver_number=driver_number,
                date=date,
                recording_url=raw_msg.get("recording_url"),
                duration=self._estimate_duration(raw_msg),
                category=category,
                importance=importance,
                driver_name=self._get_driver_name(driver_number),
                team_name=self._get_team_name(driver_number),
                transcript=None  # Would need speech-to-text service
            )
            
        except Exception as e:
            print(f"Error parsing radio message: {e}")
            return None
    
    def _categorize_message(self, raw_msg: Dict[str, Any]) -> MessageCategory:
        """Categorize message based on available data"""
        # This is a simplified categorization
        # In reality, you'd need speech-to-text and NLP
        
        recording_url = raw_msg.get("recording_url", "").lower()
        
        # Simple heuristics based on timing or URL patterns
        if "pit" in recording_url or "stop" in recording_url:
            return MessageCategory.STRATEGY
        elif "engine" in recording_url or "brake" in recording_url:
            return MessageCategory.TECHNICAL
        elif "push" in recording_url or "go" in recording_url:
            return MessageCategory.MOTIVATIONAL
        elif "yellow" in recording_url or "safety" in recording_url:
            return MessageCategory.WARNING
        else:
            return MessageCategory.GENERAL
    
    def _calculate_importance(self, raw_msg: Dict[str, Any], category: MessageCategory) -> int:
        """Calculate message importance on 1-5 scale"""
        importance = 3  # Default
        
        # Strategy messages are generally more important
        if category == MessageCategory.STRATEGY:
            importance = 4
        elif category == MessageCategory.WARNING:
            importance = 5
        elif category == MessageCategory.MOTIVATIONAL:
            importance = 2
        
        return importance
    
    def _estimate_duration(self, raw_msg: Dict[str, Any]) -> Optional[float]:
        """Estimate audio duration (placeholder)"""
        # In real implementation, you'd get this from audio metadata
        # For now, return a random duration between 2-15 seconds
        import random
        return random.uniform(2.0, 15.0)
    
    def _get_driver_name(self, driver_number: int) -> Optional[str]:
        """Get driver name by number (placeholder)"""
        # This would normally come from a driver lookup service
        driver_names = {
            1: "Max Verstappen",
            11: "Sergio Perez",
            44: "Lewis Hamilton",
            63: "George Russell",
            16: "Charles Leclerc",
            55: "Carlos Sainz",
            4: "Lando Norris",
            81: "Oscar Piastri",
            14: "Fernando Alonso",
            18: "Lance Stroll"
        }
        return driver_names.get(driver_number, f"Driver {driver_number}")
    
    def _get_team_name(self, driver_number: int) -> Optional[str]:
        """Get team name by driver number (placeholder)"""
        # This would normally come from a team lookup service
        team_mapping = {
            1: "Red Bull Racing", 11: "Red Bull Racing",
            44: "Mercedes", 63: "Mercedes",
            16: "Ferrari", 55: "Ferrari",
            4: "McLaren", 81: "McLaren",
            14: "Aston Martin", 18: "Aston Martin"
        }
        return team_mapping.get(driver_number, "Unknown Team")
    
    async def get_driver_timeline(
        self, 
        session_key: int, 
        driver_number: int
    ) -> List[Dict[str, Any]]:
        """Get chronological timeline of driver's radio messages"""
        try:
            messages = await self.get_driver_messages(session_key, driver_number, limit=100)
            
            # Sort chronologically (oldest first for timeline)
            messages.sort(key=lambda x: x.date)
            
            timeline = []
            for msg in messages:
                timeline.append({
                    "timestamp": msg.date.isoformat(),
                    "category": msg.category.value,
                    "importance": msg.importance,
                    "recording_url": msg.recording_url,
                    "duration": msg.duration,
                    "driver_name": msg.driver_name,
                    "team_name": msg.team_name
                })
            
            return timeline
            
        except Exception as e:
            print(f"Error getting driver timeline: {e}")
            return []

# Global instance
team_radio_service = TeamRadioService()