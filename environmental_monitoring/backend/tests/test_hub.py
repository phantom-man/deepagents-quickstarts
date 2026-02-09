"""
Tests for Data Hub API endpoints.
"""
import pytest


@pytest.mark.asyncio
async def test_hub_info(async_client):
    """Test hub info endpoint."""
    response = await async_client.get("/api/v1/hub")
    assert response.status_code == 200
    
    data = response.json()
    assert data["name"] == "Environmental Data Aggregation Hub"
    assert "total_sources" in data
    assert "categories" in data
    assert "endpoints" in data


@pytest.mark.asyncio
async def test_hub_sources_list(async_client):
    """Test listing all hub sources."""
    response = await async_client.get("/api/v1/hub/sources")
    assert response.status_code == 200
    
    data = response.json()
    assert "total" in data
    assert "sources" in data
    assert isinstance(data["sources"], list)


@pytest.mark.asyncio
async def test_hub_sources_filter_by_category(async_client):
    """Test filtering sources by category."""
    response = await async_client.get("/api/v1/hub/sources?category=weather")
    assert response.status_code == 200
    
    data = response.json()
    assert data["filter"] == "weather"


@pytest.mark.asyncio
async def test_hub_sources_invalid_category(async_client):
    """Test invalid category returns 400."""
    response = await async_client.get("/api/v1/hub/sources?category=invalid_category")
    assert response.status_code == 400
    
    data = response.json()
    assert "Invalid category" in data["detail"]


@pytest.mark.asyncio
async def test_hub_categories(async_client):
    """Test listing all categories."""
    response = await async_client.get("/api/v1/hub/categories")
    assert response.status_code == 200
    
    data = response.json()
    assert "categories" in data
    assert "available_categories" in data


@pytest.mark.asyncio
async def test_hub_quick_check_default_location(async_client):
    """Test quick environmental check with default San Francisco location."""
    response = await async_client.get("/api/v1/hub/quick")
    assert response.status_code == 200
    
    data = response.json()
    assert "location" in data
    assert data["location"]["latitude"] == 37.7749
    assert data["location"]["longitude"] == -122.4194
    assert "summary" in data
    assert "quick_status" in data


@pytest.mark.asyncio
async def test_hub_quick_check_custom_location(async_client):
    """Test quick check with custom location."""
    response = await async_client.get("/api/v1/hub/quick?lat=40.7128&lon=-74.0060")
    assert response.status_code == 200
    
    data = response.json()
    assert data["location"]["latitude"] == 40.7128
    assert data["location"]["longitude"] == -74.0060


@pytest.mark.asyncio
async def test_hub_location_invalid_coordinates(async_client):
    """Test invalid coordinates return 422."""
    # Latitude out of range
    response = await async_client.get("/api/v1/hub/location?lat=100&lon=0")
    assert response.status_code == 422
    
    # Longitude out of range
    response = await async_client.get("/api/v1/hub/location?lat=0&lon=200")
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_hub_analyze_rules(async_client):
    """Test getting analysis correlation rules."""
    response = await async_client.get("/api/v1/hub/analyze/rules")
    assert response.status_code == 200
    
    data = response.json()
    assert "rules" in data
    assert "description" in data
