"""
API Client for Environmental Monitoring Dashboard

Handles all communication with the backend API.
"""
import asyncio
import json
import logging
from typing import Any, Dict, List, Optional

import httpx
from cachetools import TTLCache

from config import API_BASE_URL, API_TIMEOUT, CACHE_TTL_SHORT


# Set up logging
logger = logging.getLogger(__name__)

# In-memory cache for frequently accessed data
_cache = TTLCache(maxsize=1000, ttl=CACHE_TTL_SHORT)


class APIClient:
    """Async HTTP client for the Environmental Monitoring API."""
    
    def __init__(self, base_url: str = API_BASE_URL, timeout: int = API_TIMEOUT):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._client: Optional[httpx.AsyncClient] = None
    
    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                base_url=self.base_url,
                timeout=self.timeout,
                follow_redirects=True
            )
        return self._client
    
    async def close(self):
        """Close the HTTP client."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()
    
    async def get(self, endpoint: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """Make GET request to API."""
        cache_key = f"{endpoint}:{json.dumps(params or {}, sort_keys=True)}"
        
        # Check cache
        if cache_key in _cache:
            return _cache[cache_key]
        
        try:
            client = await self._get_client()
            response = await client.get(endpoint, params=params)
            response.raise_for_status()
            data = response.json()
            
            # Cache successful responses
            _cache[cache_key] = data
            return data
            
        except httpx.HTTPStatusError as e:
            return {"error": f"HTTP {e.response.status_code}: {e.response.text}", "success": False}
        except httpx.RequestError as e:
            return {"error": f"Request failed: {str(e)}", "success": False}
        except Exception as e:
            return {"error": f"Unexpected error: {str(e)}", "success": False}
    
    async def post(self, endpoint: str, data: Optional[Dict] = None) -> Dict[str, Any]:
        """Make POST request to API."""
        try:
            client = await self._get_client()
            response = await client.post(endpoint, json=data)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {"error": str(e), "success": False}
    
    # ==================== Hub Endpoints ====================
    
    async def get_hub_info(self) -> Dict:
        """Get hub information and available endpoints."""
        return await self.get("/api/v1/hub")
    
    async def get_sources(self, category: Optional[str] = None) -> Dict:
        """Get available data sources."""
        params = {"category": category} if category else None
        return await self.get("/api/v1/hub/sources", params)
    
    async def get_categories(self) -> Dict:
        """Get available data categories."""
        return await self.get("/api/v1/hub/categories")
    
    async def proxy_request(self, source_id: str, endpoint: str) -> Dict:
        """Proxy request to external data source."""
        return await self.get(f"/api/v1/hub/proxy/{source_id}", {"endpoint": endpoint})
    
    async def get_location_data(
        self,
        lat: float,
        lon: float,
        radius_km: float = 50.0,
        categories: Optional[List[str]] = None
    ) -> Dict:
        """Get all environmental data for a location."""
        params: Dict[str, Any] = {
            "lat": lat,
            "lon": lon,
            "radius_km": radius_km
        }
        if categories:
            params["categories"] = ",".join(categories)
        return await self.get("/api/v1/hub/location", params)
    
    async def get_category_data(
        self,
        category: str,
        lat: float = 37.7749,
        lon: float = -122.4194
    ) -> Dict:
        """Get data from all sources in a category."""
        return await self.get(f"/api/v1/hub/category/{category}", {"lat": lat, "lon": lon})
    
    async def analyze_location(
        self,
        lat: float,
        lon: float,
        days: int = 7
    ) -> Dict:
        """Get connect-the-dots analysis for a location."""
        return await self.get("/api/v1/hub/analyze", {
            "lat": lat,
            "lon": lon,
            "days": days
        })
    
    async def quick_check(self, lat: float, lon: float) -> Dict:
        """Quick environmental check for a location."""
        return await self.get("/api/v1/hub/quick", {"lat": lat, "lon": lon})
    
    # ==================== Data Source Endpoints ====================
    
    async def get_air_quality(
        self,
        city: Optional[str] = None,
        country: str = "US",
        parameter: str = "pm25"
    ) -> Dict:
        """Get air quality data."""
        params = {"country": country, "parameter": parameter}
        if city:
            params["city"] = city
        return await self.get("/api/v1/data-sources/air-quality", params)
    
    async def get_water_quality(self, state_code: str = "CA") -> Dict:
        """Get water quality data."""
        return await self.get("/api/v1/data-sources/water-quality", {"state_code": state_code})
    
    async def get_weather(self, lat: float, lon: float) -> Dict:
        """Get weather data."""
        return await self.get("/api/v1/data-sources/weather", {"lat": lat, "lon": lon})
    
    async def get_marine_data(
        self,
        station_id: str = "46026",
        region: Optional[str] = None
    ) -> Dict:
        """Get marine/ocean data."""
        params = {"station_id": station_id}
        if region:
            params["region"] = region
        return await self.get("/api/v1/data-sources/marine", params)
    
    async def get_all_data_sources(self) -> Dict:
        """Fetch from all data sources in parallel."""
        return await self.get("/api/v1/data-sources/all")
    
    # ==================== Data Quality Endpoints ====================
    
    async def get_data_freshness(self) -> Dict:
        """Check freshness of all data sources."""
        return await self.get("/api/v1/data-quality/freshness")
    
    async def get_supported_parameters(self) -> Dict:
        """Get supported parameters and validation ranges."""
        return await self.get("/api/v1/data-quality/parameters")
    
    # ==================== Dashboard Endpoints ====================
    
    async def get_dashboard_stats(self) -> Dict:
        """Get dashboard statistics."""
        return await self.get("/api/v1/dashboard/stats")
    
    async def get_sensor_stats(self) -> Dict:
        """Get sensor statistics."""
        return await self.get("/api/v1/dashboard/sensor-stats")
    
    # ==================== System Endpoints ====================
    
    async def get_health(self) -> Dict:
        """Get system health status."""
        return await self.get("/health")
    
    async def get_system_health(self) -> Dict:
        """Get comprehensive system health."""
        return await self.get("/api/v1/system/health")


# Singleton instance
api_client = APIClient()


# Synchronous wrapper for Dash callbacks
def sync_api_call(coro):
    """Run async API call synchronously for Dash callbacks."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # Event loop already running (e.g., in production), use thread
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, coro)
                return future.result(timeout=API_TIMEOUT)
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    return loop.run_until_complete(coro)


