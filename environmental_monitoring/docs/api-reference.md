# Environmental Monitoring System - API Reference

## Base URL

- **Production:** `https://env-monitor-api-758343025648.us-central1.run.app/api/v1`
- **Local:** `http://localhost:8000/api/v1`

## Authentication

Most endpoints are public, but some require an API key:

```bash
# Header authentication
curl -H "X-API-Key: your-api-key" https://api.example.com/api/v1/endpoint

# Bearer token authentication
curl -H "Authorization: Bearer your-api-key" https://api.example.com/api/v1/endpoint
```

## Rate Limiting

| Endpoint Type | Limit | Period |
|---------------|-------|--------|
| General | 100 calls | 60 seconds |
| Hub proxy | 10 calls | 60 seconds |
| Metadata | 30 calls | 60 seconds |

Rate limit headers returned:
- `X-RateLimit-Remaining`: Calls remaining
- `Retry-After`: Seconds until reset (when limited)

---

## Health Endpoints

### GET /ok
Simple liveness check.

**Response:**
```json
{"status": "ok"}
```

### GET /ready
Readiness probe - checks if service can accept traffic.

**Response (200):**
```json
{"status": "ready"}
```

**Response (503):**
```json
{"detail": "Service not ready"}
```

### GET /health
Detailed health check with dependency status.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00Z",
  "version": "1.0.0",
  "environment": "production",
  "services": {
    "database": "connected",
    "cache": "connected",
    "moltbook": "connected"
  }
}
```

---

## Data Hub Endpoints

### GET /api/v1/hub
Get hub information and available endpoints.

**Response:**
```json
{
  "name": "Environmental Data Aggregation Hub",
  "description": "One-stop shop for environmental data from 15+ public APIs",
  "version": "1.0.0",
  "total_sources": 15,
  "categories": {...},
  "endpoints": {...}
}
```

### GET /api/v1/hub/sources
List all available data sources.

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| category | string | Filter by category (optional) |

**Example:**
```bash
curl "https://api.example.com/api/v1/hub/sources?category=weather"
```

**Response:**
```json
{
  "total": 3,
  "filter": "weather",
  "sources": [
    {
      "id": "open_meteo",
      "name": "Open-Meteo",
      "category": "weather",
      "base_url": "https://api.open-meteo.com/v1"
    }
  ]
}
```

### GET /api/v1/hub/categories
List all data categories.

**Response:**
```json
{
  "categories": {
    "air_quality": ["openaq", "airnow"],
    "weather": ["open_meteo"],
    "earthquakes": ["usgs_earthquake"]
  },
  "available_categories": ["air_quality", "water", "weather", ...]
}
```

### GET /api/v1/hub/proxy/{source_id}
Proxy a request to an external data source.

**Path Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| source_id | string | Data source identifier |

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| endpoint | string | API endpoint path (required) |

**Example:**
```bash
curl "https://api.example.com/api/v1/hub/proxy/open_meteo?endpoint=/forecast?latitude=37.77&longitude=-122.42"
```

### GET /api/v1/hub/location
Aggregate all environmental data for a location.

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| lat | float | - | Latitude (-90 to 90) |
| lon | float | - | Longitude (-180 to 180) |
| radius_km | float | 50.0 | Search radius in km |
| categories | string | - | Comma-separated categories |

**Example:**
```bash
curl "https://api.example.com/api/v1/hub/location?lat=37.77&lon=-122.42&radius_km=25&categories=weather,earthquakes"
```

**Response:**
```json
{
  "location": {"latitude": 37.77, "longitude": -122.42},
  "timestamp": "2024-01-15T10:30:00Z",
  "data": {
    "weather": {...},
    "earthquakes": {...}
  }
}
```

### GET /api/v1/hub/quick
Quick environmental check for a location.

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| lat | float | 37.7749 | Latitude |
| lon | float | -122.4194 | Longitude |

**Response:**
```json
{
  "location": {"latitude": 37.7749, "longitude": -122.4194},
  "timestamp": "2024-01-15T10:30:00Z",
  "summary": {
    "weather": {
      "temperature_c": 15.2,
      "windspeed_kmh": 12.5
    },
    "recent_earthquakes_nearby": 0
  },
  "quick_status": "✅ No immediate hazards detected"
}
```

### GET /api/v1/hub/analyze
Analyze environmental correlations for a location.

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| lat | float | - | Latitude |
| lon | float | - | Longitude |
| days | int | 7 | Days of history (1-30) |

**Response:**
```json
{
  "analysis": {
    "correlations_found": [...],
    "insights": [...],
    "recommendations": [...]
  }
}
```

### GET /api/v1/hub/analyze/rules
Get correlation rules used for analysis.

**Response:**
```json
{
  "rules": [...],
  "description": "Rules used to find connections between environmental data"
}
```

---

## Sensor Endpoints

### GET /api/v1/sensors
List all sensors.

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| sensor_type | string | Filter by type |
| location | string | Filter by location |
| status | string | Filter by status |
| skip | int | Pagination offset |
| limit | int | Results per page (max 100) |

### POST /api/v1/sensors
Create a new sensor.

**Request Body:**
```json
{
  "name": "Temperature Sensor A",
  "sensor_type": "temperature",
  "location": "Building A",
  "latitude": 37.77,
  "longitude": -122.42,
  "metadata": {}
}
```

### GET /api/v1/sensors/{sensor_id}
Get sensor by ID.

### PUT /api/v1/sensors/{sensor_id}
Update sensor.

### DELETE /api/v1/sensors/{sensor_id}
Delete sensor.

### POST /api/v1/sensors/{sensor_id}/readings
Submit a reading for a sensor.

**Request Body:**
```json
{
  "value": 23.5,
  "unit": "celsius",
  "timestamp": "2024-01-15T10:30:00Z"
}
```

### GET /api/v1/sensors/{sensor_id}/readings
Get readings for a sensor.

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| start_time | datetime | Start of time range |
| end_time | datetime | End of time range |
| limit | int | Max results |

---

## Prediction Endpoints

### POST /api/v1/predictions/forecast
Generate forecast predictions.

**Request Body:**
```json
{
  "sensor_ids": ["sensor-1", "sensor-2"],
  "horizon_hours": 24,
  "model": "arima"
}
```

### GET /api/v1/predictions/anomalies
Get detected anomalies.

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| sensor_id | string | Filter by sensor |
| severity | string | Filter by severity |
| since | datetime | Start time |

---

## Alert Endpoints

### GET /api/v1/alerts
List alerts.

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| severity | string | Filter by severity |
| acknowledged | bool | Filter by acknowledgment |
| limit | int | Max results |

### POST /api/v1/alerts
Create alert.

### GET /api/v1/alerts/{alert_id}
Get alert by ID.

### PUT /api/v1/alerts/{alert_id}/acknowledge
Acknowledge an alert.

---

## GIS Endpoints

### GET /api/v1/gis/sensors
Get sensors as GeoJSON.

### GET /api/v1/gis/heatmap
Get heatmap data.

**Query Parameters:**
| Parameter | Type | Description |
|-----------|------|-------------|
| metric | string | Metric to visualize |
| resolution | float | Grid resolution |

### POST /api/v1/gis/spatial-query
Perform spatial query.

**Request Body:**
```json
{
  "geometry": {
    "type": "Polygon",
    "coordinates": [...]
  },
  "query_type": "within"
}
```

---

## Error Responses

All errors follow this format:

```json
{
  "error_code": "VALIDATION_ERROR",
  "message": "Invalid coordinates provided",
  "status_code": 400,
  "details": {"latitude": 100, "longitude_error": "Must be between -180 and 180"},
  "correlation_id": "abc-123-def"
}
```

### Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| VALIDATION_ERROR | 400 | Invalid input |
| INVALID_COORDINATES | 400 | Lat/lon out of range |
| AUTHENTICATION_FAILED | 401 | Missing or invalid API key |
| AUTHORIZATION_FAILED | 403 | Insufficient permissions |
| RESOURCE_NOT_FOUND | 404 | Resource doesn't exist |
| RATE_LIMIT_EXCEEDED | 429 | Too many requests |
| EXTERNAL_SERVICE_ERROR | 502 | External API failure |
| DATA_SOURCE_TIMEOUT | 504 | External API timeout |
| INTERNAL_ERROR | 500 | Unexpected server error |

---

## Interactive Documentation

When running locally with `ENVIRONMENT != production`:

- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc
