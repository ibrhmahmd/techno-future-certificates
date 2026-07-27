"""
FastAPI application factory for Certificate Service.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routers.certificates import router as certificates_router


def create_app() -> FastAPI:
    app = FastAPI(
        title="Certificate Service API",
        description="Certificate generation, verification, and management for Techno Future",
        version="1.0.0",
        docs_url="/api/v1/docs",
        redoc_url="/api/v1/redoc",
        openapi_url="/api/v1/openapi.json",
    )

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Routers
    app.include_router(
        certificates_router,
        prefix="/api/v1",
        tags=["Certificates"],
    )

    @app.get("/health")
    def health_check():
        return {"status": "ok"}

    return app


app = create_app()
