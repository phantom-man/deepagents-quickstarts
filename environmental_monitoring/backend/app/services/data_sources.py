"""
Public Environmental Data Sources Configuration

This module provides configuration and clients for real public environmental data APIs:
- OpenAQ: Air quality data (free, no API key required for basic access)
- NOAA Climate Data: Weather and climate data (requires token)
- EPA AirNow: US air quality index data (requires API key)
- OpenWeatherMap: Weather data (free tier available)
- USGS Water Services: Water quality and stream data (free, no key)
- PurpleAir: Community air quality sensors (free tier)

All APIs are free or have free tiers suitable for monitoring applications.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import httpx
import os
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class DataSourceType(Enum):
    """Types of environmental data sources."""
    AIR_QUALITY = "air_quality"
    WEATHER = "weather"
    WATER_QUALITY = "water_quality"
    CLIMATE = "climate"
    RADIATION = "radiation"


@dataclass
class DataSourceConfig:
    """Configuration for a data source."""
    name: str
    source_type: DataSourceType
    base_url: str
    requires_api_key: bool = False
    api_key_env_var: Optional[str] = None
    rate_limit_per_minute: int = 60
    default_poll_interval: int = 300  # 5 minutes
    retry_attempts: int = 3
    retry_delay: int = 5
    headers: Dict[str, str] = field(default_factory=dict)


# ============================================================================
# PUBLIC DATA SOURCE CONFIGURATIONS
# ============================================================================

DATA_SOURCES: Dict[str, DataSourceConfig] = {
    # OpenAQ - Free air quality data, no API key required for basic access
    "openaq": DataSourceConfig(
        name="OpenAQ",
        source_type=DataSourceType.AIR_QUALITY,
        base_url="https://api.openaq.org/v2",
        requires_api_key=False,
        rate_limit_per_minute=60,
        default_poll_interval=600,  # 10 minutes
    ),
    
    # NOAA Climate Data Online - Free with token
    "noaa": DataSourceConfig(
        name="NOAA Climate Data",
        source_type=DataSourceType.CLIMATE,
        base_url="https://www.ncdc.noaa.gov/cdo-web/api/v2",
        requires_api_key=True,
        api_key_env_var="NOAA_API_TOKEN",
        rate_limit_per_minute=5,  # NOAA has strict limits
        default_poll_interval=3600,  # 1 hour
    ),
    
    # EPA AirNow - US air quality
    "airnow": DataSourceConfig(
        name="EPA AirNow",
        source_type=DataSourceType.AIR_QUALITY,
        base_url="https://www.airnowapi.org/aq",
        requires_api_key=True,
        api_key_env_var="AIRNOW_API_KEY",
        rate_limit_per_minute=60,
        default_poll_interval=3600,  # 1 hour (data updates hourly)
    ),
    
    # OpenWeatherMap - Weather data
    "openweathermap": DataSourceConfig(
        name="OpenWeatherMap",
        source_type=DataSourceType.WEATHER,
        base_url="https://api.openweathermap.org/data/2.5",
        requires_api_key=True,
        api_key_env_var="OPENWEATHERMAP_API_KEY",
        rate_limit_per_minute=60,
        default_poll_interval=600,  # 10 minutes
    ),
    
    # USGS Water Services - Free, no API key
    "usgs_water": DataSourceConfig(
        name="USGS Water Services",
        source_type=DataSourceType.WATER_QUALITY,
        base_url="https://waterservices.usgs.gov/nwis",
        requires_api_key=False,
        rate_limit_per_minute=30,
        default_poll_interval=900,  # 15 minutes
    ),
    
    # PurpleAir - Community air sensors
    "purpleair": DataSourceConfig(
        name="PurpleAir",
        source_type=DataSourceType.AIR_QUALITY,
        base_url="https://api.purpleair.com/v1",
        requires_api_key=True,
        api_key_env_var="PURPLEAIR_API_KEY",
        rate_limit_per_minute=60,
        default_poll_interval=300,  # 5 minutes
    ),
    
    # NOAA Buoy Data - Marine/Ocean monitoring (free, no API key)
    # Suggestion from FiverrClawOfficial on Moltbook
    "noaa_buoy": DataSourceConfig(
        name="NOAA Buoy Data",
        source_type=DataSourceType.WATER_QUALITY,  # Marine data
        base_url="https://www.ndbc.noaa.gov",
        requires_api_key=False,
        rate_limit_per_minute=30,
        default_poll_interval=1800,  # 30 minutes (buoy updates hourly)
    ),
}


# ============================================================================
# BASE DATA SOURCE CLIENT
# ============================================================================

class BaseDataSourceClient(ABC):
    """Abstract base class for data source clients."""
    
    def __init__(self, config: DataSourceConfig):
        self.config = config
        self.api_key: Optional[str] = None
        self._last_request_time: datetime = datetime.min
        self._request_count: int = 0
        self._http_client: Optional[httpx.AsyncClient] = None
        
        # Load API key if required
        if config.requires_api_key and config.api_key_env_var:
            self.api_key = os.environ.get(config.api_key_env_var)
            if not self.api_key:
                logger.warning(
                    f"API key not found for {config.name}. "
                    f"Set {config.api_key_env_var} environment variable."
                )
    
    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._http_client is None or self._http_client.is_closed:
            self._http_client = httpx.AsyncClient(
                timeout=30.0,
                headers=self.config.headers
            )
        return self._http_client
    
    async def close(self):
        """Close the HTTP client."""
        if self._http_client and not self._http_client.is_closed:
            await self._http_client.aclose()
    
    async def _rate_limit(self):
        """Apply rate limiting."""
        now = datetime.utcnow()
        
        # Reset counter if a minute has passed
        if (now - self._last_request_time).seconds >= 60:
            self._request_count = 0
            self._last_request_time = now
        
        # Wait if we've hit the rate limit
        if self._request_count >= self.config.rate_limit_per_minute:
            wait_time = 60 - (now - self._last_request_time).seconds
            if wait_time > 0:
                logger.info(f"Rate limit reached for {self.config.name}, waiting {wait_time}s")
                await asyncio.sleep(wait_time)
                self._request_count = 0
                self._last_request_time = datetime.utcnow()
        
        self._request_count += 1
    
    async def _make_request(
        self, 
        endpoint: str, 
        params: Optional[Dict[str, Any]] = None,
        method: str = "GET"
    ) -> Optional[Dict[str, Any]]:
        """Make an authenticated request with retry logic."""
        await self._rate_limit()
        
        client = await self._get_client()
        url = f"{self.config.base_url}{endpoint}"
        headers = dict(self.config.headers)
        
        # Add API key if required
        if self.api_key:
            # Different APIs use different auth methods
            if "openweathermap" in self.config.base_url:
                params = params or {}
                params["appid"] = self.api_key
            elif "airnow" in self.config.base_url:
                params = params or {}
                params["api_key"] = self.api_key
            elif "ncdc.noaa" in self.config.base_url:
                headers["token"] = self.api_key
            elif "purpleair" in self.config.base_url:
                headers["X-API-Key"] = self.api_key
        
        for attempt in range(self.config.retry_attempts):
            try:
                if method == "GET":
                    response = await client.get(url, params=params, headers=headers)
                else:
                    response = await client.post(url, params=params, headers=headers)
                
                response.raise_for_status()
                return response.json()
                
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 429:  # Rate limited
                    wait_time = int(e.response.headers.get("Retry-After", 60))
                    logger.warning(f"Rate limited by {self.config.name}, waiting {wait_time}s")
                    await asyncio.sleep(wait_time)
                elif e.response.status_code in (401, 403):
                    logger.error(f"Authentication failed for {self.config.name}")
                    return None
                else:
                    logger.error(f"HTTP error from {self.config.name}: {e}")
                    if attempt < self.config.retry_attempts - 1:
                        await asyncio.sleep(self.config.retry_delay * (attempt + 1))
                        
            except httpx.RequestError as e:
                logger.error(f"Request error for {self.config.name}: {e}")
                if attempt < self.config.retry_attempts - 1:
                    await asyncio.sleep(self.config.retry_delay * (attempt + 1))
            
            except Exception as e:
                logger.error(f"Unexpected error from {self.config.name}: {e}")
                if attempt < self.config.retry_attempts - 1:
                    await asyncio.sleep(self.config.retry_delay)
        
        return None
    
    @abstractmethod
    async def fetch_data(self, **kwargs) -> List[Dict[str, Any]]:
        """Fetch data from the source. Must be implemented by subclasses."""
        pass
    
    @abstractmethod
    def normalize_data(self, raw_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Normalize raw data to standard format. Must be implemented by subclasses."""
        pass


