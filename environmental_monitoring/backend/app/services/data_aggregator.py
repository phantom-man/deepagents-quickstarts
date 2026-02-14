"""
Environmental Data Aggregation Hub

A one-stop-shop for environmental data that:
1. Aggregates data from multiple external APIs
2. Proxies requests to APIs we don't store locally
3. Caches frequently accessed data
4. Provides unified query interface across all sources
5. Enables "Connect the Dots" correlation analysis

This is NOT a data warehouse - we forward requests to external APIs
and aggregate results, reducing storage costs while providing comprehensive access.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
import httpx

logger = logging.getLogger(__name__)


class DataCategory(Enum):
    """Categories of environmental data."""
    AIR_QUALITY = "air_quality"
    WATER = "water"
    WEATHER = "weather"
    CLIMATE = "climate"
    MARINE = "marine"
    RADIATION = "radiation"
    WILDFIRES = "wildfires"
    EARTHQUAKES = "earthquakes"
    BIODIVERSITY = "biodiversity"
    SOIL = "soil"


@dataclass
class ExternalDataSource:
    """Configuration for an external data source we aggregate from."""
    name: str
    category: DataCategory
    base_url: str
    description: str
    documentation_url: str
    requires_api_key: bool = False
    api_key_env_var: Optional[str] = None
    rate_limit_per_minute: int = 60
    is_free: bool = True
    coverage: str = "Global"  # Geographic coverage
    update_frequency: str = "Real-time"  # How often data updates
    data_format: str = "JSON"
    sample_endpoint: str = ""


# ============================================================================
# COMPREHENSIVE PUBLIC DATA SOURCE REGISTRY
# These are sources we can proxy/aggregate - we don't store their data
# ============================================================================

EXTERNAL_SOURCES: Dict[str, ExternalDataSource] = {
    # === AIR QUALITY ===
    "open_meteo_aq": ExternalDataSource(
        name="Open-Meteo Air Quality",
        category=DataCategory.AIR_QUALITY,
        base_url="https://air-quality-api.open-meteo.com/v1",
        description="Air quality index, PM2.5, PM10, ozone, NO2 from CAMS reanalysis (hourly aggregated to daily)",
        documentation_url="https://open-meteo.com/en/docs/air-quality-api",
        requires_api_key=False,
        coverage="Global",
        update_frequency="Hourly",
        sample_endpoint="/air-quality?latitude=37.77&longitude=-122.42&current=us_aqi,pm10,pm2_5,carbon_monoxide,nitrogen_dioxide,sulphur_dioxide,ozone&hourly=us_aqi,pm2_5,pm10,ozone,nitrogen_dioxide&past_days=7"
    ),
    "openaq": ExternalDataSource(
        name="OpenAQ",
        category=DataCategory.AIR_QUALITY,
        base_url="https://api.openaq.org/v2",
        description="Global air quality data from government and research stations (V2 retired)",
        documentation_url="https://docs.openaq.org/",
        requires_api_key=False,
        coverage="Global (90+ countries)",
        update_frequency="Real-time",
        sample_endpoint=""
    ),
    "airnow": ExternalDataSource(
        name="EPA AirNow",
        category=DataCategory.AIR_QUALITY,
        base_url="https://www.airnowapi.org/aq",
        description="Daily AQI aggregate from 2,500+ US monitoring stations",
        documentation_url="https://docs.airnowapi.org/",
        requires_api_key=True,
        api_key_env_var="AIRNOW_API_KEY",
        coverage="United States",
        update_frequency="Daily",
        sample_endpoint="__DAILY_AGGREGATE__&latitude=37.77&longitude=-122.42&distance=50"
    ),
    "iqair": ExternalDataSource(
        name="IQAir",
        category=DataCategory.AIR_QUALITY,
        base_url="https://api.airvisual.com/v2",
        description="Worldwide air quality data with health recommendations",
        documentation_url="https://www.iqair.com/air-quality-api",
        requires_api_key=True,
        api_key_env_var="IQAIR_API_KEY",
        coverage="Global",
        update_frequency="Real-time"
    ),
    
    # === WATER ===
    "usgs_water": ExternalDataSource(
        name="USGS Water Services (NWIS)",
        category=DataCategory.WATER,
        base_url="https://waterservices.usgs.gov/nwis",
        description="US stream flow, gage height, water temperature from 15-minute interval monitoring stations",
        documentation_url="https://waterservices.usgs.gov/docs/instantaneous-values/",
        requires_api_key=False,
        coverage="United States",
        update_frequency="15-minute intervals",
        sample_endpoint="/iv/?format=json&bBox=-122.92,37.27,-121.92,38.27&parameterCd=00060,00065,00010&period=PT2H&siteStatus=active&siteType=ST"
    ),
    "usgs_water_dv": ExternalDataSource(
        name="USGS Water Services Daily Values (Mirror)",
        category=DataCategory.WATER,
        base_url="https://waterservices.usgs.gov/nwis",
        description="Mirror: USGS daily average stream flow, gage height (identical JSON structure to instantaneous values)",
        documentation_url="https://waterservices.usgs.gov/docs/dv-service/",
        requires_api_key=False,
        coverage="United States",
        update_frequency="Daily",
        sample_endpoint="/dv/?format=json&bBox=-122.92,37.27,-121.92,38.27&parameterCd=00060,00065,00010&period=P7D&siteStatus=active&siteType=ST"
    ),
    "epa_waters": ExternalDataSource(
        name="EPA WATERS",
        category=DataCategory.WATER,
        base_url="https://watersgeo.epa.gov/arcgis/rest/services",
        description="US water quality assessments and impairments",
        documentation_url="https://www.epa.gov/waterdata/waters-geospatial-data-downloads",
        requires_api_key=False,
        coverage="United States",
        update_frequency="Annual updates"
    ),
    
    # === MARINE/OCEAN ===
    "open_meteo_marine": ExternalDataSource(
        name="Open-Meteo Marine",
        category=DataCategory.MARINE,
        base_url="https://marine-api.open-meteo.com/v1",
        description="Global marine/ocean forecast — wave height, period, direction, sea surface temp",
        documentation_url="https://open-meteo.com/en/docs/marine-weather-api",
        requires_api_key=False,
        coverage="Global Oceans",
        update_frequency="Hourly",
        sample_endpoint="/marine?latitude=37.77&longitude=-122.42&current=wave_height,wave_direction,wave_period,ocean_current_velocity&hourly=wave_height,wave_period,wave_direction,sea_surface_temperature"
    ),
    "noaa_buoy": ExternalDataSource(
        name="NOAA Buoy Data",
        category=DataCategory.MARINE,
        base_url="https://www.ndbc.noaa.gov",
        description="Real-time ocean buoy observations - waves, temp, wind (plain text format)",
        documentation_url="https://www.ndbc.noaa.gov/docs/",
        requires_api_key=False,
        coverage="US Coastal Waters, Pacific, Atlantic, Gulf",
        update_frequency="Hourly",
        sample_endpoint=""
    ),
    "copernicus_marine": ExternalDataSource(
        name="Copernicus Marine",
        category=DataCategory.MARINE,
        base_url="https://marine.copernicus.eu/api",
        description="European ocean data - sea surface temp, currents, salinity",
        documentation_url="https://marine.copernicus.eu/services",
        requires_api_key=True,
        api_key_env_var="COPERNICUS_API_KEY",
        coverage="Global oceans",
        update_frequency="Daily"
    ),
    
    # === WEATHER & CLIMATE ===
    "openweathermap": ExternalDataSource(
        name="OpenWeatherMap",
        category=DataCategory.WEATHER,
        base_url="https://api.openweathermap.org/data/2.5",
        description="Current weather, forecasts, historical data",
        documentation_url="https://openweathermap.org/api",
        requires_api_key=True,
        api_key_env_var="OPENWEATHERMAP_API_KEY",
        coverage="Global",
        update_frequency="Real-time"
    ),
    "noaa_climate": ExternalDataSource(
        name="NOAA Climate Data Online",
        category=DataCategory.CLIMATE,
        base_url="https://www.ncdc.noaa.gov/cdo-web/api/v2",
        description="Historical climate data and normals",
        documentation_url="https://www.ncdc.noaa.gov/cdo-web/webservices/v2",
        requires_api_key=True,
        api_key_env_var="NOAA_API_TOKEN",
        rate_limit_per_minute=5,
        coverage="Global",
        update_frequency="Daily updates"
    ),
    "open_meteo": ExternalDataSource(
        name="Open-Meteo",
        category=DataCategory.WEATHER,
        base_url="https://api.open-meteo.com/v1",
        description="Free weather API - forecasts, historical, climate models",
        documentation_url="https://open-meteo.com/en/docs",
        requires_api_key=False,
        coverage="Global",
        update_frequency="Hourly",
        sample_endpoint="/forecast?latitude=37.77&longitude=-122.42&current_weather=true&hourly=temperature_2m,relative_humidity_2m,wind_speed_10m,precipitation&forecast_days=3"
    ),
    "open_meteo_climate": ExternalDataSource(
        name="Open-Meteo Climate",
        category=DataCategory.CLIMATE,
        base_url="https://climate-api.open-meteo.com/v1",
        description="Free climate API - historical daily aggregates from ERA5 reanalysis",
        documentation_url="https://open-meteo.com/en/docs/climate-api",
        requires_api_key=False,
        coverage="Global",
        update_frequency="Daily",
        sample_endpoint="/climate?latitude=37.77&longitude=-122.42&start_date=2024-01-01&end_date=2024-01-30&daily=temperature_2m_max,temperature_2m_min,precipitation_sum&models=EC_Earth3P_HR"
    ),
    
    # === NATURAL HAZARDS ===
    "usgs_earthquake": ExternalDataSource(
        name="USGS Earthquake Hazards",
        category=DataCategory.EARTHQUAKES,
        base_url="https://earthquake.usgs.gov/fdsnws/event/1",
        description="Real-time earthquake data worldwide",
        documentation_url="https://earthquake.usgs.gov/fdsnws/event/1/",
        requires_api_key=False,
        coverage="Global",
        update_frequency="Real-time",
        sample_endpoint="/query?format=geojson&limit=10&orderby=time"
    ),
    "nasa_firms": ExternalDataSource(
        name="NASA FIRMS (Fire Information)",
        category=DataCategory.WILDFIRES,
        base_url="https://firms.modaps.eosdis.nasa.gov/api",
        description="Near real-time active fire/hotspot detections from VIIRS and MODIS satellites via LANCE",
        documentation_url="https://firms.modaps.eosdis.nasa.gov/api/",
        requires_api_key=True,
        api_key_env_var="FIRMS_MAP_KEY",
        coverage="Global",
        update_frequency="3-hour intervals (NRT)",
        sample_endpoint="/area/csv/{MAP_KEY}/VIIRS_SNPP_NRT/-122.92,37.27,-121.92,38.27/1"
    ),
    "nasa_firms_noaa20": ExternalDataSource(
        name="NASA FIRMS NOAA-20 (Mirror)",
        category=DataCategory.WILDFIRES,
        base_url="https://firms.modaps.eosdis.nasa.gov/api",
        description="Mirror: VIIRS fire detections from NOAA-20 satellite (identical format to primary SNPP)",
        documentation_url="https://firms.modaps.eosdis.nasa.gov/api/area/",
        requires_api_key=True,
        api_key_env_var="FIRMS_MAP_KEY",
        coverage="Global",
        update_frequency="Near real-time (3-5 hour lag)",
        sample_endpoint="/area/csv/{MAP_KEY}/VIIRS_NOAA20_NRT/-122.92,37.27,-121.92,38.27/1"
    ),
    "nifc_wildfires": ExternalDataSource(
        name="NIFC Active Fires",
        category=DataCategory.WILDFIRES,
        base_url="https://services3.arcgis.com/T4QMspbfLg3qTGWY/arcgis/rest/services",
        description="US National Interagency Fire Center active fire perimeters",
        documentation_url="https://data-nifc.opendata.arcgis.com/",
        requires_api_key=False,
        coverage="United States",
        update_frequency="Daily",
        data_format="GeoJSON",
        sample_endpoint=""
    ),
    
    # === RADIATION ===
    "open_meteo_uv": ExternalDataSource(
        name="Open-Meteo UV & Radiation",
        category=DataCategory.RADIATION,
        base_url="https://api.open-meteo.com/v1",
        description="UV index, direct/diffuse radiation, shortwave radiation from weather models",
        documentation_url="https://open-meteo.com/en/docs",
        requires_api_key=False,
        coverage="Global",
        update_frequency="Hourly",
        sample_endpoint="/forecast?latitude=37.77&longitude=-122.42&hourly=uv_index,direct_radiation,diffuse_radiation,shortwave_radiation&forecast_days=3"
    ),
    "epa_radnet": ExternalDataSource(
        name="EPA RadNet",
        category=DataCategory.RADIATION,
        base_url="https://www.epa.gov/radnet/radnet-csv-file-downloads",
        description="US radiation monitoring network (CSV format, no live endpoint)",
        documentation_url="https://www.epa.gov/radnet",
        requires_api_key=False,
        coverage="United States",
        update_frequency="Hourly",
        data_format="CSV"
    ),
    "nasa_power": ExternalDataSource(
        name="NASA POWER (Solar Radiation)",
        category=DataCategory.RADIATION,
        base_url="https://power.larc.nasa.gov/api/temporal/daily",
        description="Solar irradiance, UV index, and clear-sky radiation from NASA satellites and reanalysis models",
        documentation_url="https://power.larc.nasa.gov/",
        requires_api_key=False,
        coverage="Global",
        update_frequency="Weekly (1-2 week data lag)",
        sample_endpoint="/point?parameters=ALLSKY_SFC_SW_DWN,ALLSKY_SFC_UV_INDEX,CLRSKY_SFC_SW_DWN&community=RE&longitude=-122.42&latitude=37.77&start=20251201&end=20251231&format=json"
    ),
    
    # === BIODIVERSITY ===
    "gbif": ExternalDataSource(
        name="GBIF (Biodiversity)",
        category=DataCategory.BIODIVERSITY,
        base_url="https://api.gbif.org/v1",
        description="Global Biodiversity Information Facility - species occurrences",
        documentation_url="https://www.gbif.org/developer/summary",
        requires_api_key=False,
        coverage="Global",
        update_frequency="Continuous updates",
        sample_endpoint="/occurrence/search?limit=50&country=US"
    ),
    "inaturalist": ExternalDataSource(
        name="iNaturalist",
        category=DataCategory.BIODIVERSITY,
        base_url="https://api.inaturalist.org/v1",
        description="Citizen science biodiversity observations",
        documentation_url="https://api.inaturalist.org/v1/docs/",
        requires_api_key=False,
        coverage="Global",
        update_frequency="Real-time"
    ),
    
    # === SOIL ===
    "soilgrids": ExternalDataSource(
        name="SoilGrids",
        category=DataCategory.SOIL,
        base_url="https://rest.isric.org/soilgrids/v2.0",
        description="Global soil property predictions at 250m resolution",
        documentation_url="https://www.isric.org/explore/soilgrids",
        requires_api_key=False,
        coverage="Global",
        update_frequency="Static (model outputs)",
        sample_endpoint="/properties/query?lat=37.77&lon=-122.42&property=clay&property=sand&property=silt&property=phh2o&property=soc&property=nitrogen&depth=0-5cm&depth=5-15cm&depth=15-30cm&depth=30-60cm&depth=60-100cm&depth=100-200cm&value=mean&value=Q0.05&value=Q0.95"
    ),
    
    # === MAJOR PUBLIC DATA PORTALS ===
    "nasa_earthdata": ExternalDataSource(
        name="NASA Earthdata",
        category=DataCategory.CLIMATE,
        base_url="https://cmr.earthdata.nasa.gov/search",
        description="Gateway to 128+ petabytes of NASA Earth science data from satellite sensors and airborne missions",
        documentation_url="https://earthdata.nasa.gov/",
        requires_api_key=True,
        api_key_env_var="NASA_EARTHDATA_TOKEN",
        coverage="Global",
        update_frequency="Continuous",
        sample_endpoint="/collections.json?keyword=temperature&page_size=10"
    ),
    "noaa_ncei": ExternalDataSource(
        name="NOAA NCEI (National Centers for Environmental Information)",
        category=DataCategory.CLIMATE,
        base_url="https://www.ncei.noaa.gov/cdo-web/api/v2",
        description="Comprehensive archives for climate, coastal, oceanographic, and geophysical data",
        documentation_url="https://www.ncei.noaa.gov/",
        requires_api_key=True,
        api_key_env_var="NOAA_API_TOKEN",
        coverage="Global",
        update_frequency="Daily",
        sample_endpoint="/datasets"
    ),
    "epa_water_sensors": ExternalDataSource(
        name="EPA Water Sensors Toolbox",
        category=DataCategory.WATER,
        base_url="https://www.waterqualitydata.us/data",
        description="Water quality data aggregated from 400+ federal, state, and tribal agencies via the Water Quality Portal",
        documentation_url="https://www.waterqualitydata.us/",
        requires_api_key=False,
        coverage="United States",
        update_frequency="Continuous",
        sample_endpoint=""
    ),
    "us_ioos": ExternalDataSource(
        name="U.S. IOOS (Integrated Ocean Observing System)",
        category=DataCategory.MARINE,
        base_url="https://sensors.ioos.us/api",
        description="Master inventory of marine sensor data including real-time oceanographic readings via Environmental Sensor Map",
        documentation_url="https://ioos.noaa.gov/",
        requires_api_key=False,
        coverage="US Coastal and Ocean Waters",
        update_frequency="Real-time",
        sample_endpoint="/stations?limit=10"
    ),
    
    # === COMMUNITY & CROWDSOURCED SOURCES ===
    "sensor_community": ExternalDataSource(
        name="Sensor.Community",
        category=DataCategory.AIR_QUALITY,
        base_url="https://data.sensor.community/static/v2/data.json",
        description="Contributor-driven global network with 12,000+ active sensors in 82 countries tracking PM2.5, PM10, and climate variables",
        documentation_url="https://sensor.community/en/",
        requires_api_key=False,
        coverage="Global (82 countries, 12,000+ sensors)",
        update_frequency="Real-time (5 min intervals)",
        sample_endpoint=""
    ),
    "purpleair": ExternalDataSource(
        name="PurpleAir",
        category=DataCategory.AIR_QUALITY,
        base_url="https://api.purpleair.com/v1",
        description="Massive network of community-owned air quality sensors for hyper-local pollution monitoring",
        documentation_url="https://api.purpleair.com/",
        requires_api_key=True,
        api_key_env_var="PURPLEAIR_API_KEY",
        coverage="Global (dense in US, Europe)",
        update_frequency="Real-time (2 min intervals)"
    ),
    "microsoft_planetary_computer": ExternalDataSource(
        name="Microsoft Planetary Computer",
        category=DataCategory.CLIMATE,
        base_url="https://planetarycomputer.microsoft.com/api/stac/v1",
        description="Petabytes of environmental data combined with cloud computing for sustainability and conservation projects",
        documentation_url="https://planetarycomputer.microsoft.com/",
        requires_api_key=True,
        api_key_env_var="PLANETARY_COMPUTER_KEY",
        coverage="Global",
        update_frequency="Varies by dataset",
        sample_endpoint="/collections"
    ),
}


# ============================================================================
# PRIMARY / MIRROR FAILOVER ARCHITECTURE
# Each category has ONE primary source and ONE mirror fallback.
# Mirror fires only if primary fails. Output is normalized to primary format.
# Categories not listed here use existing multi-source behavior.
# ============================================================================

CATEGORY_FAILOVER: Dict[str, List[str]] = {
    "water": ["usgs_water", "usgs_water_dv"],
    "wildfires": ["nasa_firms", "nasa_firms_noaa20"],
    "air_quality": ["airnow", "open_meteo_aq"],
    "radiation": ["open_meteo_uv", "nasa_power"],
}


def _aqi_category(aqi: float) -> Dict[str, Any]:
    """Map AQI value to EPA category."""
    if aqi <= 50:
        return {"Number": 1, "Name": "Good"}
    if aqi <= 100:
        return {"Number": 2, "Name": "Moderate"}
    if aqi <= 150:
        return {"Number": 3, "Name": "Unhealthy for Sensitive Groups"}
    if aqi <= 200:
        return {"Number": 4, "Name": "Unhealthy"}
    if aqi <= 300:
        return {"Number": 5, "Name": "Very Unhealthy"}
    return {"Number": 6, "Name": "Hazardous"}


def _normalize_openmeteo_aq_to_airnow(data: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize Open-Meteo AQ hourly data to daily_aqi aggregate format.

    Open-Meteo returns hourly us_aqi, pm2_5, pm10, ozone, etc. for past_days.
    We aggregate to daily averages matching the AirNow daily format.
    """
    hourly = data.get("hourly") or {}
    times = hourly.get("time", [])
    aqi_vals = hourly.get("us_aqi", [])
    pm25_vals = hourly.get("pm2_5", [])
    pm10_vals = hourly.get("pm10", [])
    o3_vals = hourly.get("ozone", [])
    no2_vals = hourly.get("nitrogen_dioxide", [])

    if not times or not aqi_vals:
        # Fallback: try current{} for single-day
        current = data.get("current") or {}
        aqi = current.get("us_aqi")
        if aqi is None:
            return data
        today = datetime.utcnow().strftime("%Y-%m-%d")
        return {
            "daily_aqi": [{
                "date": today,
                "overall_aqi": int(aqi),
                "category": _aqi_category(aqi),
                "parameters": {
                    "PM2.5": int(current.get("pm2_5") or 0),
                    "PM10": int(current.get("pm10") or 0),
                    "OZONE": int(current.get("ozone") or 0),
                },
                "reporting_area": "Open-Meteo Estimate",
            }],
            "period_days": 1,
            "source_type": "open_meteo_normalized",
        }

    # Group hourly values by date
    from collections import defaultdict
    daily_buckets: Dict[str, Dict[str, list]] = defaultdict(
        lambda: {"aqi": [], "pm25": [], "pm10": [], "o3": [], "no2": []}
    )
    for i, t in enumerate(times):
        date_str = t[:10]  # "2026-02-10T14:00" -> "2026-02-10"
        if i < len(aqi_vals) and aqi_vals[i] is not None:
            daily_buckets[date_str]["aqi"].append(aqi_vals[i])
        if i < len(pm25_vals) and pm25_vals[i] is not None:
            daily_buckets[date_str]["pm25"].append(pm25_vals[i])
        if i < len(pm10_vals) and pm10_vals[i] is not None:
            daily_buckets[date_str]["pm10"].append(pm10_vals[i])
        if i < len(o3_vals) and o3_vals[i] is not None:
            daily_buckets[date_str]["o3"].append(o3_vals[i])
        if i < len(no2_vals) and no2_vals[i] is not None:
            daily_buckets[date_str]["no2"].append(no2_vals[i])

    daily_aqi = []
    for date_str in sorted(daily_buckets.keys()):
        bucket = daily_buckets[date_str]
        if not bucket["aqi"]:
            continue
        avg_aqi = sum(bucket["aqi"]) / len(bucket["aqi"])
        daily_aqi.append({
            "date": date_str,
            "overall_aqi": round(avg_aqi),
            "category": _aqi_category(avg_aqi),
            "parameters": {
                "PM2.5": round(sum(bucket["pm25"]) / len(bucket["pm25"])) if bucket["pm25"] else None,
                "PM10": round(sum(bucket["pm10"]) / len(bucket["pm10"])) if bucket["pm10"] else None,
                "OZONE": round(sum(bucket["o3"]) / len(bucket["o3"])) if bucket["o3"] else None,
                "NO2": round(sum(bucket["no2"]) / len(bucket["no2"])) if bucket["no2"] else None,
            },
            "reporting_area": "Open-Meteo Estimate",
        })

    # Filter out future dates — Open-Meteo includes forecast days
    today_str = datetime.utcnow().strftime("%Y-%m-%d")
    daily_aqi = [d for d in daily_aqi if d["date"] <= today_str]

    return {
        "daily_aqi": daily_aqi,
        "period_days": len(daily_aqi),
        "source_type": "open_meteo_normalized",
    }


