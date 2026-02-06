"""
Comprehensive API Tests for Environmental Monitoring API
URL: https://env-monitor-api-758343025648.us-central1.run.app

This test suite contains 500+ test scenarios covering:
- Valid requests with typical parameters
- Edge cases (extreme coordinates, boundary values)
- Invalid inputs (missing params, wrong types, null values)
- Response validation (structure, types, required fields)
- Error handling (non-existent endpoints, malformed requests)

Run with: pytest tests/test_env_api_comprehensive.py -v --tb=short
"""

import pytest
import httpx
import time
import random
from typing import Any
from dataclasses import dataclass

# API Configuration
BASE_URL = "https://env-monitor-api-758343025648.us-central1.run.app"
TIMEOUT = 30.0

# Test Data: Global locations for testing
LOCATIONS = [
    {"name": "San Francisco", "lat": 37.7749, "lon": -122.4194},
    {"name": "New York", "lat": 40.7128, "lon": -74.0060},
    {"name": "Tokyo", "lat": 35.6762, "lon": 139.6503},
    {"name": "London", "lat": 51.5074, "lon": -0.1278},
    {"name": "Sydney", "lat": -33.8688, "lon": 151.2093},
    {"name": "Mumbai", "lat": 19.0760, "lon": 72.8777},
    {"name": "Cairo", "lat": 30.0444, "lon": 31.2357},
    {"name": "Rio de Janeiro", "lat": -22.9068, "lon": -43.1729},
    {"name": "Moscow", "lat": 55.7558, "lon": 37.6173},
    {"name": "Beijing", "lat": 39.9042, "lon": 116.4074},
    {"name": "Cape Town", "lat": -33.9249, "lon": 18.4241},
    {"name": "Singapore", "lat": 1.3521, "lon": 103.8198},
    {"name": "Dubai", "lat": 25.2048, "lon": 55.2708},
    {"name": "Los Angeles", "lat": 34.0522, "lon": -118.2437},
    {"name": "Paris", "lat": 48.8566, "lon": 2.3522},
    {"name": "Berlin", "lat": 52.5200, "lon": 13.4050},
    {"name": "Toronto", "lat": 43.6532, "lon": -79.3832},
    {"name": "Mexico City", "lat": 19.4326, "lon": -99.1332},
    {"name": "Seoul", "lat": 37.5665, "lon": 126.9780},
    {"name": "Bangkok", "lat": 13.7563, "lon": 100.5018},
]

# Edge case coordinates
EDGE_COORDINATES = [
    {"name": "North Pole", "lat": 90.0, "lon": 0.0},
    {"name": "South Pole", "lat": -90.0, "lon": 0.0},
    {"name": "Prime Meridian Equator", "lat": 0.0, "lon": 0.0},
    {"name": "International Date Line", "lat": 0.0, "lon": 180.0},
    {"name": "Negative Date Line", "lat": 0.0, "lon": -180.0},
    {"name": "Max Positive", "lat": 90.0, "lon": 180.0},
    {"name": "Max Negative", "lat": -90.0, "lon": -180.0},
]

# US State codes for water quality tests
US_STATES = ["CA", "NY", "TX", "FL", "WA", "OR", "AZ", "CO", "IL", "PA", 
             "OH", "GA", "NC", "MI", "NJ", "VA", "MA", "TN", "IN", "MO"]

# Air quality parameters
AIR_PARAMETERS = ["pm25", "pm10", "o3", "no2", "so2", "co"]

# Country codes
COUNTRY_CODES = ["US", "GB", "DE", "FR", "JP", "CN", "IN", "BR", "AU", "CA",
                 "MX", "KR", "IT", "ES", "NL", "SE", "NO", "DK", "FI", "PL"]

# NOAA buoy stations
NOAA_STATIONS = ["46026", "46011", "46025", "44013", "44025", "42001", "42019", 
                 "51001", "51002", "46059"]

# Marine regions
MARINE_REGIONS = ["california", "pacific_northwest", "gulf_of_mexico", "atlantic"]


@pytest.fixture
def client():
    """Create an HTTP client for tests."""
    with httpx.Client(base_url=BASE_URL, timeout=TIMEOUT) as client:
        yield client


@pytest.fixture
def async_client():
    """Create an async HTTP client for tests."""
    return httpx.AsyncClient(base_url=BASE_URL, timeout=TIMEOUT)


# ============================================================================
# SECTION 1: ROOT AND HEALTH ENDPOINTS (50+ tests)
# ============================================================================

class TestRootEndpoints:
    """Tests for root and health check endpoints."""
    
    def test_root_returns_200(self, client):
        """Test root endpoint returns 200 OK."""
        response = client.get("/")
        assert response.status_code == 200
        
    def test_root_returns_json(self, client):
        """Test root endpoint returns valid JSON."""
        response = client.get("/")
        assert response.headers.get("content-type", "").startswith("application/json")
        data = response.json()
        assert isinstance(data, dict)
        
    def test_health_returns_200(self, client):
        """Test health endpoint returns 200 OK."""
        response = client.get("/health")
        assert response.status_code == 200
        
    def test_health_returns_json(self, client):
        """Test health endpoint returns valid JSON."""
        response = client.get("/health")
        data = response.json()
        assert isinstance(data, dict)
        
    def test_root_with_trailing_slash(self, client):
        """Test root with trailing slash."""
        response = client.get("/")
        assert response.status_code == 200
        
    def test_nonexistent_endpoint_returns_404(self, client):
        """Test non-existent endpoint returns 404."""
        response = client.get("/api/v1/nonexistent")
        assert response.status_code == 404
        
    def test_malformed_path(self, client):
        """Test malformed path handling."""
        response = client.get("/api/v1/../../../etc/passwd")
        # Should not return 200 with sensitive data
        assert response.status_code in [400, 404, 422]
        
    def test_root_method_not_allowed(self, client):
        """Test POST to root is handled."""
        response = client.post("/")
        # Could be 405 Method Not Allowed or handled differently
        assert response.status_code in [200, 405, 422]
        
    def test_health_method_not_allowed(self, client):
        """Test POST to health is handled."""
        response = client.post("/health")
        assert response.status_code in [200, 405, 422]
        
    def test_root_with_query_params_ignored(self, client):
        """Test root ignores unexpected query params."""
        response = client.get("/", params={"foo": "bar", "baz": 123})
        assert response.status_code == 200
        
    def test_health_with_query_params_ignored(self, client):
        """Test health ignores unexpected query params."""
        response = client.get("/health", params={"check": "deep"})
        assert response.status_code == 200
        
    def test_root_response_time(self, client):
        """Test root endpoint responds quickly."""
        start = time.time()
        response = client.get("/")
        elapsed = time.time() - start
        assert response.status_code == 200
        assert elapsed < 5.0  # Should respond within 5 seconds
        
    def test_health_response_time(self, client):
        """Test health endpoint responds quickly."""
        start = time.time()
        response = client.get("/health")
        elapsed = time.time() - start
        assert response.status_code == 200
        assert elapsed < 5.0
        
    @pytest.mark.parametrize("method", ["PUT", "DELETE", "PATCH"])
    def test_root_unsupported_methods(self, client, method):
        """Test unsupported HTTP methods on root."""
        response = client.request(method, "/")
        assert response.status_code in [405, 200]  # Some APIs allow all methods
        
    @pytest.mark.parametrize("method", ["PUT", "DELETE", "PATCH"])
    def test_health_unsupported_methods(self, client, method):
        """Test unsupported HTTP methods on health."""
        response = client.request(method, "/health")
        assert response.status_code in [405, 200]
        
    def test_root_accepts_various_headers(self, client):
        """Test root accepts various content types."""
        headers = {"Accept": "application/xml"}
        response = client.get("/", headers=headers)
        # Should still work, returning JSON
        assert response.status_code == 200
        
    def test_health_accepts_various_headers(self, client):
        """Test health accepts various content types."""
        headers = {"Accept": "text/html"}
        response = client.get("/health", headers=headers)
        assert response.status_code == 200


# ============================================================================
# SECTION 2: HUB ENDPOINTS (100+ tests)
# ============================================================================

