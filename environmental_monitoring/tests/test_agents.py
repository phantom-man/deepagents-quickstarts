"""
Tests for Environmental Monitoring System
"""

import pytest
import asyncio
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

from app.agents.ecodata_agent import EcoDataAgent
from app.agents.climateml_agent import ClimateMLAgent
from app.agents.geospatial_agent import GeoSpatialAgent
from app.agents.alertsystem_agent import AlertSystemAgent
from app.services.moltbook_collaboration import MoltbookCollaborationService

class TestEcoDataAgent:
    """Test cases for EcoData Agent."""

    @pytest.fixture
    async def ecodata_agent(self):
        """Create EcoData agent for testing."""
        agent = EcoDataAgent()
        # Mock the HTTP client to avoid real API calls
        agent.http_client = AsyncMock()
        yield agent
        await agent.cleanup()

    @pytest.mark.asyncio
    async def test_agent_initialization(self, ecodata_agent):
        """Test agent initialization."""
        await ecodata_agent.initialize()
        assert len(ecodata_agent.sensors) > 0
        assert not ecodata_agent.running

    @pytest.mark.asyncio
    async def test_sensor_data_validation(self, ecodata_agent):
        """Test sensor reading validation."""
        # Valid temperature reading
        valid_reading = {
            "value": 25.5,
            "unit": "celsius"
        }
        assert ecodata_agent._validate_reading(valid_reading)

        # Invalid temperature reading (too high)
        invalid_reading = {
            "value": 100.0,
            "unit": "celsius"
        }
        assert not ecodata_agent._validate_reading(invalid_reading)

        # Invalid percentage reading
        invalid_percentage = {
            "value": 150.0,
            "unit": "percent"
        }
        assert not ecodata_agent._validate_reading(invalid_percentage)

    @pytest.mark.asyncio
    async def test_sensor_registration(self, ecodata_agent):
        """Test sensor registration."""
        from app.schemas.schemas import SensorCreate

        sensor_data = SensorCreate(
            name="Test Sensor",
            type="temperature",
            location="Test Location",
            latitude=51.5074,
            longitude=-0.1276
        )

        sensor_id = await ecodata_agent.register_sensor(sensor_data)
        assert sensor_id > 0

class TestClimateMLAgent:
    """Test cases for ClimateML Agent."""

    @pytest.fixture
    async def climateml_agent(self):
        """Create ClimateML agent for testing."""
        agent = ClimateMLAgent()
        yield agent
        await agent.cleanup()

    @pytest.mark.asyncio
    async def test_agent_initialization(self, climateml_agent):
        """Test agent initialization."""
        await climateml_agent.initialize()
        assert len(climateml_agent.models) > 0
        assert not climateml_agent.running

    @pytest.mark.asyncio
    async def test_temperature_prediction(self, climateml_agent):
        """Test temperature prediction logic."""
        values = [20.0, 21.0, 19.5, 22.0, 20.5]
        predictions = climateml_agent._predict_temperature(values, 6)

        assert len(predictions) == 6
        for pred in predictions:
            assert "value" in pred
            assert "confidence" in pred
            assert "features" in pred
            # Check reasonable temperature range
            assert -50 <= pred["value"] <= 60

    @pytest.mark.asyncio
    async def test_air_quality_prediction(self, climateml_agent):
        """Test air quality prediction logic."""
        values = [40.0, 42.0, 38.0, 45.0, 41.0]
        predictions = climateml_agent._predict_air_quality(values, 4)

        assert len(predictions) == 4
        for pred in predictions:
            assert "value" in pred
            assert "confidence" in pred
            assert "features" in pred
            # Air quality should be non-negative
            assert pred["value"] >= 0

