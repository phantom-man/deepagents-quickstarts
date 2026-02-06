# 🌱 Environmental Monitoring System

A comprehensive AI-powered environmental monitoring system built with collaborative agents using the Moltbook platform. This system demonstrates advanced multi-agent coordination for real-time environmental data analysis, prediction, and alerting.

## 🤖 Agent Architecture

The system consists of four specialized AI agents working collaboratively:

### EcoData Agent

- **Role**: Real-time sensor data ingestion and processing
- **Capabilities**:
  - API polling from environmental sensors
  - Data validation and cleaning
  - Sensor health monitoring
  - Real-time data streaming

### ClimateML Agent

- **Role**: ML models for environmental prediction and anomaly detection
- **Capabilities**:
  - Time series forecasting
  - Anomaly detection with Isolation Forests
  - Model performance monitoring
  - Automated model retraining

### GeoSpatial Agent

- **Role**: GIS integration and spatial analysis
- **Capabilities**:
  - Spatial data processing with GeoPandas
  - Interactive map generation with Folium
  - Sensor coverage analysis
  - Environmental zone classification

### AlertSystem Agent

- **Role**: Real-time alerting and reporting system
- **Capabilities**:
  - Multi-channel notifications (Email, SMS, Slack, Webhooks)
  - Automated report generation
  - Alert escalation protocols
  - Subscription management

## 🏗️ System Architecture

```text
┌─────────────────┐    ┌─────────────────┐
│   EcoData       │    │   ClimateML     │
│   Agent         │    │   Agent         │
│                 │    │                 │
│ • Sensor Data   │    │ • Predictions   │
│ • Validation    │    │ • Anomalies     │
│ • Streaming     │    │ • ML Models     │
└─────────┬───────┘    └─────────┬───────┘
          │                     │
          └─────────┬───────────┘
                    │
          ┌─────────▼───────────┐
          │                     │
          │  Moltbook           │
          │  Collaboration      │
          │  Service            │
          │                     │
          └─────────┬───────────┘
                    │
          ┌─────────▼───────────┐
          │                     │
          │   GeoSpatial        │
          │   Agent             │
          │                     │
          │ • GIS Analysis      │
          │ • Maps              │
          │ • Spatial Queries   │
          └─────────┬───────────┘
                    │
          ┌─────────▼───────────┐
          │                     │
          │  AlertSystem        │
          │  Agent              │
          │                     │
          │ • Notifications     │
          │ • Reports           │
          │ • Escalation        │
          └─────────────────────┘
```

## 🚀 Quick Start

### Prerequisites

- Python 3.9+
- PostgreSQL (optional, uses SQLite by default)
- Redis (optional, uses in-memory cache by default)

### Installation

1. **Clone the repository**

   ```bash
   git clone <repository-url>
   cd environmental_monitoring
   ```

2. **Install dependencies**

   ```bash
   cd backend
   pip install -r requirements.txt
   ```

3. **Configure environment variables**

   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

4. **Initialize the database**

   ```bash
   python -c "from app.services.database import init_database; import asyncio; asyncio.run(init_database())"
   ```

5. **Run the application**
   ```bash
   python main.py
   ```

The API will be available at `http://localhost:8000`

## 📡 API Endpoints

### Sensors

- `GET /api/v1/sensors` - List all sensors
- `POST /api/v1/sensors` - Register new sensor
- `GET /api/v1/sensors/{id}/status` - Get sensor status
- `GET /api/v1/sensors/{id}/readings` - Get sensor readings


### ML Predictions

- `GET /api/v1/predictions/sensor/{id}` - Get predictions for sensor
- `GET /api/v1/ml/performance` - Get model performance metrics

### GIS & Spatial
- `GET /api/v1/gis/analysis/{type}` - Get spatial analysis
- `GET /api/v1/gis/map` - Get interactive environmental map
- `GET /api/v1/gis/nearest-sensor` - Find nearest sensor to location
- `GET /api/v1/gis/zone-info` - Get environmental zone info

### Alerts
- `POST /api/v1/alerts` - Create manual alert
- `GET /api/v1/alerts/history` - Get alert history
- `GET /api/v1/alerts/statistics` - Get alert statistics

### Dashboard
- `GET /api/v1/dashboard/stats` - Get dashboard statistics
- `GET /api/v1/dashboard/sensor-stats` - Get sensor statistics

### Collaboration
- `POST /api/v1/collaboration/run` - Trigger collaborative analysis
- `GET /api/v1/collaboration/status` - Get collaboration status
- `GET /api/v1/collaboration/history` - Get collaboration history

## 🔧 Configuration

### Environment Variables

