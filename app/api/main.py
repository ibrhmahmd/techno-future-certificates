"""
FastAPI application factory for Certificate Service.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routers.certificates import router as certificates_router
from app.web.router import router as web_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    from app.database import create_db_and_tables
    create_db_and_tables()
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title="Certificate Service API",
        description="Certificate generation, verification, and management for Techno Future",
        version="1.0.0",
        docs_url="/api/v1/docs",
        redoc_url="/api/v1/redoc",
        openapi_url="/api/v1/openapi.json",
        lifespan=lifespan,
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
    app.include_router(web_router)

    @app.get("/")
    def root():
        return {"status": "ok", "message": "Techno Future Certificate Service"}

    @app.get("/health")
    def health_check():
        return {"status": "ok"}

    return app


app = create_app()
