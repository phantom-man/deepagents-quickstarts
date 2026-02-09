#!/usr/bin/env python3
"""
Environmental Monitoring System - Main FastAPI Application

A collaborative AI-powered environmental monitoring system built with multiple specialized agents:
- EcoData Agent: Real-time sensor data ingestion
- ClimateML Agent: ML models for prediction and anomaly detection
- GeoSpatial Agent: GIS integration and spatial analysis
- AlertSystem Agent: Real-time alerting and reporting

Built using the Moltbook collaboration platform for agent coordination.
"""

import os
import uuid
import logging
from datetime import datetime
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, HTTPException, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Import our modules
from app.api.routes import router as api_router
from app.services.moltbook_collaboration import MoltbookCollaborationService
from app.services.database import init_database, close_database
from app.services.cache import init_cache, close_cache
from app.config import settings
from app.security import check_rate_limit, get_client_ip
from app.exceptions import (
    EnvironmentalMonitoringError,
    ValidationError,
    ResourceNotFoundError,
    AuthenticationError,
    AuthorizationError,
    RateLimitExceededError,
    ExternalServiceError,
    DatabaseError,
)

# ==================== Structured Logging ====================
class StructuredLogger(logging.Logger):
    """Logger that adds correlation ID and structured context."""
    
    def _log_with_context(self, level, msg, *args, **kwargs):
        # Add extra context if available
        extra = kwargs.get('extra', {})
        if not isinstance(extra, dict):
            extra = {}
        kwargs['extra'] = extra
        super()._log(level, msg, *args, **kwargs)


# Configure logging based on settings
log_format = '%(asctime)s - %(name)s - %(levelname)s - [%(correlation_id)s] - %(message)s'
if settings.log_format == "json":
    # JSON format for production (easier to parse in Cloud Logging)
    log_format = '{"timestamp": "%(asctime)s", "logger": "%(name)s", "level": "%(levelname)s", "correlation_id": "%(correlation_id)s", "message": "%(message)s"}'

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format=log_format,
    datefmt='%Y-%m-%dT%H:%M:%S%z'
)

# Add default filter for correlation_id
class CorrelationIdFilter(logging.Filter):
    def filter(self, record):
        if not hasattr(record, 'correlation_id'):
            record.correlation_id = 'no-correlation-id'
        return True

logging.getLogger().addFilter(CorrelationIdFilter())
logger = logging.getLogger(__name__)