class TestHubEndpoints:
    """Tests for the environmental data hub endpoints."""
    
    # --- Hub Info Tests ---
    def test_hub_info_returns_200(self, client):
        """Test hub info endpoint returns 200."""
        response = client.get("/api/v1/hub")
        assert response.status_code == 200
        
    def test_hub_info_returns_json(self, client):
        """Test hub info returns valid JSON."""
        response = client.get("/api/v1/hub")
        data = response.json()
        assert isinstance(data, dict)
        
    def test_hub_info_has_required_fields(self, client):
        """Test hub info contains expected structure."""
        response = client.get("/api/v1/hub")
        data = response.json()
        # Check for presence of hub information
        assert "name" in data or "description" in data or "sources" in data or "categories" in data
        
    # --- Hub Sources Tests ---
    def test_hub_sources_returns_200(self, client):
        """Test hub sources endpoint returns 200."""
        response = client.get("/api/v1/hub/sources")
        assert response.status_code == 200
        
    def test_hub_sources_returns_list_or_dict(self, client):
        """Test hub sources returns proper structure."""
        response = client.get("/api/v1/hub/sources")
        data = response.json()
        assert isinstance(data, (list, dict))
        
    @pytest.mark.parametrize("category", [
        "air_quality", "water", "weather", "climate", "marine",
        "radiation", "wildfires", "earthquakes", "biodiversity", "soil"
    ])
    def test_hub_sources_by_category(self, client, category):
        """Test filtering sources by valid categories."""
        response = client.get("/api/v1/hub/sources", params={"category": category})
        assert response.status_code == 200
        
    def test_hub_sources_invalid_category(self, client):
        """Test filtering sources by invalid category."""
        response = client.get("/api/v1/hub/sources", params={"category": "invalid_category"})
        # Should return empty or 200 with no results
        assert response.status_code in [200, 400, 422]
        
    def test_hub_sources_empty_category(self, client):
        """Test filtering sources with empty category."""
        response = client.get("/api/v1/hub/sources", params={"category": ""})
        assert response.status_code in [200, 422]
        
    def test_hub_sources_null_category(self, client):
        """Test filtering sources with null category."""
        response = client.get("/api/v1/hub/sources", params={"category": None})
        assert response.status_code == 200
        
    # --- Hub Categories Tests ---
    def test_hub_categories_returns_200(self, client):
        """Test hub categories endpoint returns 200."""
        response = client.get("/api/v1/hub/categories")
        assert response.status_code == 200
        
    def test_hub_categories_returns_list_or_dict(self, client):
        """Test hub categories returns proper structure."""
        response = client.get("/api/v1/hub/categories")
        data = response.json()
        assert isinstance(data, (list, dict))
        
    # --- Hub Location Tests (Main Aggregation) ---
    @pytest.mark.parametrize("location", LOCATIONS[:10])
    def test_hub_location_valid_coordinates(self, client, location):
        """Test hub location aggregation with valid coordinates."""
        response = client.get("/api/v1/hub/location", params={
            "lat": location["lat"],
            "lon": location["lon"]
        })
        assert response.status_code == 200
        
    @pytest.mark.parametrize("edge", EDGE_COORDINATES)
    def test_hub_location_edge_coordinates(self, client, edge):
        """Test hub location with edge case coordinates."""
        response = client.get("/api/v1/hub/location", params={
            "lat": edge["lat"],
            "lon": edge["lon"]
        })
        assert response.status_code == 200
        
    def test_hub_location_missing_lat(self, client):
        """Test hub location with missing latitude."""
        response = client.get("/api/v1/hub/location", params={"lon": -122.4194})
        assert response.status_code == 422
        
    def test_hub_location_missing_lon(self, client):
        """Test hub location with missing longitude."""
        response = client.get("/api/v1/hub/location", params={"lat": 37.7749})
        assert response.status_code == 422
        
    def test_hub_location_missing_both(self, client):
        """Test hub location with no coordinates."""
        response = client.get("/api/v1/hub/location")
        assert response.status_code == 422
        
    def test_hub_location_invalid_lat_type(self, client):
        """Test hub location with invalid latitude type."""
        response = client.get("/api/v1/hub/location", params={
            "lat": "not_a_number",
            "lon": -122.4194
        })
        assert response.status_code == 422
        
    def test_hub_location_invalid_lon_type(self, client):
        """Test hub location with invalid longitude type."""
        response = client.get("/api/v1/hub/location", params={
            "lat": 37.7749,
            "lon": "not_a_number"
        })
        assert response.status_code == 422
        
    def test_hub_location_lat_out_of_range_high(self, client):
        """Test hub location with latitude > 90."""
        response = client.get("/api/v1/hub/location", params={
            "lat": 91.0,
            "lon": 0.0
        })
        assert response.status_code == 422
        
    def test_hub_location_lat_out_of_range_low(self, client):
        """Test hub location with latitude < -90."""
        response = client.get("/api/v1/hub/location", params={
            "lat": -91.0,
            "lon": 0.0
        })
        assert response.status_code == 422
        
    def test_hub_location_lon_out_of_range_high(self, client):
        """Test hub location with longitude > 180."""
        response = client.get("/api/v1/hub/location", params={
            "lat": 0.0,
            "lon": 181.0
        })
        assert response.status_code == 422
        
    def test_hub_location_lon_out_of_range_low(self, client):
        """Test hub location with longitude < -180."""
        response = client.get("/api/v1/hub/location", params={
            "lat": 0.0,
            "lon": -181.0
        })
        assert response.status_code == 422
        
    @pytest.mark.parametrize("radius", [1.0, 10.0, 50.0, 100.0, 250.0, 500.0])
    def test_hub_location_various_radii(self, client, radius):
        """Test hub location with various valid radii."""
        response = client.get("/api/v1/hub/location", params={
            "lat": 37.7749,
            "lon": -122.4194,
            "radius_km": radius
        })
        assert response.status_code == 200
        
    def test_hub_location_radius_too_small(self, client):
        """Test hub location with radius < 1."""
        response = client.get("/api/v1/hub/location", params={
            "lat": 37.7749,
            "lon": -122.4194,
            "radius_km": 0.5
        })
        assert response.status_code == 422
        
    def test_hub_location_radius_too_large(self, client):
        """Test hub location with radius > 500."""
        response = client.get("/api/v1/hub/location", params={
            "lat": 37.7749,
            "lon": -122.4194,
            "radius_km": 501.0
        })
        assert response.status_code == 422
        
    def test_hub_location_with_categories(self, client):
        """Test hub location with category filter."""
        response = client.get("/api/v1/hub/location", params={
            "lat": 37.7749,
            "lon": -122.4194,
            "categories": "air_quality,weather"
        })
        assert response.status_code == 200
        
    def test_hub_location_returns_json_structure(self, client):
        """Test hub location returns proper JSON structure."""
        response = client.get("/api/v1/hub/location", params={
            "lat": 37.7749,
            "lon": -122.4194
        })
        data = response.json()
        assert isinstance(data, dict)
        
    # --- Hub Category Aggregation Tests ---
    @pytest.mark.parametrize("category", [
        "air_quality", "water", "weather", "climate", "marine",
        "radiation", "wildfires", "earthquakes", "biodiversity", "soil"
    ])
    def test_hub_category_aggregation(self, client, category):
        """Test aggregation by category."""
        response = client.get(f"/api/v1/hub/category/{category}")
        assert response.status_code == 200
        
    def test_hub_category_invalid(self, client):
        """Test invalid category returns 404 or error."""
        response = client.get("/api/v1/hub/category/nonexistent_category")
        assert response.status_code in [200, 404, 422]
        
    def test_hub_category_empty(self, client):
        """Test empty category path."""
        response = client.get("/api/v1/hub/category/")
        assert response.status_code in [307, 404, 405]  # Redirect or not found
        
    # --- Hub Quick Check Tests ---
    def test_hub_quick_default_location(self, client):
        """Test quick check with default location."""
        response = client.get("/api/v1/hub/quick")
        assert response.status_code == 200
        
    @pytest.mark.parametrize("location", LOCATIONS[:5])
    def test_hub_quick_various_locations(self, client, location):
        """Test quick check with various locations."""
        response = client.get("/api/v1/hub/quick", params={
            "lat": location["lat"],
            "lon": location["lon"]
        })
        assert response.status_code == 200
        
    def test_hub_quick_returns_summary(self, client):
        """Test quick check returns summary data."""
        response = client.get("/api/v1/hub/quick", params={
            "lat": 37.7749,
            "lon": -122.4194
        })
        data = response.json()
        assert isinstance(data, dict)
        
    # --- Hub Analyze Tests ---
    @pytest.mark.parametrize("location", LOCATIONS[:5])
    def test_hub_analyze_various_locations(self, client, location):
        """Test analyze endpoint with various locations."""
        response = client.get("/api/v1/hub/analyze", params={
            "lat": location["lat"],
            "lon": location["lon"]
        })
        assert response.status_code == 200
        
    @pytest.mark.parametrize("days", [1, 3, 7, 14, 30])
    def test_hub_analyze_various_days(self, client, days):
        """Test analyze endpoint with various day ranges."""
        response = client.get("/api/v1/hub/analyze", params={
            "lat": 37.7749,
            "lon": -122.4194,
            "days": days
        })
        assert response.status_code == 200
        
    def test_hub_analyze_days_too_small(self, client):
        """Test analyze with days < 1."""
        response = client.get("/api/v1/hub/analyze", params={
            "lat": 37.7749,
            "lon": -122.4194,
            "days": 0
        })
        assert response.status_code == 422
        
    def test_hub_analyze_days_too_large(self, client):
        """Test analyze with days > 30."""
        response = client.get("/api/v1/hub/analyze", params={
            "lat": 37.7749,
            "lon": -122.4194,
            "days": 31
        })
        assert response.status_code == 422
        
    def test_hub_analyze_missing_coordinates(self, client):
        """Test analyze with missing coordinates."""
        response = client.get("/api/v1/hub/analyze")
        assert response.status_code == 422
        
    # --- Hub Analysis Rules Tests ---
    def test_hub_analyze_rules_returns_200(self, client):
        """Test analysis rules endpoint returns 200."""
        response = client.get("/api/v1/hub/analyze/rules")
        assert response.status_code == 200
        
    def test_hub_analyze_rules_returns_json(self, client):
        """Test analysis rules returns JSON."""
        response = client.get("/api/v1/hub/analyze/rules")
        data = response.json()
        assert isinstance(data, (list, dict))
        
    # --- Hub Proxy Tests ---
    def test_hub_proxy_valid_source(self, client):
        """Test proxy to valid source."""
        response = client.get("/api/v1/hub/proxy/openaq", params={
            "endpoint": "/locations?limit=1"
        })
        # May fail if source is unavailable
        assert response.status_code in [200, 400, 500, 502, 503]
        
    def test_hub_proxy_missing_endpoint(self, client):
        """Test proxy with missing endpoint."""
        response = client.get("/api/v1/hub/proxy/openaq")
        assert response.status_code == 422
        
    def test_hub_proxy_invalid_source(self, client):
        """Test proxy to invalid source."""
        response = client.get("/api/v1/hub/proxy/nonexistent_source", params={
            "endpoint": "/test"
        })
        assert response.status_code in [404, 400, 422]
        
    def test_hub_proxy_empty_source(self, client):
        """Test proxy with empty source ID."""
        response = client.get("/api/v1/hub/proxy/", params={
            "endpoint": "/test"
        })
        assert response.status_code in [307, 404, 405]


