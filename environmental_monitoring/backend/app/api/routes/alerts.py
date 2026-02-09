"""
Alert management routes.
"""

from fastapi import APIRouter, Query, Depends
from datetime import datetime

from app.schemas.schemas import Alert, AlertCreate
from app.agents.alertsystem_agent import alertsystem_agent
from app.security import verify_api_key

router = APIRouter()


@router.post("", response_model=Alert, dependencies=[Depends(verify_api_key)])
async def create_manual_alert(alert: AlertCreate):
    """Create a manual alert. Requires authentication."""
    alert_id = await alertsystem_agent.create_manual_alert(alert)
    return Alert(
        id=alert_id,
        **alert.dict(),
        status="pending",
        sent_at=None,
        created_at=datetime.utcnow()
    )


@router.get("/history")
async def get_alert_history(days: int = Query(7, ge=1, le=30)):
    """Get alert history."""
    return await alertsystem_agent.get_alert_history(days)


@router.get("/statistics")
async def get_alert_statistics():
    """Get alert statistics."""
    return await alertsystem_agent.get_alert_statistics()
