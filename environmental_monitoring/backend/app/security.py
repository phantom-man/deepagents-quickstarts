"""
Security utilities for Environmental Monitoring System

Provides:
- API key authentication
- Rate limiting
- Request validation
"""
import logging
import time
from collections import defaultdict
from typing import Optional

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import APIKeyHeader, HTTPAuthorizationCredentials, HTTPBearer

from app.config import settings

logger = logging.getLogger(__name__)

# Security scheme for Bearer token
bearer_scheme = HTTPBearer(auto_error=False)

# Security scheme for API Key header
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


class AuthenticationError(HTTPException):
    """Raised when authentication fails."""
    
    def __init__(self, detail: str = "Authentication required"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"}
        )


class AuthorizationError(HTTPException):
    """Raised when authorization fails."""
    
    def __init__(self, detail: str = "Insufficient permissions"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail
        )


async def verify_api_key(
    api_key: Optional[str] = Depends(api_key_header),
    bearer: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme)
) -> str:
    """
    Verify API key from either X-API-Key header or Bearer token.
    
    Usage:
        @router.get("/protected", dependencies=[Depends(verify_api_key)])
        async def protected_endpoint():
            ...
    """
    # Check if API key is configured
    if not settings.api_key_configured:
        # In development without API key, allow all requests but log warning
        if not settings.is_production:
            logger.warning("API key not configured - allowing unauthenticated access in development")
            return "development"
        # In production, require API key to be configured
        logger.error("API key not configured in production!")
        raise AuthenticationError("Server configuration error - contact administrator")
    
    # Try API key header first
    if api_key:
        if api_key == settings.api_key:
            return "api_key"
        logger.warning("Invalid API key attempt from header")
        raise AuthenticationError("Invalid API key")
    
    # Try Bearer token
    if bearer:
        if bearer.credentials == settings.api_key:
            return "bearer"
        logger.warning("Invalid Bearer token attempt")
        raise AuthenticationError("Invalid Bearer token")
    
    raise AuthenticationError("API key or Bearer token required")


async def optional_api_key(
    api_key: Optional[str] = Depends(api_key_header),
    bearer: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme)
) -> Optional[str]:
    """
    Optional API key verification - doesn't fail if not provided.
    
    Useful for endpoints that have different behavior for authenticated vs anonymous.
    """
    if not settings.api_key_configured:
        return None
    
    if api_key and api_key == settings.api_key:
        return "api_key"
    
    if bearer and bearer.credentials == settings.api_key:
        return "bearer"
    
    return None


def require_admin(auth_type: str = Depends(verify_api_key)) -> str:
    """
    Require admin authentication for sensitive operations.
    
    Currently uses same API key, but can be extended for role-based access.
    """
    # Future: Check if the API key has admin privileges
    return auth_type


# ==================== Rate Limiting ====================
# Simple in-memory rate limiter (use Redis in production for distributed limiting)

_rate_limit_store: dict = defaultdict(list)


def get_client_ip(request: Request) -> str:
    """Extract client IP from request, handling proxies."""
    # Check X-Forwarded-For header (set by Cloud Run, load balancers)
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        # Take the first IP (original client)
        return forwarded_for.split(",")[0].strip()
    
    # Check X-Real-IP header
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip
    
    # Fall back to direct client
    return request.client.host if request.client else "unknown"


async def check_rate_limit(request: Request) -> None:
    """
    Check rate limit for the request.
    
    Simple sliding window implementation.
    For production, use slowapi with Redis backend.
    """
    client_ip = get_client_ip(request)
    current_time = time.time()
    window_start = current_time - 60  # 1 minute window
    
    # Clean old entries
    _rate_limit_store[client_ip] = [
        t for t in _rate_limit_store[client_ip] if t > window_start
    ]
    
    # Check limit
    if len(_rate_limit_store[client_ip]) >= settings.rate_limit_per_minute:
        logger.warning(f"Rate limit exceeded for {client_ip}")
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded. Please try again later.",
            headers={"Retry-After": "60"}
        )
    
    # Record this request
    _rate_limit_store[client_ip].append(current_time)


class RateLimiter:
    """
    Rate limiter dependency with configurable limits.
    
    Usage:
        @router.get("/endpoint", dependencies=[Depends(RateLimiter(calls=10, period=60))])
        async def limited_endpoint():
            ...
    """
    
    def __init__(self, calls: int = 60, period: int = 60):
        self.calls = calls
        self.period = period
    
    async def __call__(self, request: Request):
        client_ip = get_client_ip(request)
        current_time = time.time()
        window_start = current_time - self.period
        
        key = f"{client_ip}:{request.url.path}"
        
        # Clean old entries
        _rate_limit_store[key] = [
            t for t in _rate_limit_store[key] if t > window_start
        ]
        
        if len(_rate_limit_store[key]) >= self.calls:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded ({self.calls} requests per {self.period} seconds)",
                headers={"Retry-After": str(self.period)}
            )
        
        _rate_limit_store[key].append(current_time)