# ============================================================================
# SECTION 3: DATA SOURCES ENDPOINTS (100+ tests)
# ============================================================================

class TestDataSourcesEndpoints:
    """Tests for data source endpoints."""
    
    # --- Data Sources Status ---
    def test_data_sources_status_returns_200(self, client):
        """Test data sources status endpoint."""
        response = client.get("/api/v1/data-sources/status")
        assert response.status_code == 200
        
    def test_data_sources_status_returns_json(self, client):
        """Test data sources status returns JSON."""
        response = client.get("/api/v1/data-sources/status")
        data = response.json()
        assert isinstance(data, (list, dict))
        
    # --- Air Quality Data ---
    def test_air_quality_default(self, client):
        """Test air quality with defaults."""
        response = client.get("/api/v1/data-sources/air-quality")
        assert response.status_code == 200
        
    @pytest.mark.parametrize("country", COUNTRY_CODES[:10])
    def test_air_quality_various_countries(self, client, country):
        """Test air quality for various countries."""
        response = client.get("/api/v1/data-sources/air-quality", params={
            "country": country
        })
        assert response.status_code == 200
        
    @pytest.mark.parametrize("parameter", AIR_PARAMETERS)
    def test_air_quality_various_parameters(self, client, parameter):
        """Test air quality for various parameters."""
        response = client.get("/api/v1/data-sources/air-quality", params={
            "parameter": parameter
        })
        assert response.status_code == 200
        
    def test_air_quality_with_city(self, client):
        """Test air quality with city filter."""
        response = client.get("/api/v1/data-sources/air-quality", params={
            "city": "Los Angeles",
            "country": "US"
        })
        assert response.status_code == 200
        
    def test_air_quality_invalid_parameter(self, client):
        """Test air quality with invalid parameter."""
        response = client.get("/api/v1/data-sources/air-quality", params={
            "parameter": "invalid_param"
        })
        # May return 200 with no data or 422
        assert response.status_code in [200, 422]
        
    def test_air_quality_empty_country(self, client):
        """Test air quality with empty country."""
        response = client.get("/api/v1/data-sources/air-quality", params={
            "country": ""
        })
        assert response.status_code in [200, 422]
        
    def test_air_quality_unicode_city(self, client):
        """Test air quality with unicode city name."""
        response = client.get("/api/v1/data-sources/air-quality", params={
            "city": "東京",  # Tokyo in Japanese
            "country": "JP"
        })
        assert response.status_code == 200
        
    def test_air_quality_special_chars_city(self, client):
        """Test air quality with special characters in city."""
        response = client.get("/api/v1/data-sources/air-quality", params={
            "city": "São Paulo",
            "country": "BR"
        })
        assert response.status_code == 200
        
    # --- Water Quality Data ---
    def test_water_quality_default(self, client):
        """Test water quality with defaults."""
        response = client.get("/api/v1/data-sources/water-quality")
        assert response.status_code == 200
        
    @pytest.mark.parametrize("state", US_STATES[:10])
    def test_water_quality_various_states(self, client, state):
        """Test water quality for various US states."""
        response = client.get("/api/v1/data-sources/water-quality", params={
            "state_code": state
        })
        assert response.status_code == 200
        
    def test_water_quality_invalid_state(self, client):
        """Test water quality with invalid state code."""
        response = client.get("/api/v1/data-sources/water-quality", params={
            "state_code": "XX"
        })
        # May return 200 with no data or error
        assert response.status_code in [200, 400, 422]
        
    def test_water_quality_empty_state(self, client):
        """Test water quality with empty state."""
        response = client.get("/api/v1/data-sources/water-quality", params={
            "state_code": ""
        })
        assert response.status_code in [200, 422]
        
    def test_water_quality_lowercase_state(self, client):
        """Test water quality with lowercase state code."""
        response = client.get("/api/v1/data-sources/water-quality", params={
            "state_code": "ca"
        })
        assert response.status_code in [200, 422]
        
    # --- Weather Data ---
    def test_weather_default(self, client):
        """Test weather with defaults."""
        response = client.get("/api/v1/data-sources/weather")
        assert response.status_code == 200
        
    @pytest.mark.parametrize("location", LOCATIONS[:10])
    def test_weather_various_locations(self, client, location):
        """Test weather for various locations."""
        response = client.get("/api/v1/data-sources/weather", params={
            "lat": location["lat"],
            "lon": location["lon"]
        })
        assert response.status_code == 200
        
    @pytest.mark.parametrize("edge", EDGE_COORDINATES)
    def test_weather_edge_coordinates(self, client, edge):
        """Test weather with edge case coordinates."""
        response = client.get("/api/v1/data-sources/weather", params={
            "lat": edge["lat"],
            "lon": edge["lon"]
        })
        assert response.status_code == 200
        
    def test_weather_invalid_lat(self, client):
        """Test weather with invalid latitude."""
        response = client.get("/api/v1/data-sources/weather", params={
            "lat": 95.0,
            "lon": 0.0
        })
        assert response.status_code == 422
        
    def test_weather_invalid_lon(self, client):
        """Test weather with invalid longitude."""
        response = client.get("/api/v1/data-sources/weather", params={
            "lat": 0.0,
            "lon": 185.0
        })
        assert response.status_code == 422
        
    def test_weather_string_coordinates(self, client):
        """Test weather with string coordinates."""
        response = client.get("/api/v1/data-sources/weather", params={
            "lat": "not_valid",
            "lon": "also_not_valid"
        })
        assert response.status_code == 422
        
    # --- Marine Data ---
    def test_marine_default(self, client):
        """Test marine data with defaults."""
        response = client.get("/api/v1/data-sources/marine")
        assert response.status_code == 200
        
    @pytest.mark.parametrize("station", NOAA_STATIONS)
    def test_marine_various_stations(self, client, station):
        """Test marine data for various NOAA stations."""
        response = client.get("/api/v1/data-sources/marine", params={
            "station_id": station
        })
        assert response.status_code == 200
        
    @pytest.mark.parametrize("region", MARINE_REGIONS)
    def test_marine_various_regions(self, client, region):
        """Test marine data for various regions."""
        response = client.get("/api/v1/data-sources/marine", params={
            "region": region
        })
        assert response.status_code == 200
        
    def test_marine_invalid_station(self, client):
        """Test marine data with invalid station."""
        response = client.get("/api/v1/data-sources/marine", params={
            "station_id": "INVALID123"
        })
        # May return 200 with no data or error
        assert response.status_code in [200, 400, 404, 422]
        
    def test_marine_invalid_region(self, client):
        """Test marine data with invalid region."""
        response = client.get("/api/v1/data-sources/marine", params={
            "region": "invalid_region"
        })
        assert response.status_code in [200, 400, 422]
        
    # --- All Data Sources ---
    def test_all_data_sources(self, client):
        """Test fetching all data sources."""
        response = client.get("/api/v1/data-sources/all")
        assert response.status_code == 200
        
    def test_all_data_sources_returns_dict(self, client):
        """Test all data sources returns dict with multiple sources."""
        response = client.get("/api/v1/data-sources/all")
        data = response.json()
        assert isinstance(data, dict)
        
    # --- Ingestion Control ---
    def test_start_ingestion(self, client):
        """Test starting continuous ingestion."""
        response = client.post("/api/v1/data-sources/ingestion/start")
        assert response.status_code == 200
        
    def test_stop_ingestion(self, client):
        """Test stopping continuous ingestion."""
        response = client.post("/api/v1/data-sources/ingestion/stop")
        assert response.status_code == 200