# ============================================================================
# OPENAQ CLIENT - Air Quality Data
# ============================================================================

class OpenAQClient(BaseDataSourceClient):
    """Client for OpenAQ air quality data (free, no API key required)."""
    
    def __init__(self):
        super().__init__(DATA_SOURCES["openaq"])
    
    async def fetch_data(
        self, 
        city: Optional[str] = None,
        country: str = "US",
        parameter: str = "pm25",
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Fetch air quality measurements."""
        params = {
            "country": country,
            "parameter": parameter,
            "limit": limit,
            "order_by": "datetime",
            "sort": "desc"
        }
        if city:
            params["city"] = city
        
        data = await self._make_request("/measurements", params)
        if data and "results" in data:
            return self.normalize_data(data)
        return []
    
    async def fetch_locations(
        self, 
        country: str = "US",
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Fetch available monitoring locations."""
        params = {"country": country, "limit": limit}
        data = await self._make_request("/locations", params)
        if data and "results" in data:
            return data["results"]
        return []
    
    def normalize_data(self, raw_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Normalize OpenAQ data to standard format."""
        normalized = []
        for result in raw_data.get("results", []):
            normalized.append({
                "source": "openaq",
                "type": "air_quality",
                "parameter": result.get("parameter"),
                "value": result.get("value"),
                "unit": result.get("unit"),
                "location": result.get("location"),
                "city": result.get("city"),
                "country": result.get("country"),
                "coordinates": result.get("coordinates"),
                "timestamp": result.get("date", {}).get("utc"),
                "quality_score": 0.9 if result.get("value") is not None else 0.0
            })
        return normalized


# ============================================================================
# USGS WATER CLIENT - Water Quality Data
# ============================================================================

class USGSWaterClient(BaseDataSourceClient):
    """Client for USGS Water Services (free, no API key required)."""
    
    def __init__(self):
        super().__init__(DATA_SOURCES["usgs_water"])
    
    async def fetch_data(
        self,
        state_code: str = "CA",
        parameter_codes: Optional[List[str]] = None,
        period: str = "P1D"  # Last 1 day
    ) -> List[Dict[str, Any]]:
        """Fetch instantaneous water data."""
        # Default parameters: discharge, temperature, dissolved oxygen
        if parameter_codes is None:
            parameter_codes = ["00060", "00010", "00300"]  # Discharge, Temp, DO
        
        params = {
            "format": "json",
            "stateCd": state_code,
            "parameterCd": ",".join(parameter_codes),
            "period": period,
            "siteStatus": "active"
        }
        
        data = await self._make_request("/iv/", params)
        if data and "value" in data:
            return self.normalize_data(data)
        return []
    
    async def fetch_sites(
        self,
        state_code: str = "CA",
        site_type: str = "ST"  # Stream sites
    ) -> List[Dict[str, Any]]:
        """Fetch available monitoring sites."""
        params = {
            "format": "json",
            "stateCd": state_code,
            "siteType": site_type,
            "siteStatus": "active"
        }
        data = await self._make_request("/site/", params)
        if data and "value" in data:
            return data["value"].get("timeSeries", [])
        return []
    
    def normalize_data(self, raw_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Normalize USGS data to standard format."""
        normalized = []
        time_series = raw_data.get("value", {}).get("timeSeries", [])
        
        for series in time_series:
            site_info = series.get("sourceInfo", {})
            variable = series.get("variable", {})
            values = series.get("values", [{}])[0].get("value", [])
            
            # Get most recent value
            if values:
                latest = values[-1]
                
                # Map parameter codes to readable names
                param_code = variable.get("variableCode", [{}])[0].get("value", "")
                param_name = {
                    "00060": "discharge",
                    "00010": "temperature",
                    "00300": "dissolved_oxygen",
                    "00400": "ph"
                }.get(param_code, param_code)
                
                normalized.append({
                    "source": "usgs",
                    "type": "water_quality",
                    "parameter": param_name,
                    "value": float(latest.get("value", 0)) if latest.get("value") else None,
                    "unit": variable.get("unit", {}).get("unitCode", "unknown"),
                    "location": site_info.get("siteName"),
                    "site_code": site_info.get("siteCode", [{}])[0].get("value"),
                    "coordinates": {
                        "latitude": site_info.get("geoLocation", {}).get("geogLocation", {}).get("latitude"),
                        "longitude": site_info.get("geoLocation", {}).get("geogLocation", {}).get("longitude")
                    },
                    "timestamp": latest.get("dateTime"),
                    "quality_score": 0.95 if latest.get("value") else 0.0
                })
        
        return normalized


# ============================================================================
# NOAA BUOY CLIENT - Marine/Ocean Monitoring Data
# Suggested by FiverrClawOfficial on Moltbook
# ============================================================================

class NOAABuoyClient(BaseDataSourceClient):
    """Client for NOAA National Data Buoy Center (free, no API key required).
    
    Provides real-time marine/ocean data from buoys including:
    - Water temperature
    - Wave height and period
    - Wind speed and direction
    - Air temperature
    - Atmospheric pressure
    """
    
    def __init__(self):
        super().__init__(DATA_SOURCES["noaa_buoy"])
    
    async def fetch_data(
        self,
        station_id: str = "46026",  # San Francisco Buoy default
    ) -> List[Dict[str, Any]]:
        """Fetch current buoy observations.
        
        Args:
            station_id: NOAA buoy station ID (e.g., "46026" for SF Bay area)
        
        Returns:
            List of normalized marine observation data
        """
        # NOAA NDBC provides data as text files
        # Standard Meteorological Data
        endpoint = f"/data/realtime2/{station_id}.txt"
        
        try:
            client = await self._get_client()
            await self._rate_limit()
            
            url = f"{self.config.base_url}{endpoint}"
            response = await client.get(url)
            
            if response.status_code == 200:
                return self.parse_buoy_data(response.text, station_id)
            else:
                logger.warning(f"NOAA Buoy request failed: {response.status_code}")
                return []
        except Exception as e:
            logger.error(f"Error fetching NOAA buoy data: {e}")
            return []
    
    async def fetch_stations(
        self,
        region: str = "california"
    ) -> List[Dict[str, Any]]:
        """Fetch list of active buoy stations in a region."""
        # Known buoy stations by region (subset)
        stations = {
            "california": [
                {"id": "46026", "name": "San Francisco", "lat": 37.759, "lon": -122.833},
                {"id": "46012", "name": "Half Moon Bay", "lat": 37.361, "lon": -122.881},
                {"id": "46014", "name": "Point Arena", "lat": 39.235, "lon": -123.969},
                {"id": "46022", "name": "Eel River", "lat": 40.749, "lon": -124.577},
                {"id": "46028", "name": "Cape San Martin", "lat": 35.741, "lon": -121.884},
            ],
            "pacific_northwest": [
                {"id": "46005", "name": "Washington - 300 NM West of Aberdeen", "lat": 46.050, "lon": -131.001},
                {"id": "46041", "name": "Cape Elizabeth", "lat": 47.353, "lon": -124.731},
                {"id": "46050", "name": "Stonewall Banks", "lat": 44.641, "lon": -124.500},
            ],
            "gulf_of_mexico": [
                {"id": "42001", "name": "Mid Gulf", "lat": 25.888, "lon": -89.658},
                {"id": "42002", "name": "West Gulf", "lat": 25.790, "lon": -93.666},
                {"id": "42019", "name": "Freeport, TX", "lat": 27.913, "lon": -95.360},
            ],
            "atlantic": [
                {"id": "41001", "name": "East Hatteras", "lat": 34.700, "lon": -72.660},
                {"id": "41002", "name": "South Hatteras", "lat": 31.760, "lon": -74.840},
                {"id": "44013", "name": "Boston", "lat": 42.346, "lon": -70.651},
            ],
        }
        return stations.get(region.lower(), stations["california"])
    
    def parse_buoy_data(self, raw_text: str, station_id: str) -> List[Dict[str, Any]]:
        """Parse NOAA buoy text data to structured format.
        
        NOAA provides data in fixed-width text format with headers:
        #YY  MM DD hh mm WDIR WSPD GST  WVHT   DPD   APD MWD   PRES  ATMP  WTMP  DEWP  VIS PTDY  TIDE
        """
        normalized = []
        lines = raw_text.strip().split('\n')
        
        # Skip header lines (start with #)
        data_lines = [line for line in lines if not line.startswith('#')]
        
        if not data_lines:
            return []
        
        # Parse the most recent observation (first data line)
        try:
            latest = data_lines[0].split()
            if len(latest) >= 14:
                # Extract timestamp
                year = int(latest[0]) + 2000 if int(latest[0]) < 100 else int(latest[0])
                timestamp = f"{year}-{latest[1]}-{latest[2]}T{latest[3]}:{latest[4]}:00Z"
                
                # Parse values (MM = missing data)
                def safe_float(val):
                    return float(val) if val != 'MM' and val != '999' else None
                
                # Water temperature
                wtmp = safe_float(latest[14]) if len(latest) > 14 else None
                if wtmp is not None:
                    normalized.append({
                        "source": "noaa_buoy",
                        "type": "marine",
                        "parameter": "water_temperature",
                        "value": wtmp,
                        "unit": "celsius",
                        "station_id": station_id,
                        "timestamp": timestamp,
                        "quality_score": 0.95
                    })
                
                # Wave height
                wvht = safe_float(latest[8]) if len(latest) > 8 else None
                if wvht is not None:
                    normalized.append({
                        "source": "noaa_buoy",
                        "type": "marine",
                        "parameter": "wave_height",
                        "value": wvht,
                        "unit": "meters",
                        "station_id": station_id,
                        "timestamp": timestamp,
                        "quality_score": 0.95
                    })
                
                # Wind speed
                wspd = safe_float(latest[6]) if len(latest) > 6 else None
                if wspd is not None:
                    normalized.append({
                        "source": "noaa_buoy",
                        "type": "marine",
                        "parameter": "wind_speed",
                        "value": wspd,
                        "unit": "m/s",
                        "station_id": station_id,
                        "timestamp": timestamp,
                        "quality_score": 0.95
                    })
                
                # Air temperature
                atmp = safe_float(latest[13]) if len(latest) > 13 else None
                if atmp is not None:
                    normalized.append({
                        "source": "noaa_buoy",
                        "type": "marine",
                        "parameter": "air_temperature",
                        "value": atmp,
                        "unit": "celsius",
                        "station_id": station_id,
                        "timestamp": timestamp,
                        "quality_score": 0.95
                    })
                
                # Atmospheric pressure
                pres = safe_float(latest[12]) if len(latest) > 12 else None
                if pres is not None:
                    normalized.append({
                        "source": "noaa_buoy",
                        "type": "marine",
                        "parameter": "atmospheric_pressure",
                        "value": pres,
                        "unit": "hPa",
                        "station_id": station_id,
                        "timestamp": timestamp,
                        "quality_score": 0.95
                    })
                
        except (IndexError, ValueError) as e:
            logger.warning(f"Error parsing buoy data: {e}")
        
        return normalized
    
    def normalize_data(self, raw_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Normalize raw NOAA buoy data.
        
        For NOAA buoy data, normalization happens in parse_buoy_data.
        This method is provided for API compatibility.
        """
        # NOAA data comes as text, normalization is done in parse_buoy_data
        if isinstance(raw_data, dict) and "raw_text" in raw_data:
            return self.parse_buoy_data(raw_data["raw_text"], raw_data.get("station_id", "unknown"))
        return []


# ============================================================================
# OPENWEATHERMAP CLIENT - Weather Data
# ============================================================================

class OpenWeatherMapClient(BaseDataSourceClient):
    """Client for OpenWeatherMap API (requires free API key)."""
    
    def __init__(self):
        super().__init__(DATA_SOURCES["openweathermap"])
    
    async def fetch_data(
        self,
        lat: float = 37.7749,  # San Francisco default
        lon: float = -122.4194
    ) -> List[Dict[str, Any]]:
        """Fetch current weather data."""
        if not self.api_key:
            logger.warning("OpenWeatherMap API key not configured")
            return []
        
        params = {
            "lat": lat,
            "lon": lon,
            "units": "metric"
        }
        
        data = await self._make_request("/weather", params)
        if data:
            return self.normalize_data(data)
        return []
    
    async def fetch_air_pollution(
        self,
        lat: float = 37.7749,
        lon: float = -122.4194
    ) -> List[Dict[str, Any]]:
        """Fetch air pollution data."""
        if not self.api_key:
            return []
        
        params = {"lat": lat, "lon": lon}
        data = await self._make_request("/air_pollution", params)
        if data and "list" in data:
            return self._normalize_pollution_data(data)
        return []
    
    def normalize_data(self, raw_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Normalize weather data to standard format."""
        normalized = []
        main = raw_data.get("main", {})
        wind = raw_data.get("wind", {})
        coord = raw_data.get("coord", {})
        
        # Temperature
        if "temp" in main:
            normalized.append({
                "source": "openweathermap",
                "type": "weather",
                "parameter": "temperature",
                "value": main["temp"],
                "unit": "celsius",
                "location": raw_data.get("name"),
                "coordinates": coord,
                "timestamp": datetime.utcnow().isoformat(),
                "quality_score": 0.95
            })
        
        # Humidity
        if "humidity" in main:
            normalized.append({
                "source": "openweathermap",
                "type": "weather",
                "parameter": "humidity",
                "value": main["humidity"],
                "unit": "percent",
                "location": raw_data.get("name"),
                "coordinates": coord,
                "timestamp": datetime.utcnow().isoformat(),
                "quality_score": 0.95
            })
        
        # Pressure
        if "pressure" in main:
            normalized.append({
                "source": "openweathermap",
                "type": "weather",
                "parameter": "pressure",
                "value": main["pressure"],
                "unit": "hPa",
                "location": raw_data.get("name"),
                "coordinates": coord,
                "timestamp": datetime.utcnow().isoformat(),
                "quality_score": 0.95
            })
        
        # Wind speed
        if "speed" in wind:
            normalized.append({
                "source": "openweathermap",
                "type": "weather",
                "parameter": "wind_speed",
                "value": wind["speed"],
                "unit": "m/s",
                "location": raw_data.get("name"),
                "coordinates": coord,
                "timestamp": datetime.utcnow().isoformat(),
                "quality_score": 0.95
            })
        
        return normalized
    
    def _normalize_pollution_data(self, raw_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Normalize air pollution data."""
        normalized = []
        if raw_data.get("list"):
            item = raw_data["list"][0]
            components = item.get("components", {})
            
            for param, value in components.items():
                normalized.append({
                    "source": "openweathermap",
                    "type": "air_quality",
                    "parameter": param,
                    "value": value,
                    "unit": "μg/m³",
                    "aqi": item.get("main", {}).get("aqi"),
                    "timestamp": datetime.utcfromtimestamp(item.get("dt", 0)).isoformat(),
                    "quality_score": 0.9
                })
        
        return normalized


# ============================================================================
# EPA AIRNOW CLIENT - US Air Quality Index
# ============================================================================

class AirNowClient(BaseDataSourceClient):
    """Client for EPA AirNow API (requires free API key)."""
    
    def __init__(self):
        super().__init__(DATA_SOURCES["airnow"])
    
    async def fetch_data(
        self,
        zipcode: Optional[str] = None,
        lat: Optional[float] = None,
        lon: Optional[float] = None,
        distance: int = 25
    ) -> List[Dict[str, Any]]:
        """Fetch current AQI observations."""
        if not self.api_key:
            logger.warning("AirNow API key not configured")
            return []
        
        params = {"format": "application/json", "distance": distance}
        
        if zipcode:
            endpoint = "/observation/zipCode/current/"
            params["zipCode"] = zipcode
        elif lat and lon:
            endpoint = "/observation/latLong/current/"
            params["latitude"] = lat
            params["longitude"] = lon
        else:
            logger.warning("AirNow requires zipcode or lat/lon")
            return []
        
        data = await self._make_request(endpoint, params)
        if data:
            return self.normalize_data({"results": data})
        return []
    
    def normalize_data(self, raw_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Normalize AirNow data to standard format."""
        normalized = []
        for result in raw_data.get("results", []):
            normalized.append({
                "source": "airnow",
                "type": "air_quality",
                "parameter": result.get("ParameterName"),
                "value": result.get("AQI"),
                "unit": "AQI",
                "category": result.get("Category", {}).get("Name"),
                "location": result.get("ReportingArea"),
                "state": result.get("StateCode"),
                "timestamp": f"{result.get('DateObserved')}T{result.get('HourObserved')}:00:00Z",
                "quality_score": 0.95
            })
        return normalized


# ============================================================================
# DATA INGESTION MANAGER
# ============================================================================

class DataIngestionManager:
    """
    Manages data ingestion from multiple public environmental data sources.
    
    Features:
    - Automatic source discovery and configuration
    - Parallel data fetching with rate limiting
    - Data normalization to common format
    - Configurable polling intervals
    - Health monitoring and alerting
    """
    
    def __init__(self):
        self.clients: Dict[str, BaseDataSourceClient] = {}
        self.running = False
        self.tasks: List[asyncio.Task] = []
        self._initialize_clients()
    
    def _initialize_clients(self):
        """Initialize all data source clients."""
        # Always available (no API key required)
        self.clients["openaq"] = OpenAQClient()
        self.clients["usgs_water"] = USGSWaterClient()
        
        # Optional (require API keys)
        if os.environ.get("OPENWEATHERMAP_API_KEY"):
            self.clients["openweathermap"] = OpenWeatherMapClient()
            logger.info("OpenWeatherMap client initialized")
        
        if os.environ.get("AIRNOW_API_KEY"):
            self.clients["airnow"] = AirNowClient()
            logger.info("AirNow client initialized")
        
        logger.info(f"Initialized {len(self.clients)} data source clients")
    
    async def fetch_all_data(self) -> Dict[str, List[Dict[str, Any]]]:
        """Fetch data from all configured sources in parallel."""
        results = {}
        tasks = []
        
        # Create fetch tasks for each client
        for name, client in self.clients.items():
            tasks.append(self._fetch_with_name(name, client))
        
        # Execute in parallel
        completed = await asyncio.gather(*tasks, return_exceptions=True)
        
        for name, data in completed:
            if isinstance(data, Exception):
                logger.error(f"Error fetching from {name}: {data}")
                results[name] = []
            else:
                results[name] = data
        
        return results
    
    async def _fetch_with_name(
        self, 
        name: str, 
        client: BaseDataSourceClient
    ) -> tuple:
        """Fetch data and return with source name."""
        try:
            data = await client.fetch_data()
            return (name, data)
        except Exception as e:
            return (name, e)
    
    async def start_continuous_ingestion(
        self, 
        callback: Optional[callable] = None
    ):
        """Start continuous data ingestion loop."""
        if self.running:
            logger.warning("Ingestion already running")
            return
        
        self.running = True
        logger.info("Starting continuous data ingestion...")
        
        for name, client in self.clients.items():
            interval = client.config.default_poll_interval
            task = asyncio.create_task(
                self._ingestion_loop(name, client, interval, callback)
            )
            self.tasks.append(task)
    
    async def _ingestion_loop(
        self,
        name: str,
        client: BaseDataSourceClient,
        interval: int,
        callback: Optional[callable]
    ):
        """Continuous ingestion loop for a single source."""
        while self.running:
            try:
                data = await client.fetch_data()
                
                if data:
                    logger.info(f"Fetched {len(data)} records from {name}")
                    
                    if callback:
                        await callback(name, data)
                
                await asyncio.sleep(interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in ingestion loop for {name}: {e}")
                await asyncio.sleep(60)  # Wait before retry
    
    async def stop(self):
        """Stop all ingestion tasks."""
        self.running = False
        
        for task in self.tasks:
            task.cancel()
        
        if self.tasks:
            await asyncio.gather(*self.tasks, return_exceptions=True)
        
        # Close all clients
        for client in self.clients.values():
            await client.close()
        
        logger.info("Data ingestion stopped")
    
    def get_status(self) -> Dict[str, Any]:
        """Get status of all data sources."""
        status = {
            "running": self.running,
            "sources": {}
        }
        
        for name, client in self.clients.items():
            config = client.config
            status["sources"][name] = {
                "name": config.name,
                "type": config.source_type.value,
                "requires_api_key": config.requires_api_key,
                "api_key_configured": bool(client.api_key) if config.requires_api_key else True,
                "poll_interval": config.default_poll_interval,
                "rate_limit": config.rate_limit_per_minute
            }
        
        return status


# ============================================================================
# SINGLETON INSTANCE
# ============================================================================

# Global data ingestion manager instance
data_ingestion_manager = DataIngestionManager()


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

async def fetch_air_quality(city: Optional[str] = None, country: str = "US") -> List[Dict[str, Any]]:
    """Convenience function to fetch air quality data."""
    client = OpenAQClient()
    try:
        return await client.fetch_data(city=city, country=country)
    finally:
        await client.close()


async def fetch_water_quality(state_code: str = "CA") -> List[Dict[str, Any]]:
    """Convenience function to fetch water quality data."""
    client = USGSWaterClient()
    try:
        return await client.fetch_data(state_code=state_code)
    finally:
        await client.close()


async def fetch_weather(lat: float, lon: float) -> List[Dict[str, Any]]:
    """Convenience function to fetch weather data."""
    client = OpenWeatherMapClient()
    try:
        return await client.fetch_data(lat=lat, lon=lon)
    finally:
        await client.close()
