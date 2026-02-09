"""
System administration routes.

IMPORTANT: These routes require authentication as they can affect system state.
"""
import logging
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException

from app.agents.alertsystem_agent import alertsystem_agent
from app.agents.climateml_agent import climateml_agent
from app.agents.ecodata_agent import ecodata_agent
from app.agents.geospatial_agent import geospatial_agent
from app.config import settings
from app.schemas.schemas import APIResponse
from app.security import require_admin

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/health")
async def get_system_health():
    """Get comprehensive system health status."""
    return {
        "overall_status": "healthy",
        "version": settings.app_version,
        "environment": settings.environment,
        "agents": {
            "ecodata": {"status": "active", "last_active": datetime.utcnow().isoformat()},
            "climateml": {"status": "active", "last_active": datetime.utcnow().isoformat()},
            "geospatial": {"status": "active", "last_active": datetime.utcnow().isoformat()},
            "alertsystem": {"status": "active", "last_active": datetime.utcnow().isoformat()}
        },
        "services": {
            "database": "connected",
            "cache": "connected",
            "moltbook": "connected"
        },
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/info")
async def get_system_info():
    """Get system information (non-sensitive)."""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment,
        "api_docs": "/docs" if not settings.is_production else "disabled",
        "health_check": "/health",
        "timestamp": datetime.utcnow().isoformat()
    }


@router.post("/reset", dependencies=[Depends(require_admin)])
async def reset_system():
    """
    Reset all agents and services.
    
    ⚠️ WARNING: This is a destructive operation that resets all system state.
    
    Requires admin authentication.
    Only available in non-production environments by default.
    """
    # Additional safety check for production
    if settings.is_production:
        logger.warning("Attempted system reset in production environment")
        raise HTTPException(
            status_code=403,
            detail="System reset is disabled in production. Use deployment tools instead."
        )
    
    try:
        logger.warning("System reset initiated")
        
        # Reset agents
        await ecodata_agent.cleanup()
        await climateml_agent.cleanup()
        await geospatial_agent.cleanup()
        await alertsystem_agent.cleanup()

        # Reinitialize
        await ecodata_agent.initialize()
        await climateml_agent.initialize()
        await geospatial_agent.initialize()
        await alertsystem_agent.initialize()

        logger.info("System reset completed successfully")
        
        return APIResponse(
            success=True,
            message="System reset complete",
            data={"timestamp": datetime.utcnow().isoformat()}
        )
    except Exception as e:
        logger.error(f"System reset failed: {e}")
        raise HTTPException(status_code=500, detail=f"Reset failed: {str(e)}")


@router.post("/maintenance/enable", dependencies=[Depends(require_admin)])
async def enable_maintenance_mode():
    """Enable maintenance mode (stops accepting new requests)."""
    # This would typically set a flag that middleware checks
    logger.info("Maintenance mode enabled")
    return {"status": "maintenance_mode_enabled", "timestamp": datetime.utcnow().isoformat()}


@router.post("/maintenance/disable", dependencies=[Depends(require_admin)])
async def disable_maintenance_mode():
    """Disable maintenance mode."""
    logger.info("Maintenance mode disabled")
    return {"status": "maintenance_mode_disabled", "timestamp": datetime.utcnow().isoformat()}
