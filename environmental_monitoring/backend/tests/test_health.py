"""
Tests for health check endpoints.
"""
import pytest


@pytest.mark.asyncio
async def test_root_endpoint(async_client):
    """Test root endpoint returns system status."""
    response = await async_client.get("/")
    assert response.status_code == 200
    
    data = response.json()
    assert data["message"] == "Environmental Monitoring System API"
    assert data["status"] == "running"
    assert "timestamp" in data
    assert "agents" in data


@pytest.mark.asyncio
async def test_ok_endpoint(async_client):
    """Test simple liveness probe."""
    response = await async_client.get("/ok")
    assert response.status_code == 200
    
    data = response.json()
    assert data["status"] == "ok"


@pytest.mark.asyncio
async def test_health_endpoint(async_client):
    """Test health check with service status."""
    response = await async_client.get("/health")
    assert response.status_code == 200
    
    data = response.json()
    assert "status" in data
    assert "timestamp" in data
    assert "version" in data
    assert "services" in data
    
    # Services should include these checks
    assert "database" in data["services"]
    assert "cache" in data["services"]
    assert "moltbook" in data["services"]


@pytest.mark.asyncio
async def test_ready_endpoint_returns_ready_or_503(async_client):
    """Test readiness probe returns ready or 503."""
    response = await async_client.get("/ready")
    # Should return 200 (ready) or 503 (not ready)
    assert response.status_code in [200, 503]
    
    if response.status_code == 200:
        data = response.json()
        assert data["status"] == "ready"
