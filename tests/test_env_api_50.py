"""
Comprehensive API Tests for Environmental Monitoring API
URL: https://env-monitor-api-758343025648.us-central1.run.app

50+ Test Functions covering:
- Valid requests (15 tests)
- Edge cases (15 tests)
- Invalid inputs (15 tests)
- Response validation (5+ tests)

Run with: pytest tests/test_env_api_50.py -v --tb=short
"""

import pytest
import httpx
from typing import Any
from datetime import datetime

# API Configuration
BASE_URL = "https://env-monitor-api-758343025648.us-central1.run.app"
TIMEOUT = 60.0  # 60 seconds for slow endpoints


@pytest.fixture(scope="module")
def client():
    """Create an HTTP client for tests - module scoped for efficiency."""
    with httpx.Client(base_url=BASE_URL, timeout=TIMEOUT) as client:
        yield client


# ===========================================================================
# SECTION 1: VALID REQUEST TESTS (15 tests)
# ===========================================================================

class TestValidRequests:
    """Tests for valid API requests that should return 200."""

    def test_01_hub_endpoint_returns_200(self, client):
        """Test the main hub endpoint returns 200."""
        response = client.get("/api/v1/hub")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)

    def test_02_hub_endpoint_has_sources(self, client):
        """Test hub endpoint contains source information."""
        response = client.get("/api/v1/hub")
        data = response.json()
        # Should have some indication of available data sources
        assert "name" in data or "sources" in data or "categories" in data

    def test_03_weather_san_francisco(self, client):
        """Test weather data for San Francisco."""
        response = client.get("/api/v1/data-sources/weather", params={
            "lat": 37.7749,
            "lon": -122.4194
        })
        assert response.status_code == 200

    def test_04_weather_new_york(self, client):
        """Test weather data for New York."""
        response = client.get("/api/v1/data-sources/weather", params={
            "lat": 40.7128,
            "lon": -74.0060
        })
        assert response.status_code == 200

    def test_05_weather_london(self, client):
        """Test weather data for London."""
        response = client.get("/api/v1/data-sources/weather", params={
            "lat": 51.5074,
            "lon": -0.1278
        })
        assert response.status_code == 200

    def test_06_weather_tokyo(self, client):
        """Test weather data for Tokyo."""
        response = client.get("/api/v1/data-sources/weather", params={
            "lat": 35.6762,
            "lon": 139.6503
        })
        assert response.status_code == 200

    def test_07_weather_sydney(self, client):
        """Test weather data for Sydney (Southern hemisphere)."""
        response = client.get("/api/v1/data-sources/weather", params={
            "lat": -33.8688,
            "lon": 151.2093
        })
        assert response.status_code == 200

    def test_08_air_quality_default(self, client):
        """Test air quality endpoint with defaults."""
        response = client.get("/api/v1/data-sources/air-quality")
        assert response.status_code == 200

    def test_09_air_quality_pm25(self, client):
        """Test air quality for PM2.5 parameter."""
        response = client.get("/api/v1/data-sources/air-quality", params={
            "parameter": "pm25",
            "country": "US"
        })
        assert response.status_code == 200

    def test_10_water_quality_california(self, client):
        """Test water quality for California."""
        response = client.get("/api/v1/data-sources/water-quality", params={
            "state_code": "CA"
        })
        assert response.status_code == 200

    def test_11_marine_data_default(self, client):
        """Test marine data endpoint with defaults."""
        response = client.get("/api/v1/data-sources/marine")
        assert response.status_code == 200

    def test_12_hub_quick_check(self, client):
        """Test the quick environmental check endpoint."""
        response = client.get("/api/v1/hub/quick", params={
            "lat": 37.7749,
            "lon": -122.4194
        })
        assert response.status_code == 200

    def test_13_gis_nearest_sensor(self, client):
        """Test finding nearest sensor to a location."""
        response = client.get("/api/v1/gis/nearest-sensor", params={
            "latitude": 37.7749,
            "longitude": -122.4194
        })
        assert response.status_code == 200

    def test_14_sensors_list(self, client):
        """Test listing all sensors."""
        response = client.get("/api/v1/sensors")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_15_dashboard_stats(self, client):
        """Test dashboard statistics endpoint."""
        response = client.get("/api/v1/dashboard/stats")
        assert response.status_code == 200


