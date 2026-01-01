"""Tests for health check endpoints."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_root_endpoint(client: AsyncClient) -> None:
    """Test the root endpoint returns welcome message."""
    response = await client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "Open Insurance" in data["message"]
    assert "docs" in data
    assert "health" in data


@pytest.mark.asyncio
async def test_health_check(client: AsyncClient) -> None:
    """Test the basic health check endpoint."""
    response = await client.get("/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "environment" in data
    assert "version" in data
    assert "timestamp" in data


@pytest.mark.asyncio
async def test_detailed_health_check(client: AsyncClient) -> None:
    """Test the detailed health check endpoint with database connection."""
    response = await client.get("/v1/health/detailed")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "components" in data
    assert "database" in data["components"]