def sync_get(endpoint: str, params: Optional[Dict] = None) -> Dict:
    """Make synchronous GET request to API."""
    url = f"{API_BASE_URL.rstrip('/')}{endpoint}"
    cache_key = f"{endpoint}:{json.dumps(params or {}, sort_keys=True)}"
    
    # Check cache
    if cache_key in _cache:
        return _cache[cache_key]
    
    try:
        with httpx.Client(timeout=API_TIMEOUT, follow_redirects=True) as client:
            response = client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            _cache[cache_key] = data
            return data
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error {e.response.status_code} for {endpoint}: {e.response.text[:100]}")
        return {"error": f"HTTP {e.response.status_code}", "success": False}
    except httpx.RequestError as e:
        logger.error(f"Request error for {endpoint}: {str(e)}")
        return {"error": f"Request failed: {str(e)}", "success": False}
    except Exception as e:
        logger.error(f"Unexpected error for {endpoint}: {str(e)}")
        return {"error": f"Unexpected error: {str(e)}", "success": False}


def get_sources(category: Optional[str] = None) -> Dict:
    """Sync wrapper for get_sources using direct HTTP client."""
    params = {"category": category} if category else None
    return sync_get("/api/v1/hub/sources", params)


def get_categories() -> Dict:
    """Sync wrapper for get_categories using direct HTTP client."""
    return sync_get("/api/v1/hub/categories")


def get_location_data(lat: float, lon: float, **kwargs) -> Dict:
    """Sync wrapper for get_location_data using direct HTTP client."""
    params = {"lat": lat, "lon": lon, **kwargs}
    return sync_get("/api/v1/hub/location", params)


def get_category_data(category: str, lat: float = 37.7749, lon: float = -122.4194) -> Dict:
    """Sync wrapper for get_category_data using direct HTTP client."""
    return sync_get(f"/api/v1/hub/category/{category}", {"lat": lat, "lon": lon})


def analyze_location(lat: float, lon: float, days: int = 7) -> Dict:
    """Sync wrapper for analyze_location using direct HTTP client."""
    return sync_get("/api/v1/hub/analyze", {"lat": lat, "lon": lon, "days": days})


def quick_check(lat: float, lon: float) -> Dict:
    """Sync wrapper for quick_check using direct HTTP client."""
    return sync_get("/api/v1/hub/quick", {"lat": lat, "lon": lon})


def get_hub_info() -> Dict:
    """Sync wrapper for get_hub_info using direct HTTP client."""
    return sync_get("/api/v1/hub")


def get_health() -> Dict:
    """Sync wrapper for get_health using direct HTTP client."""
    return sync_get("/health")


def proxy_request(source_id: str, endpoint: str) -> Dict:
    """Sync wrapper for proxy_request using direct HTTP client."""
    return sync_get(f"/api/v1/hub/proxy/{source_id}", {"endpoint": endpoint})
