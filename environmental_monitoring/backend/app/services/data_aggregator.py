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
    "openaq": ExternalDataSource(
        name="OpenAQ",
        category=DataCategory.AIR_QUALITY,
        base_url="https://api.openaq.org/v2",
        description="Global air quality data from government and research stations",
        documentation_url="https://docs.openaq.org/",
        requires_api_key=False,
        coverage="Global (90+ countries)",
        update_frequency="Real-time",
        sample_endpoint="/locations?limit=10&country=US"
    ),
    "airnow": ExternalDataSource(
        name="EPA AirNow",
        category=DataCategory.AIR_QUALITY,
        base_url="https://www.airnowapi.org/aq",
        description="US EPA official air quality index and forecasts",
        documentation_url="https://docs.airnowapi.org/",
        requires_api_key=True,
        api_key_env_var="AIRNOW_API_KEY",
        coverage="United States",
        update_frequency="Hourly"
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
        name="USGS Water Services",
        category=DataCategory.WATER,
        base_url="https://waterservices.usgs.gov/nwis",
        description="US stream flow, water quality, groundwater levels",
        documentation_url="https://waterservices.usgs.gov/",
        requires_api_key=False,
        coverage="United States",
        update_frequency="15-minute intervals",
        sample_endpoint="/iv/?format=json&stateCd=CA&parameterCd=00060&siteType=ST"
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
    "noaa_buoy": ExternalDataSource(
        name="NOAA Buoy Data",
        category=DataCategory.MARINE,
        base_url="https://www.ndbc.noaa.gov",
        description="Real-time ocean buoy observations - waves, temp, wind",
        documentation_url="https://www.ndbc.noaa.gov/docs/",
        requires_api_key=False,
        coverage="US Coastal Waters, Pacific, Atlantic, Gulf",
        update_frequency="Hourly",
        sample_endpoint="/data/realtime2/46026.txt"
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
        sample_endpoint="/forecast?latitude=37.77&longitude=-122.42&current_weather=true"
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
        description="Active fire data from MODIS and VIIRS satellites",
        documentation_url="https://firms.modaps.eosdis.nasa.gov/api/",
        requires_api_key=True,
        api_key_env_var="NASA_FIRMS_API_KEY",
        coverage="Global",
        update_frequency="3-hour intervals"
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
        data_format="GeoJSON"
    ),
    
    # === RADIATION ===
    "epa_radnet": ExternalDataSource(
        name="EPA RadNet",
        category=DataCategory.RADIATION,
        base_url="https://www.epa.gov/radnet/radnet-csv-file-downloads",
        description="US radiation monitoring network",
        documentation_url="https://www.epa.gov/radnet",
        requires_api_key=False,
        coverage="United States",
        update_frequency="Hourly",
        data_format="CSV"
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
        sample_endpoint="/occurrence/search?limit=10&country=US"
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
        update_frequency="Static (model outputs)"
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
        sample_endpoint="/Station/search?statecode=US:06&mimeType=geojson&zip=no"
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
                if "noaa" in source.base_url and "ncdc" in source.base_url:
                    headers["token"] = api_key
                else:
                    params = params or {}
                    params["api_key"] = api_key
            
            response = await client.get(url, params=params, headers=headers)
            
            result = {
                "success": True,
                "source": source.name,
                "source_id": source_id,
                "endpoint": endpoint,
                "timestamp": datetime.utcnow().isoformat(),
                "data": response.json() if "json" in response.headers.get("content-type", "") else response.text
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
        
        # Define which sources to query for location-based data
        location_sources = {
            "air_quality": [
                ("openaq", f"/locations?coordinates={latitude},{longitude}&radius={int(radius_km * 1000)}"),
            ],
            "weather": [
                ("open_meteo", f"/forecast?latitude={latitude}&longitude={longitude}&current_weather=true"),
            ],
            "earthquakes": [
                ("usgs_earthquake", f"/query?format=geojson&latitude={latitude}&longitude={longitude}&maxradiuskm={radius_km}&limit=10"),
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
    
    async def aggregate_by_category(
        self,
        category: str,
        params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Aggregate data from all sources in a category.
        """
        try:
            cat_enum = DataCategory(category)
        except ValueError:
            return {
                "success": False,
                "error": f"Invalid category: {category}",
                "valid_categories": [c.value for c in DataCategory]
            }
        
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
            tasks.append(self.proxy_request(source_id, source.sample_endpoint, params))
        
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