async def _aggregate_airnow_daily(
    client: httpx.AsyncClient,
    latitude: float,
    longitude: float,
    api_key: str,
    days: int = 7,
) -> Dict[str, Any]:
    """Call AirNow historical endpoint for each of the last N days and aggregate.

    AirNow historical returns per-day: [{DateObserved, ParameterName, AQI, Category}]
    We combine into: {daily_aqi: [{date, overall_aqi, category, parameters: {...}}]}
    """
    daily_aqi = []
    today = datetime.utcnow()

    async def _fetch_day(days_ago: int):
        target = today - timedelta(days=days_ago)
        date_str = target.strftime("%Y-%m-%d")
        url = (
            f"https://www.airnowapi.org/aq/observation/latLong/historical/"
            f"?format=application/json"
            f"&latitude={latitude}&longitude={longitude}"
            f"&date={date_str}T00-0000&distance=50"
            f"&API_KEY={api_key}"
        )
        try:
            resp = await client.get(url, timeout=15.0)
            resp.raise_for_status()
            return date_str, resp.json()
        except Exception as exc:
            logger.warning("AirNow historical %s failed: %s: %s", date_str, type(exc).__name__, exc)
            return date_str, []

    # Fetch all days in parallel
    results = await asyncio.gather(*[_fetch_day(d) for d in range(1, days + 1)])

    for date_str, obs_list in sorted(results, key=lambda x: x[0]):
        if not isinstance(obs_list, list) or not obs_list:
            continue
        params = {}
        max_aqi = 0
        reporting_area = ""
        for obs in obs_list:
            if not isinstance(obs, dict):
                continue
            pname = obs.get("ParameterName", "unknown")
            aqi = obs.get("AQI")
            if aqi is not None:
                params[pname] = int(aqi)
                max_aqi = max(max_aqi, int(aqi))
            if not reporting_area:
                reporting_area = obs.get("ReportingArea", "")

        if params:
            daily_aqi.append({
                "date": date_str,
                "overall_aqi": max_aqi,
                "category": _aqi_category(max_aqi),
                "parameters": params,
                "reporting_area": reporting_area,
            })

    return {
        "daily_aqi": daily_aqi,
        "period_days": len(daily_aqi),
        "source_type": "airnow_historical",
    }


