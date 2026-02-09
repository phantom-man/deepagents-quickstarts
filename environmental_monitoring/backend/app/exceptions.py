"""
Custom Exception Classes for Environmental Monitoring System.

This module defines domain-specific exceptions that provide:
- Clear error categorization
- Consistent error response format
- Proper HTTP status code mapping
- Structured error details for debugging
"""
from typing import Any, Dict, Optional


class EnvironmentalMonitoringError(Exception):
    """Base exception for all environmental monitoring errors."""
    
    status_code: int = 500
    error_code: str = "INTERNAL_ERROR"
    message: str = "An unexpected error occurred"
    
    def __init__(
        self,
        message: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None
    ):
        self.message = message or self.message
        self.details = details or {}
        self.cause = cause
        super().__init__(self.message)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to a dictionary for API responses."""
        result = {
            "error_code": self.error_code,
            "message": self.message,
            "status_code": self.status_code,
        }
        if self.details:
            result["details"] = self.details
        if self.cause:
            result["cause"] = str(self.cause)
        return result


# ============================================================================
# Validation Errors (4xx)
# ============================================================================

class ValidationError(EnvironmentalMonitoringError):
    """Raised when input validation fails."""
    
    status_code = 400
    error_code = "VALIDATION_ERROR"
    message = "Input validation failed"


class InvalidCoordinatesError(ValidationError):
    """Raised when latitude/longitude values are invalid."""
    
    error_code = "INVALID_COORDINATES"
    message = "Invalid geographic coordinates"
    
    def __init__(self, lat: Optional[float] = None, lon: Optional[float] = None, **kwargs):
        details: Dict[str, Any] = {"latitude": lat, "longitude": lon}
        if lat is not None and (lat < -90 or lat > 90):
            details["latitude_error"] = "Must be between -90 and 90"
        if lon is not None and (lon < -180 or lon > 180):
            details["longitude_error"] = "Must be between -180 and 180"
        super().__init__(details=details, **kwargs)


class InvalidDateRangeError(ValidationError):
    """Raised when date range is invalid."""
    
    error_code = "INVALID_DATE_RANGE"
    message = "Invalid date range specified"


class DataFormatError(ValidationError):
    """Raised when data format is incorrect."""
    
    error_code = "DATA_FORMAT_ERROR"
    message = "Data format is invalid"


# ============================================================================
# Resource Errors (4xx)
# ============================================================================

class ResourceNotFoundError(EnvironmentalMonitoringError):
    """Raised when a requested resource doesn't exist."""
    
    status_code = 404
    error_code = "RESOURCE_NOT_FOUND"
    message = "The requested resource was not found"


class SensorNotFoundError(ResourceNotFoundError):
    """Raised when a sensor doesn't exist."""
    
    error_code = "SENSOR_NOT_FOUND"
    message = "Sensor not found"
    
    def __init__(self, sensor_id: str, **kwargs):
        super().__init__(
            message=f"Sensor '{sensor_id}' not found",
            details={"sensor_id": sensor_id},
            **kwargs
        )


class AlertNotFoundError(ResourceNotFoundError):
    """Raised when an alert doesn't exist."""
    
    error_code = "ALERT_NOT_FOUND"
    message = "Alert not found"
    
    def __init__(self, alert_id: str, **kwargs):
        super().__init__(
            message=f"Alert '{alert_id}' not found",
            details={"alert_id": alert_id},
            **kwargs
        )


class DataSourceNotFoundError(ResourceNotFoundError):
    """Raised when a data source doesn't exist."""
    
    error_code = "DATA_SOURCE_NOT_FOUND"
    message = "Data source not found"
    
    def __init__(self, source_id: str, **kwargs):
        super().__init__(
            message=f"Data source '{source_id}' not found",
            details={"source_id": source_id},
            **kwargs
        )


# ============================================================================
# Authorization Errors (4xx)
# ============================================================================

class AuthenticationError(EnvironmentalMonitoringError):
    """Raised when authentication fails."""
    
    status_code = 401
    error_code = "AUTHENTICATION_FAILED"
    message = "Authentication required"


class AuthorizationError(EnvironmentalMonitoringError):
    """Raised when user lacks required permissions."""
    
    status_code = 403
    error_code = "AUTHORIZATION_FAILED"
    message = "You don't have permission to perform this action"


class RateLimitExceededError(EnvironmentalMonitoringError):
    """Raised when rate limit is exceeded."""
    
    status_code = 429
    error_code = "RATE_LIMIT_EXCEEDED"
    message = "Too many requests. Please try again later."
    
    def __init__(self, retry_after: int = 60, **kwargs):
        super().__init__(
            details={"retry_after_seconds": retry_after},
            **kwargs
        )
        self.retry_after = retry_after


# ============================================================================
# External Service Errors (5xx)
# ============================================================================

class ExternalServiceError(EnvironmentalMonitoringError):
    """Raised when an external service fails."""
    
    status_code = 502
    error_code = "EXTERNAL_SERVICE_ERROR"
    message = "External service is unavailable"


class DataSourceConnectionError(ExternalServiceError):
    """Raised when connection to a data source fails."""
    
    error_code = "DATA_SOURCE_CONNECTION_FAILED"
    message = "Failed to connect to data source"
    
    def __init__(self, source_id: str, cause: Optional[Exception] = None, **kwargs):
        super().__init__(
            message=f"Failed to connect to data source '{source_id}'",
            details={"source_id": source_id},
            cause=cause,
            **kwargs
        )


class DataSourceTimeoutError(ExternalServiceError):
    """Raised when a data source request times out."""
    
    status_code = 504
    error_code = "DATA_SOURCE_TIMEOUT"
    message = "Data source request timed out"
    
    def __init__(self, source_id: str, timeout_seconds: Optional[float] = None, **kwargs):
        super().__init__(
            message=f"Request to data source '{source_id}' timed out",
            details={
                "source_id": source_id,
                "timeout_seconds": timeout_seconds
            },
            **kwargs
        )


class MoltbookConnectionError(ExternalServiceError):
    """Raised when Moltbook collaboration platform is unavailable."""
    
    error_code = "MOLTBOOK_CONNECTION_FAILED"
    message = "Failed to connect to Moltbook collaboration platform"


# ============================================================================
# Database Errors (5xx)
# ============================================================================

class DatabaseError(EnvironmentalMonitoringError):
    """Base exception for database-related errors."""
    
    status_code = 500
    error_code = "DATABASE_ERROR"
    message = "A database error occurred"


class DatabaseConnectionError(DatabaseError):
    """Raised when database connection fails."""
    
    error_code = "DATABASE_CONNECTION_FAILED"
    message = "Failed to connect to database"


class DatabaseQueryError(DatabaseError):
    """Raised when a database query fails."""
    
    error_code = "DATABASE_QUERY_FAILED"
    message = "Database query failed"


# ============================================================================
# Service Errors (5xx)
# ============================================================================

class PredictionServiceError(EnvironmentalMonitoringError):
    """Raised when ML prediction service fails."""
    
    status_code = 500
    error_code = "PREDICTION_SERVICE_ERROR"
    message = "Prediction service failed"


class CacheError(EnvironmentalMonitoringError):
    """Raised when cache operations fail."""
    
    status_code = 500
    error_code = "CACHE_ERROR"
    message = "Cache operation failed"


class ConfigurationError(EnvironmentalMonitoringError):
    """Raised when configuration is invalid."""
    
    status_code = 500
    error_code = "CONFIGURATION_ERROR"
    message = "System configuration error"
