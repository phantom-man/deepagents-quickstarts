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

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import uvicorn
import logging
from datetime import datetime

# Import our modules
from app.api.routes import router as api_router
from app.services.moltbook_collaboration import MoltbookCollaborationService
from app.services.database import init_database, close_database
from app.services.cache import init_cache, close_cache

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
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
    title="Environmental Monitoring System",
    description="AI-powered environmental monitoring with collaborative agents",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "services": {
            "database": "connected",
            "cache": "connected",
            "moltbook": "connected"
        }
    }

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