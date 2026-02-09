"""
API Routes Package

Organizes routes into domain-specific modules for better maintainability.
"""

from fastapi import APIRouter

from .sensors import router as sensors_router
from .predictions import router as predictions_router
from .gis import router as gis_router
from .alerts import router as alerts_router
from .dashboard import router as dashboard_router
from .collaboration import router as collaboration_router
from .system import router as system_router
from .data_sources import router as data_sources_router
from .hub import router as hub_router

# Main router that aggregates all sub-routers
router = APIRouter()

# Include all route modules with appropriate prefixes and tags
router.include_router(sensors_router, prefix="/sensors", tags=["Sensors"])
router.include_router(predictions_router, prefix="/predictions", tags=["Predictions"])
router.include_router(gis_router, prefix="/gis", tags=["GIS"])
router.include_router(alerts_router, prefix="/alerts", tags=["Alerts"])
router.include_router(dashboard_router, prefix="/dashboard", tags=["Dashboard"])
router.include_router(collaboration_router, prefix="/collaboration", tags=["Collaboration"])
router.include_router(system_router, prefix="/system", tags=["System"])
router.include_router(data_sources_router, prefix="/data-sources", tags=["Data Sources"])
router.include_router(hub_router, prefix="/hub", tags=["Data Hub"])
