"""API v1 router - aggregates all v1 endpoints."""

from fastapi import APIRouter

from app.api.v1.endpoints import (
    chat,
    completeness,
    compliance,
    conflicts,
    dashboard,
    documents,
    gaps,
    health,
    health_score,
    policies,
    properties,
    renewals,
)

api_router = APIRouter()

# Include endpoint routers
api_router.include_router(health.router, tags=["health"])
api_router.include_router(documents.router, prefix="/documents", tags=["documents"])
api_router.include_router(chat.router, prefix="/chat", tags=["chat"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])
api_router.include_router(properties.router, prefix="/properties", tags=["properties"])
api_router.include_router(policies.router, prefix="/policies", tags=["policies"])
api_router.include_router(gaps.router, prefix="/gaps", tags=["gaps"])
api_router.include_router(compliance.router, prefix="/compliance", tags=["compliance"])
api_router.include_router(completeness.router, prefix="/completeness", tags=["completeness"])
api_router.include_router(health_score.router, prefix="/health-score", tags=["health-score"])
api_router.include_router(conflicts.router, prefix="/conflicts", tags=["conflicts"])
api_router.include_router(renewals.router, prefix="/renewals", tags=["renewals"])
