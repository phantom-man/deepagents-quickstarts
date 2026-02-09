# Environmental Monitoring System - Architecture

## Overview

The Environmental Monitoring System is a collaborative AI-powered platform that aggregates environmental data from 15+ public APIs into a unified interface. It features:

- **Real-time data aggregation** from multiple environmental sources
- **ML-powered predictions** for environmental trends
- **GIS integration** for spatial analysis
- **Alerting system** for environmental hazards
- **Multi-agent collaboration** via Moltbook platform

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        ENVIRONMENTAL MONITORING SYSTEM                   │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐              │
│  │   Frontend   │    │   Backend    │    │   Database   │              │
│  │  Dash/Plotly │◄──►│   FastAPI    │◄──►│   SQLite     │              │
│  │  (Cloud Run) │    │  (Cloud Run) │    │  (Async)     │              │
│  └──────────────┘    └──────────────┘    └──────────────┘              │
│         │                   │                                           │
│         │                   ▼                                           │
│         │          ┌──────────────────────────────────────┐            │
│         │          │        Data Aggregation Hub          │            │
│         │          │   (15+ External API Integrations)    │            │
│         │          └──────────────────────────────────────┘            │
│         │                   │                                           │
│         │    ┌──────────────┼──────────────┬──────────────┐            │
│         │    ▼              ▼              ▼              ▼            │
│         │ ┌──────┐    ┌──────────┐   ┌──────────┐   ┌──────────┐      │
│         │ │OpenAQ│    │Open-Meteo│   │   USGS   │   │   NOAA   │      │
│         │ │(Air) │    │(Weather) │   │(Quakes)  │   │ (Marine) │      │
│         │ └──────┘    └──────────┘   └──────────┘   └──────────┘      │
│         │                                                               │
│         └──────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                    Specialized AI Agents                         │   │
│  ├─────────────┬─────────────┬─────────────┬─────────────┐         │   │
│  │  EcoData    │  ClimateML  │ GeoSpatial  │ AlertSystem │         │   │
│  │  Agent      │  Agent      │  Agent      │  Agent      │         │   │
│  │ (Ingestion) │ (Prediction)│ (Analysis)  │ (Alerting)  │         │   │
│  └─────────────┴─────────────┴─────────────┴─────────────┘         │   │
│                           │                                          │   │
│                           ▼                                          │   │
│                  ┌──────────────────┐                               │   │
│                  │     Moltbook     │                               │   │
│                  │  Collaboration   │                               │   │
│                  │    Platform      │                               │   │
│                  └──────────────────┘                               │   │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

## Component Details

### Backend (FastAPI)

**Location:** `backend/`

The backend is built with FastAPI and provides:

- **RESTful API** for all environmental data operations
- **Async support** for high-concurrency data aggregation
- **Rate limiting** to prevent abuse
- **API key authentication** for sensitive endpoints
- **Structured logging** with correlation IDs

#### Route Modules

| Module | Prefix | Description |
|--------|--------|-------------|
| `sensors.py` | `/sensors` | Sensor CRUD operations |
| `predictions.py` | `/predictions` | ML model predictions |
| `gis.py` | `/gis` | Spatial analysis endpoints |
| `alerts.py` | `/alerts` | Alert management |
| `dashboard.py` | `/dashboard` | Dashboard statistics |
| `hub.py` | `/hub` | Data aggregation hub |
| `data_sources.py` | `/data-sources` | Data source management |
| `collaboration.py` | `/collaboration` | Agent collaboration |
| `system.py` | `/system` | Admin operations |

### Frontend (Dash/Plotly)

**Location:** `frontend/`

Interactive dashboard built with Plotly Dash featuring:

- Real-time environmental data visualization
- Interactive maps with earthquake and weather overlays
- Time range selection (24h, 7d, 30d, custom)
- Responsive design for desktop and mobile

### Data Aggregation Hub

**Location:** `backend/app/services/data_aggregator.py`

The hub aggregates data from 15+ external APIs:

| Category | Sources |
|----------|---------|
| Air Quality | OpenAQ, AirNow, PurpleAir |
| Weather | Open-Meteo, OpenWeatherMap |
| Earthquakes | USGS Earthquake API |
| Marine | NOAA, Copernicus Marine |
| Climate | NOAA Climate Data |
| Wildfires | NIFC, NASA FIRMS |
| Biodiversity | GBIF, iNaturalist |
| Radiation | EPA RadNet |
| Soil | USDA |
| Water | USGS Water Services |

## Security Architecture

### Authentication

```
┌─────────────────────────────────────────────────────────────┐
│                   Authentication Flow                        │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Request ──► Check Headers ──► Validate Key ──► Grant Access │
│                   │                 │                        │
│                   ▼                 ▼                        │
│             X-API-Key         API_KEY env var               │
│                or              ADMIN_API_KEY                │
│          Authorization:                                      │
│          Bearer <token>                                      │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### Rate Limiting

- **Default:** 100 requests per minute per IP
- **Hub proxy:** 10 requests per minute (resource-intensive)
- **Metadata endpoints:** 30 requests per minute

### Protected Endpoints

| Endpoint | Protection Level |
|----------|-----------------|
| `/api/v1/system/reset` | Admin + blocked in production |
| `/api/v1/data-sources/ingestion/*` | API key required |
| `/api/v1/collaboration/run` | API key required |

## Logging Architecture

### Structured Logging Format

```json
{
  "timestamp": "2024-01-15T10:30:00Z",
  "logger": "main",
  "level": "INFO",
  "correlation_id": "abc-123-def",
  "message": "Request processed"
}
```

### Correlation ID Flow

1. Client sends `X-Correlation-ID` header (optional)
2. Server generates UUID if not provided
3. ID propagates through all log entries
4. ID returned in response header

## Error Handling

### Custom Exceptions

```python
EnvironmentalMonitoringError (base)
├── ValidationError (400)
│   ├── InvalidCoordinatesError
│   └── DataFormatError
├── ResourceNotFoundError (404)
│   ├── SensorNotFoundError
│   └── DataSourceNotFoundError
├── AuthenticationError (401)
├── AuthorizationError (403)
├── RateLimitExceededError (429)
├── ExternalServiceError (502)
│   ├── DataSourceConnectionError
│   └── DataSourceTimeoutError (504)
└── DatabaseError (500)
```

### Error Response Format

```json
{
  "error_code": "SENSOR_NOT_FOUND",
  "message": "Sensor 'sensor-123' not found",
  "status_code": 404,
  "details": {"sensor_id": "sensor-123"},
  "correlation_id": "abc-123-def"
}
```

## Configuration

All configuration is managed through environment variables with Pydantic Settings:

```python
# app/config.py
class Settings(BaseSettings):
    # Application
    app_name: str = "Environmental Monitoring System"
    environment: str = "development"
    
    # Security
    api_key: str = "change-me-in-production"
    admin_api_key: str = "change-me-admin"
    cors_origins: str = "*"
    
    # Rate Limiting
    rate_limit_calls: int = 100
    rate_limit_period: int = 60
    
    # External APIs
    openaq_api_key: Optional[str] = None
    openweathermap_api_key: Optional[str] = None
```

## Deployment

### Cloud Run Deployment

Both frontend and backend are deployed to Google Cloud Run:

- **API:** `env-monitor-api-*.run.app`
- **Dashboard:** `env-monitor-dashboard-*.run.app`

See [deployment.md](deployment.md) for detailed deployment instructions.
