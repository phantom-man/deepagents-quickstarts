"""
ML Prediction routes.
"""

from fastapi import APIRouter, Query

from app.agents.climateml_agent import climateml_agent

router = APIRouter()


@router.get("/sensor/{sensor_id}")
async def get_sensor_predictions(
    sensor_id: int,
    hours: int = Query(24, ge=1, le=168)
):
    """Get predictions for a sensor."""
    predictions = await climateml_agent.get_predictions(sensor_id, hours)
    return predictions


@router.get("/ml/performance")
async def get_ml_performance():
    """Get ML model performance metrics."""
    return await climateml_agent.get_model_performance()