# ===========================================================================
# SECTION 2: EDGE CASE TESTS (15 tests)
# ===========================================================================

class TestEdgeCases:
    """Tests for edge case coordinates and boundary values."""

    def test_16_coords_at_equator(self, client):
        """Test coordinates at the equator (0,0)."""
        response = client.get("/api/v1/hub/location", params={
            "lat": 0.0,
            "lon": 0.0
        })
        assert response.status_code == 200

    def test_17_coords_north_pole(self, client):
        """Test coordinates at the North Pole."""
        response = client.get("/api/v1/hub/location", params={
            "lat": 90.0,
            "lon": 0.0
        })
        assert response.status_code == 200

    def test_18_coords_south_pole(self, client):
        """Test coordinates at the South Pole."""
        response = client.get("/api/v1/hub/location", params={
            "lat": -90.0,
            "lon": 0.0
        })
        assert response.status_code == 200

    def test_19_coords_date_line_positive(self, client):
        """Test coordinates at the International Date Line (+180)."""
        response = client.get("/api/v1/hub/location", params={
            "lat": 0.0,
            "lon": 180.0
        })
        assert response.status_code == 200

    def test_20_coords_date_line_negative(self, client):
        """Test coordinates at the International Date Line (-180)."""
        response = client.get("/api/v1/hub/location", params={
            "lat": 0.0,
            "lon": -180.0
        })
        assert response.status_code == 200

    def test_21_extreme_decimal_precision(self, client):
        """Test coordinates with extreme decimal precision."""
        response = client.get("/api/v1/hub/quick", params={
            "lat": 37.77490000001234,
            "lon": -122.41940000005678
        })
        assert response.status_code == 200

    def test_22_ocean_pacific_middle(self, client):
        """Test coordinates in the middle of Pacific Ocean."""
        response = client.get("/api/v1/hub/quick", params={
            "lat": 0.0,
            "lon": -160.0
        })
        assert response.status_code == 200

    def test_23_remote_antarctica(self, client):
        """Test coordinates in Antarctica."""
        response = client.get("/api/v1/hub/quick", params={
            "lat": -75.0,
            "lon": 0.0
        })
        assert response.status_code == 200

    def test_24_smallest_valid_radius(self, client):
        """Test with minimum valid radius (1 km)."""
        response = client.get("/api/v1/hub/location", params={
            "lat": 37.7749,
            "lon": -122.4194,
            "radius_km": 1.0
        })
        assert response.status_code == 200

    def test_25_largest_valid_radius(self, client):
        """Test with maximum valid radius (500 km)."""
        response = client.get("/api/v1/hub/location", params={
            "lat": 37.7749,
            "lon": -122.4194,
            "radius_km": 500.0
        })
        assert response.status_code == 200

    def test_26_exactly_boundary_lat_positive(self, client):
        """Test latitude at exactly +90 boundary."""
        response = client.get("/api/v1/gis/nearest-sensor", params={
            "latitude": 90.0,
            "longitude": 0.0
        })
        assert response.status_code == 200

    def test_27_exactly_boundary_lat_negative(self, client):
        """Test latitude at exactly -90 boundary."""
        response = client.get("/api/v1/gis/nearest-sensor", params={
            "latitude": -90.0,
            "longitude": 0.0
        })
        assert response.status_code == 200

    def test_28_exactly_boundary_lon_positive(self, client):
        """Test longitude at exactly +180 boundary."""
        response = client.get("/api/v1/gis/nearest-sensor", params={
            "latitude": 0.0,
            "longitude": 180.0
        })
        assert response.status_code == 200

    def test_29_exactly_boundary_lon_negative(self, client):
        """Test longitude at exactly -180 boundary."""
        response = client.get("/api/v1/gis/nearest-sensor", params={
            "latitude": 0.0,
            "longitude": -180.0
        })
        assert response.status_code == 200

    def test_30_weather_negative_coords(self, client):
        """Test weather with negative coordinates (Southern/Western)."""
        response = client.get("/api/v1/data-sources/weather", params={
            "lat": -33.8688,
            "lon": -70.6483  # Santiago, Chile
        })
        assert response.status_code == 200


