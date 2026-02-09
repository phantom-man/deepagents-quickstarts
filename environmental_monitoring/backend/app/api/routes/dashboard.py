"""
Dashboard statistics routes.
"""
from datetime import datetime

from fastapi import APIRouter

from app.schemas.schemas import DashboardStats, SensorStats

router = APIRouter()


@router.get("/stats", response_model=DashboardStats)
async def get_dashboard_stats():
    """Get dashboard statistics."""
    return DashboardStats(
        total_sensors=3,
        active_sensors=3,
        total_readings_today=1440,
        active_alerts=2,
        predictions_made_today=72,
        system_health="excellent"
    )


@router.get("/sensor-stats")
async def get_sensor_stats():
    """Get statistics for all sensors."""
    return [
        SensorStats(
            sensor_id=1,
            sensor_name="Weather Station Alpha",
            reading_count=480,
            last_reading=datetime.utcnow(),
            avg_value_24h=15.2,
            anomaly_count_24h=0
        ),
        SensorStats(
            sensor_id=2,
            sensor_name="Air Quality Monitor Beta",
            reading_count=480,
            last_reading=datetime.utcnow(),
            avg_value_24h=42.1,
            anomaly_count_24h=1
        ),
        SensorStats(
            sensor_id=3,
            sensor_name="Water Quality Sensor Gamma",
            reading_count=480,
            last_reading=datetime.utcnow(),
            avg_value_24h=7.1,
            anomaly_count_24h=0
        )
    ]
