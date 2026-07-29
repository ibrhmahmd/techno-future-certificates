"""
FastAPI application factory for Certificate Service.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routers.certificates import router as certificates_router
from app.web.router import router as web_router

log = logging.getLogger(__name__)


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

    # Log request bodies for debugging
    @app.middleware("http")
    async def log_request_body(request: Request, call_next):
        if request.method in ("POST", "PUT", "PATCH"):
            body = await request.body()
            if body:
                log.info(
                    "%s %s body: %s",
                    request.method,
                    request.url.path,
                    body.decode("utf-8", errors="replace"),
                )
        return await call_next(request)

    # Log validation errors
    @app.exception_handler(RequestValidationError)
    async def log_validation_error(request: Request, exc: RequestValidationError):
        body = await request.body()
        log.error(
            "422 — %s %s\n  Body: %s\n  Errors: %s",
            request.method,
            request.url.path,
            body.decode("utf-8", errors="replace"),
            exc.errors(),
        )
        return JSONResponse(
            status_code=422,
            content={"detail": exc.errors()},
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
