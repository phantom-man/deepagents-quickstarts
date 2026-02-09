"""
Public data source routes - fetching from external APIs.
"""
import logging
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from app.services.data_sources import (
    data_ingestion_manager,
    fetch_air_quality,
    fetch_water_quality,
    fetch_weather
)
from app.services.data_quality import (
    data_validator,
    freshness_monitor,
    DataQualityLevel,
    PARAMETER_RANGES
)
from app.security import verify_api_key, RateLimiter

logger = logging.getLogger(__name__)

router = APIRouter()


# ============================================================================
# PUBLIC DATA SOURCE ROUTES
# ============================================================================

@router.get("/status")
async def get_data_sources_status():
    """Get status of all configured public data sources."""
    return data_ingestion_manager.get_status()


@router.get("/air-quality", dependencies=[Depends(RateLimiter(calls=30, period=60))])
async def get_air_quality_data(
    city: Optional[str] = Query(None, description="City name (optional)"),
    country: str = Query("US", description="Country code (ISO 3166-1 alpha-2)"),
    parameter: str = Query("pm25", description="Parameter: pm25, pm10, o3, no2, so2, co")
):
    """
    Fetch real-time air quality data from OpenAQ.
    
    This endpoint uses OpenAQ, a free and open-source air quality data platform
    that aggregates data from government monitoring stations worldwide.
    
    No API key required.
    """
    try:
        data = await fetch_air_quality(city=city, country=country)
        return {
            "success": True,
            "source": "OpenAQ",
            "data_count": len(data),
            "data": data,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to fetch air quality data: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch air quality data: {str(e)}")


@router.get("/water-quality", dependencies=[Depends(RateLimiter(calls=30, period=60))])
async def get_water_quality_data(
    state_code: str = Query("CA", description="US state code (e.g., CA, NY, TX)")
):
    """
    Fetch real-time water quality data from USGS Water Services.
    
    This endpoint uses USGS National Water Information System, which provides
    real-time stream flow, temperature, and water quality data from monitoring
    stations across the United States.
    
    No API key required.
    """
    try:
        data = await fetch_water_quality(state_code=state_code)
        return {
            "success": True,
            "source": "USGS Water Services",
            "data_count": len(data),
            "data": data,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to fetch water quality data: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch water quality data: {str(e)}")


@router.get("/weather", dependencies=[Depends(RateLimiter(calls=30, period=60))])
async def get_weather_data(
    lat: float = Query(37.7749, ge=-90, le=90, description="Latitude"),
    lon: float = Query(-122.4194, ge=-180, le=180, description="Longitude")
):
    """
    Fetch current weather data from OpenWeatherMap.
    
    This endpoint uses OpenWeatherMap API which provides current weather,
    forecasts, and historical data. Requires OPENWEATHERMAP_API_KEY environment variable.
    
    Free tier: 1000 calls/day, 60 calls/minute.
    """
    try:
        data = await fetch_weather(lat=lat, lon=lon)
        if not data:
            return {
                "success": False,
                "error": "OpenWeatherMap API key not configured or request failed",
                "hint": "Set OPENWEATHERMAP_API_KEY environment variable"
            }
        return {
            "success": True,
            "source": "OpenWeatherMap",
            "data_count": len(data),
            "data": data,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to fetch weather data: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch weather data: {str(e)}")


@router.get("/marine", dependencies=[Depends(RateLimiter(calls=30, period=60))])
async def get_marine_data(
    station_id: str = Query("46026", description="NOAA buoy station ID (e.g., 46026 for San Francisco)"),
    region: Optional[str] = Query(None, description="Region to list stations: california, pacific_northwest, gulf_of_mexico, atlantic")
):
    """
    Fetch marine/ocean data from NOAA National Data Buoy Center.
    
    This endpoint provides real-time marine observations including:
    - Water temperature
    - Wave height and period
    - Wind speed and direction
    - Air temperature over water
    - Atmospheric pressure
    
    Free, no API key required. Data updates hourly.
    """
    try:
        from app.services.data_sources import NOAABuoyClient
        
        client = NOAABuoyClient()
        
        # If region specified, return station list
        if region:
            stations = await client.fetch_stations(region=region)
            return {
                "success": True,
                "source": "NOAA NDBC",
                "region": region,
                "stations": stations
            }
        
        # Otherwise fetch data for the station
        data = await client.fetch_data(station_id=station_id)
        await client.close()
        
        return {
            "success": True,
            "source": "NOAA NDBC",
            "station_id": station_id,
            "data_count": len(data),
            "data": data,
            "timestamp": datetime.utcnow().isoformat(),
            "note": "Data from NOAA National Data Buoy Center"
        }
    except Exception as e:
        logger.error(f"Failed to fetch marine data: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch marine data: {str(e)}")


@router.get("/all", dependencies=[Depends(RateLimiter(calls=10, period=60))])
async def fetch_all_data_sources():
    """
    Fetch data from all configured public data sources in parallel.
    
    This endpoint aggregates data from:
    - OpenAQ (air quality)
    - USGS Water Services (water quality)
    - OpenWeatherMap (weather, if API key configured)
    - EPA AirNow (US AQI, if API key configured)
    
    Returns normalized data from all sources.
    """
    try:
        all_data = await data_ingestion_manager.fetch_all_data()
        
        total_records = sum(len(records) for records in all_data.values())
        
        return {
            "success": True,
            "sources_queried": list(all_data.keys()),
            "total_records": total_records,
            "data": all_data,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to fetch data: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch data: {str(e)}")


@router.post("/ingestion/start", dependencies=[Depends(verify_api_key)])
async def start_continuous_ingestion():
    """
    Start continuous data ingestion from all configured sources.
    
    Requires authentication as this starts a resource-intensive background process.
    
    This runs in the background and polls each data source at its configured
    interval (typically 5-60 minutes depending on source).
    """
    try:
        await data_ingestion_manager.start_continuous_ingestion()
        return {
            "success": True,
            "message": "Continuous data ingestion started",
            "status": data_ingestion_manager.get_status()
        }
    except Exception as e:
        logger.error(f"Failed to start ingestion: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start ingestion: {str(e)}")


@router.post("/ingestion/stop", dependencies=[Depends(verify_api_key)])
async def stop_continuous_ingestion():
    """
    Stop continuous data ingestion.
    
    Requires authentication.
    """
    try:
        await data_ingestion_manager.stop()
        return {
            "success": True,
            "message": "Continuous data ingestion stopped"
        }
    except Exception as e:
        logger.error(f"Failed to stop ingestion: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to stop ingestion: {str(e)}")


# ============================================================================
# DATA QUALITY ROUTES
# ============================================================================

@router.get("/quality/freshness")
async def get_data_freshness():
    """
    Check freshness status of all data sources.
    
    Returns status for each configured source:
    - fresh: Data received within expected interval
    - stale: Data is older than expected but not critical
    - critical: Data is significantly old, possible outage
    """
    return freshness_monitor.check_freshness()


@router.get("/quality/parameters")
async def get_supported_parameters():
    """
    Get list of supported environmental parameters with their validation ranges.
    
    Returns valid ranges for each parameter type that can be used for
    data validation and quality scoring.
    """
    return {
        "parameters": PARAMETER_RANGES,
        "quality_levels": [level.value for level in DataQualityLevel]
    }


@router.post("/quality/validate")
async def validate_data(data: List[dict]):
    """
    Validate a batch of environmental data records.
    
    Each record should include:
    - parameter: The type of measurement (e.g., "pm25", "temperature")
    - value: The numeric measurement value
    - timestamp: ISO format timestamp
    - source: Data source identifier
    
    Returns validation results including quality scores and any issues found.
    """
    if not data:
        raise HTTPException(status_code=400, detail="No data provided")
    
    if len(data) > 1000:
        raise HTTPException(status_code=400, detail="Maximum 1000 records per batch")
    
    return data_validator.validate_batch(data)
