"""FastAPI application entry point."""

import logging

from fastapi import FastAPI

from app.config import get_settings
from app.routers.employees import router as employees_router
from app.schemas import HealthResponse

settings = get_settings()
logging.basicConfig(
    level=settings.log_level,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)


app = FastAPI(
    title=settings.app_name,
    description="Employee CRUD API protected at the edge by Azure API Management.",
    version=settings.app_version,
)
app.include_router(employees_router)


@app.get("/health", response_model=HealthResponse, tags=["operations"])
def health() -> HealthResponse:
    """Return process health and deployment identity."""

    return HealthResponse(
        status="healthy",
        environment=settings.app_environment,
        version=settings.app_version,
        release_message="Employee API v2 deployment verified",
    )
