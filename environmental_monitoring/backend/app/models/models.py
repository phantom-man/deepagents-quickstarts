"""
Database models for Environmental Monitoring System
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Boolean, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class Sensor(Base):
    """Environmental sensor model."""
    __tablename__ = "sensors"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    type = Column(String(50), nullable=False)  # temperature, humidity, air_quality, etc.
    location = Column(String(200), nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    altitude = Column(Float, nullable=True)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    readings = relationship("SensorReading", back_populates="sensor")

class SensorReading(Base):
    """Sensor reading model."""
    __tablename__ = "sensor_readings"

    id = Column(Integer, primary_key=True, index=True)
    sensor_id = Column(Integer, ForeignKey("sensors.id"), nullable=False)
    timestamp = Column(DateTime, nullable=False, index=True)
    value = Column(Float, nullable=False)
    unit = Column(String(20), nullable=False)
    quality_score = Column(Float, nullable=True)  # 0-1 quality indicator
    extra_data = Column(JSON, nullable=True)  # Additional sensor-specific data

    # Relationships
    sensor = relationship("Sensor", back_populates="readings")

class EnvironmentalEvent(Base):
    """Environmental event/incident model."""
    __tablename__ = "environmental_events"

    id = Column(Integer, primary_key=True, index=True)
    event_type = Column(String(50), nullable=False)  # anomaly, alert, prediction
    severity = Column(String(20), nullable=False)  # low, medium, high, critical
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    timestamp = Column(DateTime, nullable=False, default=datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)
    is_resolved = Column(Boolean, default=False)
    extra_data = Column(JSON, nullable=True)

class Prediction(Base):
    """ML prediction model."""
    __tablename__ = "predictions"

    id = Column(Integer, primary_key=True, index=True)
    sensor_id = Column(Integer, ForeignKey("sensors.id"), nullable=False)
    prediction_type = Column(String(50), nullable=False)  # temperature, pollution, etc.
    timestamp = Column(DateTime, nullable=False, index=True)
    predicted_value = Column(Float, nullable=False)
    confidence_score = Column(Float, nullable=True)  # 0-1 confidence level
    prediction_window = Column(Integer, nullable=False)  # hours ahead
    model_version = Column(String(50), nullable=True)
    features_used = Column(JSON, nullable=True)  # Features used in prediction

    # Relationships
    sensor = relationship("Sensor")

class Alert(Base):
    """Alert/notification model."""
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(Integer, ForeignKey("environmental_events.id"), nullable=True)
    alert_type = Column(String(50), nullable=False)  # email, sms, webhook, etc.
    recipient = Column(String(200), nullable=False)
    subject = Column(String(200), nullable=False)
    message = Column(Text, nullable=False)
    status = Column(String(20), default="pending")  # pending, sent, failed
    sent_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    event = relationship("EnvironmentalEvent")

class GISLayer(Base):
    """GIS layer model for spatial data."""
    __tablename__ = "gis_layers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    layer_type = Column(String(50), nullable=False)  # vector, raster, point, polygon
    description = Column(Text, nullable=True)
    geojson_data = Column(JSON, nullable=True)  # For vector data
    raster_path = Column(String(500), nullable=True)  # For raster data
    bounds = Column(JSON, nullable=True)  # Bounding box coordinates
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class AgentCollaboration(Base):
    """Track agent collaborations and communications."""
    __tablename__ = "agent_collaborations"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(100), nullable=False, index=True)
    agent_name = Column(String(50), nullable=False)
    action = Column(String(100), nullable=False)
    target_agent = Column(String(50), nullable=True)
    message = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    extra_data = Column(JSON, nullable=True)