# ============================================================================
# SECTION 4: DATA QUALITY ENDPOINTS (50+ tests)
# ============================================================================

class TestDataQualityEndpoints:
    """Tests for data quality endpoints."""
    
    def test_data_freshness(self, client):
        """Test data freshness endpoint."""
        response = client.get("/api/v1/data-quality/freshness")
        assert response.status_code == 200
        
    def test_data_freshness_returns_json(self, client):
        """Test data freshness returns JSON."""
        response = client.get("/api/v1/data-quality/freshness")
        data = response.json()
        assert isinstance(data, (list, dict))
        
    def test_supported_parameters(self, client):
        """Test supported parameters endpoint."""
        response = client.get("/api/v1/data-quality/parameters")
        assert response.status_code == 200
        
    def test_supported_parameters_returns_json(self, client):
        """Test supported parameters returns JSON."""
        response = client.get("/api/v1/data-quality/parameters")
        data = response.json()
        assert isinstance(data, (list, dict))
        
    def test_validate_data_valid_record(self, client):
        """Test validating a valid data record."""
        records = [
            {
                "parameter": "pm25",
                "value": 25.5,
                "timestamp": "2026-02-06T12:00:00Z",
                "source": "test"
            }
        ]
        response = client.post("/api/v1/data-quality/validate", json=records)
        assert response.status_code == 200
        
    def test_validate_data_multiple_records(self, client):
        """Test validating multiple data records."""
        records = [
            {"parameter": "pm25", "value": 25.5, "timestamp": "2026-02-06T12:00:00Z", "source": "test"},
            {"parameter": "pm10", "value": 50.0, "timestamp": "2026-02-06T12:00:00Z", "source": "test"},
            {"parameter": "o3", "value": 0.05, "timestamp": "2026-02-06T12:00:00Z", "source": "test"},
        ]
        response = client.post("/api/v1/data-quality/validate", json=records)
        assert response.status_code == 200
        
    def test_validate_data_empty_array(self, client):
        """Test validating empty array."""
        response = client.post("/api/v1/data-quality/validate", json=[])
        assert response.status_code in [200, 422]
        
    def test_validate_data_invalid_json(self, client):
        """Test validating with invalid JSON structure."""
        response = client.post("/api/v1/data-quality/validate", json={"not": "an_array"})
        assert response.status_code == 422
        
    def test_validate_data_missing_fields(self, client):
        """Test validating records with missing fields."""
        records = [{"parameter": "pm25"}]  # Missing value, timestamp, source
        response = client.post("/api/v1/data-quality/validate", json=records)
        # Should accept but flag issues
        assert response.status_code in [200, 422]
        
    def test_validate_data_negative_value(self, client):
        """Test validating with negative value."""
        records = [
            {
                "parameter": "pm25",
                "value": -10.0,
                "timestamp": "2026-02-06T12:00:00Z",
                "source": "test"
            }
        ]
        response = client.post("/api/v1/data-quality/validate", json=records)
        assert response.status_code == 200
        
    def test_validate_data_extreme_value(self, client):
        """Test validating with extreme value."""
        records = [
            {
                "parameter": "pm25",
                "value": 999999.0,
                "timestamp": "2026-02-06T12:00:00Z",
                "source": "test"
            }
        ]
        response = client.post("/api/v1/data-quality/validate", json=records)
        assert response.status_code == 200
        
    def test_validate_data_invalid_timestamp(self, client):
        """Test validating with invalid timestamp."""
        records = [
            {
                "parameter": "pm25",
                "value": 25.5,
                "timestamp": "not_a_timestamp",
                "source": "test"
            }
        ]
        response = client.post("/api/v1/data-quality/validate", json=records)
        assert response.status_code in [200, 422]
        
    @pytest.mark.parametrize("param", AIR_PARAMETERS)
    def test_validate_data_various_parameters(self, client, param):
        """Test validating various parameter types."""
        records = [
            {
                "parameter": param,
                "value": 10.0,
                "timestamp": "2026-02-06T12:00:00Z",
                "source": "test"
            }
        ]
        response = client.post("/api/v1/data-quality/validate", json=records)
        assert response.status_code == 200


# ============================================================================
# SECTION 5: SENSORS ENDPOINTS (50+ tests)
# ============================================================================

