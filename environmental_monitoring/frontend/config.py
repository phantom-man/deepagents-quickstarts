"""
Configuration for Environmental Monitoring Dashboard
"""
import os
from dotenv import load_dotenv

load_dotenv()

# API Configuration
API_BASE_URL = os.getenv("API_BASE_URL", "https://env-monitor-api-758343025648.us-central1.run.app")
API_TIMEOUT = int(os.getenv("API_TIMEOUT", "30"))

# Google Maps Configuration
GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY", "")
GOOGLE_MAPS_REGION = os.getenv("GOOGLE_MAPS_REGION", "us")

# Google Data Commons Configuration
DATA_COMMONS_API_KEY = os.getenv(
    "DATA_COMMONS_API_KEY",
    "AIzaSyCTI4Xz-UW_G2Q2RfknhcfdAnTHq5X5XuI",  # public trial key
)
DC_TIMEOUT = float(os.getenv("DC_TIMEOUT", "15"))

# Cache Configuration
CACHE_DIR = os.getenv("CACHE_DIR", ".cache")
CACHE_TTL_SHORT = 300  # 5 minutes for real-time data
CACHE_TTL_MEDIUM = 3600  # 1 hour for historical data
CACHE_TTL_LONG = 86400  # 24 hours for static data

# Dashboard Configuration
DASHBOARD_TITLE = "Environmental Monitoring Dashboard"
DASHBOARD_SUBTITLE = "Real-time environmental data exploration and analysis"

# Theme Configuration
THEME = {
    "primary": "#2E86AB",  # Blue
    "secondary": "#A23B72",  # Purple
    "success": "#28A745",  # Green
    "warning": "#F18F01",  # Orange
    "danger": "#C73E1D",  # Red
    "info": "#17A2B8",  # Cyan
    "background": "#F8F9FA",
    "surface": "#FFFFFF",
    "text": "#212529",
    "text_secondary": "#6C757D"
}

# AQI Color Scale (EPA Standard)
AQI_COLORS = {
    "good": "#00E400",  # 0-50
    "moderate": "#FFFF00",  # 51-100
    "unhealthy_sensitive": "#FF7E00",  # 101-150
    "unhealthy": "#FF0000",  # 151-200
    "very_unhealthy": "#8F3F97",  # 201-300
    "hazardous": "#7E0023"  # 301+
}

# Data Categories
DATA_CATEGORIES = [
    {"id": "air_quality", "name": "Air Quality", "icon": "💨"},
    {"id": "water", "name": "Water Quality", "icon": "💧"},
    {"id": "weather", "name": "Weather", "icon": "🌤️"},
    {"id": "climate", "name": "Climate", "icon": "🌡️"},
    {"id": "marine", "name": "Marine/Ocean", "icon": "🌊"},
    {"id": "earthquakes", "name": "Earthquakes", "icon": "🌍"},
    {"id": "wildfires", "name": "Wildfires", "icon": "🔥"},
    {"id": "radiation", "name": "Radiation", "icon": "☢️"},
    {"id": "biodiversity", "name": "Biodiversity", "icon": "🦋"},
    {"id": "soil", "name": "Soil", "icon": "🌱"}
]

# Time Range Presets
TIME_RANGES = [
    {"label": "1 Hour", "value": "1H"},
    {"label": "6 Hours", "value": "6H"},
    {"label": "24 Hours", "value": "24H"},
    {"label": "7 Days", "value": "7D"},
    {"label": "30 Days", "value": "30D"},
    {"label": "90 Days", "value": "90D"},
    {"label": "1 Year", "value": "1Y"},
    {"label": "Custom", "value": "custom"}
]

# Analysis Types
ANALYSIS_TYPES = [
    {"id": "time_series", "name": "Time Series Analysis"},
    {"id": "correlation", "name": "Correlation Analysis"},
    {"id": "anomaly", "name": "Anomaly Detection"},
    {"id": "trend", "name": "Trend Analysis"},
    {"id": "comparison", "name": "Comparative Analysis"},
    {"id": "distribution", "name": "Distribution Analysis"},
    {"id": "cross_domain", "name": "Cross-Domain Analysis"},
    {"id": "forecasting", "name": "Forecasting"}
]

# Report Types
REPORT_TYPES = [
    {"id": "summary", "name": "Executive Summary"},
    {"id": "detailed", "name": "Detailed Analysis"},
    {"id": "compliance", "name": "Regulatory Compliance"},
    {"id": "health_advisory", "name": "Public Health Advisory"},
    {"id": "alert_history", "name": "Alert History"},
    {"id": "custom", "name": "Custom Report"}
]

# Export Formats
EXPORT_FORMATS = [
    {"id": "pdf", "name": "PDF Report", "extension": ".pdf"},
    {"id": "csv", "name": "CSV Data", "extension": ".csv"},
    {"id": "json", "name": "JSON Data", "extension": ".json"},
    {"id": "excel", "name": "Excel Workbook", "extension": ".xlsx"},
    {"id": "png", "name": "PNG Image", "extension": ".png"},
    {"id": "svg", "name": "SVG Vector", "extension": ".svg"}
]

# Statistical Methods
STAT_METHODS = [
    {"id": "mean", "name": "Mean", "description": "Arithmetic average"},
    {"id": "median", "name": "Median", "description": "Middle value"},
    {"id": "std", "name": "Standard Deviation", "description": "Spread of data"},
    {"id": "percentile", "name": "Percentiles", "description": "P10, P25, P50, P75, P90"},
    {"id": "moving_avg", "name": "Moving Average", "description": "Smoothed trend"},
    {"id": "correlation", "name": "Correlation", "description": "Pearson correlation coefficient"},
    {"id": "regression", "name": "Linear Regression", "description": "Trend line fitting"}
]

# Map Configuration
MAP_CONFIG = {
    "default_lat": 37.7749,
    "default_lon": -122.4194,
    "default_zoom": 10,
    "style": "carto-positron"
}
