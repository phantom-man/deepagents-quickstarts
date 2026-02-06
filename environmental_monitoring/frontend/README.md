# Environmental Monitoring Dashboard

A comprehensive data exploration and analytics dashboard for environmental data from 24+ public APIs.

## Features

### 📊 Data Exploration
- **Multi-Source Data**: Access data from 24+ environmental APIs (air quality, water, weather, marine, earthquakes, wildfires, etc.)
- **Date/Time Range Selection**: Quick presets (1H, 6H, 24H, 7D, 30D, 1Y) and custom date/time pickers
- **Location-Based Queries**: Search by coordinates with configurable radius
- **Category Filtering**: Filter by environmental category (air, water, weather, climate, marine, etc.)

### 🔬 Advanced Analytics
- **Time Series Analysis**: Moving averages, smoothing, seasonal decomposition
- **Correlation Analysis**: Pearson, Spearman, Kendall correlations with significance testing
- **Anomaly Detection**: Z-score, IQR, rolling statistics, isolation forest methods
- **Trend Analysis**: Linear regression, Mann-Kendall, Sen's slope with forecasting

### 🔗 Cross-Domain Analysis
- **Dataset Linking**: Join datasets across environmental domains
- **Correlation Discovery**: Find relationships between different parameters
- **Multi-variate Analysis**: Analyze interactions between air, water, weather, and more

### 📋 Reporting
- **Report Templates**: Executive summary, detailed analysis, compliance, health advisory
- **Multiple Export Formats**: PDF, CSV, JSON, Excel, PNG, SVG
- **Scheduled Reports**: Daily, weekly, monthly automated report generation
- **Customizable Sections**: Choose which sections to include in reports

## Tech Stack

- **Framework**: Plotly Dash 2.14+
- **UI Components**: Dash Bootstrap Components
- **Visualization**: Plotly.js with interactive charts and maps
- **Data Processing**: Pandas, NumPy, SciPy
- **Export**: Kaleido (images), ReportLab (PDF)
- **Backend API**: FastAPI (separate service)

## Installation

### Local Development

```bash
# Clone the repository
cd environmental_monitoring/frontend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp .env.example .env
# Edit .env with your API URL

# Run the dashboard
python app.py
```

### Docker

```bash
# Build and run with Docker Compose (from parent directory)
docker-compose up frontend

# Or build standalone
docker build -t env-monitor-dashboard .
docker run -p 8050:8050 -e API_BASE_URL=https://your-api-url env-monitor-dashboard
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `API_BASE_URL` | Backend API URL | `http://localhost:8000` |
| `PORT` | Dashboard port | `8050` |
| `DEBUG` | Enable debug mode | `False` |
| `CACHE_DIR` | Cache directory | `.cache` |

### API Requirements

The dashboard expects a backend API with these endpoints:
- `GET /api/v1/hub` - Hub information
- `GET /api/v1/hub/sources` - Available data sources
- `GET /api/v1/hub/categories` - Data categories
- `GET /api/v1/hub/location` - Location-based aggregation
- `GET /api/v1/hub/analyze` - Cross-domain analysis
- `GET /health` - Health check

## Project Structure

```
frontend/
├── app.py                 # Main Dash application
├── config.py              # Configuration settings
├── api_client.py          # Backend API client
├── data_processing.py     # Data processing utilities
├── components/
│   ├── __init__.py
│   ├── charts.py          # Plotly chart components
│   └── layout.py          # Layout components
├── pages/
│   ├── __init__.py
│   ├── dashboard.py       # Main dashboard page
│   ├── explore.py         # Data exploration page
│   ├── analyze.py         # Analytics page
│   └── reports.py         # Reports page
├── requirements.txt       # Python dependencies
├── Dockerfile            # Container configuration
└── .env.example          # Environment template
```

## Usage

### Dashboard Page
- View key metrics and system status
- Quick location check for environmental conditions
- Overview map with data points
- Current AQI and weather conditions

### Explore Page
1. Select data categories (air, water, weather, etc.)
2. Enter location coordinates
3. Set time range
4. Click "Search Location"
5. View results in Map, Table, Charts, or Raw data tabs

### Analyze Page
1. Configure analysis parameters
2. Select analysis type (time series, correlation, anomaly, trend)
3. For cross-domain analysis, select primary and secondary datasets
4. Click "Run Analysis"
5. Review statistics, charts, and insights

### Reports Page
1. Select report type and format
2. Choose sections to include
3. Click "Generate Report" for preview
4. Download or schedule for regular delivery

## API Endpoints

The dashboard connects to the Environmental Monitoring API which aggregates data from:

- **Air Quality**: OpenAQ, EPA AirNow, AQICN
- **Water**: USGS Water Services
- **Weather**: Open-Meteo, OpenWeatherMap
- **Marine**: NOAA Buoy Center, Copernicus
- **Climate**: NOAA Climate, Global Carbon Atlas
- **Earthquakes**: USGS Earthquake Hazards
- **Wildfires**: NASA FIRMS, NIFC
- **Radiation**: Safecast, EPA RadNet
- **Biodiversity**: GBIF
- **Soil**: ISRIC SoilGrids

## License

MIT License - See LICENSE file for details