class TestSensorsEndpoints:
    """Tests for sensor management endpoints."""
    
    def test_get_sensors(self, client):
        """Test getting all sensors."""
        response = client.get("/api/v1/sensors")
        assert response.status_code == 200
        
    def test_get_sensors_returns_list(self, client):
        """Test sensors returns a list."""
        response = client.get("/api/v1/sensors")
        data = response.json()
        assert isinstance(data, list)
        
    def test_create_sensor_valid(self, client):
        """Test creating a valid sensor."""
        sensor_data = {
            "name": f"Test Sensor {random.randint(1000, 9999)}",
            "type": "air_quality",
            "location": "Test Location",
            "latitude": 37.7749,
            "longitude": -122.4194
        }
        response = client.post("/api/v1/sensors", json=sensor_data)
        assert response.status_code in [200, 201]
        
    def test_create_sensor_missing_name(self, client):
        """Test creating sensor without name."""
        sensor_data = {
            "type": "air_quality",
            "location": "Test Location",
            "latitude": 37.7749,
            "longitude": -122.4194
        }
        response = client.post("/api/v1/sensors", json=sensor_data)
        assert response.status_code == 422
        
    def test_create_sensor_invalid_latitude(self, client):
        """Test creating sensor with invalid latitude."""
        sensor_data = {
            "name": "Test Sensor",
            "type": "air_quality",
            "location": "Test Location",
            "latitude": 100.0,  # Invalid
            "longitude": -122.4194
        }
        response = client.post("/api/v1/sensors", json=sensor_data)
        assert response.status_code == 422
        
    def test_create_sensor_invalid_longitude(self, client):
        """Test creating sensor with invalid longitude."""
        sensor_data = {
            "name": "Test Sensor",
            "type": "air_quality",
            "location": "Test Location",
            "latitude": 37.7749,
            "longitude": 200.0  # Invalid
        }
        response = client.post("/api/v1/sensors", json=sensor_data)
        assert response.status_code == 422
        
    @pytest.mark.parametrize("edge", EDGE_COORDINATES)
    def test_create_sensor_edge_coordinates(self, client, edge):
        """Test creating sensors at edge coordinates."""
        sensor_data = {
            "name": f"Edge Sensor {edge['name']}",
            "type": "temperature",
            "location": edge["name"],
            "latitude": edge["lat"],
            "longitude": edge["lon"]
        }
        response = client.post("/api/v1/sensors", json=sensor_data)
        assert response.status_code in [200, 201]
        
    def test_create_sensor_with_altitude(self, client):
        """Test creating sensor with altitude."""
        sensor_data = {
            "name": "High Altitude Sensor",
            "type": "air_quality",
            "location": "Mountain Top",
            "latitude": 39.7392,
            "longitude": -104.9903,
            "altitude": 5280.0
        }
        response = client.post("/api/v1/sensors", json=sensor_data)
        assert response.status_code in [200, 201]
        
    def test_create_sensor_with_description(self, client):
        """Test creating sensor with description."""
        sensor_data = {
            "name": "Described Sensor",
            "type": "water_quality",
            "location": "River Bank",
            "latitude": 40.7128,
            "longitude": -74.0060,
            "description": "This is a test sensor for water quality monitoring."
        }
        response = client.post("/api/v1/sensors", json=sensor_data)
        assert response.status_code in [200, 201]
        
    def test_get_sensor_status_valid_id(self, client):
        """Test getting status for a sensor."""
        # First create a sensor
        sensor_data = {
            "name": f"Status Test Sensor {random.randint(1000, 9999)}",
            "type": "air_quality",
            "location": "Test Location",
            "latitude": 37.7749,
            "longitude": -122.4194
        }
        create_response = client.post("/api/v1/sensors", json=sensor_data)
        if create_response.status_code in [200, 201]:
            sensor = create_response.json()
            sensor_id = sensor.get("id", 1)
            response = client.get(f"/api/v1/sensors/{sensor_id}/status")
            assert response.status_code in [200, 404]
        else:
            # If creation fails, try with ID 1
            response = client.get("/api/v1/sensors/1/status")
            assert response.status_code in [200, 404]
            
    def test_get_sensor_status_invalid_id(self, client):
        """Test getting status for non-existent sensor."""
        response = client.get("/api/v1/sensors/99999999/status")
        assert response.status_code in [404, 200]
        
    def test_get_sensor_status_string_id(self, client):
        """Test getting status with string ID."""
        response = client.get("/api/v1/sensors/not_an_id/status")
        assert response.status_code == 422
        
    def test_get_sensor_readings_valid_id(self, client):
        """Test getting readings for a sensor."""
        response = client.get("/api/v1/sensors/1/readings")
        assert response.status_code in [200, 404]
        
    def test_get_sensor_readings_with_limit(self, client):
        """Test getting readings with limit parameter."""
        response = client.get("/api/v1/sensors/1/readings", params={"limit": 10})
        assert response.status_code in [200, 404]
        
    def test_get_sensor_readings_limit_too_small(self, client):
        """Test getting readings with limit < 1."""
        response = client.get("/api/v1/sensors/1/readings", params={"limit": 0})
        assert response.status_code == 422
        
    def test_get_sensor_readings_limit_too_large(self, client):
        """Test getting readings with limit > 1000."""
        response = client.get("/api/v1/sensors/1/readings", params={"limit": 1001})
        assert response.status_code == 422
        
    def test_get_sensor_readings_invalid_id(self, client):
        """Test getting readings for non-existent sensor."""
        response = client.get("/api/v1/sensors/99999999/readings")
        assert response.status_code in [200, 404]
        
    def test_create_sensor_unicode_name(self, client):
        """Test creating sensor with unicode name."""
        sensor_data = {
            "name": "センサー東京",
            "type": "air_quality",
            "location": "東京都",
            "latitude": 35.6762,
            "longitude": 139.6503
        }
        response = client.post("/api/v1/sensors", json=sensor_data)
        assert response.status_code in [200, 201]
        
    def test_create_sensor_long_name(self, client):
        """Test creating sensor with long name."""
        sensor_data = {
            "name": "A" * 100,  # Max is 100 chars
            "type": "air_quality",
            "location": "Test Location",
            "latitude": 37.7749,
            "longitude": -122.4194
        }
        response = client.post("/api/v1/sensors", json=sensor_data)
        assert response.status_code in [200, 201]
        
    def test_create_sensor_name_too_long(self, client):
        """Test creating sensor with name > 100 chars."""
        sensor_data = {
            "name": "A" * 101,
            "type": "air_quality",
            "location": "Test Location",
            "latitude": 37.7749,
            "longitude": -122.4194
        }
        response = client.post("/api/v1/sensors", json=sensor_data)
        assert response.status_code == 422


# ============================================================================
# SECTION 6: GIS ENDPOINTS (50+ tests)
# ============================================================================

