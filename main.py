"""
AI Service API - Main application entry point.

Production-ready FastAPI application for crypto trading analysis.
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

import structlog
import uvicorn
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request as StarletteRequest
from starlette.responses import Response
from fastapi.responses import JSONResponse

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.exceptions import AppException
from app.db.session import async_engine
from app.db.models import Base  # noqa: F401 – import so all models are registered

# Configure structured logging
logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Lifespan context manager for startup and shutdown events.

    This replaces the deprecated @app.on_event("startup") and @app.on_event("shutdown").
    """
    # Startup
    logger.info("Starting up AI Service API", version=settings.APP_VERSION)

    # Auto-create all tables that don't exist yet (safe for production – uses IF NOT EXISTS)
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables verified / created")

    # Initialize database connection pool
    # The engine is already created in app.db.session
    logger.info("Database connection pool initialized")

    yield

    # Shutdown
    logger.info("Shutting down AI Service API")

    # Close database connections
    await async_engine.dispose()
    logger.info("Database connections closed")

    # Add more cleanup tasks here:
    # - Close Redis connections
    # - Save state
    # - Cancel background tasks


# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="""
    AI Service API for Crypto Trading Analysis
    
    This API provides:
    * News article management and storage
    * Sentiment analysis on financial news
    * Real-time text sentiment analysis
    
    Built with FastAPI, SQLAlchemy 2.0, and modern Python best practices.
    """,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
    lifespan=lifespan,
    debug=settings.DEBUG,
)


# Custom CORS middleware that skips adding CORS headers when request comes from Gateway
# This prevents duplicate CORS headers (Gateway already adds them)
class ConditionalCORSMiddleware(BaseHTTPMiddleware):
    """
    Only add CORS headers if the request does NOT come from the Gateway.
    Gateway adds X-Gateway-Validated header to indicate it has already handled CORS.
    """
    async def dispatch(self, request: StarletteRequest, call_next) -> Response:
        # Check if request comes from Gateway (has X-Gateway-Validated header)
        is_from_gateway = request.headers.get("X-Gateway-Validated") == "true"
        
        response = await call_next(request)
        
        # Only add CORS headers if NOT from gateway (e.g., direct access for health checks)
        if not is_from_gateway:
            origin = request.headers.get("origin")
            # Allow all origins with wildcard
            if "*" in settings.CORS_ORIGINS or (origin and origin in settings.CORS_ORIGINS):
                response.headers["Access-Control-Allow-Origin"] = "*"
                response.headers["Access-Control-Allow-Credentials"] = "false"
                response.headers["Access-Control-Allow-Methods"] = "*"
                response.headers["Access-Control-Allow-Headers"] = "*"
        
        return response

# Use conditional CORS middleware instead of default CORSMiddleware
app.add_middleware(ConditionalCORSMiddleware)


# Custom exception handlers
@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    """Handle custom application exceptions."""
    logger.error(
        "Application exception",
        status_code=exc.status_code,
        message=exc.message,
        details=exc.details,
        path=request.url.path,
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.message,
            "error_code": exc.__class__.__name__,
            "errors": exc.details,
        },
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Handle Pydantic validation errors."""
    logger.warning(
        "Validation error",
        errors=exc.errors(),
        path=request.url.path,
    )
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": "Validation error",
            "error_code": "VALIDATION_ERROR",
            "errors": exc.errors(),
        },
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle all unhandled exceptions."""
    logger.exception(
        "Unhandled exception",
        exception=str(exc),
        path=request.url.path,
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "Internal server error",
            "error_code": "INTERNAL_SERVER_ERROR",
        },
    )


# Include API routers
app.include_router(api_router, prefix=settings.API_V1_PREFIX)


# Root endpoint
@app.get("/", tags=["Root"])
async def root() -> dict[str, str]:
    """
    Root endpoint providing API information.
    
    Returns basic information about the API service.
    """
    return {
        "message": "AI Service API",
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "health": f"{settings.API_V1_PREFIX}/health",
    }


if __name__ == "__main__":
    # Run with uvicorn when executed directly
    # In production, use: uvicorn main:app or fastapi run
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
    )

