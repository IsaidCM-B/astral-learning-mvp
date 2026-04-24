from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from contextlib import asynccontextmanager
import structlog
import os

from src.core.config import settings
from src.api.v1.api import api_router
from src.core.logging import setup_logging
from src.core.exceptions import setup_exception_handlers
from src.services.health_service import HealthService

# Setup logging
setup_logging()
logger = structlog.get_logger()

# Security
security = HTTPBearer()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("AI Orchestrator starting up...")
    yield
    # Shutdown
    logger.info("AI Orchestrator shutting down...")

# Create FastAPI app
app = FastAPI(
    title="Astral Learning AI Orchestrator",
    description="Multi-agent AI system for personalized learning",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Setup CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # Backend
        "http://localhost:3001",  # Frontend parent
        "http://localhost:3002",  # Frontend student
        "https://astral-learning.com",  # Production
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Setup exception handlers
setup_exception_handlers(app)

# Include API routes
app.include_router(api_router, prefix="/api/v1")

# Health check endpoint
@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint"""
    health_service = HealthService()
    return await health_service.get_health_status()

# Root endpoint
@app.get("/", tags=["Root"])
async def root():
    return {
        "message": "Astral Learning AI Orchestrator",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }

# Protected endpoint example
@app.get("/api/v1/protected", tags=["Protected"])
async def protected_endpoint(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Example protected endpoint"""
    # Here you would validate the JWT token with the backend service
    return {"message": "This is a protected endpoint", "user": "validated"}

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level="info" if not settings.DEBUG else "debug"
    )
