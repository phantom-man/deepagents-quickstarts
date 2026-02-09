"""
Tests for custom exception handling.
"""
from app.exceptions import (
    DataSourceConnectionError,
    EnvironmentalMonitoringError,
    InvalidCoordinatesError,
    RateLimitExceededError,
    ResourceNotFoundError,
    SensorNotFoundError,
    ValidationError,
)


class TestExceptionClasses:
    """Test exception class behavior."""
    
    def test_base_exception_defaults(self):
        """Test base exception has correct defaults."""
        exc = EnvironmentalMonitoringError()
        assert exc.status_code == 500
        assert exc.error_code == "INTERNAL_ERROR"
        assert exc.message == "An unexpected error occurred"
    
    def test_base_exception_custom_message(self):
        """Test custom message is used."""
        exc = EnvironmentalMonitoringError(message="Custom error message")
        assert exc.message == "Custom error message"
        assert str(exc) == "Custom error message"
    
    def test_base_exception_to_dict(self):
        """Test exception serialization."""
        exc = EnvironmentalMonitoringError(
            message="Test error",
            details={"key": "value"}
        )
        result = exc.to_dict()
        
        assert result["error_code"] == "INTERNAL_ERROR"
        assert result["message"] == "Test error"
        assert result["status_code"] == 500
        assert result["details"] == {"key": "value"}
    
    def test_validation_error_status_code(self):
        """Test validation error has correct status code."""
        exc = ValidationError()
        assert exc.status_code == 400
        assert exc.error_code == "VALIDATION_ERROR"
    
    def test_invalid_coordinates_details(self):
        """Test invalid coordinates includes coordinate details."""
        exc = InvalidCoordinatesError(lat=100, lon=200)
        assert exc.details["latitude"] == 100
        assert exc.details["longitude"] == 200
        assert "latitude_error" in exc.details
        assert "longitude_error" in exc.details
    
    def test_sensor_not_found_includes_id(self):
        """Test sensor not found includes sensor ID."""
        exc = SensorNotFoundError(sensor_id="sensor-123")
        assert exc.status_code == 404
        assert "sensor-123" in exc.message
        assert exc.details["sensor_id"] == "sensor-123"
    
    def test_rate_limit_exceeded_retry_after(self):
        """Test rate limit includes retry-after."""
        exc = RateLimitExceededError(retry_after=120)
        assert exc.status_code == 429
        assert exc.retry_after == 120
        assert exc.details["retry_after_seconds"] == 120
    
    def test_data_source_connection_error_with_cause(self):
        """Test external error includes cause."""
        cause = Exception("Network timeout")
        exc = DataSourceConnectionError(
            source_id="openaq",
            cause=cause
        )
        assert exc.status_code == 502
        assert exc.cause == cause
        assert exc.details["source_id"] == "openaq"
        
        result = exc.to_dict()
        assert "Network timeout" in result["cause"]


class TestExceptionInheritance:
    """Test exception inheritance hierarchy."""
    
    def test_validation_error_is_base_error(self):
        """Test ValidationError inherits from base."""
        exc = ValidationError()
        assert isinstance(exc, EnvironmentalMonitoringError)
    
    def test_resource_not_found_is_base_error(self):
        """Test ResourceNotFoundError inherits from base."""
        exc = ResourceNotFoundError()
        assert isinstance(exc, EnvironmentalMonitoringError)
    
    def test_sensor_not_found_is_resource_not_found(self):
        """Test SensorNotFoundError inherits from ResourceNotFoundError."""
        exc = SensorNotFoundError(sensor_id="test")
        assert isinstance(exc, ResourceNotFoundError)
        assert isinstance(exc, EnvironmentalMonitoringError)
