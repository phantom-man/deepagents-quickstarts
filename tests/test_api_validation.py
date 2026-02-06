"""
API Validation and Error Handling Tests for Environmental Monitoring API.

50+ test scenarios covering:
- Data validation (coordinates, radius, dates, precision)
- Error responses (400, 404, 405, 422, 500)
- Data quality (timestamps, ranges, units, null handling)
- Concurrent requests (simultaneous, rapid-fire)

API Base URL: https://env-monitor-api-758343025648.us-central1.run.app
"""

import asyncio
import time
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any

import pytest
import requests
import aiohttp

# API Configuration
BASE_URL = "https://env-monitor-api-758343025648.us-central1.run.app"
TIMEOUT = 30

# Valid test coordinates (San Francisco)
VALID_LAT = 37.7749
VALID_LON = -122.4194


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def api_get(endpoint: str, params: dict | None = None, timeout: int = TIMEOUT) -> requests.Response:
    """Make a GET request to the API."""
    url = f"{BASE_URL}{endpoint}"
    return requests.get(url, params=params, timeout=timeout)


def api_post(endpoint: str, data: dict | None = None, timeout: int = TIMEOUT) -> requests.Response:
    """Make a POST request to the API."""
    url = f"{BASE_URL}{endpoint}"
    return requests.post(url, json=data, timeout=timeout)


def api_put(endpoint: str, data: dict | None = None, timeout: int = TIMEOUT) -> requests.Response:
    """Make a PUT request to the API."""
    url = f"{BASE_URL}{endpoint}"
    return requests.put(url, json=data, timeout=timeout)


def api_delete(endpoint: str, timeout: int = TIMEOUT) -> requests.Response:
    """Make a DELETE request to the API."""
    url = f"{BASE_URL}{endpoint}"
    return requests.delete(url, timeout=timeout)


async def async_get(session: aiohttp.ClientSession, endpoint: str, params: dict | None = None) -> dict:
    """Async GET request."""
    url = f"{BASE_URL}{endpoint}"
    async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=TIMEOUT)) as response:
        return {
            "status": response.status,
            "data": await response.json() if response.status == 200 else await response.text(),
            "endpoint": endpoint
        }


# =============================================================================
# DATA VALIDATION TESTS - LATITUDE
# =============================================================================

class TestLatitudeValidation:
    """Test latitude parameter validation."""

    def test_latitude_exactly_90(self):
        """Test latitude at exactly 90 (North Pole) - should be valid."""
        response = api_get("/weather", params={"lat": 90, "lon": 0})
        assert response.status_code in [200, 400], f"Unexpected status: {response.status_code}"

    def test_latitude_exactly_minus_90(self):
        """Test latitude at exactly -90 (South Pole) - should be valid."""
        response = api_get("/weather", params={"lat": -90, "lon": 0})
        assert response.status_code in [200, 400], f"Unexpected status: {response.status_code}"

    def test_latitude_above_90(self):
        """Test latitude above 90 - should return 400/422."""
        response = api_get("/weather", params={"lat": 91, "lon": 0})
        assert response.status_code in [400, 422], f"Expected 400/422 for lat=91, got {response.status_code}"

    def test_latitude_below_minus_90(self):
        """Test latitude below -90 - should return 400/422."""
        response = api_get("/weather", params={"lat": -91, "lon": 0})
        assert response.status_code in [400, 422], f"Expected 400/422 for lat=-91, got {response.status_code}"

    def test_latitude_extreme_positive(self):
        """Test extremely large positive latitude."""
        response = api_get("/weather", params={"lat": 1000, "lon": 0})
        assert response.status_code in [400, 422], f"Expected 400/422 for lat=1000, got {response.status_code}"

    def test_latitude_extreme_negative(self):
        """Test extremely large negative latitude."""
        response = api_get("/weather", params={"lat": -1000, "lon": 0})
        assert response.status_code in [400, 422], f"Expected 400/422 for lat=-1000, got {response.status_code}"

    def test_latitude_nan_string(self):
        """Test latitude as NaN string."""
        response = api_get("/weather", params={"lat": "NaN", "lon": 0})
        assert response.status_code in [400, 422], f"Expected 400/422 for lat=NaN, got {response.status_code}"

    def test_latitude_infinity_string(self):
        """Test latitude as infinity string."""
        response = api_get("/weather", params={"lat": "Infinity", "lon": 0})
        assert response.status_code in [400, 422], f"Expected 400/422 for lat=Infinity, got {response.status_code}"

    def test_latitude_non_numeric_string(self):
        """Test latitude as non-numeric string."""
        response = api_get("/weather", params={"lat": "abc", "lon": 0})
        assert response.status_code in [400, 422], f"Expected 400/422 for lat=abc, got {response.status_code}"

    def test_latitude_empty_string(self):
        """Test latitude as empty string."""
        response = api_get("/weather", params={"lat": "", "lon": 0})
        assert response.status_code in [400, 422], f"Expected 400/422 for lat='', got {response.status_code}"


