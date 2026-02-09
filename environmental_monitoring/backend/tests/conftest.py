"""
Test configuration and fixtures.
"""
import os
import pytest
import pytest_asyncio
from typing import AsyncGenerator
from httpx import AsyncClient, ASGITransport

# Set test environment before importing app
os.environ["ENVIRONMENT"] = "test"
os.environ["API_KEY"] = "test-api-key-12345"
os.environ["ADMIN_API_KEY"] = "test-admin-key-12345"
os.environ["CORS_ORIGINS"] = "http://localhost:3000,http://localhost:8050"

from main import app


@pytest_asyncio.fixture
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    """Create async test client."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client


@pytest.fixture
def api_key_header() -> dict:
    """Return headers with valid API key."""
    return {"X-API-Key": "test-api-key-12345"}


@pytest.fixture
def admin_api_key_header() -> dict:
    """Return headers with valid admin API key."""
    return {"X-API-Key": "test-admin-key-12345"}


@pytest.fixture
def invalid_api_key_header() -> dict:
    """Return headers with invalid API key."""
    return {"X-API-Key": "invalid-key"}
