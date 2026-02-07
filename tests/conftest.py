"""
Pytest configuration for environmental monitoring tests.
"""
import pytest


def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line("markers", "api: API tests")
    config.addinivalue_line("markers", "frontend: Frontend tests")
    config.addinivalue_line("markers", "slow: Tests that take longer to run")
    config.addinivalue_line("markers", "external: Tests that depend on external services")
    config.addinivalue_line("markers", "integration: Integration tests")
    config.addinivalue_line("markers", "stress: Stress/load tests")
