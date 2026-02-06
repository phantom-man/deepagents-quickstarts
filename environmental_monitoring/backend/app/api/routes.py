"""
API routes for Environmental Monitoring System
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from datetime import datetime

from app.schemas.schemas import (
    Sensor, SensorCreate,
    Alert, AlertCreate,
    GISLayer, GISLayerCreate,
    DashboardStats, SensorStats,
    APIResponse
)
from app.agents.ecodata_agent import ecodata_agent
from app.agents.climateml_agent import climateml_agent
from app.agents.geospatial_agent import geospatial_agent
from app.agents.alertsystem_agent import alertsystem_agent
from app.services.moltbook_collaboration import moltbook_collaboration
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

router = APIRouter()

# Sensor routes
@router.get("/sensors", response_model=List[Sensor])
async def get_sensors():
    """Get all sensors."""
    # In production, this would query the database
    # For demo, return mock data
    return [
        Sensor(
            id=1,
            name="Weather Station Alpha",
            type="weather",
            location="London Central",
            latitude=51.5074,
            longitude=-0.1276,
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
    ]

@router.post("/sensors", response_model=Sensor)
async def create_sensor(sensor: SensorCreate):
    """Create a new sensor."""
    sensor_id = await ecodata_agent.register_sensor(sensor)
    return Sensor(
        id=sensor_id,
        **sensor.dict(),
        is_active=True,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )

@router.get("/sensors/{sensor_id}/status")
async def get_sensor_status(sensor_id: int):
    """Get status for a specific sensor."""
    status = await ecodata_agent.get_sensor_status(sensor_id)
    if not status:
        raise HTTPException(status_code=404, detail="Sensor not found")
    return status

@router.get("/sensors/{sensor_id}/readings")
async def get_sensor_readings(
    sensor_id: int,
    limit: int = Query(100, ge=1, le=1000)
):
    """Get recent readings for a sensor."""
    readings = await ecodata_agent.get_sensor_readings(sensor_id, limit)
    return [dict(r) for r in readings]

# ML Prediction routes
@router.get("/predictions/sensor/{sensor_id}")
async def get_sensor_predictions(
    sensor_id: int,
    hours: int = Query(24, ge=1, le=168)
):
    """Get predictions for a sensor."""
    predictions = await climateml_agent.get_predictions(sensor_id, hours)
    return predictions

@router.get("/ml/performance")
async def get_ml_performance():
    """Get ML model performance metrics."""
    return await climateml_agent.get_model_performance()

# GIS and Spatial routes
@router.get("/gis/analysis/{analysis_type}")
async def get_spatial_analysis(analysis_type: str):
    """Get spatial analysis results."""
    valid_types = ["coverage", "zones", "interpolation"]
    if analysis_type not in valid_types:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid analysis type. Must be one of: {valid_types}"
        )
    return await geospatial_agent.get_spatial_analysis(analysis_type)

@router.get("/gis/map")
async def get_environmental_map():
    """Get the environmental monitoring map."""
    return await geospatial_agent.get_map()

@router.get("/gis/nearest-sensor")
async def find_nearest_sensor(
    latitude: float = Query(..., ge=-90, le=90),
    longitude: float = Query(..., ge=-180, le=180)
):
    """Find the nearest sensor to a location."""
    return await geospatial_agent.find_nearest_sensor(latitude, longitude)

@router.get("/gis/zone-info")
async def get_zone_info(
    latitude: float = Query(..., ge=-90, le=90),
    longitude: float = Query(..., ge=-180, le=180)
):
    """Get environmental zone information for a location."""
    return await geospatial_agent.get_zone_info(latitude, longitude)

@router.post("/gis/layers", response_model=GISLayer)
async def create_gis_layer(layer: GISLayerCreate):
    """Create a new GIS layer."""
    layer_id = await geospatial_agent.create_gis_layer(layer)
    return GISLayer(
        id=layer_id,
        **layer.dict(),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )

# Alert routes
@router.post("/alerts", response_model=Alert)
async def create_manual_alert(alert: AlertCreate):
    """Create a manual alert."""
    alert_id = await alertsystem_agent.create_manual_alert(alert)
    return Alert(
        id=alert_id,
        **alert.dict(),
        status="pending",
        sent_at=None,
        created_at=datetime.utcnow()
    )

@router.get("/alerts/history")
async def get_alert_history(days: int = Query(7, ge=1, le=30)):
    """Get alert history."""
    return await alertsystem_agent.get_alert_history(days)

@router.get("/alerts/statistics")
async def get_alert_statistics():
    """Get alert statistics."""
    return await alertsystem_agent.get_alert_statistics()

# Dashboard routes
@router.get("/dashboard/stats", response_model=DashboardStats)
async def get_dashboard_stats():
    """Get dashboard statistics."""
    # Mock data - in production, this would aggregate from all services
    return DashboardStats(
        total_sensors=3,
        active_sensors=3,
        total_readings_today=1440,
        active_alerts=2,
        predictions_made_today=72,
        system_health="excellent"
    )

@router.get("/dashboard/sensor-stats")
async def get_sensor_stats():
    """Get statistics for all sensors."""
    # Mock data
    return [
        SensorStats(
            sensor_id=1,
            sensor_name="Weather Station Alpha",
            reading_count=480,
            last_reading=datetime.utcnow(),
            avg_value_24h=15.2,
            anomaly_count_24h=0
        ),
        SensorStats(
            sensor_id=2,
            sensor_name="Air Quality Monitor Beta",
            reading_count=480,
            last_reading=datetime.utcnow(),
            avg_value_24h=42.1,
            anomaly_count_24h=1
        ),
        SensorStats(
            sensor_id=3,
            sensor_name="Water Quality Sensor Gamma",
            reading_count=480,
            last_reading=datetime.utcnow(),
            avg_value_24h=7.1,
            anomaly_count_24h=0
        )
    ]

# Collaboration routes
@router.post("/collaboration/run")
async def trigger_collaboration():
    """Trigger a collaborative analysis session."""
    await moltbook_collaboration.run_collaborative_analysis()
    return APIResponse(
        success=True,
        message="Collaborative analysis initiated",
        data={"session_id": moltbook_collaboration.session_id}
    )

@router.get("/collaboration/status")
async def get_collaboration_status():
    """Get current collaboration status."""
    return await moltbook_collaboration.get_collaboration_status()

@router.get("/collaboration/history")
async def get_collaboration_history(limit: int = Query(10, ge=1, le=100)):
    """Get collaboration history."""
    # Mock data - in production, this would query the database
    return [
        {
            "session_id": "session-001",
            "timestamp": datetime.utcnow().isoformat(),
            "agents_involved": ["ecodata", "climateml", "geospatial", "alertsystem"],
            "outcome": "success",
            "metrics": {
                "data_processed": 1440,
                "predictions_generated": 72,
                "alerts_created": 3
            }
        }
    ]

# System routes
@router.get("/system/health")
async def get_system_health():
    """Get comprehensive system health status."""
    return {
        "overall_status": "healthy",
        "agents": {
            "ecodata": {"status": "active", "last_active": datetime.utcnow().isoformat()},
            "climateml": {"status": "active", "last_active": datetime.utcnow().isoformat()},
            "geospatial": {"status": "active", "last_active": datetime.utcnow().isoformat()},
            "alertsystem": {"status": "active", "last_active": datetime.utcnow().isoformat()}
        },
        "services": {
            "database": "connected",
            "cache": "connected",
            "moltbook": "connected"
        },
        "timestamp": datetime.utcnow().isoformat()
    }

@router.post("/system/reset")
async def reset_system():
    """Reset all agents and services (for testing/development)."""
    # In production, this would have proper authentication and safeguards
    try:
        # Reset agents
        await ecodata_agent.cleanup()
        await climateml_agent.cleanup()
        await geospatial_agent.cleanup()
        await alertsystem_agent.cleanup()

        # Reinitialize
        await ecodata_agent.initialize()
        await climateml_agent.initialize()
        await geospatial_agent.initialize()
        await alertsystem_agent.initialize()

        return APIResponse(
            success=True,
            message="System reset complete",
            data={"timestamp": datetime.utcnow().isoformat()}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Reset failed: {str(e)}")


# ============================================================================
# PUBLIC DATA SOURCE ROUTES
# ============================================================================

@router.get("/data-sources/status")
async def get_data_sources_status():
    """Get status of all configured public data sources."""
    return data_ingestion_manager.get_status()


@router.get("/data-sources/air-quality")
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
        raise HTTPException(status_code=500, detail=f"Failed to fetch air quality data: {str(e)}")


@router.get("/data-sources/water-quality")
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
        raise HTTPException(status_code=500, detail=f"Failed to fetch water quality data: {str(e)}")


@router.get("/data-sources/weather")
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
        raise HTTPException(status_code=500, detail=f"Failed to fetch weather data: {str(e)}")


@router.get("/data-sources/marine")
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
    
    Suggested by FiverrClawOfficial on Moltbook.
    """
    try:
        from ..services.data_sources import NOAABuoyClient
        
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
        raise HTTPException(status_code=500, detail=f"Failed to fetch marine data: {str(e)}")