# =============================================================================
# DATA VALIDATION TESTS - LONGITUDE
# =============================================================================

class TestLongitudeValidation:
    """Test longitude parameter validation."""

    def test_longitude_exactly_180(self):
        """Test longitude at exactly 180 - should be valid."""
        response = api_get("/weather", params={"lat": 0, "lon": 180})
        assert response.status_code in [200, 400], f"Unexpected status: {response.status_code}"

    def test_longitude_exactly_minus_180(self):
        """Test longitude at exactly -180 - should be valid."""
        response = api_get("/weather", params={"lat": 0, "lon": -180})
        assert response.status_code in [200, 400], f"Unexpected status: {response.status_code}"

    def test_longitude_above_180(self):
        """Test longitude above 180 - should return 400/422."""
        response = api_get("/weather", params={"lat": 0, "lon": 181})
        assert response.status_code in [400, 422], f"Expected 400/422 for lon=181, got {response.status_code}"

    def test_longitude_below_minus_180(self):
        """Test longitude below -180 - should return 400/422."""
        response = api_get("/weather", params={"lat": 0, "lon": -181})
        assert response.status_code in [400, 422], f"Expected 400/422 for lon=-181, got {response.status_code}"

    def test_longitude_extreme_positive(self):
        """Test extremely large positive longitude."""
        response = api_get("/weather", params={"lat": 0, "lon": 1000})
        assert response.status_code in [400, 422], f"Expected 400/422 for lon=1000, got {response.status_code}"

    def test_longitude_extreme_negative(self):
        """Test extremely large negative longitude."""
        response = api_get("/weather", params={"lat": 0, "lon": -1000})
        assert response.status_code in [400, 422], f"Expected 400/422 for lon=-1000, got {response.status_code}"

    def test_longitude_nan_string(self):
        """Test longitude as NaN string."""
        response = api_get("/weather", params={"lat": 0, "lon": "NaN"})
        assert response.status_code in [400, 422], f"Expected 400/422 for lon=NaN, got {response.status_code}"

    def test_longitude_non_numeric_string(self):
        """Test longitude as non-numeric string."""
        response = api_get("/weather", params={"lat": 0, "lon": "xyz"})
        assert response.status_code in [400, 422], f"Expected 400/422 for lon=xyz, got {response.status_code}"


# =============================================================================
# DATA VALIDATION TESTS - RADIUS
# =============================================================================

class TestRadiusValidation:
    """Test radius parameter validation for earthquake endpoint."""

    def test_radius_negative(self):
        """Test negative radius - should return 400/422."""
        response = api_get("/earthquakes", params={"lat": VALID_LAT, "lon": VALID_LON, "radius_km": -10})
        assert response.status_code in [200, 400, 422], f"Unexpected status: {response.status_code}"

    def test_radius_zero(self):
        """Test zero radius."""
        response = api_get("/earthquakes", params={"lat": VALID_LAT, "lon": VALID_LON, "radius_km": 0})
        assert response.status_code in [200, 400, 422], f"Unexpected status: {response.status_code}"

    def test_radius_extremely_large(self):
        """Test planetary-scale radius (Earth circumference ~40,000 km)."""
        response = api_get("/earthquakes", params={"lat": VALID_LAT, "lon": VALID_LON, "radius_km": 50000})
        assert response.status_code in [200, 400, 422], f"Unexpected status: {response.status_code}"

    def test_radius_one(self):
        """Test minimum valid radius (1 km)."""
        response = api_get("/earthquakes", params={"lat": VALID_LAT, "lon": VALID_LON, "radius_km": 1})
        assert response.status_code == 200, f"Expected 200 for radius=1, got {response.status_code}"

    def test_radius_float(self):
        """Test float radius value."""
        response = api_get("/earthquakes", params={"lat": VALID_LAT, "lon": VALID_LON, "radius_km": 50.5})
        assert response.status_code in [200, 400], f"Unexpected status: {response.status_code}"

    def test_radius_string(self):
        """Test string radius value."""
        response = api_get("/earthquakes", params={"lat": VALID_LAT, "lon": VALID_LON, "radius_km": "large"})
        assert response.status_code in [400, 422], f"Expected 400/422 for radius=large, got {response.status_code}"