```bash
# Database
DATABASE_URL=sqlite+aiosqlite:///./environmental_monitoring.db

# Redis Cache (optional)
REDIS_URL=redis://localhost:6379

# Moltbook Integration
MOLTBOOK_API_KEY=your_api_key
MOLTBOOK_AGENT_NAME=EnvironmentalMonitor

# Email Configuration
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_password

# SMS Configuration (Twilio)
TWILIO_ACCOUNT_SID=your_account_sid
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_FROM_NUMBER=+1234567890

# Slack Configuration
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK
```

## 🧪 Testing

Run the test suite:

```bash
cd backend
pytest tests/ -v --cov=app
```

Run specific agent tests:

```bash
pytest tests/test_agents.py::TestEcoDataAgent -v
pytest tests/test_agents.py::TestClimateMLAgent -v
```

## 📊 Data Models

### Sensor Data
- **Temperature**: -50°C to 60°C
- **Humidity**: 0-100%
- **Air Quality**: PM2.5, PM10, NO2, SO2, CO, O3
- **Water Quality**: pH (0-14), dissolved oxygen, turbidity

### Prediction Models
- **Temperature**: Exponential smoothing
- **Air Quality**: Moving average with trend analysis
- **Water Quality**: Linear regression with seasonal adjustment

### Spatial Data
- **Coordinate System**: WGS84 (EPSG:4326)
- **Layers**: Sensor locations, environmental zones, boundaries
- **Formats**: GeoJSON, Shapefile, raster data

## 🚨 Alert System

### Alert Types
- **Anomaly**: Statistical outliers detected
- **Threshold**: Environmental parameters exceed limits
- **System**: Sensor failures or communication issues
- **Maintenance**: Scheduled maintenance notifications

### Alert Channels
- **Email**: SMTP-based notifications
- **SMS**: Twilio integration
- **Slack**: Webhook-based team notifications
- **Webhooks**: Custom integrations

### Escalation Protocol
1. **Low**: Email notification only
2. **Medium**: Email + Slack notification
3. **High**: Email + Slack + SMS
4. **Critical**: All channels + emergency contacts

## 🤝 Moltbook Collaboration

The system uses Moltbook for agent coordination:

### Collaboration Phases
1. **Data Collection**: EcoData agent gathers sensor data
2. **Analysis**: ClimateML agent processes and predicts
3. **Spatial Analysis**: GeoSpatial agent maps and analyzes
4. **Alert Generation**: AlertSystem agent notifies stakeholders

### Communication Protocol
```
COLLAB:request_data     - Request data from another agent
COLLAB:share_findings   - Share analysis results
COLLAB:alert_triggered  - Notify of alerts/anomalies
COLLAB:status_update    - Report agent status changes
```

## 📈 Monitoring & Analytics

### System Metrics
- **Data Ingestion Rate**: Readings per minute
- **Prediction Accuracy**: MAE, RMSE for forecasts
- **Alert Response Time**: Time to notification
- **System Uptime**: 99.9% target

### Agent Performance
- **EcoData**: Sensor connectivity, data quality
- **ClimateML**: Model accuracy, prediction coverage
- **GeoSpatial**: Map generation time, query performance
- **AlertSystem**: Delivery success rate, response times

## 🔒 Security

### Data Protection
- **Encryption**: TLS 1.3 for data in transit
- **Access Control**: API key authentication
- **Data Validation**: Input sanitization and validation

### Agent Security
- **Isolated Execution**: Agents run in separate processes
- **Resource Limits**: CPU and memory restrictions
- **Audit Logging**: All agent actions logged

## 📚 Documentation

### API Documentation
Interactive API docs available at `http://localhost:8000/docs`

### Agent Documentation
- `docs/ecodata_agent.md` - EcoData agent specifications
- `docs/climateml_agent.md` - ClimateML agent specifications
- `docs/geospatial_agent.md` - GeoSpatial agent specifications
- `docs/alertsystem_agent.md` - AlertSystem agent specifications

### System Architecture
- `docs/architecture.md` - System design and components
- `docs/deployment.md` - Deployment and scaling guide
- `docs/monitoring.md` - Monitoring and alerting setup

## 🚀 Deployment

### Docker Deployment
```bash
docker build -t environmental-monitor .
docker run -p 8000:8000 environmental-monitor
```

### Kubernetes Deployment
```bash
kubectl apply -f k8s/
```

### Cloud Deployment
- **AWS**: ECS Fargate with RDS and ElastiCache
- **GCP**: Cloud Run with Cloud SQL and Memorystore
- **Azure**: Container Apps with PostgreSQL and Redis

## 🤝 Contributing

### Development Workflow
1. Fork the repository
2. Create a feature branch
3. Make changes with tests
4. Submit pull request

### Agent Development
- Follow agent interface specifications
- Include comprehensive tests
- Update documentation
- Test collaboration scenarios

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- **Moltbook** for the agent collaboration platform
- **DeepAgents** framework for multi-agent orchestration
- **Open-source ML libraries** for prediction capabilities
- **GIS community** for spatial analysis tools

---

**Built with ❤️ using collaborative AI agents on the Moltbook platform**