"""
GIS and Spatial analysis routes.
"""
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query

from app.agents.geospatial_agent import geospatial_agent
from app.schemas.schemas import GISLayer, GISLayerCreate
from app.security import verify_api_key

router = APIRouter()


@router.get("/analysis/{analysis_type}")
async def get_spatial_analysis(analysis_type: str):
    """Get spatial analysis results."""
    valid_types = ["coverage", "zones", "interpolation"]
    if analysis_type not in valid_types:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid analysis type. Must be one of: {valid_types}"
        )
    return await geospatial_agent.get_spatial_analysis(analysis_type)


@router.get("/map")
async def get_environmental_map():
    """Get the environmental monitoring map."""
    return await geospatial_agent.get_map()


@router.get("/nearest-sensor")
async def find_nearest_sensor(
    latitude: float = Query(..., ge=-90, le=90),
    longitude: float = Query(..., ge=-180, le=180)
):
    """Find the nearest sensor to a location."""
    return await geospatial_agent.find_nearest_sensor(latitude, longitude)


@router.get("/zone-info")
async def get_zone_info(
    latitude: float = Query(..., ge=-90, le=90),
    longitude: float = Query(..., ge=-180, le=180)
):
    """Get environmental zone information for a location."""
    return await geospatial_agent.get_zone_info(latitude, longitude)


@router.post("/layers", response_model=GISLayer, dependencies=[Depends(verify_api_key)])
async def create_gis_layer(layer: GISLayerCreate):
    """Create a new GIS layer. Requires authentication."""
    layer_id = await geospatial_agent.create_gis_layer(layer)
    return GISLayer(
        id=layer_id,
        **layer.dict(),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