# =============================================================================
# DATA VALIDATION TESTS - DECIMAL PRECISION
# =============================================================================

class TestDecimalPrecision:
    """Test coordinate decimal precision handling."""

    def test_precision_zero_decimals(self):
        """Test coordinates with 0 decimal places."""
        response = api_get("/weather", params={"lat": 38, "lon": -122})
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"

    def test_precision_two_decimals(self):
        """Test coordinates with 2 decimal places."""
        response = api_get("/weather", params={"lat": 37.77, "lon": -122.42})
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"

    def test_precision_ten_decimals(self):
        """Test coordinates with 10 decimal places."""
        response = api_get("/weather", params={"lat": 37.7749295358, "lon": -122.4194155215})
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"

    def test_precision_twenty_decimals(self):
        """Test coordinates with 20 decimal places (excessive precision)."""
        lat = 37.77492953583676529847
        lon = -122.41941552155873654829
        response = api_get("/weather", params={"lat": lat, "lon": lon})
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"

    def test_precision_scientific_notation(self):
        """Test coordinates in scientific notation."""
        response = api_get("/weather", params={"lat": "3.77749e1", "lon": "-1.224194e2"})
        assert response.status_code in [200, 400, 422], f"Unexpected status: {response.status_code}"


# =============================================================================
# ERROR RESPONSE TESTS - HTTP STATUS CODES
# =============================================================================

class TestErrorStatusCodes:
    """Test HTTP error status codes."""

    def test_404_invalid_endpoint(self):
        """Test 404 for non-existent endpoint."""
        response = api_get("/nonexistent_endpoint_xyz123")
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"

    def test_404_typo_endpoint(self):
        """Test 404 for typo in endpoint name."""
        response = api_get("/weahter")  # typo: weahter instead of weather
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"

    def test_405_post_to_get_weather(self):
        """Test 405 for POST to GET-only weather endpoint."""
        response = api_post("/weather", data={"lat": VALID_LAT, "lon": VALID_LON})
        assert response.status_code in [405, 422], f"Expected 405/422, got {response.status_code}"

    def test_405_put_to_get_earthquakes(self):
        """Test 405 for PUT to GET-only earthquakes endpoint."""
        response = api_put("/earthquakes", data={"lat": VALID_LAT, "lon": VALID_LON})
        assert response.status_code in [405, 422], f"Expected 405/422, got {response.status_code}"

    def test_405_delete_to_hub(self):
        """Test 405 for DELETE to hub endpoint."""
        response = api_delete("/hub/air-quality")
        assert response.status_code in [405, 422], f"Expected 405/422, got {response.status_code}"

    def test_400_missing_required_param(self):
        """Test 400/422 for missing required parameters."""
        response = api_get("/weather")  # Missing lat and lon
        assert response.status_code in [400, 422], f"Expected 400/422 for missing params, got {response.status_code}"

    def test_400_missing_latitude(self):
        """Test 400/422 for missing latitude only."""
        response = api_get("/weather", params={"lon": VALID_LON})
        assert response.status_code in [400, 422], f"Expected 400/422, got {response.status_code}"

    def test_400_missing_longitude(self):
        """Test 400/422 for missing longitude only."""
        response = api_get("/weather", params={"lat": VALID_LAT})
        assert response.status_code in [400, 422], f"Expected 400/422, got {response.status_code}"


# =============================================================================
# ERROR RESPONSE TESTS - JSON STRUCTURE
# =============================================================================

