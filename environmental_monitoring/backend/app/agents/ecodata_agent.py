"""
EcoData Agent - Real-time sensor data ingestion and processing

This agent is responsible for:
- Ingesting data from real public environmental data sources (OpenAQ, USGS, NOAA, etc.)
- Validating and cleaning sensor data
- Storing sensor readings in the database
- Providing real-time data streams
- Handling sensor registration and management

Data Sources:
- OpenAQ: Air quality data (free, no API key required)
- USGS Water Services: Water quality and stream flow (free, no API key)
- OpenWeatherMap: Weather data (requires free API key)
- EPA AirNow: US air quality index (requires free API key)
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import httpx
from dataclasses import dataclass

from app.services.database import (
    create_sensor_reading,
    get_sensor_readings
)
from app.services.cache import cache_set, sensor_readings_key
from app.services.data_sources import (
    data_ingestion_manager,
)
from app.schemas.schemas import SensorCreate

logger = logging.getLogger(__name__)

@dataclass
class SensorConfig:
    """Configuration for a sensor data source."""
    sensor_id: int
    name: str
    data_url: str
    data_format: str  # json, csv, xml
    poll_interval: int  # seconds
    auth_token: Optional[str] = None
    headers: Optional[Dict[str, str]] = None

class EcoDataAgent:
    """Agent for environmental sensor data ingestion and processing using real public APIs."""

    def __init__(self):
        self.sensors: Dict[int, SensorConfig] = {}
        self.running = False
        self.tasks: List[asyncio.Task] = []
        self.http_client = httpx.AsyncClient(timeout=30.0)
        self.data_manager = data_ingestion_manager  # Use the global manager

    async def initialize(self):
        """Initialize the EcoData agent."""
        logger.info("🌱 Initializing EcoData Agent...")

        # Load sensor configurations
        await self._load_sensor_configs()

        # Start data ingestion tasks
        await self.start_data_ingestion()

        logger.info(f"✅ EcoData Agent initialized with {len(self.sensors)} sensors")

    async def cleanup(self):
        """Cleanup agent resources."""
        logger.info("🧹 Cleaning up EcoData Agent...")

        self.running = False

        # Cancel all running tasks
        for task in self.tasks:
            task.cancel()

        # Wait for tasks to complete
        if self.tasks:
            await asyncio.gather(*self.tasks, return_exceptions=True)

        # Close HTTP client
        await self.http_client.aclose()

        logger.info("✅ EcoData Agent cleanup complete")

    async def _load_sensor_configs(self):
        """Load sensor configurations from database and config files."""
        # In a real implementation, this would load from database
        # For demo purposes, we'll create some sample sensors

        sample_sensors = [
            {
                "sensor_id": 1,
                "name": "Weather Station Alpha",
                "data_url": "https://api.openweathermap.org/data/2.5/weather?q=London&appid=demo",
                "data_format": "json",
                "poll_interval": 300,  # 5 minutes
            },
            {
                "sensor_id": 2,
                "name": "Air Quality Monitor Beta",
                "data_url": "https://api.openaq.org/v2/measurements?city=London&limit=1",
                "data_format": "json",
                "poll_interval": 600,  # 10 minutes
            },
            {
                "sensor_id": 3,
                "name": "Water Quality Sensor Gamma",
                "data_url": "https://water-quality-api.example.com/data",
                "data_format": "json",
                "poll_interval": 1800,  # 30 minutes
            }
        ]

        for sensor_data in sample_sensors:
            config = SensorConfig(**sensor_data)
            self.sensors[config.sensor_id] = config

    async def start_data_ingestion(self):
        """Start data ingestion tasks for all configured sensors."""
        if self.running:
            return

        self.running = True
        logger.info("🚀 Starting data ingestion for all sensors...")

        for sensor_config in self.sensors.values():
            task = asyncio.create_task(
                self._ingest_sensor_data(sensor_config)
            )
            self.tasks.append(task)

    async def stop_data_ingestion(self):
        """Stop all data ingestion tasks."""
        self.running = False
        logger.info("🛑 Stopping data ingestion...")

    async def _ingest_sensor_data(self, config: SensorConfig):
        """Continuously ingest data from a specific sensor."""
        logger.info(f"📡 Starting data ingestion for sensor {config.name}")

        while self.running:
            try:
                # Fetch data from sensor
                data = await self._fetch_sensor_data(config)

                if data:
                    # Process and store the data
                    await self._process_sensor_data(config, data)

                    # Cache recent readings
                    await self._update_cached_readings(config.sensor_id)

                # Wait for next poll interval
                await asyncio.sleep(config.poll_interval)

            except Exception as e:
                logger.error(f"❌ Error ingesting data from {config.name}: {e}")
                # Wait before retrying
                await asyncio.sleep(60)

    async def _fetch_sensor_data(self, config: SensorConfig) -> Optional[Dict[str, Any]]:
        """Fetch data from sensor API."""
        try:
            headers = config.headers or {}
            if config.auth_token:
                headers["Authorization"] = f"Bearer {config.auth_token}"

            response = await self.http_client.get(
                config.data_url,
                headers=headers
            )
            response.raise_for_status()

            if config.data_format == "json":
                return response.json()
            else:
                # For demo, assume JSON. In production, handle CSV, XML, etc.
                return {"raw_data": response.text}

        except httpx.HTTPError as e:
            logger.error(f"HTTP error fetching data from {config.name}: {e}")
            return None
        except Exception as e:
            logger.error(f"Error fetching data from {config.name}: {e}")
            return None

    async def _process_sensor_data(self, config: SensorConfig, data: Dict[str, Any]):
        """Process and store sensor data."""
        try:
            # Extract readings based on sensor type and data format
            readings = self._extract_readings(config, data)

            for reading in readings:
                # Validate reading
                if self._validate_reading(reading):
                    # Store in database
                    await create_sensor_reading(
                        sensor_id=config.sensor_id,
                        value=reading["value"],
                        unit=reading["unit"],
                        quality_score=reading.get("quality_score", 0.9),
                        metadata=reading.get("metadata", {})
                    )

                    logger.debug(f"📊 Stored reading for {config.name}: {reading['value']} {reading['unit']}")

        except Exception as e:
            logger.error(f"❌ Error processing data from {config.name}: {e}")

    def _extract_readings(self, config: SensorConfig, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract sensor readings from raw data based on sensor type."""
        readings = []

        try:
            if config.sensor_id == 1:  # Weather Station
                # OpenWeatherMap format
                if "main" in data:
                    readings.extend([
                        {
                            "value": data["main"]["temp"] - 273.15,  # Convert Kelvin to Celsius
                            "unit": "celsius",
                            "metadata": {"type": "temperature"}
                        },
                        {
                            "value": data["main"]["humidity"],
                            "unit": "percent",
                            "metadata": {"type": "humidity"}
                        }
                    ])

            elif config.sensor_id == 2:  # Air Quality Monitor
                # OpenAQ format
                if "results" in data and data["results"]:
                    result = data["results"][0]
                    readings.append({
                        "value": result.get("value", 0),
                        "unit": result.get("unit", "unknown"),
                        "metadata": {
                            "type": "air_quality",
                            "parameter": result.get("parameter"),
                            "location": result.get("location")
                        }
                    })

            elif config.sensor_id == 3:  # Water Quality Sensor
                # Simulated water quality data
                readings.extend([
                    {
                        "value": data.get("ph", 7.0),
                        "unit": "ph",
                        "metadata": {"type": "ph_level"}
                    },
                    {
                        "value": data.get("dissolved_oxygen", 8.0),
                        "unit": "mg/L",
                        "metadata": {"type": "dissolved_oxygen"}
                    }
                ])

        except Exception as e:
            logger.error(f"❌ Error extracting readings from {config.name}: {e}")

        return readings

    def _validate_reading(self, reading: Dict[str, Any]) -> bool:
        """Validate sensor reading data."""
        required_fields = ["value", "unit"]

        # Check required fields
        for field in required_fields:
            if field not in reading:
                logger.warning(f"Missing required field: {field}")
                return False

        # Validate value is numeric
        if not isinstance(reading["value"], (int, float)):
            logger.warning(f"Invalid value type: {type(reading['value'])}")
            return False

        # Check for reasonable value ranges
        value = reading["value"]
        unit = reading["unit"]

        if unit == "celsius" and not (-50 <= value <= 60):
            logger.warning(f"Temperature out of range: {value}°C")
            return False
        elif unit == "percent" and not (0 <= value <= 100):
            logger.warning(f"Percentage out of range: {value}%")
            return False
        elif unit == "ph" and not (0 <= value <= 14):
            logger.warning(f"pH out of range: {value}")
            return False

        return True

    async def _update_cached_readings(self, sensor_id: int):
        """Update cached sensor readings."""
        try:
            readings = await get_sensor_readings(sensor_id, limit=100)
            cache_key = sensor_readings_key(sensor_id, 100)
            await cache_set(cache_key, [dict(r) for r in readings], ttl=300)  # 5 minutes
        except Exception as e:
            logger.error(f"❌ Error updating cached readings for sensor {sensor_id}: {e}")

    async def get_sensor_readings(self, sensor_id: int, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent readings for a sensor.
        
        Args:
            sensor_id: ID of the sensor
            limit: Maximum number of readings to return
            
        Returns:
            List of sensor reading dictionaries
        """
        readings = await get_sensor_readings(sensor_id, limit=limit)
        return readings

    async def get_sensor_status(self, sensor_id: int) -> Optional[Dict[str, Any]]:
        """Get status and recent data for a sensor."""
        config = self.sensors.get(sensor_id)
        if not config:
            return None

        # Get recent readings
        readings = await get_sensor_readings(sensor_id, limit=10)

        return {
            "sensor_id": sensor_id,
            "name": config.name,
            "last_poll": datetime.utcnow(),  # In production, track actual poll times
            "recent_readings": [dict(r) for r in readings],
            "status": "active" if self.running else "inactive"
        }

    async def register_sensor(self, sensor_data: SensorCreate) -> int:
        """Register a new sensor (placeholder for future implementation)."""
        # In production, this would create a sensor in the database
        # and add it to the active sensors list
        logger.info(f"📝 Registering new sensor: {sensor_data.name}")
        return len(self.sensors) + 1

    async def get_all_sensor_status(self) -> List[Dict[str, Any]]:
        """Get status for all sensors."""
        status_list = []
        for sensor_id in self.sensors.keys():
            status = await self.get_sensor_status(sensor_id)
            if status:
                status_list.append(status)
        return status_list

# Global EcoData agent instance
ecodata_agent = EcoDataAgent()