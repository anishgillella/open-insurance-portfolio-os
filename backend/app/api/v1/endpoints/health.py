"""Health check endpoints."""

from datetime import UTC, datetime

from fastapi import APIRouter
from pydantic import BaseModel
from sqlalchemy import text

from app.core.config import settings
from app.core.dependencies import AsyncSessionDep

router = APIRouter()


class HealthResponse(BaseModel):
    """Health check response schema."""

    status: str
    environment: str
    version: str
    timestamp: str
    database: str


class DetailedHealthResponse(HealthResponse):
    """Detailed health check response with component status."""

    components: dict[str, dict[str, str]]


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Basic health check endpoint.

    Returns a simple status indicating the API is running.
    """
    return HealthResponse(
        status="healthy",
        environment=settings.environment,
        version="0.1.0",
        timestamp=datetime.now(UTC).isoformat(),
        database="not_checked",
    )


@router.get("/health/detailed", response_model=DetailedHealthResponse)
async def detailed_health_check(
    db: AsyncSessionDep,
) -> DetailedHealthResponse:
    """Detailed health check with database connectivity.

    Checks database connection and returns component-level status.
    """
    components: dict[str, dict[str, str]] = {}

    # Check database connection
    try:
        result = await db.execute(text("SELECT 1"))
        result.scalar()
        components["database"] = {"status": "healthy", "message": "Connected"}
        db_status = "connected"
    except Exception as e:
        components["database"] = {"status": "unhealthy", "message": str(e)}
        db_status = "disconnected"

    # Check external services (placeholder - will be implemented later)
    components["s3"] = {"status": "not_configured", "message": "S3 check not implemented"}
    components["pinecone"] = {
        "status": "not_configured",
        "message": "Pinecone check not implemented",
    }

    overall_status = "healthy" if db_status == "connected" else "degraded"

    return DetailedHealthResponse(
        status=overall_status,
        environment=settings.environment,
        version="0.1.0",
        timestamp=datetime.now(UTC).isoformat(),
        database=db_status,
        components=components,
    )
