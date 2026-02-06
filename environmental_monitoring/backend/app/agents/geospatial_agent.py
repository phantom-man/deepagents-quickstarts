"""
GeoSpatial Agent - GIS integration and spatial analysis

This agent is responsible for:
- Managing GIS layers and spatial data
- Performing spatial analysis on environmental data
- Generating maps and visualizations
- Spatial interpolation of sensor data
- Geographic queries and region analysis
- Integration with mapping services
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import json
import geopandas as gpd
import pandas as pd
from shapely.geometry import Point, Polygon
from shapely.ops import nearest_points
import folium
from folium.plugins import HeatMap, MarkerCluster
import numpy as np
from scipy.interpolate import griddata

from app.services.database import get_sensor_readings, get_active_alerts
from app.services.cache import cache_set, cache_get, gis_layer_key
from app.models.models import GISLayer, Sensor
from app.schemas.schemas import GISLayerCreate

logger = logging.getLogger(__name__)

class GeoSpatialAgent:
    """Agent for GIS integration and spatial analysis."""

    def __init__(self):
        self.layers: Dict[int, gpd.GeoDataFrame] = {}
        self.running = False
        self.tasks: List[asyncio.Task] = []
        self.map_cache: Dict[str, str] = {}  # Cache for generated maps

    async def initialize(self):
        """Initialize the GeoSpatial agent."""
        logger.info("🗺️ Initializing GeoSpatial Agent...")

        # Load GIS layers
        await self._load_gis_layers()

        # Start spatial analysis tasks
        await self.start_spatial_analysis()

        logger.info("✅ GeoSpatial Agent initialized")

    async def cleanup(self):
        """Cleanup agent resources."""
        logger.info("🧹 Cleaning up GeoSpatial Agent...")

        self.running = False

        # Cancel all running tasks
        for task in self.tasks:
            task.cancel()

        # Wait for tasks to complete
        if self.tasks:
            await asyncio.gather(*self.tasks, return_exceptions=True)

        logger.info("✅ GeoSpatial Agent cleanup complete")

    async def _load_gis_layers(self):
        """Load GIS layers from database and files."""
        # Create sample layers for demo
        await self._create_sample_layers()

    async def _create_sample_layers(self):
        """Create sample GIS layers for demonstration."""
        # London boundary layer
        london_bounds = Polygon([
            (-0.5104, 51.2868),  # Southwest
            (0.3340, 51.2868),   # Southeast
            (0.3340, 51.6919),   # Northeast
            (-0.5104, 51.6919),  # Northwest
            (-0.5104, 51.2868)   # Close polygon
        ])

        london_gdf = gpd.GeoDataFrame({
            'name': ['London'],
            'area_km2': [1572],
            'population': [9000000]
        }, geometry=[london_bounds], crs='EPSG:4326')

        self.layers[1] = london_gdf

        # Sensor locations layer
        sensor_locations = [
            {'sensor_id': 1, 'name': 'Weather Station Alpha', 'lon': -0.1276, 'lat': 51.5074},
            {'sensor_id': 2, 'name': 'Air Quality Monitor Beta', 'lon': -0.0999, 'lat': 51.5155},
            {'sensor_id': 3, 'name': 'Water Quality Sensor Gamma', 'lon': -0.0895, 'lat': 51.5045}
        ]

        sensor_gdf = gpd.GeoDataFrame(sensor_locations,
                                     geometry=[Point(xy['lon'], xy['lat']) for xy in sensor_locations],
                                     crs='EPSG:4326')

        self.layers[2] = sensor_gdf

        # Environmental zones layer
        zones = [
            {'zone_id': 1, 'name': 'Urban Center', 'risk_level': 'high'},
            {'zone_id': 2, 'name': 'Residential Area', 'risk_level': 'medium'},
            {'zone_id': 3, 'name': 'Green Space', 'risk_level': 'low'}
        ]

        # Create zone polygons (simplified)
        zone_polygons = [
            Polygon([(-0.15, 51.50), (-0.10, 51.50), (-0.10, 51.52), (-0.15, 51.52), (-0.15, 51.50)]),
            Polygon([(-0.10, 51.48), (-0.05, 51.48), (-0.05, 51.50), (-0.10, 51.50), (-0.10, 51.48)]),
            Polygon([(-0.05, 51.50), (0.00, 51.50), (0.00, 51.55), (-0.05, 51.55), (-0.05, 51.50)])
        ]

        zones_gdf = gpd.GeoDataFrame(zones, geometry=zone_polygons, crs='EPSG:4326')
        self.layers[3] = zones_gdf

        logger.info("🗺️ Sample GIS layers created")

    async def start_spatial_analysis(self):
        """Start spatial analysis tasks."""
        if self.running:
            return

        self.running = True
        logger.info("🚀 Starting spatial analysis pipeline...")

        # Start spatial analysis task
        analysis_task = asyncio.create_task(self._run_spatial_analysis())
        self.tasks.append(analysis_task)

        # Start map generation task
        map_task = asyncio.create_task(self._run_map_generation())
        self.tasks.append(map_task)

    async def _run_spatial_analysis(self):
        """Run spatial analysis tasks."""
        while self.running:
            try:
                # Perform spatial analysis
                await self._perform_spatial_analysis()

                # Wait for next analysis cycle (30 minutes)
                await asyncio.sleep(1800)

            except Exception as e:
                logger.error(f"❌ Error in spatial analysis: {e}")
                await asyncio.sleep(300)

    async def _perform_spatial_analysis(self):
        """Perform spatial analysis on environmental data."""
        try:
            # Analyze sensor coverage
            coverage_analysis = await self._analyze_sensor_coverage()
            logger.info(f"📊 Sensor coverage analysis: {coverage_analysis}")

            # Perform spatial interpolation
            interpolation_results = await self._perform_spatial_interpolation()
            logger.info(f"🔄 Spatial interpolation completed for {len(interpolation_results)} points")

            # Analyze environmental zones
            zone_analysis = await self._analyze_environmental_zones()
            logger.info(f"🏷️ Environmental zone analysis: {zone_analysis}")

        except Exception as e:
            logger.error(f"❌ Error performing spatial analysis: {e}")

    async def _analyze_sensor_coverage(self) -> Dict[str, Any]:
        """Analyze spatial coverage of sensors."""
        sensor_layer = self.layers.get(2)  # Sensor locations
        boundary_layer = self.layers.get(1)  # London boundary

        if sensor_layer is None or boundary_layer is None:
            return {"error": "Required layers not available"}

        # Calculate coverage metrics
        total_area = boundary_layer.geometry.area.sum()
        sensor_count = len(sensor_layer)

        # Calculate average distance between sensors
        distances = []
        for i, point1 in enumerate(sensor_layer.geometry):
            for j, point2 in enumerate(sensor_layer.geometry):
                if i != j:
                    distances.append(point1.distance(point2))

        avg_distance = np.mean(distances) if distances else 0

        return {
            "total_sensors": sensor_count,
            "coverage_area_km2": float(total_area * 111 * 111),  # Rough conversion to km²
            "average_sensor_distance": float(avg_distance),
            "coverage_density": sensor_count / float(total_area * 111 * 111) if total_area > 0 else 0
        }

    async def _perform_spatial_interpolation(self) -> List[Dict[str, Any]]:
        """Perform spatial interpolation of sensor data."""
        sensor_layer = self.layers.get(2)
        if sensor_layer is None:
            return []

        # Get recent sensor readings
        interpolation_points = []

        for _, sensor in sensor_layer.iterrows():
            sensor_id = sensor['sensor_id']
            readings = await get_sensor_readings(sensor_id, limit=10)

            if readings:
                latest_reading = readings[0]  # Most recent
                interpolation_points.append({
                    'sensor_id': sensor_id,
                    'longitude': sensor.geometry.x,
                    'latitude': sensor.geometry.y,
                    'value': latest_reading.value,
                    'timestamp': latest_reading.timestamp.isoformat()
                })

        return interpolation_points

    async def _analyze_environmental_zones(self) -> Dict[str, Any]:
        """Analyze environmental conditions by zone."""
        zones_layer = self.layers.get(3)
        sensor_layer = self.layers.get(2)

        if zones_layer is None or sensor_layer is None:
            return {"error": "Required layers not available"}

        zone_analysis = {}

        for _, zone in zones_layer.iterrows():
            zone_name = zone['name']
            zone_geom = zone.geometry

            # Find sensors within this zone
            sensors_in_zone = sensor_layer[sensor_layer.geometry.within(zone_geom)]

            zone_analysis[zone_name] = {
                "sensor_count": len(sensors_in_zone),
                "risk_level": zone['risk_level'],
                "area_km2": zone_geom.area * 111 * 111  # Rough conversion
            }

        return zone_analysis

    async def _run_map_generation(self):
        """Generate and update maps periodically."""
        while self.running:
            try:
                # Generate environmental monitoring map
                map_html = await self._generate_environmental_map()

                # Cache the map
                self.map_cache["environmental_monitoring"] = map_html

                # Wait for next map generation (1 hour)
                await asyncio.sleep(3600)

            except Exception as e:
                logger.error(f"❌ Error generating maps: {e}")
                await asyncio.sleep(300)

    async def _generate_environmental_map(self) -> str:
        """Generate an interactive environmental monitoring map."""
        try:
            # Create base map centered on London
            m = folium.Map(location=[51.5074, -0.1276], zoom_start=11)

            # Add sensor locations
            sensor_layer = self.layers.get(2)
            if sensor_layer is not None:
                sensor_cluster = MarkerCluster().add_to(m)

                for _, sensor in sensor_layer.iterrows():
                    # Get latest reading for this sensor
                    readings = await get_sensor_readings(sensor['sensor_id'], limit=1)
                    latest_value = readings[0].value if readings else "No data"

                    popup_text = f"""
                    <b>{sensor['name']}</b><br>
                    Sensor ID: {sensor['sensor_id']}<br>
                    Latest Reading: {latest_value}<br>
                    Location: {sensor.geometry.y:.4f}, {sensor.geometry.x:.4f}
                    """

                    folium.Marker(
                        location=[sensor.geometry.y, sensor.geometry.x],
                        popup=popup_text,
                        icon=folium.Icon(color='blue', icon='info-sign')
                    ).add_to(sensor_cluster)

            # Add environmental zones
            zones_layer = self.layers.get(3)
            if zones_layer is not None:
                for _, zone in zones_layer.iterrows():
                    # Style based on risk level
                    color = {'high': 'red', 'medium': 'orange', 'low': 'green'}.get(zone['risk_level'], 'gray')

                    folium.GeoJson(
                        zone.geometry.__geo_interface__,
                        style_function=lambda x, color=color: {
                            'fillColor': color,
                            'color': color,
                            'weight': 2,
                            'fillOpacity': 0.3
                        },
                        tooltip=f"{zone['name']} (Risk: {zone['risk_level']})"
                    ).add_to(m)

            # Add active alerts as markers
            alerts = await get_active_alerts()
            for alert in alerts:
                if alert.latitude and alert.longitude:
                    folium.Marker(
                        location=[alert.latitude, alert.longitude],
                        popup=f"<b>Alert:</b> {alert.title}<br><i>{alert.description}</i>",
                        icon=folium.Icon(color='red', icon='warning')
                    ).add_to(m)

            # Convert map to HTML string
            from folium import IFrame
            import base64
            map_html = m.get_root().render()
            return map_html

        except Exception as e:
            logger.error(f"❌ Error generating environmental map: {e}")
            return "<html><body><h3>Error generating map</h3></body></html>"

    async def get_spatial_analysis(self, analysis_type: str) -> Dict[str, Any]:
        """Get spatial analysis results."""
        if analysis_type == "coverage":
            return await self._analyze_sensor_coverage()
        elif analysis_type == "zones":
            return await self._analyze_environmental_zones()
        elif analysis_type == "interpolation":
            return {"points": await self._perform_spatial_interpolation()}
        else:
            return {"error": f"Unknown analysis type: {analysis_type}"}

    async def get_map(self, map_type: str = "environmental_monitoring") -> str:
        """Get generated map HTML."""
        return self.map_cache.get(map_type, "<html><body><h3>Map not available</h3></body></html>")

    async def find_nearest_sensor(self, latitude: float, longitude: float) -> Optional[Dict[str, Any]]:
        """Find the nearest sensor to a given location."""
        sensor_layer = self.layers.get(2)
        if sensor_layer is None:
            return None

        target_point = Point(longitude, latitude)

        # Find nearest sensor
        min_distance = float('inf')
        nearest_sensor = None

        for _, sensor in sensor_layer.iterrows():
            distance = target_point.distance(sensor.geometry)
            if distance < min_distance:
                min_distance = distance
                nearest_sensor = sensor

        if nearest_sensor is not None:
            # Get latest reading
            readings = await get_sensor_readings(nearest_sensor['sensor_id'], limit=1)
            latest_reading = readings[0] if readings else None

            return {
                "sensor_id": nearest_sensor['sensor_id'],
                "name": nearest_sensor['name'],
                "distance_km": min_distance * 111,  # Rough conversion to km
                "latitude": nearest_sensor.geometry.y,
                "longitude": nearest_sensor.geometry.x,
                "latest_reading": {
                    "value": latest_reading.value if latest_reading else None,
                    "unit": latest_reading.unit if latest_reading else None,
                    "timestamp": latest_reading.timestamp.isoformat() if latest_reading else None
                } if latest_reading else None
            }

        return None

    async def get_zone_info(self, latitude: float, longitude: float) -> Optional[Dict[str, Any]]:
        """Get information about the environmental zone for a location."""
        zones_layer = self.layers.get(3)
        if zones_layer is None:
            return None

        point = Point(longitude, latitude)

        # Find which zone contains this point
        for _, zone in zones_layer.iterrows():
            if zone.geometry.contains(point):
                return {
                    "zone_id": zone['zone_id'],
                    "name": zone['name'],
                    "risk_level": zone['risk_level'],
                    "area_km2": zone.geometry.area * 111 * 111
                }

        return {"message": "Location not within any defined environmental zone"}

    async def create_gis_layer(self, layer_data: GISLayerCreate) -> int:
        """Create a new GIS layer."""
        # In production, this would save to database
        layer_id = len(self.layers) + 1

        # Create GeoDataFrame from geojson if provided
        if layer_data.geojson_data:
            gdf = gpd.GeoDataFrame.from_features(layer_data.geojson_data['features'])
            self.layers[layer_id] = gdf

        logger.info(f"🗺️ Created GIS layer: {layer_data.name} (ID: {layer_id})")
        return layer_id

    async def get_layer_statistics(self) -> Dict[str, Any]:
        """Get statistics for all GIS layers."""
        stats = {}

        for layer_id, gdf in self.layers.items():
            stats[layer_id] = {
                "feature_count": len(gdf),
                "geometry_type": str(gdf.geometry.type.iloc[0]) if len(gdf) > 0 else "empty",
                "bounds": gdf.total_bounds.tolist() if len(gdf) > 0 else None,
                "crs": str(gdf.crs)
            }

        return stats

# Global GeoSpatial agent instance
geospatial_agent = GeoSpatialAgent()