def _normalize_nasa_power_to_uv(data: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize NASA POWER daily data to Open-Meteo UV hourly-like format.

    NASA POWER returns: {"properties": {"parameter": {"ALLSKY_SFC_UV_INDEX": {"20251201": val}}}}
    Open-Meteo UV returns: {"hourly": {"time": [...], "uv_index": [...], ...}}
    """
    params = (data.get("properties") or {}).get("parameter") or {}
    uv_daily = params.get("ALLSKY_SFC_UV_INDEX", {})
    sw_daily = params.get("ALLSKY_SFC_SW_DWN", {})
    clr_daily = params.get("CLRSKY_SFC_SW_DWN", {})

    times = sorted(uv_daily.keys())
    valid = [
        (t, uv_daily.get(t, -999), sw_daily.get(t, -999), clr_daily.get(t, -999))
        for t in times
    ]
    valid = [(t, u, s, c) for t, u, s, c in valid if u != -999]

    if not valid:
        return data  # Return as-is if no valid data

    # Convert YYYYMMDD to ISO format at solar noon
    times_fmt = [f"{t[:4]}-{t[4:6]}-{t[6:8]}T12:00" for t, _, _, _ in valid]
    # NASA POWER: kWh/m2/day -> approximate W/m2 by dividing by ~5 peak sun hours * 1000
    sw_factor = 1000.0 / 5.0  # rough daily total -> peak instantaneous

    return {
        "hourly": {
            "time": times_fmt,
            "uv_index": [round(u, 1) for _, u, _, _ in valid],
            "shortwave_radiation": [round(s * sw_factor, 0) for _, _, s, _ in valid],
            "direct_radiation": [round(c * sw_factor, 0) for _, _, _, c in valid],
            "diffuse_radiation": [round((s - c) * sw_factor, 0) for _, _, s, c in valid],
        },
        "_normalized_from": "nasa_power",
        "_note": "Daily averages presented at solar noon; radiation approximated from daily totals",
    }


# Map of (category, source_id) -> normalizer function
_NORMALIZERS: Dict[tuple, Any] = {
    ("air_quality", "open_meteo_aq"): _normalize_openmeteo_aq_to_airnow,
    ("radiation", "nasa_power"): _normalize_nasa_power_to_uv,
}


class DataAggregator:
    """
    Central hub for aggregating environmental data from multiple sources.
    
    This service acts as a proxy/aggregator - it forwards requests to
    external APIs and combines results. We don't store the data, we
    just provide unified access.
    """
    
    def __init__(self):
        self.sources = EXTERNAL_SOURCES
        self._http_client: Optional[httpx.AsyncClient] = None
        self._cache: Dict[str, Any] = {}  # Simple in-memory cache
        self._cache_ttl: Dict[str, datetime] = {}
        
    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._http_client is None or self._http_client.is_closed:
            self._http_client = httpx.AsyncClient(timeout=30.0)
        return self._http_client
    
    async def close(self):
        """Close HTTP client."""
        if self._http_client and not self._http_client.is_closed:
            await self._http_client.aclose()
    
    def get_available_sources(self, category: Optional[DataCategory] = None) -> List[Dict[str, Any]]:
        """Get list of all available data sources, optionally filtered by category."""
        sources = []
        for key, source in self.sources.items():
            if category and source.category != category:
                continue
            sources.append({
                "id": key,
                "name": source.name,
                "category": source.category.value,
                "description": source.description,
                "documentation_url": source.documentation_url,
                "requires_api_key": source.requires_api_key,
                "is_free": source.is_free,
                "coverage": source.coverage,
                "update_frequency": source.update_frequency
            })
        return sources
    
    def get_categories(self) -> List[Dict[str, Any]]:
        """Get all data categories with source counts."""
        category_counts = {}
        for source in self.sources.values():
            cat = source.category.value
            if cat not in category_counts:
                category_counts[cat] = {"count": 0, "sources": []}
            category_counts[cat]["count"] += 1
            category_counts[cat]["sources"].append(source.name)
        
        return [
            {"category": cat, "source_count": info["count"], "sources": info["sources"]}
            for cat, info in category_counts.items()
        ]
    
    async def proxy_request(
        self,
        source_id: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Proxy a request to an external data source.
        
        This forwards the request to the external API and returns the response.
        We act as a gateway, not a storage system.
        """
        if source_id not in self.sources:
            return {"success": False, "error": f"Unknown source: {source_id}"}
        
        source = self.sources[source_id]
        
        # Check cache first
        cache_key = f"{source_id}:{endpoint}:{str(params)}"
        if cache_key in self._cache:
            if datetime.utcnow() < self._cache_ttl.get(cache_key, datetime.min):
                logger.info(f"Cache hit for {source_id}")
                return self._cache[cache_key]
        
        try:
            client = await self._get_client()
            url = f"{source.base_url}{endpoint}"
            
            headers = {}
            if source.requires_api_key and source.api_key_env_var:
                import os
                api_key = os.environ.get(source.api_key_env_var)
                if not api_key:
                    return {
                        "success": False,
                        "error": f"API key not configured for {source.name}",
                        "hint": f"Set {source.api_key_env_var} environment variable"
                    }
                # Different APIs use different auth methods
                if "firms" in source_id:
                    # FIRMS: MAP_KEY embedded in URL path
                    url = url.replace("{MAP_KEY}", api_key)
                elif source_id == "nasa_earthdata":
                    headers["Authorization"] = f"Bearer {api_key}"
                elif "noaa" in source.base_url and "ncdc" in source.base_url:
                    headers["token"] = api_key
                elif source_id == "airnow":
                    params = params or {}
                    params["API_KEY"] = api_key
                else:
                    params = params or {}
                    params["api_key"] = api_key
            
            response = await client.get(url, params=params, headers=headers)
            
            # Parse response based on content type
            content_type = response.headers.get("content-type", "")
            if "json" in content_type:
                data = response.json()
            elif "csv" in content_type or (
                response.text
                and len(response.text) > 20
                and response.text.strip().split("\n")[0].count(",") >= 3
                and not response.text.strip().startswith(("<", "{", "["))
            ):
                # Parse CSV responses (e.g., FIRMS fire data) into list of dicts
                import csv
                import io
                try:
                    reader = csv.DictReader(io.StringIO(response.text))
                    data = list(reader)
                except Exception:
                    data = response.text
            else:
                data = response.text
            
            # Truncate large USGS water responses to prevent oversized payloads
            if isinstance(data, dict) and "value" in data:
                ts = (data.get("value") or {}).get("timeSeries", [])
                if isinstance(ts, list) and len(ts) > 20:
                    total = len(ts)
                    data["value"]["timeSeries"] = ts[:20]
                    data["_truncated"] = True
                    data["_total_stations"] = total

            # Wrap list data in a dict so merge_category_sources can handle it
            if isinstance(data, list):
                if "firms" in source_id:
                    data = {"fires": data, "count": len(data)}
                elif "airnow" in source_id:
                    data = {"observations": data, "count": len(data)}
                else:
                    data = {"records": data, "count": len(data)}

            result = {
                "success": True,
                "source": source.name,
                "source_id": source_id,
                "endpoint": endpoint,
                "timestamp": datetime.utcnow().isoformat(),
                "data": data
            }
            
            # Cache for 5 minutes
            self._cache[cache_key] = result
            self._cache_ttl[cache_key] = datetime.utcnow() + timedelta(minutes=5)
            
            return result
            
        except Exception as e:
            logger.error(f"Error proxying to {source_id}: {e}")
            return {
                "success": False,
                "source": source.name,
                "error": str(e)
            }
    
    async def aggregate_by_location(
        self,
        latitude: float,
        longitude: float,
        categories: Optional[List[str]] = None,
        radius_km: float = 50.0
    ) -> Dict[str, Any]:
        """
        Aggregate environmental data for a specific location from multiple sources.
        
        This is the "one-stop-shop" query - get air quality, weather, water,
        hazards, etc. all for one location.
        """
        results = {
            "location": {"latitude": latitude, "longitude": longitude},
            "radius_km": radius_km,
            "timestamp": datetime.utcnow().isoformat(),
            "data": {}
        }
        
        # Calculate bounding box for sources that need it
        bbox_half = 0.5  # ±0.5 degrees ≈ ±55km
        bbox = f"{longitude-bbox_half:.2f},{latitude-bbox_half:.2f},{longitude+bbox_half:.2f},{latitude+bbox_half:.2f}"
        
        # Define which sources to query for location-based data
        location_sources = {
            "air_quality": [
                ("airnow", f"/observation/latLong/current/?format=application/json&latitude={latitude}&longitude={longitude}&distance=50"),
            ],
            "weather": [
                ("open_meteo", f"/forecast?latitude={latitude}&longitude={longitude}&current_weather=true&hourly=temperature_2m,relative_humidity_2m,wind_speed_10m,precipitation&forecast_days=3"),
            ],
            "water": [
                ("usgs_water", f"/iv/?format=json&bBox={bbox}&parameterCd=00060,00065,00010&period=PT2H&siteStatus=active&siteType=ST"),
            ],
            "earthquakes": [
                ("usgs_earthquake", f"/query?format=geojson&latitude={latitude}&longitude={longitude}&maxradiuskm={radius_km}&limit=10"),
            ],
            "climate": [
                ("open_meteo_climate", f"/climate?latitude={latitude}&longitude={longitude}&start_date=2024-01-01&end_date=2024-01-30&daily=temperature_2m_max,temperature_2m_min,precipitation_sum&models=EC_Earth3P_HR"),
            ],
            "soil": [
                ("soilgrids", f"/properties/query?lat={latitude}&lon={longitude}&property=clay&property=sand&property=silt&property=phh2o&property=soc&property=nitrogen&depth=0-5cm&depth=5-15cm&depth=15-30cm&depth=30-60cm&depth=60-100cm&depth=100-200cm&value=mean&value=Q0.05&value=Q0.95"),
            ],
            "marine": [
                ("open_meteo_marine", f"/marine?latitude={latitude}&longitude={longitude}&current=wave_height,wave_direction,wave_period,sea_surface_temperature&hourly=wave_height,wave_period,wave_direction,sea_surface_temperature&forecast_days=3"),
            ],
            "radiation": [
                ("open_meteo_uv", f"/forecast?latitude={latitude}&longitude={longitude}&hourly=uv_index,direct_radiation,diffuse_radiation,shortwave_radiation&forecast_days=3"),
            ],
            "wildfires": [
                ("nasa_firms", f"/area/csv/{{MAP_KEY}}/VIIRS_SNPP_NRT/{bbox}/1"),
            ],
            "biodiversity": [
                ("gbif", f"/occurrence/search?decimalLatitude={latitude}&decimalLongitude={longitude}&radius={int(radius_km)}&limit=50"),
            ],
        }
        
        tasks = []
        source_mapping = []
        
        for category, source_list in location_sources.items():
            if categories and category not in categories:
                continue
            for source_id, endpoint in source_list:
                tasks.append(self.proxy_request(source_id, endpoint))
                source_mapping.append((category, source_id))
        
        # Execute all requests in parallel
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        
        for (category, source_id), response in zip(source_mapping, responses):
            if category not in results["data"]:
                results["data"][category] = []
            
            if isinstance(response, Exception):
                results["data"][category].append({
                    "source": source_id,
                    "error": str(response)
                })
            else:
                results["data"][category].append(response)
        
        return results
    
    def _inject_location(self, endpoint: str, params: Optional[Dict[str, Any]]) -> str:
        """Replace default coordinates in endpoint URL with actual lat/lon."""
        if not params:
            return endpoint
        lat = params.get("lat") or params.get("latitude")
        lon = params.get("lon") or params.get("longitude")
        if lat is None or lon is None:
            return endpoint
        endpoint = endpoint.replace("latitude=37.77", f"latitude={lat}")
        endpoint = endpoint.replace("longitude=-122.42", f"longitude={lon}")
        endpoint = endpoint.replace("lat=37.77", f"lat={lat}")
        endpoint = endpoint.replace("lon=-122.42", f"lon={lon}")
        default_bbox = "-122.92,37.27,-121.92,38.27"
        new_bbox = (
            f"{float(lon)-0.5:.2f},{float(lat)-0.5:.2f},"
            f"{float(lon)+0.5:.2f},{float(lat)+0.5:.2f}"
        )
        endpoint = endpoint.replace(default_bbox, new_bbox)
        return endpoint

    async def _failover_query(
        self,
        category: str,
        source_ids: List[str],
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Try sources in priority order. Return first success, normalized to primary format."""
        errors = []
        requested_days = int((params or {}).get("days", 7))
        for source_id in source_ids:
            source = self.sources.get(source_id)
            if not source or not source.sample_endpoint:
                continue

            # --- Special: AirNow daily aggregate (multi-call) ---
            if source_id == "airnow" and "__DAILY_AGGREGATE__" in source.sample_endpoint:
                lat = float((params or {}).get("lat", (params or {}).get("latitude", 37.77)))
                lon = float((params or {}).get("lon", (params or {}).get("longitude", -122.42)))
                import os
                api_key = os.environ.get("AIRNOW_API_KEY", "")
                if not api_key:
                    errors.append({"source": source.name, "source_id": source_id, "error": "AIRNOW_API_KEY not set"})
                    continue
                try:
                    client = await self._get_client()
                    data = await _aggregate_airnow_daily(client, lat, lon, api_key, days=requested_days)
                    if data.get("daily_aqi"):
                        result = {
                            "success": True,
                            "source": source.name,
                            "source_id": source_id,
                            "timestamp": datetime.utcnow().isoformat(),
                            "data": data,
                        }
                        return {
                            "category": category,
                            "timestamp": datetime.utcnow().isoformat(),
                            "sources_queried": 1,
                            "primary_source": source_ids[0],
                            "active_source": source_id,
                            "failover_used": False,
                            "data": [result],
                        }
                    else:
                        errors.append({"source": source.name, "source_id": source_id, "error": "No daily data returned"})
                        continue
                except Exception as exc:
                    errors.append({"source": source.name, "source_id": source_id, "error": str(exc)})
                    continue

            endpoint = self._inject_location(source.sample_endpoint, params)

            # Rewrite past_days= in endpoint to match requested days
            if "past_days=" in endpoint:
                import re
                endpoint = re.sub(r'past_days=\d+', f'past_days={requested_days}', endpoint)

            try:
                result = await self.proxy_request(source_id, endpoint, None)
            except Exception as exc:
                errors.append({"source": source.name, "source_id": source_id, "error": str(exc)})
                continue

            if result.get("success"):
                # Normalize secondary source output to match primary format
                normalizer = _NORMALIZERS.get((category, source_id))
                if normalizer and isinstance(result.get("data"), dict):
                    result["data"] = normalizer(result["data"])
                    result["_normalized_from"] = source_id

                is_mirror = source_id != source_ids[0]
                return {
                    "category": category,
                    "timestamp": datetime.utcnow().isoformat(),
                    "sources_queried": 1,
                    "primary_source": source_ids[0],
                    "active_source": source_id,
                    "failover_used": is_mirror,
                    "data": [result],
                }
            else:
                errors.append({
                    "source": source.name,
                    "source_id": source_id,
                    "error": result.get("error", "Unknown error"),
                })

        return {
            "category": category,
            "timestamp": datetime.utcnow().isoformat(),
            "sources_queried": len(errors),
            "success": False,
            "error": "All sources failed",
            "data": errors,
        }

    async def aggregate_by_category(
        self,
        category: str,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Get data for a category using primary/mirror failover when configured.

        For categories in CATEGORY_FAILOVER: tries primary source first, then
        mirror if primary fails. Returns exactly ONE result in consistent format.

        For other categories: queries all available sources in parallel (legacy).
        """
        try:
            cat_enum = DataCategory(category)
        except ValueError:
            return {
                "success": False,
                "error": f"Invalid category: {category}",
                "valid_categories": [c.value for c in DataCategory]
            }

        # ---- Failover path: primary -> mirror, return ONE result ----
        if category in CATEGORY_FAILOVER:
            return await self._failover_query(
                category, CATEGORY_FAILOVER[category], params
            )

        # ---- Legacy path: query all sources in parallel ----
        sources_in_category = [
            (key, source) for key, source in self.sources.items()
            if source.category == cat_enum and source.sample_endpoint
        ]

        if not sources_in_category:
            return {
                "success": False,
                "error": f"No sources with sample endpoints in category: {category}"
            }

        tasks = []
        for source_id, source in sources_in_category:
            endpoint = self._inject_location(source.sample_endpoint, params)
            tasks.append(self.proxy_request(source_id, endpoint, None))

        responses = await asyncio.gather(*tasks, return_exceptions=True)

        results = {
            "category": category,
            "timestamp": datetime.utcnow().isoformat(),
            "sources_queried": len(sources_in_category),
            "data": []
        }

        for (source_id, source), response in zip(sources_in_category, responses):
            if isinstance(response, Exception):
                results["data"].append({
                    "source": source.name,
                    "source_id": source_id,
                    "error": str(response)
                })
            else:
                results["data"].append(response)

        return results


# ============================================================================
# CONNECT THE DOTS - Correlation Analysis
# ============================================================================

class ConnectionAnalyzer:
    """
    Analyzes environmental data to find correlations and connections.
    
    This turns raw data into actionable insights by finding patterns like:
    - Air quality correlations with weather patterns
    - Earthquake activity affecting water quality
    - Wildfire smoke impacting air quality hundreds of miles away
    - Marine temperature changes correlating with weather patterns
    """
    
    def __init__(self, aggregator: DataAggregator):
        self.aggregator = aggregator
        
    async def analyze_location(
        self,
        latitude: float,
        longitude: float,
        days_back: int = 7
    ) -> Dict[str, Any]:
        """
        Comprehensive analysis for a location - find all relevant connections.
        """
        # Get aggregated data
        data = await self.aggregator.aggregate_by_location(latitude, longitude)
        
        connections = []
        insights = []
        
        # Analyze air quality vs weather
        air_data = data.get("data", {}).get("air_quality", [])
        weather_data = data.get("data", {}).get("weather", [])
        
        if air_data and weather_data:
            connections.append({
                "type": "air_weather_correlation",
                "description": "Air quality often correlates with temperature inversions and wind patterns",
                "data_sources": ["openaq", "open_meteo"],
                "action": "Check if high pollution coincides with low wind speeds or temperature inversions"
            })
        
        # Check for nearby earthquakes
        earthquake_data = data.get("data", {}).get("earthquakes", [])
        for eq_result in earthquake_data:
            if eq_result.get("success") and eq_result.get("data"):
                eq_features = eq_result["data"].get("features", [])
                if eq_features:
                    insights.append({
                        "type": "seismic_activity",
                        "severity": "info",
                        "message": f"Found {len(eq_features)} recent earthquakes within radius",
                        "recommendation": "Monitor water quality - seismic activity can affect groundwater"
                    })
        
        return {
            "location": {"latitude": latitude, "longitude": longitude},
            "analysis_timestamp": datetime.utcnow().isoformat(),
            "raw_data_summary": {
                category: len(sources) for category, sources in data.get("data", {}).items()
            },
            "connections_found": connections,
            "insights": insights,
            "recommended_monitoring": [
                "Air quality (PM2.5, O3)",
                "Water quality if near streams",
                "Weather patterns for correlation analysis"
            ]
        }
    
    def get_correlation_rules(self) -> List[Dict[str, Any]]:
        """Get the rules used for correlation analysis."""
        return [
            {
                "rule_id": "air_temp_inversion",
                "name": "Temperature Inversion Effect",
                "description": "High pollution often correlates with temperature inversions",
                "data_sources": ["air_quality", "weather"],
                "trigger": "AQI > 100 AND temp_gradient < 0"
            },
            {
                "rule_id": "wildfire_smoke_transport",
                "name": "Wildfire Smoke Transport",
                "description": "Smoke can travel hundreds of miles affecting air quality",
                "data_sources": ["wildfires", "air_quality", "weather"],
                "trigger": "Active fires upwind AND elevated PM2.5"
            },
            {
                "rule_id": "marine_weather_link",
                "name": "Marine-Weather Connection",
                "description": "Ocean temperatures affect coastal weather patterns",
                "data_sources": ["marine", "weather"],
                "trigger": "Sea surface temp anomaly > 2°C"
            },
            {
                "rule_id": "earthquake_water_impact",
                "name": "Seismic Water Quality Impact",
                "description": "Earthquakes can affect groundwater and stream turbidity",
                "data_sources": ["earthquakes", "water"],
                "trigger": "Magnitude > 4.0 within 100km"
            },
            {
                "rule_id": "biodiversity_habitat_stress",
                "name": "Habitat Stress Indicators",
                "description": "Species observations can indicate environmental stress",
                "data_sources": ["biodiversity", "air_quality", "water"],
                "trigger": "Declining species counts OR unusual migration patterns"
            }
        ]


# Singleton instances
data_aggregator = DataAggregator()
connection_analyzer = ConnectionAnalyzer(data_aggregator)
