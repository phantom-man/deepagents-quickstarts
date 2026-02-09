"""
Tests for authentication and security.
"""
import pytest


@pytest.mark.asyncio
async def test_protected_endpoint_requires_api_key(async_client):
    """Test that protected endpoints require API key."""
    # Attempt to start ingestion without API key
    response = await async_client.post("/api/v1/data-sources/ingestion/start")
    assert response.status_code == 401
    
    data = response.json()
    assert "detail" in data


@pytest.mark.asyncio
async def test_protected_endpoint_accepts_valid_api_key(async_client, api_key_header):
    """Test that protected endpoints accept valid API key."""
    response = await async_client.post(
        "/api/v1/data-sources/ingestion/start",
        headers=api_key_header
    )
    # Should not return 401 (may return other status based on actual operation)
    assert response.status_code != 401


@pytest.mark.asyncio
async def test_protected_endpoint_rejects_invalid_api_key(async_client, invalid_api_key_header):
    """Test that protected endpoints reject invalid API key."""
    response = await async_client.post(
        "/api/v1/data-sources/ingestion/start",
        headers=invalid_api_key_header
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_bearer_token_authentication(async_client):
    """Test Bearer token authentication works."""
    response = await async_client.post(
        "/api/v1/data-sources/ingestion/start",
        headers={"Authorization": "Bearer test-api-key-12345"}
    )
    # Should not return 401
    assert response.status_code != 401


@pytest.mark.asyncio
async def test_admin_endpoint_requires_admin_key(async_client, api_key_header):
    """Test that admin endpoints require admin API key."""
    # Regular API key should not have admin access
    response = await async_client.post(
        "/api/v1/system/reset",
        headers=api_key_header
    )
    # Should be 401 (not admin) or 403 (blocked in production)
    assert response.status_code in [401, 403]


@pytest.mark.asyncio
async def test_correlation_id_in_response(async_client):
    """Test that correlation ID is returned in response headers."""
    response = await async_client.get("/")
    assert "X-Correlation-ID" in response.headers


@pytest.mark.asyncio
async def test_custom_correlation_id_respected(async_client):
    """Test that custom correlation ID in request is used."""
    custom_id = "my-custom-correlation-id-12345"
    response = await async_client.get(
        "/",
        headers={"X-Correlation-ID": custom_id}
    )
    assert response.headers.get("X-Correlation-ID") == custom_id
