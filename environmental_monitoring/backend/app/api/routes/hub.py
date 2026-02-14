"""
Data Aggregation Hub Routes - One-Stop Shop for Environmental Data.

This module provides the central aggregation endpoints that combine data
from 15+ external APIs into unified responses.
"""
import asyncio
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query

from app.security import RateLimiter
from app.services.data_aggregator import (
    data_aggregator,
    connection_analyzer,
    DataCategory
)


router = APIRouter(tags=["Data Hub"])


# Rate limiter for resource-intensive aggregation operations
heavy_rate_limiter = RateLimiter(calls=10, period=60)  # 10 calls per minute
light_rate_limiter = RateLimiter(calls=30, period=60)  # 30 calls per minute


@router.get("", dependencies=[Depends(light_rate_limiter)])
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


@router.get("/sources", dependencies=[Depends(light_rate_limiter)])
async def get_hub_sources(
    category: Optional[str] = Query(
        None,
        description="Filter by category (air_quality, water, weather, etc.)"
    )
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


@router.get("/categories", dependencies=[Depends(light_rate_limiter)])
async def get_hub_categories():
    """
    List all data categories with their available sources.
    """
    return {
        "categories": data_aggregator.get_categories(),
        "available_categories": [c.value for c in DataCategory]
    }


@router.get("/proxy/{source_id}", dependencies=[Depends(heavy_rate_limiter)])
async def proxy_to_source(
    source_id: str,
    endpoint: str = Query(
        ...,
        description="API endpoint path (e.g., /locations?limit=10)"
    ),
):
    """
    Proxy a request to an external data source.
    
    This forwards your request to the external API and returns the response.
    Use this for direct access to any source's API.
    
    Example: /hub/proxy/openaq?endpoint=/locations?limit=5&country=US
    """
    result = await data_aggregator.proxy_request(source_id, endpoint)
    if not result.get("success"):
        raise HTTPException(
            status_code=400,
            detail=result.get("error", "Request failed")
        )
    return result


@router.get("/location", dependencies=[Depends(heavy_rate_limiter)])
async def aggregate_for_location(
    lat: float = Query(..., ge=-90, le=90, description="Latitude"),
    lon: float = Query(..., ge=-180, le=180, description="Longitude"),
    radius_km: float = Query(
        50.0,
        ge=1,
        le=500,
        description="Search radius in kilometers"
    ),
    categories: Optional[str] = Query(
        None,
        description="Comma-separated categories to include"
    )
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
    result = await data_aggregator.aggregate_by_location(
        lat, lon, cat_list, radius_km
    )
    return result


@router.get("/category/{category}", dependencies=[Depends(heavy_rate_limiter)])
async def aggregate_by_category(
    category: str,
    lat: Optional[float] = Query(None, ge=-90, le=90, description="Latitude for location-aware sources"),
    lon: Optional[float] = Query(None, ge=-180, le=180, description="Longitude for location-aware sources"),
    days: Optional[int] = Query(None, ge=1, le=365, description="Number of days to aggregate (e.g. 7, 30, 90)"),
):
    """
    Get data from all sources in a specific category.
    
    Categories: air_quality, water, weather, climate, marine, radiation,
    wildfires, earthquakes, biodiversity, soil
    
    Pass lat/lon for sources that require location (e.g. SoilGrids, Climate).
    Pass days to control the time-aggregation window (default varies by source).
    """
    params = {}
    if lat is not None:
        params["lat"] = lat
        params["latitude"] = lat
    if lon is not None:
        params["lon"] = lon
        params["longitude"] = lon
    if days is not None:
        params["days"] = days
    result = await data_aggregator.aggregate_by_category(category, params if params else None)
    if not result.get("success", True):
        raise HTTPException(status_code=400, detail=result.get("error"))
    return result


# ============================================================================
# CONNECT THE DOTS - Turn Data into Actionable Insights
# ============================================================================

@router.get("/analyze", dependencies=[Depends(heavy_rate_limiter)])
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


@router.get("/analyze/rules", dependencies=[Depends(light_rate_limiter)])
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


@router.get("/quick", dependencies=[Depends(heavy_rate_limiter)])
async def quick_environmental_check(
    lat: float = Query(
        37.7749,
        ge=-90,
        le=90,
        description="Latitude (default: San Francisco)"
    ),
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
        f"/query?format=geojson&latitude={lat}&longitude={lon}"
        f"&maxradiuskm=100&limit=5"
    )
    
    # Summarize — normalize to canonical field names
    weather_current = {}
    if weather.get("success") and weather.get("data"):
        cw = weather["data"].get("current_weather", {})
        weather_current = {
            "temperature_c": cw.get("temperature"),
            "wind_speed_kmh": cw.get("windspeed"),
            "wind_direction_deg": cw.get("winddirection"),
            "weather_code": cw.get("weathercode")
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
        "quick_status": (
            "✅ No immediate hazards detected"
            if eq_count == 0
            else f"⚠️ {eq_count} recent earthquakes in area"
        )
    }


# ============================================================================
# STATE-LEVEL MAP DATA - Spatial data for entire state bounding box
# ============================================================================

@router.get("/state-map", dependencies=[Depends(heavy_rate_limiter)])
async def get_state_map_data(
    south: float = Query(..., ge=-90, le=90, description="Southern latitude bound"),
    west: float = Query(..., ge=-180, le=180, description="Western longitude bound"),
    north: float = Query(..., ge=-90, le=90, description="Northern latitude bound"),
    east: float = Query(..., ge=-180, le=180, description="Eastern longitude bound"),
):
    """
    Get map-plottable data points for an entire state/region bounding box.

    Queries spatial sources (earthquakes, water, wildfires, biodiversity, air quality)
    using the bounding box, and point sources (weather, soil, climate, marine, radiation)
    at a grid of sample locations within the box.

    Returns data optimized for map rendering with lat/lon coordinates for each point.
    """
    bbox_str = f"{west:.2f},{south:.2f},{east:.2f},{north:.2f}"
    center_lat = (south + north) / 2
    center_lon = (west + east) / 2

    # Calculate rough diagonal for reference
    lat_diff = north - south
    lon_diff = east - west

    results = {
        "bbox": {"south": south, "west": west, "north": north, "east": east},
        "timestamp": datetime.utcnow().isoformat(),
        "sources": {}
    }

    # ---- Spatial sources (support bbox or large radius) ----
    spatial_tasks = {}

    # Earthquakes - USGS supports bbox
    spatial_tasks["earthquakes"] = data_aggregator.proxy_request(
        "usgs_earthquake",
        f"/query?format=geojson&minlatitude={south}&maxlatitude={north}"
        f"&minlongitude={west}&maxlongitude={east}&limit=50"
    )

    # Water stations - USGS supports bbox
    spatial_tasks["water"] = data_aggregator.proxy_request(
        "usgs_water",
        f"/iv/?format=json&bBox={bbox_str}"
        f"&parameterCd=00060,00065,00010&period=PT2H&siteStatus=active&siteType=ST"
    )

    # Biodiversity - GBIF supports bbox via decimalLatitude/decimalLongitude ranges
    spatial_tasks["biodiversity"] = data_aggregator.proxy_request(
        "gbif",
        f"/occurrence/search?decimalLatitude={south},{north}"
        f"&decimalLongitude={west},{east}&limit=80&hasCoordinate=true"
    )

    # Wildfires - NASA FIRMS supports bbox
    spatial_tasks["wildfires"] = data_aggregator.proxy_request(
        "nasa_firms",
        f"/area/csv/{{MAP_KEY}}/VIIRS_SNPP_NRT/{bbox_str}/1"
    )

    # Marine - Open-Meteo marine at center
    spatial_tasks["marine"] = data_aggregator.proxy_request(
        "open_meteo_marine",
        f"/marine?latitude={center_lat}&longitude={center_lon}"
        f"&current=wave_height,wave_direction,wave_period,sea_surface_temperature"
        f"&hourly=wave_height&forecast_days=1"
    )

    # ---- Grid-based sources (sample multiple points) ----
    # Generate a 3x3 grid across the state
    grid_points = []
    lat_step = lat_diff / 4
    lon_step = lon_diff / 4
    for i in range(1, 4):
        for j in range(1, 4):
            grid_points.append((
                round(south + i * lat_step, 4),
                round(west + j * lon_step, 4)
            ))

    # Weather at grid points
    weather_tasks = []
    for glat, glon in grid_points:
        weather_tasks.append(data_aggregator.proxy_request(
            "open_meteo",
            f"/forecast?latitude={glat}&longitude={glon}&current_weather=true"
        ))

    # Air quality at grid points (Open-Meteo AQ is free, no key needed)
    aq_tasks = []
    for glat, glon in grid_points:
        aq_tasks.append(data_aggregator.proxy_request(
            "open_meteo_aq",
            f"/air-quality?latitude={glat}&longitude={glon}"
            f"&current=us_aqi,pm2_5,pm10"
        ))

    # Radiation at grid points
    radiation_tasks = []
    for glat, glon in grid_points:
        radiation_tasks.append(data_aggregator.proxy_request(
            "open_meteo_uv",
            f"/forecast?latitude={glat}&longitude={glon}"
            f"&hourly=uv_index,direct_radiation&forecast_days=1"
        ))

    # Execute all spatial tasks in parallel
    spatial_keys = list(spatial_tasks.keys())
    spatial_results = await asyncio.gather(
        *spatial_tasks.values(), return_exceptions=True
    )
    for key, resp in zip(spatial_keys, spatial_results):
        if isinstance(resp, Exception):
            results["sources"][key] = {"error": str(resp)}
        else:
            results["sources"][key] = resp

    # Execute grid tasks in parallel
    weather_results = await asyncio.gather(*weather_tasks, return_exceptions=True)
    aq_results = await asyncio.gather(*aq_tasks, return_exceptions=True)
    radiation_results = await asyncio.gather(*radiation_tasks, return_exceptions=True)

    # Package grid results with their coordinates (canonical field names)
    weather_points = []
    for (glat, glon), resp in zip(grid_points, weather_results):
        if isinstance(resp, Exception) or not resp.get("success"):
            continue
        cw = (resp.get("data") or {}).get("current_weather", {})
        if cw:
            weather_points.append({
                "lat": glat, "lon": glon,
                "temperature_c": cw.get("temperature"),
                "wind_speed_kmh": cw.get("windspeed"),
                "weather_code": cw.get("weathercode"),
            })
    results["sources"]["weather"] = {"points": weather_points}

    aq_points = []
    for (glat, glon), resp in zip(grid_points, aq_results):
        if isinstance(resp, Exception) or not resp.get("success"):
            continue
        current = (resp.get("data") or {}).get("current", {})
        if current:
            aq_points.append({
                "lat": glat, "lon": glon,
                "us_aqi": current.get("us_aqi"),
                "pm2_5": current.get("pm2_5"),
                "pm10": current.get("pm10"),
            })
    results["sources"]["air_quality"] = {"points": aq_points}

    radiation_points = []
    for (glat, glon), resp in zip(grid_points, radiation_results):
        if isinstance(resp, Exception) or not resp.get("success"):
            continue
        hourly = (resp.get("data") or {}).get("hourly", {})
        uv_vals = hourly.get("uv_index", [])
        if uv_vals:
            # Take the maximum UV index for display
            clean = [v for v in uv_vals if v is not None]
            max_uv = max(clean) if clean else None
            if max_uv is not None:
                radiation_points.append({
                    "lat": glat, "lon": glon,
                    "uv_index_max": max_uv,
                })
    results["sources"]["radiation"] = {"points": radiation_points}

    results["grid_points"] = len(grid_points)
    return results
