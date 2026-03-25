"""
FastAPI application entry point.
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import api_router
from app.auth.middleware import auth_middleware
from app.core.config import settings
from app.core.logging import configure_logging, get_logger
from app.core.database import init_db

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    configure_logging()
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    
    # Create tables
    await init_db()
    logger.info("Database tables created")
    
    yield
    
    # Shutdown
    logger.info("Shutting down application")


def create_application() -> FastAPI:
    """Create FastAPI application."""
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="ZKH Benchmark Platform API",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )
    
    # CORS middleware - must be before auth middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # SSO Auth middleware (only if SSO is enabled)
    if settings.sso_enabled:
        app.middleware("http")(auth_middleware)
    
    # Include API routers
    app.include_router(api_router, prefix="/api")
    
    # Health check endpoint
    @app.get("/health")
    async def health_check():
        return {"status": "healthy", "version": settings.app_version}
    
    @app.get("/")
    async def root():
        return {
            "name": settings.app_name,
            "version": settings.app_version,
            "docs": "/docs",
        }
    
    return app


app = create_application()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
    )