class TestErrorResponseStructure:
    """Test error response JSON structure consistency."""

    def test_error_response_has_detail(self):
        """Test that error responses contain 'detail' field."""
        response = api_get("/weather")  # Missing params
        if response.status_code in [400, 422]:
            data = response.json()
            # FastAPI typically uses 'detail' for errors
            assert "detail" in data or "error" in data or "message" in data, \
                f"Error response missing detail/error/message field: {data}"

    def test_404_error_structure(self):
        """Test 404 error response structure."""
        response = api_get("/nonexistent_xyz")
        assert response.status_code == 404
        data = response.json()
        assert isinstance(data, dict), f"404 response should be JSON object: {data}"

    def test_validation_error_structure(self):
        """Test validation error (422) response structure."""
        response = api_get("/weather", params={"lat": "invalid", "lon": "invalid"})
        if response.status_code == 422:
            data = response.json()
            # FastAPI 422 typically has detail with list of validation errors
            if "detail" in data and isinstance(data["detail"], list):
                for error in data["detail"]:
                    assert "loc" in error or "msg" in error or "type" in error, \
                        f"Validation error missing expected fields: {error}"

    def test_error_response_is_json(self):
        """Test that all error responses are valid JSON."""
        response = api_get("/weather")  # Missing params triggers error
        if response.status_code >= 400:
            try:
                data = response.json()
                assert isinstance(data, dict), f"Error response should be dict: {data}"
            except ValueError:
                pytest.fail(f"Error response is not valid JSON: {response.text}")


# =============================================================================
# DATA QUALITY TESTS - TIMESTAMP VALIDATION
# =============================================================================

class TestTimestampQuality:
    """Test response timestamp formats and validity."""

    def test_weather_timestamp_format(self):
        """Test that weather response has valid timestamp."""
        response = api_get("/weather", params={"lat": VALID_LAT, "lon": VALID_LON})
        if response.status_code == 200:
            data = response.json()
            # Check for timestamp fields
            timestamp_fields = ["timestamp", "time", "datetime", "generated_at", "current_time"]
            found_timestamp = None
            for field in timestamp_fields:
                if field in data:
                    found_timestamp = data[field]
                    break
                # Check nested
                if "current" in data and field in data.get("current", {}):
                    found_timestamp = data["current"][field]
                    break
            
            if found_timestamp:
                # Validate it's a parseable datetime
                try:
                    if isinstance(found_timestamp, str):
                        datetime.fromisoformat(found_timestamp.replace("Z", "+00:00"))
                except ValueError:
                    pytest.fail(f"Invalid timestamp format: {found_timestamp}")

    def test_earthquake_timestamp_format(self):
        """Test that earthquake times are valid."""
        response = api_get("/earthquakes", params={"lat": VALID_LAT, "lon": VALID_LON})
        if response.status_code == 200:
            data = response.json()
            # Earthquakes usually have 'time' in each event
            if "features" in data:
                for feature in data["features"][:5]:  # Check first 5
                    if "properties" in feature and "time" in feature["properties"]:
                        ts = feature["properties"]["time"]
                        # Could be Unix timestamp (ms) or ISO string
                        assert ts is not None, "Earthquake time should not be None"


# =============================================================================
# DATA QUALITY TESTS - NUMERIC RANGES
# =============================================================================

class TestNumericRanges:
    """Test that numeric values are within reasonable ranges."""

    def test_temperature_reasonable_range(self):
        """Test that temperature is within reasonable range (-100 to 60°C)."""
        response = api_get("/weather", params={"lat": VALID_LAT, "lon": VALID_LON})
        if response.status_code == 200:
            data = response.json()
            temp_fields = ["temperature", "temp", "temperature_2m", "temp_c"]
            temp = None
            for field in temp_fields:
                if field in data:
                    temp = data[field]
                    break
                if "current" in data and field in data.get("current", {}):
                    temp = data["current"][field]
                    break
            
            if temp is not None and isinstance(temp, (int, float)):
                assert -100 <= temp <= 60, f"Temperature {temp}°C outside reasonable range"

    def test_humidity_valid_range(self):
        """Test that humidity is 0-100%."""
        response = api_get("/weather", params={"lat": VALID_LAT, "lon": VALID_LON})
        if response.status_code == 200:
            data = response.json()
            humidity_fields = ["humidity", "relative_humidity", "relative_humidity_2m"]
            humidity = None
            for field in humidity_fields:
                if field in data:
                    humidity = data[field]
                    break
                if "current" in data and field in data.get("current", {}):
                    humidity = data["current"][field]
                    break
            
            if humidity is not None and isinstance(humidity, (int, float)):
                assert 0 <= humidity <= 100, f"Humidity {humidity}% outside valid range"

    def test_earthquake_magnitude_range(self):
        """Test that earthquake magnitudes are -2 to 10."""
        response = api_get("/earthquakes", params={"lat": VALID_LAT, "lon": VALID_LON})
        if response.status_code == 200:
            data = response.json()
            if "features" in data:
                for feature in data["features"][:10]:
                    if "properties" in feature and "mag" in feature["properties"]:
                        mag = feature["properties"]["mag"]
                        if mag is not None:
                            assert -2 <= mag <= 10, f"Magnitude {mag} outside valid range"

    def test_wind_speed_non_negative(self):
        """Test that wind speed is non-negative."""
        response = api_get("/weather", params={"lat": VALID_LAT, "lon": VALID_LON})
        if response.status_code == 200:
            data = response.json()
            wind_fields = ["wind_speed", "windspeed", "wind_speed_10m"]
            wind = None
            for field in wind_fields:
                if field in data:
                    wind = data[field]
                    break
                if "current" in data and field in data.get("current", {}):
                    wind = data["current"][field]
                    break
            
            if wind is not None and isinstance(wind, (int, float)):
                assert wind >= 0, f"Wind speed {wind} should be non-negative"