# ===========================================================================
# SECTION 3: INVALID INPUT TESTS (15 tests)
# ===========================================================================

class TestInvalidInputs:
    """Tests for invalid inputs that should return 4xx errors."""

    def test_31_missing_lat_parameter(self, client):
        """Test hub/location with missing lat parameter."""
        response = client.get("/api/v1/hub/location", params={
            "lon": -122.4194
        })
        assert response.status_code == 422  # Validation error

    def test_32_missing_lon_parameter(self, client):
        """Test hub/location with missing lon parameter."""
        response = client.get("/api/v1/hub/location", params={
            "lat": 37.7749
        })
        assert response.status_code == 422

    def test_33_lat_out_of_range_high(self, client):
        """Test latitude > 90 (out of range)."""
        response = client.get("/api/v1/hub/location", params={
            "lat": 100.0,
            "lon": 0.0
        })
        assert response.status_code == 422

    def test_34_lat_out_of_range_low(self, client):
        """Test latitude < -90 (out of range)."""
        response = client.get("/api/v1/hub/location", params={
            "lat": -100.0,
            "lon": 0.0
        })
        assert response.status_code == 422

    def test_35_lon_out_of_range_high(self, client):
        """Test longitude > 180 (out of range)."""
        response = client.get("/api/v1/hub/location", params={
            "lat": 0.0,
            "lon": 200.0
        })
        assert response.status_code == 422

    def test_36_lon_out_of_range_low(self, client):
        """Test longitude < -180 (out of range)."""
        response = client.get("/api/v1/hub/location", params={
            "lat": 0.0,
            "lon": -200.0
        })
        assert response.status_code == 422

    def test_37_lat_as_string(self, client):
        """Test latitude as non-numeric string."""
        response = client.get("/api/v1/hub/location", params={
            "lat": "invalid",
            "lon": -122.4194
        })
        assert response.status_code == 422

    def test_38_lon_as_empty_string(self, client):
        """Test longitude as empty string."""
        response = client.get("/api/v1/hub/location", params={
            "lat": 37.7749,
            "lon": ""
        })
        assert response.status_code == 422

    def test_39_nonexistent_endpoint(self, client):
        """Test a non-existent endpoint returns 404."""
        response = client.get("/api/v1/nonexistent-endpoint")
        assert response.status_code == 404

    def test_40_invalid_sensor_id(self, client):
        """Test sensor status with invalid sensor ID."""
        response = client.get("/api/v1/sensors/99999999/status")
        # Could be 404 (not found) or 200 with error message
        assert response.status_code in [200, 404, 422]

    def test_41_radius_too_small(self, client):
        """Test radius below minimum (< 1)."""
        response = client.get("/api/v1/hub/location", params={
            "lat": 37.7749,
            "lon": -122.4194,
            "radius_km": 0.5
        })
        assert response.status_code == 422

    def test_42_radius_too_large(self, client):
        """Test radius above maximum (> 500)."""
        response = client.get("/api/v1/hub/location", params={
            "lat": 37.7749,
            "lon": -122.4194,
            "radius_km": 600.0
        })
        assert response.status_code == 422

    def test_43_gis_missing_latitude(self, client):
        """Test GIS nearest-sensor without latitude."""
        response = client.get("/api/v1/gis/nearest-sensor", params={
            "longitude": -122.4194
        })
        assert response.status_code == 422

    def test_44_gis_missing_longitude(self, client):
        """Test GIS nearest-sensor without longitude."""
        response = client.get("/api/v1/gis/nearest-sensor", params={
            "latitude": 37.7749
        })
        assert response.status_code == 422

    def test_45_invalid_method_on_get_endpoint(self, client):
        """Test POST method on GET-only endpoint."""
        response = client.post("/api/v1/hub")
        assert response.status_code == 405  # Method Not Allowed