# Global collaboration service
collaboration_service = MoltbookCollaborationService()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup and shutdown events."""
    # Startup
    logger.info("🚀 Starting Environmental Monitoring System...")

    # Initialize services
    await init_database()
    await init_cache()

    # Initialize Moltbook collaboration
    await collaboration_service.initialize()

    logger.info("✅ System initialized successfully")

    yield

    # Shutdown
    logger.info("🛑 Shutting down Environmental Monitoring System...")

    # Close services
    await close_database()
    await close_cache()

    # Cleanup collaboration service
    await collaboration_service.cleanup()

    logger.info("✅ System shutdown complete")

# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    description="AI-powered environmental monitoring with collaborative agents",
    version=settings.app_version,
    lifespan=lifespan,
    docs_url="/docs" if not settings.is_production else None,  # Disable docs in production
    redoc_url="/redoc" if not settings.is_production else None,
)

# ==================== Middleware ====================

# Request ID middleware for correlation
@app.middleware("http")
async def add_correlation_id(request: Request, call_next):
    """Add correlation ID to each request for tracing."""
    correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
    request.state.correlation_id = correlation_id
    
    # Log request
    logger.info(
        f"Request: {request.method} {request.url.path}",
        extra={"correlation_id": correlation_id}
    )
    
    response = await call_next(request)
    response.headers["X-Correlation-ID"] = correlation_id
    
    # Log response
    logger.info(
        f"Response: {response.status_code}",
        extra={"correlation_id": correlation_id}
    )
    
    return response


# Rate limiting middleware
@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    """Apply rate limiting to all requests."""
    # Skip rate limiting for health checks
    if request.url.path in ["/health", "/ok", "/"]:
        return await call_next(request)
    
    try:
        await check_rate_limit(request)
    except HTTPException as e:
        return JSONResponse(
            status_code=e.status_code,
            content={"detail": e.detail},
            headers=e.headers
        )
    
    return await call_next(request)


# ==================== Exception Handlers ====================

@app.exception_handler(EnvironmentalMonitoringError)
async def handle_app_error(request: Request, exc: EnvironmentalMonitoringError):
    """Handle all custom application errors."""
    correlation_id = getattr(request.state, 'correlation_id', 'unknown')
    
    # Log the error with context
    logger.error(
        f"{exc.error_code}: {exc.message}",
        extra={
            "correlation_id": correlation_id,
            "error_code": exc.error_code,
            "details": exc.details,
        }
    )
    
    # Build response
    response_body = exc.to_dict()
    response_body["correlation_id"] = correlation_id
    
    headers = {"X-Correlation-ID": correlation_id}
    
    # Add Retry-After header for rate limit errors
    if isinstance(exc, RateLimitExceededError):
        headers["Retry-After"] = str(exc.retry_after)
    
    return JSONResponse(
        status_code=exc.status_code,
        content=response_body,
        headers=headers
    )


@app.exception_handler(ValueError)
async def handle_value_error(request: Request, exc: ValueError):
    """Handle ValueError as validation errors."""
    correlation_id = getattr(request.state, 'correlation_id', 'unknown')
    
    logger.warning(
        f"Validation error: {str(exc)}",
        extra={"correlation_id": correlation_id}
    )
    
    return JSONResponse(
        status_code=400,
        content={
            "error_code": "VALIDATION_ERROR",
            "message": str(exc),
            "correlation_id": correlation_id
        },
        headers={"X-Correlation-ID": correlation_id}
    )


@app.exception_handler(Exception)
async def handle_unexpected_error(request: Request, exc: Exception):
    """Handle unexpected errors with proper logging."""
    correlation_id = getattr(request.state, 'correlation_id', 'unknown')
    
    # Log full traceback for unexpected errors
    logger.exception(
        f"Unexpected error: {str(exc)}",
        extra={"correlation_id": correlation_id}
    )
    
    # Don't expose internal error details in production
    message = "An unexpected error occurred"
    if not settings.is_production:
        message = str(exc)
    
    return JSONResponse(
        status_code=500,
        content={
            "error_code": "INTERNAL_ERROR",
            "message": message,
            "correlation_id": correlation_id
        },
        headers={"X-Correlation-ID": correlation_id}
    )


# Configure CORS with restricted origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "X-API-Key", "X-Correlation-ID"],
)

# Include API routes
app.include_router(api_router, prefix="/api/v1")

@app.get("/")
async def root():
    """Root endpoint with system status."""
    return {
        "message": "Environmental Monitoring System API",
        "version": "1.0.0",
        "status": "running",
        "timestamp": datetime.utcnow().isoformat(),
        "agents": {
            "ecodata": "active",
            "climateml": "active",
            "geospatial": "active",
            "alertsystem": "active"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint with dependency status."""
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": settings.app_version,
        "environment": settings.environment,
        "services": {
            "database": "unknown",
            "cache": "unknown",
            "moltbook": "unknown"
        }
    }
    
    # Check database connectivity
    try:
        from app.services.database import get_db_session
        async with get_db_session() as session:
            await session.execute("SELECT 1")
        health_status["services"]["database"] = "connected"
    except Exception as e:
        health_status["services"]["database"] = f"error: {str(e)[:50]}"
        health_status["status"] = "degraded"
    
    # Check cache connectivity
    try:
        from app.services.cache import cache_get
        await cache_get("health_check")
        health_status["services"]["cache"] = "connected"
    except Exception as e:
        health_status["services"]["cache"] = f"error: {str(e)[:50]}"
        # Cache failure doesn't degrade overall health
    
    # Check Moltbook connectivity
    try:
        if collaboration_service._initialized:
            health_status["services"]["moltbook"] = "connected"
        else:
            health_status["services"]["moltbook"] = "not initialized"
    except Exception as e:
        health_status["services"]["moltbook"] = f"error: {str(e)[:50]}"
    
    return health_status


@app.get("/ok")
async def ok_check():
    """Simple liveness probe for load balancers."""
    return {"status": "ok"}


@app.get("/ready")
async def readiness_check():
    """Readiness probe - returns 503 if not ready to accept traffic."""
    try:
        from app.services.database import get_db_session
        async with get_db_session() as session:
            await session.execute("SELECT 1")
        return {"status": "ready"}
    except Exception:
        raise HTTPException(status_code=503, detail="Service not ready")

@app.post("/collaborate")
async def trigger_collaboration(background_tasks: BackgroundTasks):
    """Trigger collaborative analysis across all agents."""
    try:
        # Add background task for collaboration
        background_tasks.add_task(collaboration_service.run_collaborative_analysis)

        return {
            "message": "Collaborative analysis initiated",
            "status": "processing",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to initiate collaboration: {e}")
        raise HTTPException(status_code=500, detail="Failed to initiate collaboration")

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=False,  # Disable reload in production
        log_level="info"
    )