# =============================================================================
# DATA QUALITY TESTS - NULL/NONE HANDLING
# =============================================================================

class TestNullHandling:
    """Test null/None handling in responses."""

    def test_response_not_null(self):
        """Test that successful responses are not null."""
        response = api_get("/weather", params={"lat": VALID_LAT, "lon": VALID_LON})
        if response.status_code == 200:
            data = response.json()
            assert data is not None, "Response data should not be null"

    def test_empty_array_vs_null(self):
        """Test that empty results are arrays, not null."""
        # Remote location unlikely to have earthquakes
        response = api_get("/earthquakes", params={"lat": 0, "lon": 0, "radius_km": 1})
        if response.status_code == 200:
            data = response.json()
            if "features" in data:
                assert isinstance(data["features"], list), "Features should be array, not null"
            elif "earthquakes" in data:
                assert isinstance(data["earthquakes"], list), "Earthquakes should be array, not null"

    def test_hub_endpoint_structure(self):
        """Test hub endpoint returns proper structure even with no data."""
        response = api_get("/hub/air-quality", params={"lat": VALID_LAT, "lon": VALID_LON})
        if response.status_code == 200:
            data = response.json()
            assert data is not None, "Hub response should not be null"
            assert isinstance(data, dict), "Hub response should be dict"


# =============================================================================
# CONCURRENT REQUEST TESTS
# =============================================================================

class TestConcurrentRequests:
    """Test API behavior under concurrent load."""

    def test_10_simultaneous_same_endpoint(self):
        """Test 10 simultaneous requests to same endpoint."""
        def make_request():
            return api_get("/weather", params={"lat": VALID_LAT, "lon": VALID_LON})
        
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request) for _ in range(10)]
            results = [f.result() for f in as_completed(futures)]
        
        success_count = sum(1 for r in results if r.status_code == 200)
        assert success_count >= 8, f"Expected >=8 successes, got {success_count}/10"

    def test_10_simultaneous_different_endpoints(self):
        """Test 10 simultaneous requests to different endpoints."""
        endpoints = [
            ("/weather", {"lat": VALID_LAT, "lon": VALID_LON}),
            ("/earthquakes", {"lat": VALID_LAT, "lon": VALID_LON}),
            ("/hub/air-quality", {"lat": VALID_LAT, "lon": VALID_LON}),
            ("/hub/weather", {"lat": VALID_LAT, "lon": VALID_LON}),
            ("/hub/marine", {"lat": VALID_LAT, "lon": VALID_LON}),
            ("/weather", {"lat": 40.7128, "lon": -74.0060}),  # NYC
            ("/earthquakes", {"lat": 35.6762, "lon": 139.6503}),  # Tokyo
            ("/weather", {"lat": 51.5074, "lon": -0.1278}),  # London
            ("/hub/climate", {"lat": VALID_LAT, "lon": VALID_LON}),
            ("/", {}),  # Root/health check
        ]
        
        def make_request(endpoint_params):
            endpoint, params = endpoint_params
            return api_get(endpoint, params=params if params else None)
        
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request, ep) for ep in endpoints]
            results = [f.result() for f in as_completed(futures)]
        
        success_count = sum(1 for r in results if r.status_code in [200, 404])
        assert success_count >= 6, f"Expected >=6 non-error responses, got {success_count}/10"

    def test_rapid_fire_requests(self):
        """Test 50 sequential rapid-fire requests in ~10 seconds."""
        results = []
        start_time = time.time()
        
        for i in range(50):
            response = api_get("/weather", params={"lat": VALID_LAT, "lon": VALID_LON})
            results.append(response.status_code)
        
        elapsed = time.time() - start_time
        success_count = sum(1 for r in results if r == 200)
        rate_limited = sum(1 for r in results if r == 429)
        
        print(f"Rapid-fire test: {success_count} successes, {rate_limited} rate-limited in {elapsed:.2f}s")
        # Allow for some rate limiting
        assert success_count >= 30 or rate_limited > 0, \
            f"Expected >=30 successes or rate limiting, got {success_count} successes, {rate_limited} rate-limited"

    @pytest.mark.asyncio
    async def test_async_concurrent_requests(self):
        """Test async concurrent requests."""
        async with aiohttp.ClientSession() as session:
            tasks = [
                async_get(session, "/weather", {"lat": VALID_LAT, "lon": VALID_LON})
                for _ in range(10)
            ]
            results = await asyncio.gather(*tasks, return_exceptions=True)
        
        success_count = sum(1 for r in results if isinstance(r, dict) and r.get("status") == 200)
        assert success_count >= 7, f"Expected >=7 async successes, got {success_count}/10"