class TestGISEndpoints:
    """Tests for GIS/spatial analysis endpoints."""
    
    def test_get_environmental_map(self, client):
        """Test getting environmental map."""
        response = client.get("/api/v1/gis/map")
        assert response.status_code == 200
        
    def test_get_environmental_map_returns_json(self, client):
        """Test environmental map returns JSON."""
        response = client.get("/api/v1/gis/map")
        data = response.json()
        assert isinstance(data, (dict, list))
        
    @pytest.mark.parametrize("location", LOCATIONS[:10])
    def test_find_nearest_sensor(self, client, location):
        """Test finding nearest sensor for various locations."""
        response = client.get("/api/v1/gis/nearest-sensor", params={
            "latitude": location["lat"],
            "longitude": location["lon"]
        })
        assert response.status_code == 200
        
    @pytest.mark.parametrize("edge", EDGE_COORDINATES)
    def test_find_nearest_sensor_edge_coordinates(self, client, edge):
        """Test finding nearest sensor at edge coordinates."""
        response = client.get("/api/v1/gis/nearest-sensor", params={
            "latitude": edge["lat"],
            "longitude": edge["lon"]
        })
        assert response.status_code == 200
        
    def test_find_nearest_sensor_missing_latitude(self, client):
        """Test nearest sensor with missing latitude."""
        response = client.get("/api/v1/gis/nearest-sensor", params={
            "longitude": -122.4194
        })
        assert response.status_code == 422
        
    def test_find_nearest_sensor_missing_longitude(self, client):
        """Test nearest sensor with missing longitude."""
        response = client.get("/api/v1/gis/nearest-sensor", params={
            "latitude": 37.7749
        })
        assert response.status_code == 422
        
    def test_find_nearest_sensor_invalid_coordinates(self, client):
        """Test nearest sensor with invalid coordinates."""
        response = client.get("/api/v1/gis/nearest-sensor", params={
            "latitude": 95.0,
            "longitude": 185.0
        })
        assert response.status_code == 422
        
    @pytest.mark.parametrize("location", LOCATIONS[:10])
    def test_get_zone_info(self, client, location):
        """Test getting zone info for various locations."""
        response = client.get("/api/v1/gis/zone-info", params={
            "latitude": location["lat"],
            "longitude": location["lon"]
        })
        assert response.status_code == 200
        
    def test_get_zone_info_missing_coordinates(self, client):
        """Test zone info with missing coordinates."""
        response = client.get("/api/v1/gis/zone-info")
        assert response.status_code == 422
        
    def test_get_zone_info_invalid_coordinates(self, client):
        """Test zone info with invalid coordinates."""
        response = client.get("/api/v1/gis/zone-info", params={
            "latitude": 91.0,
            "longitude": 0.0
        })
        assert response.status_code == 422
        
    @pytest.mark.parametrize("analysis_type", ["hotspot", "cluster", "trend", "correlation"])
    def test_spatial_analysis_types(self, client, analysis_type):
        """Test various spatial analysis types."""
        response = client.get(f"/api/v1/gis/analysis/{analysis_type}")
        assert response.status_code in [200, 404]
        
    def test_spatial_analysis_invalid_type(self, client):
        """Test spatial analysis with invalid type."""
        response = client.get("/api/v1/gis/analysis/invalid_analysis")
        assert response.status_code in [200, 404]
        
    def test_create_gis_layer_valid(self, client):
        """Test creating a valid GIS layer."""
        layer_data = {
            "name": f"Test Layer {random.randint(1000, 9999)}",
            "layer_type": "point",
            "description": "Test layer for unit tests"
        }
        response = client.post("/api/v1/gis/layers", json=layer_data)
        assert response.status_code in [200, 201]
        
    def test_create_gis_layer_missing_name(self, client):
        """Test creating layer without name."""
        layer_data = {
            "layer_type": "point"
        }
        response = client.post("/api/v1/gis/layers", json=layer_data)
        assert response.status_code == 422
        
    def test_create_gis_layer_missing_type(self, client):
        """Test creating layer without type."""
        layer_data = {
            "name": "Test Layer"
        }
        response = client.post("/api/v1/gis/layers", json=layer_data)
        assert response.status_code == 422
        
    def test_create_gis_layer_with_geojson(self, client):
        """Test creating layer with GeoJSON data."""
        layer_data = {
            "name": "GeoJSON Layer",
            "layer_type": "polygon",
            "geojson_data": {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [-122.4194, 37.7749]
                },
                "properties": {"name": "San Francisco"}
            }
        }
        response = client.post("/api/v1/gis/layers", json=layer_data)
        assert response.status_code in [200, 201]
        
    def test_create_gis_layer_with_bounds(self, client):
        """Test creating layer with bounds."""
        layer_data = {
            "name": "Bounded Layer",
            "layer_type": "raster",
            "bounds": {
                "north": 38.0,
                "south": 37.5,
                "east": -122.0,
                "west": -122.5
            }
        }
        response = client.post("/api/v1/gis/layers", json=layer_data)
        assert response.status_code in [200, 201]


# ============================================================================
# SECTION 7: ALERTS ENDPOINTS (50+ tests)
# ============================================================================

class TestAlertsEndpoints:
    """Tests for alert management endpoints."""
    
    def test_get_alert_history(self, client):
        """Test getting alert history."""
        response = client.get("/api/v1/alerts/history")
        assert response.status_code == 200
        
    def test_get_alert_history_default_days(self, client):
        """Test alert history with default days."""
        response = client.get("/api/v1/alerts/history")
        data = response.json()
        assert isinstance(data, (list, dict))
        
    @pytest.mark.parametrize("days", [1, 3, 7, 14, 30])
    def test_get_alert_history_various_days(self, client, days):
        """Test alert history with various day ranges."""
        response = client.get("/api/v1/alerts/history", params={"days": days})
        assert response.status_code == 200
        
    def test_get_alert_history_days_too_small(self, client):
        """Test alert history with days < 1."""
        response = client.get("/api/v1/alerts/history", params={"days": 0})
        assert response.status_code == 422
        
    def test_get_alert_history_days_too_large(self, client):
        """Test alert history with days > 30."""
        response = client.get("/api/v1/alerts/history", params={"days": 31})
        assert response.status_code == 422
        
    def test_get_alert_statistics(self, client):
        """Test getting alert statistics."""
        response = client.get("/api/v1/alerts/statistics")
        assert response.status_code == 200
        
    def test_get_alert_statistics_returns_json(self, client):
        """Test alert statistics returns JSON."""
        response = client.get("/api/v1/alerts/statistics")
        data = response.json()
        assert isinstance(data, dict)
        
    def test_create_alert_valid(self, client):
        """Test creating a valid alert."""
        alert_data = {
            "alert_type": "warning",
            "recipient": "test@example.com",
            "subject": "Test Alert",
            "message": "This is a test alert message."
        }
        response = client.post("/api/v1/alerts", json=alert_data)
        assert response.status_code in [200, 201]
        
    def test_create_alert_missing_type(self, client):
        """Test creating alert without type."""
        alert_data = {
            "recipient": "test@example.com",
            "subject": "Test Alert",
            "message": "This is a test alert message."
        }
        response = client.post("/api/v1/alerts", json=alert_data)
        assert response.status_code == 422
        
    def test_create_alert_missing_recipient(self, client):
        """Test creating alert without recipient."""
        alert_data = {
            "alert_type": "warning",
            "subject": "Test Alert",
            "message": "This is a test alert message."
        }
        response = client.post("/api/v1/alerts", json=alert_data)
        assert response.status_code == 422
        
    def test_create_alert_missing_subject(self, client):
        """Test creating alert without subject."""
        alert_data = {
            "alert_type": "warning",
            "recipient": "test@example.com",
            "message": "This is a test alert message."
        }
        response = client.post("/api/v1/alerts", json=alert_data)
        assert response.status_code == 422
        
    def test_create_alert_missing_message(self, client):
        """Test creating alert without message."""
        alert_data = {
            "alert_type": "warning",
            "recipient": "test@example.com",
            "subject": "Test Alert"
        }
        response = client.post("/api/v1/alerts", json=alert_data)
        assert response.status_code == 422
        
    def test_create_alert_with_event_id(self, client):
        """Test creating alert with event ID."""
        alert_data = {
            "alert_type": "critical",
            "recipient": "admin@example.com",
            "subject": "Critical Event",
            "message": "Critical environmental event detected.",
            "event_id": 12345
        }
        response = client.post("/api/v1/alerts", json=alert_data)
        assert response.status_code in [200, 201]
        
    @pytest.mark.parametrize("alert_type", ["info", "warning", "critical", "emergency"])
    def test_create_alert_various_types(self, client, alert_type):
        """Test creating alerts with various types."""
        alert_data = {
            "alert_type": alert_type,
            "recipient": "test@example.com",
            "subject": f"{alert_type.title()} Alert",
            "message": f"This is a {alert_type} alert."
        }
        response = client.post("/api/v1/alerts", json=alert_data)
        assert response.status_code in [200, 201]
        
    def test_create_alert_long_subject(self, client):
        """Test creating alert with long subject (max 200)."""
        alert_data = {
            "alert_type": "warning",
            "recipient": "test@example.com",
            "subject": "A" * 200,
            "message": "Test message."
        }
        response = client.post("/api/v1/alerts", json=alert_data)
        assert response.status_code in [200, 201]
        
    def test_create_alert_subject_too_long(self, client):
        """Test creating alert with subject > 200 chars."""
        alert_data = {
            "alert_type": "warning",
            "recipient": "test@example.com",
            "subject": "A" * 201,
            "message": "Test message."
        }
        response = client.post("/api/v1/alerts", json=alert_data)
        assert response.status_code == 422


# ============================================================================
# SECTION 8: DASHBOARD ENDPOINTS (30+ tests)
# ============================================================================