# ===========================================================================
# SECTION 4: RESPONSE VALIDATION TESTS (5+ tests)
# ===========================================================================

class TestResponseValidation:
    """Tests to validate response structure and content."""

    def test_46_root_has_required_fields(self, client):
        """Test root endpoint has required fields."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        # Root should have basic system info
        assert "status" in data or "message" in data or "version" in data

    def test_47_health_endpoint_status(self, client):
        """Test health endpoint returns proper status."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        # Health should indicate system status
        assert "status" in data or "healthy" in data or len(data) > 0

    def test_48_dashboard_stats_structure(self, client):
        """Test dashboard stats has expected structure."""
        response = client.get("/api/v1/dashboard/stats")
        assert response.status_code == 200
        data = response.json()
        # Should have sensor/alert related stats
        expected_keys = ["total_sensors", "active_sensors", "total_readings_today", 
                         "active_alerts", "system_health"]
        for key in expected_keys:
            assert key in data, f"Missing key: {key}"

    def test_49_sensors_list_structure(self, client):
        """Test sensors list returns array of sensor objects."""
        response = client.get("/api/v1/sensors")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        if len(data) > 0:
            sensor = data[0]
            # Each sensor should have basic fields
            assert "id" in sensor or "name" in sensor

    def test_50_hub_quick_returns_environmental_data(self, client):
        """Test quick check returns environmental summary."""
        response = client.get("/api/v1/hub/quick", params={
            "lat": 37.7749,
            "lon": -122.4194
        })
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        # Should have some environmental data
        assert len(data) > 0

    def test_51_content_type_is_json(self, client):
        """Test all endpoints return JSON content type."""
        endpoints = ["/", "/health", "/api/v1/hub", "/api/v1/sensors"]
        for endpoint in endpoints:
            response = client.get(endpoint)
            content_type = response.headers.get("content-type", "")
            assert "application/json" in content_type, f"{endpoint} should return JSON"

    def test_52_timestamps_are_valid(self, client):
        """Test that timestamps in responses are valid ISO format."""
        response = client.get("/")
        data = response.json()
        if "timestamp" in data:
            # Should be valid ISO format
            ts = data["timestamp"]
            # Basic validation - contains T separator or is a date string
            assert "T" in ts or "-" in ts, f"Invalid timestamp format: {ts}"

    def test_53_hub_sources_returns_data(self, client):
        """Test hub/sources returns source information."""
        response = client.get("/api/v1/hub/sources")
        assert response.status_code == 200
        data = response.json()
        # Should be non-empty
        assert len(data) > 0 if isinstance(data, (list, dict)) else True

    def test_54_hub_categories_returns_list(self, client):
        """Test hub/categories returns categories."""
        response = client.get("/api/v1/hub/categories")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, (list, dict))

    def test_55_data_sources_status(self, client):
        """Test data sources status endpoint."""
        response = client.get("/api/v1/data-sources/status")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)


# ===========================================================================
# BONUS TESTS: Additional coverage
# ===========================================================================

class TestBonusCoverage:
    """Additional tests for extra coverage."""

    def test_56_system_health(self, client):
        """Test comprehensive system health endpoint."""
        response = client.get("/api/v1/system/health")
        assert response.status_code == 200

    def test_57_alerts_history(self, client):
        """Test alerts history endpoint."""
        response = client.get("/api/v1/alerts/history")
        assert response.status_code == 200

    def test_58_ml_performance(self, client):
        """Test ML performance metrics endpoint."""
        response = client.get("/api/v1/ml/performance")
        assert response.status_code == 200

    def test_59_data_quality_freshness(self, client):
        """Test data quality freshness check."""
        response = client.get("/api/v1/data-quality/freshness")
        assert response.status_code == 200

    def test_60_collaboration_status(self, client):
        """Test collaboration status endpoint."""
        response = client.get("/api/v1/collaboration/status")
        assert response.status_code == 200
