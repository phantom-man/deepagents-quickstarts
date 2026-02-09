"""
Sensor CRUD and data routes.
"""
from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query

from app.agents.ecodata_agent import ecodata_agent
from app.schemas.schemas import Sensor, SensorCreate
from app.security import verify_api_key

router = APIRouter()


@router.get("", response_model=List[Sensor])
async def get_sensors():
    """Get all sensors."""
    return [
        Sensor(
            id=1,
            name="Weather Station Alpha",
            type="weather",
            location="London Central",
            latitude=51.5074,
            longitude=-0.1276,
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
    ]


@router.post("", response_model=Sensor, dependencies=[Depends(verify_api_key)])
async def create_sensor(sensor: SensorCreate):
    """Create a new sensor. Requires authentication."""
    sensor_id = await ecodata_agent.register_sensor(sensor)
    return Sensor(
        id=sensor_id,
        **sensor.dict(),
        is_active=True,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )


@router.get("/{sensor_id}/status")
async def get_sensor_status(sensor_id: int):
    """Get status for a specific sensor."""
    status = await ecodata_agent.get_sensor_status(sensor_id)
    if not status:
        raise HTTPException(status_code=404, detail="Sensor not found")
    return status


@router.get("/{sensor_id}/readings")
async def get_sensor_readings(
    sensor_id: int,
    limit: int = Query(100, ge=1, le=1000)
):
    """Get recent readings for a sensor."""
    readings = await ecodata_agent.get_sensor_readings(sensor_id, limit)
    return [dict(r) for r in readings]