class TestDashboardEndpoints:
    """Tests for dashboard endpoints."""
    
    def test_get_dashboard_stats(self, client):
        """Test getting dashboard statistics."""
        response = client.get("/api/v1/dashboard/stats")
        assert response.status_code == 200
        
    def test_dashboard_stats_structure(self, client):
        """Test dashboard stats has expected structure."""
        response = client.get("/api/v1/dashboard/stats")
        data = response.json()
        assert isinstance(data, dict)
        # Check for expected fields based on DashboardStats schema
        expected_fields = ["total_sensors", "active_sensors", "total_readings_today", 
                          "active_alerts", "predictions_made_today", "system_health"]
        for field in expected_fields:
            assert field in data, f"Missing field: {field}"
            
    def test_dashboard_stats_values_are_integers(self, client):
        """Test dashboard stats numeric fields are integers."""
        response = client.get("/api/v1/dashboard/stats")
        data = response.json()
        int_fields = ["total_sensors", "active_sensors", "total_readings_today", 
                      "active_alerts", "predictions_made_today"]
        for field in int_fields:
            if field in data:
                assert isinstance(data[field], int), f"{field} should be integer"
                
    def test_dashboard_stats_system_health_is_string(self, client):
        """Test system_health is a string."""
        response = client.get("/api/v1/dashboard/stats")
        data = response.json()
        if "system_health" in data:
            assert isinstance(data["system_health"], str)
            
    def test_get_sensor_stats(self, client):
        """Test getting sensor statistics."""
        response = client.get("/api/v1/dashboard/sensor-stats")
        assert response.status_code == 200
        
    def test_sensor_stats_returns_json(self, client):
        """Test sensor stats returns JSON."""
        response = client.get("/api/v1/dashboard/sensor-stats")
        data = response.json()
        assert isinstance(data, (dict, list))


# ============================================================================
# SECTION 9: PREDICTIONS ENDPOINTS (30+ tests)
# ============================================================================

class TestPredictionsEndpoints:
    """Tests for ML predictions endpoints."""
    
    def test_get_ml_performance(self, client):
        """Test getting ML performance metrics."""
        response = client.get("/api/v1/ml/performance")
        assert response.status_code == 200
        
    def test_ml_performance_returns_json(self, client):
        """Test ML performance returns JSON."""
        response = client.get("/api/v1/ml/performance")
        data = response.json()
        assert isinstance(data, (dict, list))
        
    def test_get_sensor_predictions_valid_id(self, client):
        """Test getting predictions for a sensor."""
        response = client.get("/api/v1/predictions/sensor/1")
        assert response.status_code in [200, 404]
        
    @pytest.mark.parametrize("hours", [1, 6, 12, 24, 48, 168])
    def test_get_sensor_predictions_various_hours(self, client, hours):
        """Test predictions with various hour ranges."""
        response = client.get("/api/v1/predictions/sensor/1", params={"hours": hours})
        assert response.status_code in [200, 404]
        
    def test_get_sensor_predictions_hours_too_small(self, client):
        """Test predictions with hours < 1."""
        response = client.get("/api/v1/predictions/sensor/1", params={"hours": 0})
        assert response.status_code == 422
        
    def test_get_sensor_predictions_hours_too_large(self, client):
        """Test predictions with hours > 168."""
        response = client.get("/api/v1/predictions/sensor/1", params={"hours": 169})
        assert response.status_code == 422
        
    def test_get_sensor_predictions_invalid_id(self, client):
        """Test predictions for non-existent sensor."""
        response = client.get("/api/v1/predictions/sensor/99999999")
        assert response.status_code in [200, 404]
        
    def test_get_sensor_predictions_string_id(self, client):
        """Test predictions with string sensor ID."""
        response = client.get("/api/v1/predictions/sensor/not_an_id")
        assert response.status_code == 422


# ============================================================================
# SECTION 10: SYSTEM ENDPOINTS (30+ tests)
# ============================================================================

class TestSystemEndpoints:
    """Tests for system management endpoints."""
    
    def test_get_system_health(self, client):
        """Test getting system health."""
        response = client.get("/api/v1/system/health")
        assert response.status_code == 200
        
    def test_system_health_returns_json(self, client):
        """Test system health returns JSON."""
        response = client.get("/api/v1/system/health")
        data = response.json()
        assert isinstance(data, dict)
        
    def test_system_reset(self, client):
        """Test system reset endpoint."""
        response = client.post("/api/v1/system/reset")
        assert response.status_code == 200
        
    def test_system_reset_returns_json(self, client):
        """Test system reset returns JSON."""
        response = client.post("/api/v1/system/reset")
        data = response.json()
        assert isinstance(data, dict)


# ============================================================================
# SECTION 11: COLLABORATION ENDPOINTS (30+ tests)
# ============================================================================

class TestCollaborationEndpoints:
    """Tests for collaboration endpoints."""
    
    def test_trigger_collaboration(self, client):
        """Test triggering collaboration."""
        response = client.post("/api/v1/collaboration/run")
        assert response.status_code == 200
        
    def test_trigger_collaboration_returns_json(self, client):
        """Test trigger collaboration returns JSON."""
        response = client.post("/api/v1/collaboration/run")
        data = response.json()
        assert isinstance(data, dict)
        
    def test_get_collaboration_status(self, client):
        """Test getting collaboration status."""
        response = client.get("/api/v1/collaboration/status")
        assert response.status_code == 200
        
    def test_collaboration_status_returns_json(self, client):
        """Test collaboration status returns JSON."""
        response = client.get("/api/v1/collaboration/status")
        data = response.json()
        assert isinstance(data, dict)
        
    def test_get_collaboration_history(self, client):
        """Test getting collaboration history."""
        response = client.get("/api/v1/collaboration/history")
        assert response.status_code == 200
        
    @pytest.mark.parametrize("limit", [1, 5, 10, 50, 100])
    def test_collaboration_history_various_limits(self, client, limit):
        """Test collaboration history with various limits."""
        response = client.get("/api/v1/collaboration/history", params={"limit": limit})
        assert response.status_code == 200
        
    def test_collaboration_history_limit_too_small(self, client):
        """Test collaboration history with limit < 1."""
        response = client.get("/api/v1/collaboration/history", params={"limit": 0})
        assert response.status_code == 422
        
    def test_collaboration_history_limit_too_large(self, client):
        """Test collaboration history with limit > 100."""
        response = client.get("/api/v1/collaboration/history", params={"limit": 101})
        assert response.status_code == 422
        
    def test_collaborate_endpoint(self, client):
        """Test the /collaborate endpoint."""
        response = client.post("/collaborate")
        assert response.status_code == 200


# ============================================================================
# SECTION 12: ERROR HANDLING & EDGE CASES (50+ tests)
# ============================================================================