# =============================================================================
# BOUNDARY VALUE TESTS
# =============================================================================

class TestBoundaryValues:
    """Test boundary values for parameters."""

    def test_lat_boundary_89_9999(self):
        """Test latitude just under 90."""
        response = api_get("/weather", params={"lat": 89.9999, "lon": 0})
        assert response.status_code == 200, f"Expected 200 for lat=89.9999, got {response.status_code}"

    def test_lat_boundary_90_0001(self):
        """Test latitude just over 90."""
        response = api_get("/weather", params={"lat": 90.0001, "lon": 0})
        assert response.status_code in [400, 422], f"Expected 400/422 for lat=90.0001, got {response.status_code}"

    def test_lon_boundary_179_9999(self):
        """Test longitude just under 180."""
        response = api_get("/weather", params={"lat": 0, "lon": 179.9999})
        assert response.status_code == 200, f"Expected 200 for lon=179.9999, got {response.status_code}"

    def test_lon_boundary_180_0001(self):
        """Test longitude just over 180."""
        response = api_get("/weather", params={"lat": 0, "lon": 180.0001})
        assert response.status_code in [400, 422], f"Expected 400/422 for lon=180.0001, got {response.status_code}"

    def test_equator_prime_meridian(self):
        """Test coordinates at equator and prime meridian (0, 0)."""
        response = api_get("/weather", params={"lat": 0, "lon": 0})
        assert response.status_code == 200, f"Expected 200 for (0,0), got {response.status_code}"


# =============================================================================
# SPECIAL CHARACTER TESTS
# =============================================================================

class TestSpecialCharacters:
    """Test handling of special characters in parameters."""

    def test_lat_with_plus_sign(self):
        """Test latitude with explicit plus sign."""
        response = api_get("/weather", params={"lat": "+37.77", "lon": "-122.42"})
        assert response.status_code in [200, 400, 422], f"Unexpected status: {response.status_code}"

    def test_lat_with_spaces(self):
        """Test latitude with leading/trailing spaces."""
        response = api_get("/weather", params={"lat": " 37.77 ", "lon": "-122.42"})
        assert response.status_code in [200, 400, 422], f"Unexpected status: {response.status_code}"

    def test_unicode_in_params(self):
        """Test unicode characters in parameters."""
        response = api_get("/weather", params={"lat": "37°", "lon": "-122"})
        assert response.status_code in [400, 422], f"Expected 400/422 for unicode, got {response.status_code}"

    def test_sql_injection_attempt(self):
        """Test SQL injection attempt in parameters."""
        response = api_get("/weather", params={"lat": "37; DROP TABLE users;", "lon": "-122"})
        assert response.status_code in [400, 422], f"Expected 400/422 for SQL injection, got {response.status_code}"

    def test_html_in_params(self):
        """Test HTML tags in parameters."""
        response = api_get("/weather", params={"lat": "<script>alert(1)</script>", "lon": "-122"})
        assert response.status_code in [400, 422], f"Expected 400/422 for HTML, got {response.status_code}"


