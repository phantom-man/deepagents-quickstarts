"""
Database service for Environmental Monitoring System
"""

import os
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool
from contextlib import asynccontextmanager
import logging

logger = logging.getLogger(__name__)

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./environmental_monitoring.db")

# Create async engine
engine = create_async_engine(
    DATABASE_URL,
    echo=False,  # Set to True for SQL query logging
    poolclass=NullPool,  # Disable connection pooling for SQLite
)

# Create async session factory
async_session_factory = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

@asynccontextmanager
async def get_db_session():
    """Get database session with automatic cleanup."""
    session = async_session_factory()
    try:
        yield session
    finally:
        await session.close()

async def init_database():
    """Initialize database and create tables."""
    from app.models.models import Base

    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("✅ Database initialized successfully")
    except Exception as e:
        logger.error(f"❌ Failed to initialize database: {e}")
        raise

async def close_database():
    """Close database connections."""
    try:
        await engine.dispose()
        logger.info("✅ Database connections closed")
    except Exception as e:
        logger.error(f"❌ Error closing database: {e}")

async def get_sensor_readings(sensor_id: int, limit: int = 100):
    """Get recent sensor readings for a specific sensor."""
    from app.models.models import SensorReading

    async with get_db_session() as session:
        result = await session.execute(
            SensorReading.__table__.select()
            .where(SensorReading.sensor_id == sensor_id)
            .order_by(SensorReading.timestamp.desc())
            .limit(limit)
        )
        return result.fetchall()

async def get_active_alerts():
    """Get all active (unresolved) environmental events."""
    from app.models.models import EnvironmentalEvent

    async with get_db_session() as session:
        result = await session.execute(
            EnvironmentalEvent.__table__.select()
            .where(EnvironmentalEvent.is_resolved == False)
            .order_by(EnvironmentalEvent.timestamp.desc())
        )
        return result.fetchall()

async def get_recent_predictions(hours: int = 24):
    """Get predictions made in the last N hours."""
    from app.models.models import Prediction
    from datetime import datetime, timedelta

    cutoff_time = datetime.utcnow() - timedelta(hours=hours)

    async with get_db_session() as session:
        result = await session.execute(
            Prediction.__table__.select()
            .where(Prediction.timestamp >= cutoff_time)
            .order_by(Prediction.timestamp.desc())
        )
        return result.fetchall()

async def create_sensor_reading(sensor_id: int, value: float, unit: str,
                               quality_score: float = None, metadata: dict = None):
    """Create a new sensor reading."""
    from app.models.models import SensorReading
    from datetime import datetime

    reading = SensorReading(
        sensor_id=sensor_id,
        timestamp=datetime.utcnow(),
        value=value,
        unit=unit,
        quality_score=quality_score,
        metadata=metadata or {}
    )

    async with get_db_session() as session:
        session.add(reading)
        await session.commit()
        await session.refresh(reading)
        return reading

async def create_environmental_event(event_type: str, severity: str, title: str,
                                   description: str = None, latitude: float = None,
                                   longitude: float = None, metadata: dict = None):
    """Create a new environmental event."""
    from app.models.models import EnvironmentalEvent

    event = EnvironmentalEvent(
        event_type=event_type,
        severity=severity,
        title=title,
        description=description,
        latitude=latitude,
        longitude=longitude,
        metadata=metadata or {}
    )

    async with get_db_session() as session:
        session.add(event)
        await session.commit()
        await session.refresh(event)
        return event

async def log_agent_collaboration(session_id: str, agent_name: str, action: str,
                                target_agent: str = None, message: str = None,
                                metadata: dict = None):
    """Log agent collaboration activity."""
    from app.models.models import AgentCollaboration

    collaboration = AgentCollaboration(
        session_id=session_id,
        agent_name=agent_name,
        action=action,
        target_agent=target_agent,
        message=message,
        metadata=metadata or {}
    )

    async with get_db_session() as session:
        session.add(collaboration)
        await session.commit()
        await session.refresh(collaboration)
        return collaboration