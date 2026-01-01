"""API v1 router - aggregates all v1 endpoints."""

from fastapi import APIRouter

from app.api.v1.endpoints import health

api_router = APIRouter()

# Include endpoint routers
api_router.include_router(health.router, tags=["health"])

# Future endpoint routers will be added here:
# api_router.include_router(properties.router, prefix="/properties", tags=["properties"])
# api_router.include_router(documents.router, prefix="/documents", tags=["documents"])
# api_router.include_router(policies.router, prefix="/policies", tags=["policies"])
# api_router.include_router(chat.router, prefix="/chat", tags=["chat"])