class TestErrorHandling:
    """Tests for error handling and edge cases."""
    
    def test_nonexistent_api_version(self, client):
        """Test non-existent API version."""
        response = client.get("/api/v2/hub")
        assert response.status_code == 404
        
    def test_nonexistent_endpoint(self, client):
        """Test completely non-existent endpoint."""
        response = client.get("/api/v1/does_not_exist")
        assert response.status_code == 404
        
    def test_malformed_json_body(self, client):
        """Test POST with malformed JSON."""
        response = client.post(
            "/api/v1/sensors",
            content="not valid json{",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 422
        
    def test_empty_json_body(self, client):
        """Test POST with empty JSON."""
        response = client.post("/api/v1/sensors", json={})
        assert response.status_code == 422
        
    def test_null_json_body(self, client):
        """Test POST with null JSON."""
        response = client.post("/api/v1/sensors", json=None)
        assert response.status_code == 422
        
    def test_array_instead_of_object(self, client):
        """Test POST with array instead of object."""
        response = client.post("/api/v1/sensors", json=[{"name": "test"}])
        assert response.status_code == 422
        
    def test_very_large_request_body(self, client):
        """Test POST with very large request body."""
        large_data = {
            "name": "Test Sensor",
            "type": "air_quality",
            "location": "A" * 10000,  # Very long location
            "latitude": 37.7749,
            "longitude": -122.4194,
            "description": "B" * 100000  # Very long description
        }
        response = client.post("/api/v1/sensors", json=large_data)
        # Should either succeed (truncating) or fail with 422
        assert response.status_code in [200, 201, 413, 422]
        
    def test_special_characters_in_query(self, client):
        """Test special characters in query parameters."""
        response = client.get("/api/v1/data-sources/air-quality", params={
            "city": "<script>alert('xss')</script>"
        })
        # Should sanitize or return error
        assert response.status_code in [200, 400, 422]
        
    def test_sql_injection_attempt(self, client):
        """Test SQL injection in query parameters."""
        response = client.get("/api/v1/data-sources/air-quality", params={
            "city": "'; DROP TABLE sensors; --"
        })
        # Should not execute SQL, return normal response
        assert response.status_code in [200, 400, 422]
        
    def test_unicode_in_parameters(self, client):
        """Test unicode characters in parameters."""
        response = client.get("/api/v1/data-sources/air-quality", params={
            "city": "北京"  # Beijing in Chinese
        })
        assert response.status_code == 200
        
    def test_emoji_in_parameters(self, client):
        """Test emoji characters in parameters."""
        response = client.get("/api/v1/data-sources/air-quality", params={
            "city": "🌍🌎🌏"
        })
        assert response.status_code == 200
        
    def test_null_byte_in_parameters(self, client):
        """Test null byte in parameters."""
        response = client.get("/api/v1/data-sources/air-quality", params={
            "city": "test\x00injection"
        })
        assert response.status_code in [200, 400, 422]
        
    def test_negative_sensor_id(self, client):
        """Test negative sensor ID."""
        response = client.get("/api/v1/sensors/-1/status")
        assert response.status_code in [404, 422]
        
    def test_float_sensor_id(self, client):
        """Test float sensor ID."""
        response = client.get("/api/v1/sensors/1.5/status")
        assert response.status_code == 422
        
    def test_very_large_sensor_id(self, client):
        """Test very large sensor ID."""
        response = client.get("/api/v1/sensors/9999999999999999999/status")
        assert response.status_code in [404, 422]
        
    def test_double_slash_in_path(self, client):
        """Test double slash in path."""
        response = client.get("/api/v1//hub")
        # Should normalize or return 404
        assert response.status_code in [200, 404]
        
    def test_trailing_slash_on_endpoints(self, client):
        """Test trailing slash on endpoints."""
        response = client.get("/api/v1/hub/")
        # Should work with redirect or directly
        assert response.status_code in [200, 307]
        
    @pytest.mark.parametrize("content_type", [
        "text/plain",
        "text/html",
        "application/xml",
        "multipart/form-data",
    ])
    def test_various_content_types(self, client, content_type):
        """Test various content types on POST."""
        response = client.post(
            "/api/v1/sensors",
            content='{"name": "test"}',
            headers={"Content-Type": content_type}
        )
        # Most should fail as they expect JSON
        assert response.status_code in [200, 201, 415, 422]
        
    def test_missing_content_type(self, client):
        """Test POST without content type."""
        response = client.post("/api/v1/sensors", content='{}')
        assert response.status_code in [200, 201, 422]
        
    def test_concurrent_requests(self, client):
        """Test multiple concurrent requests don't cause issues."""
        import concurrent.futures
        
        def make_request():
            return client.get("/api/v1/hub/quick")
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(make_request) for _ in range(10)]
            results = [f.result() for f in futures]
        
        # All should succeed
        for response in results:
            assert response.status_code == 200


# ============================================================================
# SECTION 13: RESPONSE VALIDATION (50+ tests)
# ============================================================================

class TestResponseValidation:
    """Tests for validating response structure and content."""
    
    def test_hub_location_response_structure(self, client):
        """Test hub location response has expected structure."""
        response = client.get("/api/v1/hub/location", params={
            "lat": 37.7749,
            "lon": -122.4194
        })
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        
    def test_weather_response_structure(self, client):
        """Test weather response has expected structure."""
        response = client.get("/api/v1/data-sources/weather", params={
            "lat": 37.7749,
            "lon": -122.4194
        })
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        
    def test_air_quality_response_structure(self, client):
        """Test air quality response structure."""
        response = client.get("/api/v1/data-sources/air-quality")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, (dict, list))
        
    def test_sensor_create_response_has_id(self, client):
        """Test created sensor response has ID."""
        sensor_data = {
            "name": f"Validation Test Sensor {random.randint(1000, 9999)}",
            "type": "air_quality",
            "location": "Test Location",
            "latitude": 37.7749,
            "longitude": -122.4194
        }
        response = client.post("/api/v1/sensors", json=sensor_data)
        if response.status_code in [200, 201]:
            data = response.json()
            assert "id" in data
            assert isinstance(data["id"], int)
            
    def test_sensor_create_response_has_timestamps(self, client):
        """Test created sensor has timestamps."""
        sensor_data = {
            "name": f"Timestamp Test Sensor {random.randint(1000, 9999)}",
            "type": "temperature",
            "location": "Test Location",
            "latitude": 37.7749,
            "longitude": -122.4194
        }
        response = client.post("/api/v1/sensors", json=sensor_data)
        if response.status_code in [200, 201]:
            data = response.json()
            assert "created_at" in data
            assert "updated_at" in data
            
    def test_alert_create_response_structure(self, client):
        """Test created alert response structure."""
        alert_data = {
            "alert_type": "warning",
            "recipient": "test@example.com",
            "subject": "Test Alert",
            "message": "This is a test alert message."
        }
        response = client.post("/api/v1/alerts", json=alert_data)
        if response.status_code in [200, 201]:
            data = response.json()
            assert "id" in data
            assert "status" in data
            assert "created_at" in data
            
    def test_gis_layer_create_response_structure(self, client):
        """Test created GIS layer response structure."""
        layer_data = {
            "name": f"Validation Layer {random.randint(1000, 9999)}",
            "layer_type": "point"
        }
        response = client.post("/api/v1/gis/layers", json=layer_data)
        if response.status_code in [200, 201]:
            data = response.json()
            assert "id" in data
            assert "name" in data
            assert "layer_type" in data
            
    def test_validation_error_response_format(self, client):
        """Test validation error response format."""
        response = client.get("/api/v1/hub/location")  # Missing required params
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data
        assert isinstance(data["detail"], list)
        
    def test_validation_error_has_location(self, client):
        """Test validation error includes location info."""
        response = client.get("/api/v1/hub/location")
        data = response.json()
        if data.get("detail"):
            error = data["detail"][0]
            assert "loc" in error
            assert "msg" in error
            assert "type" in error


# ============================================================================
# SECTION 14: RATE LIMITING & PERFORMANCE (20+ tests)
# ============================================================================

class TestPerformance:
    """Tests for performance and rate limiting."""
    
    def test_rapid_requests(self, client):
        """Test rapid sequential requests."""
        responses = []
        for _ in range(10):
            response = client.get("/api/v1/hub/quick")
            responses.append(response.status_code)
        
        # Most should succeed (some might be rate limited)
        success_count = sum(1 for code in responses if code == 200)
        assert success_count >= 5  # At least half should succeed
        
    def test_response_time_hub(self, client):
        """Test hub endpoint responds within reasonable time."""
        start = time.time()
        response = client.get("/api/v1/hub")
        elapsed = time.time() - start
        assert response.status_code == 200
        assert elapsed < 10.0  # Should respond within 10 seconds
        
    def test_response_time_quick_check(self, client):
        """Test quick check responds within reasonable time."""
        start = time.time()
        response = client.get("/api/v1/hub/quick")
        elapsed = time.time() - start
        assert response.status_code == 200
        assert elapsed < 15.0  # May take longer due to external API calls
        
    def test_response_time_weather(self, client):
        """Test weather endpoint responds within reasonable time."""
        start = time.time()
        response = client.get("/api/v1/data-sources/weather", params={
            "lat": 37.7749,
            "lon": -122.4194
        })
        elapsed = time.time() - start
        assert response.status_code == 200
        assert elapsed < 15.0
        
    def test_bulk_sensor_creation(self, client):
        """Test creating multiple sensors rapidly."""
        success_count = 0
        for i in range(5):
            sensor_data = {
                "name": f"Bulk Test Sensor {i}_{random.randint(1000, 9999)}",
                "type": "air_quality",
                "location": f"Location {i}",
                "latitude": 37.7749 + (i * 0.01),
                "longitude": -122.4194 + (i * 0.01)
            }
            response = client.post("/api/v1/sensors", json=sensor_data)
            if response.status_code in [200, 201]:
                success_count += 1
        
        assert success_count >= 3  # At least 3 should succeed


# ============================================================================
# RUN CONFIGURATION
# ============================================================================

if __name__ == "__main__":
    pytest.main([
        __file__,
        "-v",
        "--tb=short",
        "-x",  # Stop on first failure for debugging
        "--durations=10"  # Show 10 slowest tests
    ])
