from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
import asyncio
import statistics
from dataclasses import dataclass

from app.services.openf1_client import openf1_client
from app.core.exceptions import OpenF1APIException

@dataclass
class WeatherCondition:
    air_temperature: float
    track_temperature: float
    humidity: float
    pressure: float
    wind_speed: float
    wind_direction: Optional[int]
    rainfall: float
    timestamp: datetime
    session_key: int

@dataclass
class WeatherTrend:
    trend_type: str  # 'rising', 'falling', 'stable'
    rate_of_change: float
    confidence: float
    prediction_window: int  # minutes

@dataclass
class TireRecommendation:
    compound: str  # 'soft', 'medium', 'hard', 'intermediate', 'full_wet'
    confidence: float
    reasoning: List[str]
    risk_factors: List[str]
    optimal_temp_range: tuple
    expected_degradation: str

class WeatherService:
    def __init__(self):
        self.cache = {}
        self.cache_duration = 60  # seconds
        
    async def get_current_weather(self, session_key: int) -> Optional[WeatherCondition]:
        """Get the most recent weather data for a session"""
        try:
            weather_data = await openf1_client.get_weather(session_key=session_key)
            
            if not weather_data:
                return None
                
            # Get the most recent weather data
            latest = max(weather_data, key=lambda x: x.get("date", ""))
            
            return WeatherCondition(
                air_temperature=latest.get("air_temperature", 0),
                track_temperature=latest.get("track_temperature", 0),
                humidity=latest.get("humidity", 0),
                pressure=latest.get("pressure", 0),
                wind_speed=latest.get("wind_speed", 0),
                wind_direction=latest.get("wind_direction"),
                rainfall=latest.get("rainfall", 0),
                timestamp=datetime.fromisoformat(latest.get("date", "").replace("Z", "+00:00")),
                session_key=session_key
            )
            
        except Exception as e:
            print(f"Error getting current weather: {e}")
            return None
    
    async def get_weather_history(self, session_key: int, hours: int = 3) -> List[WeatherCondition]:
        """Get weather history for the specified time period"""
        try:
            weather_data = await openf1_client.get_weather(
                session_key=session_key
            )
            
            # Filter data by time range locally
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(hours=hours)
            
            if not weather_data:
                return []
            
            # Convert to WeatherCondition objects
            conditions = []
            for data in weather_data:
                try:
                    timestamp = datetime.fromisoformat(data.get("date", "").replace("Z", "+00:00"))
                    # For historical data, just take the most recent data points instead of filtering by time
                    conditions.append(WeatherCondition(
                        air_temperature=data.get("air_temperature", 0),
                        track_temperature=data.get("track_temperature", 0),
                        humidity=data.get("humidity", 0),
                        pressure=data.get("pressure", 0),
                        wind_speed=data.get("wind_speed", 0),
                        wind_direction=data.get("wind_direction"),
                        rainfall=data.get("rainfall", 0),
                        timestamp=timestamp,
                        session_key=session_key
                    ))
                except Exception as e:
                    continue  # Skip invalid data points
            
            # Sort by timestamp and take the most recent data points
            sorted_conditions = sorted(conditions, key=lambda x: x.timestamp, reverse=True)
            # Return the most recent data points (limit based on hours requested)
            max_points = hours * 20  # Approximate 20 points per hour
            return sorted_conditions[:max_points][::-1]  # Reverse to get chronological order
            
            # This line is now handled above
            pass
            
        except Exception as e:
            print(f"Error getting weather history: {e}")
            return []
    
    def analyze_temperature_trend(self, conditions: List[WeatherCondition]) -> Dict[str, WeatherTrend]:
        """Analyze temperature trends from weather history"""
        if len(conditions) < 3:
            return {}
        
        air_temps = [c.air_temperature for c in conditions]
        track_temps = [c.track_temperature for c in conditions]
        
        trends = {}
        
        # Analyze air temperature trend
        if len(air_temps) >= 3:
            recent_avg = statistics.mean(air_temps[-3:])
            earlier_avg = statistics.mean(air_temps[:3])
            rate = (recent_avg - earlier_avg) / len(air_temps)
            
            if abs(rate) < 0.5:
                trend_type = "stable"
            elif rate > 0:
                trend_type = "rising"
            else:
                trend_type = "falling"
            
            trends["air_temperature"] = WeatherTrend(
                trend_type=trend_type,
                rate_of_change=rate,
                confidence=min(0.9, len(air_temps) / 10),
                prediction_window=30
            )
        
        # Analyze track temperature trend
        if len(track_temps) >= 3:
            recent_avg = statistics.mean(track_temps[-3:])
            earlier_avg = statistics.mean(track_temps[:3])
            rate = (recent_avg - earlier_avg) / len(track_temps)
            
            if abs(rate) < 1.0:
                trend_type = "stable"
            elif rate > 0:
                trend_type = "rising"
            else:
                trend_type = "falling"
            
            trends["track_temperature"] = WeatherTrend(
                trend_type=trend_type,
                rate_of_change=rate,
                confidence=min(0.9, len(track_temps) / 10),
                prediction_window=30
            )
        
        return trends
    
    def get_tire_recommendation(self, condition: WeatherCondition) -> TireRecommendation:
        """Get tire compound recommendation based on weather conditions"""
        reasoning = []
        risk_factors = []
        
        # Rain analysis
        if condition.rainfall > 0:
            if condition.rainfall > 2:
                return TireRecommendation(
                    compound="full_wet",
                    confidence=0.95,
                    reasoning=["Heavy rain detected", "Track surface wet"],
                    risk_factors=["Aquaplaning risk", "Reduced visibility"],
                    optimal_temp_range=(5, 40),
                    expected_degradation="low"
                )
            else:
                return TireRecommendation(
                    compound="intermediate",
                    confidence=0.85,
                    reasoning=["Light rain/damp conditions", "Crossover compound optimal"],
                    risk_factors=["Changing track conditions"],
                    optimal_temp_range=(10, 45),
                    expected_degradation="medium"
                )
        
        # Dry conditions analysis
        track_temp = condition.track_temperature
        air_temp = condition.air_temperature
        humidity = condition.humidity
        
        # Temperature-based compound selection
        if track_temp > 50:
            compound = "hard"
            reasoning.append(f"High track temperature ({track_temp}°C)")
            optimal_range = (40, 70)
            degradation = "low"
            confidence = 0.9
        elif track_temp > 35:
            compound = "medium"
            reasoning.append(f"Moderate track temperature ({track_temp}°C)")
            optimal_range = (30, 55)
            degradation = "medium"
            confidence = 0.85
        else:
            compound = "soft"
            reasoning.append(f"Cool track temperature ({track_temp}°C)")
            optimal_range = (25, 45)
            degradation = "high"
            confidence = 0.8
        
        # Environmental factors
        if condition.wind_speed > 15:
            risk_factors.append("Strong winds affecting car stability")
            confidence *= 0.9
        
        if humidity > 80:
            risk_factors.append("High humidity - rain risk")
            confidence *= 0.95
        
        # Temperature delta considerations
        temp_delta = track_temp - air_temp
        if temp_delta > 20:
            reasoning.append("Large temperature delta - tire warming critical")
        elif temp_delta < 10:
            reasoning.append("Small temperature delta - consistent conditions")
        
        return TireRecommendation(
            compound=compound,
            confidence=confidence,
            reasoning=reasoning,
            risk_factors=risk_factors,
            optimal_temp_range=optimal_range,
            expected_degradation=degradation
        )
    
    def calculate_race_impact(self, condition: WeatherCondition, trends: Dict[str, WeatherTrend]) -> Dict[str, Any]:
        """Calculate weather impact on race strategy"""
        impact = {
            "pit_strategy_impact": "normal",
            "safety_car_probability": "low",
            "tire_degradation_factor": 1.0,
            "fuel_consumption_impact": 1.0,
            "lap_time_impact": 0.0,  # seconds per lap
            "strategic_considerations": []
        }
        
        # Rain impact
        if condition.rainfall > 0:
            impact["safety_car_probability"] = "high" if condition.rainfall > 2 else "medium"
            impact["pit_strategy_impact"] = "critical"
            impact["lap_time_impact"] = 5.0 if condition.rainfall > 2 else 2.0
            impact["strategic_considerations"].append("Weather-dependent tire strategy")
        
        # Temperature impact
        if condition.track_temperature > 50:
            impact["tire_degradation_factor"] = 1.3
            impact["strategic_considerations"].append("High tire degradation expected")
        elif condition.track_temperature < 25:
            impact["tire_degradation_factor"] = 0.8
            impact["lap_time_impact"] = 1.0
            impact["strategic_considerations"].append("Tire warming challenges")
        
        # Wind impact
        if condition.wind_speed > 15:
            impact["fuel_consumption_impact"] = 1.05
            impact["lap_time_impact"] += 0.5
            impact["strategic_considerations"].append("Increased fuel consumption due to wind")
        
        # Trend-based predictions
        if "track_temperature" in trends:
            trend = trends["track_temperature"]
            if trend.trend_type == "rising" and trend.rate_of_change > 2:
                impact["strategic_considerations"].append("Rising track temps - consider tire strategy adjustment")
            elif trend.trend_type == "falling" and trend.rate_of_change < -2:
                impact["strategic_considerations"].append("Cooling track - grip may improve")
        
        return impact
    
    async def get_comprehensive_analysis(self, session_key: int) -> Dict[str, Any]:
        """Get comprehensive weather analysis for race strategy"""
        try:
            # Get current conditions
            current = await self.get_current_weather(session_key)
            if not current:
                # Return error if no data is available
                return {"error": "No weather data available for this session"}
            
            # Get weather history
            history = await self.get_weather_history(session_key, hours=3)
            
            # Analyze trends
            trends = self.analyze_temperature_trend(history)
            
            # Get tire recommendation
            tire_rec = self.get_tire_recommendation(current)
            
            # Calculate race impact
            race_impact = self.calculate_race_impact(current, trends)
            
            return {
                "timestamp": datetime.utcnow().isoformat(),
                "session_key": session_key,
                "current_conditions": {
                    "air_temperature": current.air_temperature,
                    "track_temperature": current.track_temperature,
                    "humidity": current.humidity,
                    "pressure": current.pressure,
                    "wind_speed": current.wind_speed,
                    "wind_direction": current.wind_direction,
                    "rainfall": current.rainfall
                },
                "trends": {
                    trend_name: {
                        "type": trend.trend_type,
                        "rate": round(trend.rate_of_change, 2),
                        "confidence": round(trend.confidence, 2)
                    }
                    for trend_name, trend in trends.items()
                },
                "tire_recommendation": {
                    "compound": tire_rec.compound,
                    "confidence": round(tire_rec.confidence, 2),
                    "reasoning": tire_rec.reasoning,
                    "risk_factors": tire_rec.risk_factors,
                    "expected_degradation": tire_rec.expected_degradation
                },
                "race_impact": race_impact,
                "data_quality": {
                    "history_points": len(history),
                    "trend_confidence": round(statistics.mean([t.confidence for t in trends.values()]), 2) if trends else 0
                }
            }
        except Exception as e:
            print(f"Error in get_comprehensive_analysis: {e}")
            return {"error": f"Failed to analyze weather data: {str(e)}"}
    
    def _get_mock_analysis(self, session_key: int) -> Dict[str, Any]:
        """Return mock analysis data for testing purposes"""
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "session_key": session_key,
            "current_conditions": {
                "air_temperature": 25.5,
                "track_temperature": 38.2,
                "humidity": 65.0,
                "pressure": 1013.2,
                "wind_speed": 12.5,
                "wind_direction": 180,
                "rainfall": 0.0
            },
            "trends": {
                "air_temperature": {
                    "type": "rising",
                    "rate": 0.5,
                    "confidence": 0.85
                },
                "track_temperature": {
                    "type": "rising",
                    "rate": 1.2,
                    "confidence": 0.9
                }
            },
            "tire_recommendation": {
                "compound": "medium",
                "confidence": 0.85,
                "reasoning": [
                    "Moderate track temperature (38.2°C)",
                    "Dry conditions expected",
                    "Small temperature delta - consistent conditions"
                ],
                "risk_factors": [],
                "expected_degradation": "medium"
            },
            "race_impact": {
                "pit_strategy_impact": "normal",
                "safety_car_probability": "low",
                "tire_degradation_factor": 1.0,
                "fuel_consumption_impact": 1.0,
                "lap_time_impact": 0.0,
                "strategic_considerations": ["Rising track temps - consider tire strategy adjustment"]
            },
            "data_quality": {
                "history_points": 15,
                "trend_confidence": 0.88
            }
        }

# Global instance
weather_service = WeatherService()