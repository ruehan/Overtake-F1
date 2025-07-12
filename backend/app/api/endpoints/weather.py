from fastapi import APIRouter, Query, HTTPException
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import statistics

from app.services.openf1_client import openf1_client
from app.core.exceptions import OpenF1APIException
from app.services.weather_service import weather_service

router = APIRouter()

@router.get("", response_model=List[Dict[str, Any]])
async def get_weather(
    session_key: Optional[int] = Query(None, description="Session key"),
    date: Optional[datetime] = Query(None, description="Date filter")
):
    try:
        weather = await openf1_client.get_weather(
            session_key=session_key,
            date=date
        )
        return weather
    except OpenF1APIException as e:
        raise HTTPException(
            status_code=e.status_code or 500,
            detail=e.message
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/current", response_model=Dict[str, Any])
async def get_current_weather(
    session_key: int = Query(..., description="Session key")
):
    try:
        weather_data = await openf1_client.get_weather(session_key=session_key)
        if not weather_data:
            raise HTTPException(status_code=404, detail="No weather data found")
        
        # Return the most recent weather data
        latest_weather = max(
            weather_data,
            key=lambda x: x.get("timestamp", 0)
        )
        return latest_weather
    except OpenF1APIException as e:
        raise HTTPException(
            status_code=e.status_code or 500,
            detail=e.message
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/analysis", response_model=Dict[str, Any])
async def get_weather_analysis(
    session_key: int = Query(..., description="Session key"),
    hours: int = Query(3, description="Hours to analyze", ge=1, le=24)
):
    """Analyze weather trends and impact on race conditions"""
    try:
        # Use the weather service for comprehensive analysis
        analysis = await weather_service.get_comprehensive_analysis(session_key)
        
        if "error" in analysis:
            raise HTTPException(status_code=404, detail=analysis["error"])
        
        return analysis
        
    except OpenF1APIException as e:
        raise HTTPException(
            status_code=e.status_code or 500,
            detail=e.message
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/tire-strategy", response_model=Dict[str, Any])
async def get_tire_strategy_analysis(
    session_key: int = Query(..., description="Session key")
):
    """Analyze tire strategy recommendations based on weather conditions"""
    try:
        # Get current weather condition
        current_weather = await weather_service.get_current_weather(session_key)
        
        if not current_weather:
            raise HTTPException(status_code=404, detail="No weather data found")
        
        # Get tire recommendation
        tire_recommendation = weather_service.get_tire_recommendation(current_weather)
        
        return {
            "session_key": session_key,
            "current_weather": {
                "air_temperature": current_weather.air_temperature,
                "track_temperature": current_weather.track_temperature,
                "humidity": current_weather.humidity,
                "pressure": current_weather.pressure,
                "wind_speed": current_weather.wind_speed,
                "wind_direction": current_weather.wind_direction,
                "rainfall": current_weather.rainfall
            },
            "tire_strategy": {
                "compound": tire_recommendation.compound,
                "confidence": tire_recommendation.confidence,
                "reasoning": tire_recommendation.reasoning,
                "risk_factors": tire_recommendation.risk_factors,
                "expected_degradation": tire_recommendation.expected_degradation
            },
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except OpenF1APIException as e:
        raise HTTPException(
            status_code=e.status_code or 500,
            detail=e.message
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

def analyze_weather_trends(weather_data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Analyze weather trends from historical data"""
    if not weather_data:
        return {}
    
    # Extract numeric values
    temperatures = [w.get("air_temperature", 0) for w in weather_data if w.get("air_temperature")]
    track_temps = [w.get("track_temperature", 0) for w in weather_data if w.get("track_temperature")]
    humidity = [w.get("humidity", 0) for w in weather_data if w.get("humidity")]
    pressure = [w.get("pressure", 0) for w in weather_data if w.get("pressure")]
    wind_speeds = [w.get("wind_speed", 0) for w in weather_data if w.get("wind_speed")]
    
    analysis = {
        "temperature_trend": {
            "air_temperature": {
                "current": temperatures[-1] if temperatures else 0,
                "average": round(statistics.mean(temperatures), 1) if temperatures else 0,
                "min": min(temperatures) if temperatures else 0,
                "max": max(temperatures) if temperatures else 0,
                "trend": "stable"
            },
            "track_temperature": {
                "current": track_temps[-1] if track_temps else 0,
                "average": round(statistics.mean(track_temps), 1) if track_temps else 0,
                "min": min(track_temps) if track_temps else 0,
                "max": max(track_temps) if track_temps else 0,
                "trend": "stable"
            }
        },
        "humidity": {
            "current": humidity[-1] if humidity else 0,
            "average": round(statistics.mean(humidity), 1) if humidity else 0,
            "trend": "stable"
        },
        "pressure": {
            "current": pressure[-1] if pressure else 0,
            "average": round(statistics.mean(pressure), 1) if pressure else 0,
            "trend": "stable"
        },
        "wind": {
            "current_speed": wind_speeds[-1] if wind_speeds else 0,
            "average_speed": round(statistics.mean(wind_speeds), 1) if wind_speeds else 0,
            "max_speed": max(wind_speeds) if wind_speeds else 0
        }
    }
    
    # Calculate trends
    if len(temperatures) >= 3:
        recent_temp = statistics.mean(temperatures[-3:])
        earlier_temp = statistics.mean(temperatures[:3])
        if recent_temp > earlier_temp + 2:
            analysis["temperature_trend"]["air_temperature"]["trend"] = "rising"
        elif recent_temp < earlier_temp - 2:
            analysis["temperature_trend"]["air_temperature"]["trend"] = "falling"
    
    if len(track_temps) >= 3:
        recent_track = statistics.mean(track_temps[-3:])
        earlier_track = statistics.mean(track_temps[:3])
        if recent_track > earlier_track + 3:
            analysis["temperature_trend"]["track_temperature"]["trend"] = "rising"
        elif recent_track < earlier_track - 3:
            analysis["temperature_trend"]["track_temperature"]["trend"] = "falling"
    
    return analysis

def analyze_tire_strategy(weather: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze optimal tire strategy based on weather conditions"""
    air_temp = weather.get("air_temperature", 20)
    track_temp = weather.get("track_temperature", 30)
    humidity = weather.get("humidity", 50)
    rainfall = weather.get("rainfall", 0)
    wind_speed = weather.get("wind_speed", 5)
    
    strategy = {
        "recommended_compound": "medium",
        "reasoning": [],
        "risk_factors": [],
        "pit_window_impact": "normal",
        "safety_car_probability": "low"
    }
    
    # Rain analysis
    if rainfall > 0:
        if rainfall > 2:
            strategy["recommended_compound"] = "full_wet"
            strategy["reasoning"].append("Heavy rain detected - full wet tires required")
            strategy["safety_car_probability"] = "high"
        else:
            strategy["recommended_compound"] = "intermediate"
            strategy["reasoning"].append("Light rain - intermediate tires recommended")
            strategy["safety_car_probability"] = "medium"
    else:
        # Dry conditions analysis
        if track_temp > 50:
            strategy["recommended_compound"] = "hard"
            strategy["reasoning"].append("High track temperature favors hard compound")
        elif track_temp > 35:
            strategy["recommended_compound"] = "medium"
            strategy["reasoning"].append("Moderate track temperature suits medium compound")
        else:
            strategy["recommended_compound"] = "soft"
            strategy["reasoning"].append("Cool track temperature allows soft compound")
    
    # Wind impact
    if wind_speed > 15:
        strategy["risk_factors"].append("Strong winds may affect car stability")
        strategy["safety_car_probability"] = "medium"
    
    # Humidity impact
    if humidity > 80:
        strategy["risk_factors"].append("High humidity increases rain probability")
        strategy["pit_window_impact"] = "monitor_closely"
    
    # Temperature delta analysis
    temp_delta = track_temp - air_temp
    if temp_delta > 20:
        strategy["reasoning"].append("Large temperature delta - tire warming critical")
    
    return strategy