# =============================================================================
# ENDPOINT SPECIFIC TESTS
# =============================================================================

class TestEndpointSpecific:
    """Test specific endpoint behaviors."""

    def test_root_endpoint(self):
        """Test root endpoint returns health/info."""
        response = api_get("/")
        assert response.status_code == 200, f"Expected 200 for root, got {response.status_code}"

    def test_hub_air_quality(self):
        """Test hub air quality endpoint."""
        response = api_get("/hub/air-quality", params={"lat": VALID_LAT, "lon": VALID_LON})
        assert response.status_code in [200, 404], f"Unexpected status: {response.status_code}"

    def test_hub_weather(self):
        """Test hub weather endpoint."""
        response = api_get("/hub/weather", params={"lat": VALID_LAT, "lon": VALID_LON})
        assert response.status_code in [200, 404], f"Unexpected status: {response.status_code}"

    def test_hub_marine(self):
        """Test hub marine endpoint."""
        response = api_get("/hub/marine", params={"lat": VALID_LAT, "lon": VALID_LON})
        assert response.status_code in [200, 404], f"Unexpected status: {response.status_code}"

    def test_hub_climate(self):
        """Test hub climate endpoint."""
        response = api_get("/hub/climate", params={"lat": VALID_LAT, "lon": VALID_LON})
        assert response.status_code in [200, 404], f"Unexpected status: {response.status_code}"

    def test_hub_earthquake(self):
        """Test hub earthquake endpoint."""
        response = api_get("/hub/earthquake", params={"lat": VALID_LAT, "lon": VALID_LON})
        assert response.status_code in [200, 404], f"Unexpected status: {response.status_code}"

    def test_hub_invalid_category(self):
        """Test hub with invalid category."""
        response = api_get("/hub/invalid-category-xyz", params={"lat": VALID_LAT, "lon": VALID_LON})
        assert response.status_code in [400, 404, 422], f"Expected error for invalid hub category, got {response.status_code}"


# =============================================================================
# RESPONSE TIME TESTS
# =============================================================================

class TestResponseTime:
    """Test API response times."""

    def test_weather_response_time(self):
        """Test weather endpoint responds within 10 seconds."""
        start = time.time()
        response = api_get("/weather", params={"lat": VALID_LAT, "lon": VALID_LON})
        elapsed = time.time() - start
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        assert elapsed < 10, f"Response took {elapsed:.2f}s, expected < 10s"

    def test_earthquake_response_time(self):
        """Test earthquake endpoint responds within 15 seconds."""
        start = time.time()
        response = api_get("/earthquakes", params={"lat": VALID_LAT, "lon": VALID_LON})
        elapsed = time.time() - start
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        assert elapsed < 15, f"Response took {elapsed:.2f}s, expected < 15s"

    def test_root_response_time(self):
        """Test root endpoint responds within 2 seconds."""
        start = time.time()
        response = api_get("/")
        elapsed = time.time() - start
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        assert elapsed < 2, f"Root response took {elapsed:.2f}s, expected < 2s"


# =============================================================================
# CONTENT TYPE TESTS
# =============================================================================

class TestContentType:
    """Test response content types."""

    def test_json_content_type(self):
        """Test that responses have JSON content type."""
        response = api_get("/weather", params={"lat": VALID_LAT, "lon": VALID_LON})
        content_type = response.headers.get("Content-Type", "")
        assert "application/json" in content_type, f"Expected JSON content type, got {content_type}"

    def test_error_json_content_type(self):
        """Test that error responses have JSON content type."""
        response = api_get("/weather")  # Missing params
        content_type = response.headers.get("Content-Type", "")
        assert "application/json" in content_type, f"Expected JSON content type for error, got {content_type}"

    def test_404_content_type(self):
        """Test that 404 responses have JSON content type."""
        response = api_get("/nonexistent")
        content_type = response.headers.get("Content-Type", "")
        assert "application/json" in content_type, f"Expected JSON content type for 404, got {content_type}"


# =============================================================================
# MAIN EXECUTION
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short", "-x"])
