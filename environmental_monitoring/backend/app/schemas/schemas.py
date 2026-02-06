"""
Pydantic schemas for API validation and serialization
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

# Sensor schemas
class SensorBase(BaseModel):
    name: str = Field(..., max_length=100)
    type: str = Field(..., max_length=50)
    location: str = Field(..., max_length=200)
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    altitude: Optional[float] = None
    description: Optional[str] = None

class SensorCreate(SensorBase):
    pass

class SensorUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=100)
    type: Optional[str] = Field(None, max_length=50)
    location: Optional[str] = Field(None, max_length=200)
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)
    altitude: Optional[float] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None

class Sensor(SensorBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# Sensor reading schemas
class SensorReadingBase(BaseModel):
    sensor_id: int
    timestamp: datetime
    value: float
    unit: str = Field(..., max_length=20)
    quality_score: Optional[float] = Field(None, ge=0, le=1)
    metadata: Optional[Dict[str, Any]] = None

class SensorReadingCreate(SensorReadingBase):
    pass

class SensorReading(SensorReadingBase):
    id: int

    class Config:
        from_attributes = True

# Environmental event schemas
class EnvironmentalEventBase(BaseModel):
    event_type: str = Field(..., max_length=50)
    severity: str = Field(..., max_length=20)
    title: str = Field(..., max_length=200)
    description: Optional[str] = None
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)
    metadata: Optional[Dict[str, Any]] = None

class EnvironmentalEventCreate(EnvironmentalEventBase):
    pass

class EnvironmentalEventUpdate(BaseModel):
    severity: Optional[str] = Field(None, max_length=20)
    title: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = None
    latitude: Optional[float] = Field(None, ge=-90, le=90)
    longitude: Optional[float] = Field(None, ge=-180, le=180)
    resolved_at: Optional[datetime] = None
    is_resolved: Optional[bool] = None
    metadata: Optional[Dict[str, Any]] = None

class EnvironmentalEvent(EnvironmentalEventBase):
    id: int
    timestamp: datetime
    resolved_at: Optional[datetime] = None
    is_resolved: bool

    class Config:
        from_attributes = True

# Prediction schemas
class PredictionBase(BaseModel):
    sensor_id: int
    prediction_type: str = Field(..., max_length=50)
    timestamp: datetime
    predicted_value: float
    confidence_score: Optional[float] = Field(None, ge=0, le=1)
    prediction_window: int = Field(..., gt=0)  # hours ahead
    model_version: Optional[str] = Field(None, max_length=50)
    features_used: Optional[Dict[str, Any]] = None

class PredictionCreate(PredictionBase):
    pass

class Prediction(PredictionBase):
    id: int

    class Config:
        from_attributes = True

# Alert schemas
class AlertBase(BaseModel):
    event_id: Optional[int] = None
    alert_type: str = Field(..., max_length=50)
    recipient: str = Field(..., max_length=200)
    subject: str = Field(..., max_length=200)
    message: str

class AlertCreate(AlertBase):
    pass

class Alert(AlertBase):
    id: int
    status: str
    sent_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True

# GIS layer schemas
class GISLayerBase(BaseModel):
    name: str = Field(..., max_length=100)
    layer_type: str = Field(..., max_length=50)
    description: Optional[str] = None
    geojson_data: Optional[Dict[str, Any]] = None
    raster_path: Optional[str] = Field(None, max_length=500)
    bounds: Optional[Dict[str, Any]] = None

class GISLayerCreate(GISLayerBase):
    pass

class GISLayerUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=100)
    layer_type: Optional[str] = Field(None, max_length=50)
    description: Optional[str] = None
    geojson_data: Optional[Dict[str, Any]] = None
    raster_path: Optional[str] = Field(None, max_length=500)
    bounds: Optional[Dict[str, Any]] = None

class GISLayer(GISLayerBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# Agent collaboration schemas
class AgentCollaborationBase(BaseModel):
    session_id: str = Field(..., max_length=100)
    agent_name: str = Field(..., max_length=50)
    action: str = Field(..., max_length=100)
    target_agent: Optional[str] = Field(None, max_length=50)
    message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class AgentCollaborationCreate(AgentCollaborationBase):
    pass

class AgentCollaboration(AgentCollaborationBase):
    id: int
    timestamp: datetime

    class Config:
        from_attributes = True

# API response schemas
class APIResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Any] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class PaginatedResponse(BaseModel):
    items: List[Any]
    total: int
    page: int
    size: int
    pages: int

# Dashboard data schemas
class DashboardStats(BaseModel):
    total_sensors: int
    active_sensors: int
    total_readings_today: int
    active_alerts: int
    predictions_made_today: int
    system_health: str

class SensorStats(BaseModel):
    sensor_id: int
    sensor_name: str
    reading_count: int
    last_reading: Optional[datetime]
    avg_value_24h: Optional[float]
    anomaly_count_24h: int