class TestGeoSpatialAgent:
    """Test cases for GeoSpatial Agent."""

    @pytest.fixture
    async def geospatial_agent(self):
        """Create GeoSpatial agent for testing."""
        agent = GeoSpatialAgent()
        yield agent
        await agent.cleanup()

    @pytest.mark.asyncio
    async def test_agent_initialization(self, geospatial_agent):
        """Test agent initialization."""
        await geospatial_agent.initialize()
        assert len(geospatial_agent.layers) > 0
        assert not geospatial_agent.running

    @pytest.mark.asyncio
    async def test_spatial_analysis(self, geospatial_agent):
        """Test spatial analysis functionality."""
        coverage = await geospatial_agent.get_spatial_analysis("coverage")
        assert "total_sensors" in coverage

        zones = await geospatial_agent.get_spatial_analysis("zones")
        assert isinstance(zones, dict)

    @pytest.mark.asyncio
    async def test_nearest_sensor_finding(self, geospatial_agent):
        """Test nearest sensor location finding."""
        # Test with coordinates near London
        result = await geospatial_agent.find_nearest_sensor(51.5074, -0.1276)
        assert result is not None
        assert "sensor_id" in result
        assert "distance_km" in result

class TestAlertSystemAgent:
    """Test cases for AlertSystem Agent."""

    @pytest.fixture
    async def alertsystem_agent(self):
        """Create AlertSystem agent for testing."""
        agent = AlertSystemAgent()
        # Mock HTTP client
        agent.http_client = AsyncMock()
        yield agent
        await agent.cleanup()

    @pytest.mark.asyncio
    async def test_agent_initialization(self, alertsystem_agent):
        """Test agent initialization."""
        await alertsystem_agent.initialize()
        assert len(alertsystem_agent.alert_channels) > 0
        assert len(alertsystem_agent.subscriptions) > 0
        assert not alertsystem_agent.running

    @pytest.mark.asyncio
    async def test_alert_message_formatting(self, alertsystem_agent):
        """Test alert message formatting."""
        from app.models.models import EnvironmentalEvent

        event = EnvironmentalEvent(
            event_type="anomaly",
            severity="high",
            title="Test Alert",
            description="Test description",
            timestamp=datetime.utcnow()
        )

        message = alertsystem_agent._format_alert_message(event)
        assert "Test Alert" in message
        assert "HIGH" in message
        assert "Test description" in message

    @pytest.mark.asyncio
    async def test_alert_statistics(self, alertsystem_agent):
        """Test alert statistics retrieval."""
        stats = await alertsystem_agent.get_alert_statistics()
        assert "total_alerts_today" in stats
        assert "active_alerts" in stats
        assert "critical_alerts" in stats

class TestMoltbookCollaboration:
    """Test cases for Moltbook Collaboration Service."""

    @pytest.fixture
    async def collaboration_service(self):
        """Create collaboration service for testing."""
        service = MoltbookCollaborationService()
        # Mock the moltbook client
        service.moltbook_client = MagicMock()
        service.moltbook_client.post.return_value = "test_post_id"
        yield service
        await service.cleanup()

    @pytest.mark.asyncio
    async def test_service_initialization(self, collaboration_service):
        """Test service initialization."""
        await collaboration_service.initialize()
        assert collaboration_service.session_id
        assert len(collaboration_service.agent_status) == 4

    @pytest.mark.asyncio
    async def test_collaboration_status(self, collaboration_service):
        """Test collaboration status retrieval."""
        status = await collaboration_service.get_collaboration_status()
        assert "session_id" in status
        assert "active" in status
        assert "agent_status" in status

# Integration test
@pytest.mark.asyncio
async def test_agent_collaboration_flow():
    """Test the complete agent collaboration flow."""
    # This would be a more comprehensive integration test
    # For now, just test that agents can be initialized together

    agents = []

    try:
        # Initialize all agents
        ecodata = EcoDataAgent()
        climateml = ClimateMLAgent()
        geospatial = GeoSpatialAgent()
        alertsystem = AlertSystemAgent()

        agents.extend([ecodata, climateml, geospatial, alertsystem])

        # Mock HTTP clients to avoid real API calls
        ecodata.http_client = AsyncMock()
        alertsystem.http_client = AsyncMock()

        # Initialize all agents
        init_tasks = [
            ecodata.initialize(),
            climateml.initialize(),
            geospatial.initialize(),
            alertsystem.initialize()
        ]

        await asyncio.gather(*init_tasks)

        # Verify all agents are initialized
        assert len(ecodata.sensors) > 0
        assert len(climateml.models) > 0
        assert len(geospatial.layers) > 0
        assert len(alertsystem.alert_channels) > 0

    finally:
        # Cleanup all agents
        cleanup_tasks = [agent.cleanup() for agent in agents]
        await asyncio.gather(*cleanup_tasks, return_exceptions=True)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])