@router.get("/data-sources/all")
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
        raise HTTPException(status_code=500, detail=f"Failed to fetch data: {str(e)}")


@router.post("/data-sources/ingestion/start")
async def start_continuous_ingestion():
    """
    Start continuous data ingestion from all configured sources.
    
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
        raise HTTPException(status_code=500, detail=f"Failed to start ingestion: {str(e)}")


@router.post("/data-sources/ingestion/stop")
async def stop_continuous_ingestion():
    """Stop continuous data ingestion."""
    try:
        await data_ingestion_manager.stop()
        return {
            "success": True,
            "message": "Continuous data ingestion stopped"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to stop ingestion: {str(e)}")


# ============================================================================
# DATA QUALITY ROUTES
# ============================================================================

@router.get("/data-quality/freshness")
async def get_data_freshness():
    """
    Check freshness status of all data sources.
    
    Returns status for each configured source:
    - fresh: Data received within expected interval
    - stale: Data is older than expected but not critical
    - critical: Data is significantly old, possible outage
    """
    return freshness_monitor.check_freshness()


@router.get("/data-quality/parameters")
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


@router.post("/data-quality/validate")
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


# ============================================================================
# DATA AGGREGATION HUB - One-Stop Shop for Environmental Data
# ============================================================================

from app.services.data_aggregator import (
    data_aggregator,
    connection_analyzer,
    DataCategory
)


@router.get("/hub")
async def get_hub_info():
    """
    Environmental Data Aggregation Hub - Your one-stop shop for environmental data.
    
    This hub aggregates data from 15+ public APIs. We don't store the data -
    we forward requests and combine results from multiple sources.
    """
    categories = data_aggregator.get_categories()
    sources = data_aggregator.get_available_sources()
    
    return {
        "name": "Environmental Data Aggregation Hub",
        "description": "One-stop shop for environmental data from 15+ public APIs",
        "version": "1.0.0",
        "total_sources": len(sources),
        "categories": categories,
        "endpoints": {
            "sources": "/api/v1/hub/sources - List all data sources",
            "categories": "/api/v1/hub/categories - List data categories",
            "proxy": "/api/v1/hub/proxy/{source_id} - Proxy request to a source",
            "location": "/api/v1/hub/location - Aggregate data for a location",
            "analyze": "/api/v1/hub/analyze - Connect-the-dots analysis"
        }
    }


@router.get("/hub/sources")
async def get_hub_sources(
    category: Optional[str] = Query(None, description="Filter by category (air_quality, water, weather, etc.)")
):
    """
    List all available external data sources.
    
    These are APIs we can proxy requests to - we aggregate their data
    without storing it locally.
    """
    cat_enum = None
    if category:
        try:
            cat_enum = DataCategory(category)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid category. Valid options: {[c.value for c in DataCategory]}"
            )
    
    sources = data_aggregator.get_available_sources(cat_enum)
    return {
        "total": len(sources),
        "filter": category,
        "sources": sources
    }


@router.get("/hub/categories")
async def get_hub_categories():
    """
    List all data categories with their available sources.
    """
    return {
        "categories": data_aggregator.get_categories(),
        "available_categories": [c.value for c in DataCategory]
    }


@router.get("/hub/proxy/{source_id}")
async def proxy_to_source(
    source_id: str,
    endpoint: str = Query(..., description="API endpoint path (e.g., /locations?limit=10)"),
):
    """
    Proxy a request to an external data source.
    
    This forwards your request to the external API and returns the response.
    Use this for direct access to any source's API.
    
    Example: /hub/proxy/openaq?endpoint=/locations?limit=5&country=US
    """
    result = await data_aggregator.proxy_request(source_id, endpoint)
    if not result.get("success"):
        raise HTTPException(status_code=400, detail=result.get("error", "Request failed"))
    return result


@router.get("/hub/location")
async def aggregate_for_location(
    lat: float = Query(..., ge=-90, le=90, description="Latitude"),
    lon: float = Query(..., ge=-180, le=180, description="Longitude"),
    radius_km: float = Query(50.0, ge=1, le=500, description="Search radius in kilometers"),
    categories: Optional[str] = Query(None, description="Comma-separated categories to include")
):
    """
    🌍 ONE-STOP SHOP: Get all environmental data for a location.
    
    This aggregates data from multiple sources including:
    - Air quality (OpenAQ)
    - Weather (Open-Meteo)
    - Earthquakes (USGS)
    - And more based on availability
    
    Perfect for getting a complete environmental picture of any location.
    """
    cat_list = categories.split(",") if categories else None
    result = await data_aggregator.aggregate_by_location(lat, lon, cat_list, radius_km)
    return result


@router.get("/hub/category/{category}")
async def aggregate_by_category(
    category: str,
):
    """
    Get data from all sources in a specific category.
    
    Categories: air_quality, water, weather, climate, marine, radiation,
    wildfires, earthquakes, biodiversity, soil
    """
    result = await data_aggregator.aggregate_by_category(category)
    if not result.get("success", True):
        raise HTTPException(status_code=400, detail=result.get("error"))
    return result


# ============================================================================
# CONNECT THE DOTS - Turn Data into Actionable Insights
# ============================================================================

@router.get("/hub/analyze")
async def analyze_location(
    lat: float = Query(..., ge=-90, le=90, description="Latitude"),
    lon: float = Query(..., ge=-180, le=180, description="Longitude"),
    days: int = Query(7, ge=1, le=30, description="Days of history to analyze")
):
    """
    🔗 CONNECT THE DOTS: Analyze environmental data for correlations and insights.
    
    This looks for patterns like:
    - Air quality correlations with weather
    - Wildfire smoke affecting distant cities
    - Earthquake impacts on water quality
    - Marine temperatures affecting weather
    
    Returns actionable insights and monitoring recommendations.
    """
    analysis = await connection_analyzer.analyze_location(lat, lon, days)
    return analysis


@router.get("/hub/analyze/rules")
async def get_analysis_rules():
    """
    Get the correlation rules used for "Connect the Dots" analysis.
    
    These rules define how different environmental factors are connected
    and what patterns we look for.
    """
    return {
        "rules": connection_analyzer.get_correlation_rules(),
        "description": "Rules used to find connections between environmental data"
    }


@router.get("/hub/quick")
async def quick_environmental_check(
    lat: float = Query(37.7749, ge=-90, le=90, description="Latitude (default: San Francisco)"),
    lon: float = Query(-122.4194, ge=-180, le=180, description="Longitude")
):
    """
    ⚡ QUICK CHECK: Fast environmental overview for a location.
    
    Returns a simplified summary with key metrics:
    - Current weather
    - Air quality status
    - Any active hazards nearby
    
    Great for dashboards and quick lookups.
    """
    # Get Open-Meteo weather (always free, no key needed)
    weather = await data_aggregator.proxy_request(
        "open_meteo",
        f"/forecast?latitude={lat}&longitude={lon}&current_weather=true"
    )
    
    # Get recent earthquakes
    earthquakes = await data_aggregator.proxy_request(
        "usgs_earthquake",
        f"/query?format=geojson&latitude={lat}&longitude={lon}&maxradiuskm=100&limit=5"
    )
    
    # Summarize
    weather_current = {}
    if weather.get("success") and weather.get("data"):
        cw = weather["data"].get("current_weather", {})
        weather_current = {
            "temperature_c": cw.get("temperature"),
            "windspeed_kmh": cw.get("windspeed"),
            "winddirection": cw.get("winddirection"),
            "weathercode": cw.get("weathercode")
        }
    
    eq_count = 0
    if earthquakes.get("success") and earthquakes.get("data"):
        eq_count = len(earthquakes["data"].get("features", []))
    
    return {
        "location": {"latitude": lat, "longitude": lon},
        "timestamp": datetime.utcnow().isoformat(),
        "summary": {
            "weather": weather_current,
            "recent_earthquakes_nearby": eq_count,
            "air_quality": "Check /hub/location for full air quality data"
        },
        "quick_status": "✅ No immediate hazards detected" if eq_count == 0 else f"⚠️ {eq_count} recent earthquakes in area"
    }