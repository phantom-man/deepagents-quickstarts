"""
Collaboration routes for multi-agent coordination.
"""
from datetime import datetime

from fastapi import APIRouter, Depends, Query

from app.schemas.schemas import APIResponse
from app.security import verify_api_key
from app.services.moltbook_collaboration import moltbook_collaboration

router = APIRouter()


@router.post("/run", dependencies=[Depends(verify_api_key)])
async def trigger_collaboration():
    """
    Trigger a collaborative analysis session.
    
    Requires authentication as this is a resource-intensive operation.
    """
    await moltbook_collaboration.run_collaborative_analysis()
    return APIResponse(
        success=True,
        message="Collaborative analysis initiated",
        data={"session_id": moltbook_collaboration.session_id}
    )


@router.get("/status")
async def get_collaboration_status():
    """Get current collaboration status."""
    return await moltbook_collaboration.get_collaboration_status()


@router.get("/history")
async def get_collaboration_history(limit: int = Query(10, ge=1, le=100)):
    """Get collaboration history."""
    return [
        {
            "session_id": "session-001",
            "timestamp": datetime.utcnow().isoformat(),
            "agents_involved": ["ecodata", "climateml", "geospatial", "alertsystem"],
            "outcome": "success",
            "metrics": {
                "data_processed": 1440,
                "predictions_generated": 72,
                "alerts_created": 3
            }
        }
    ]
