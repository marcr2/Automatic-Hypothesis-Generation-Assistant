"""
FastAPI main application entry point for AI Research Processor Web Interface.
"""
import sys
import os
from pathlib import Path

# Add parent directory to path for importing from src/
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging

from config import settings
from api import auth, hypothesis, database, export_api
from services.session_service import SessionService
from services.cleanup_service import CleanupService

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize services
session_service = SessionService()
cleanup_service = CleanupService()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events."""
    # Startup
    logger.info("🚀 Starting AI Research Processor Web API")
    logger.info(f"   Execution Mode: {settings.execution_mode}")
    logger.info(f"   ChromaDB: {settings.chroma_host}:{settings.chroma_port}")
    logger.info(f"   LLM Provider: {settings.llm_provider}")
    
    # Create necessary directories
    os.makedirs(settings.temp_sessions_path, exist_ok=True)
    os.makedirs(os.path.dirname(settings.logs_db_path), exist_ok=True)
    
    # Start cleanup service
    await cleanup_service.start()
    logger.info("✅ Cleanup service started")
    
    yield
    
    # Shutdown
    logger.info("🛑 Shutting down AI Research Processor Web API")
    await cleanup_service.stop()
    logger.info("✅ Cleanup service stopped")


# Initialize FastAPI app
app = FastAPI(
    title="AI Research Processor API",
    description="Web API for AI-powered scientific hypothesis generation",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_allowed_origins_list(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle uncaught exceptions gracefully."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "detail": "An internal server error occurred",
            "type": type(exc).__name__
        }
    )


# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(hypothesis.router, prefix="/api/hypothesis", tags=["Hypothesis Generation"])
app.include_router(database.router, prefix="/api/database", tags=["Database"])
app.include_router(export_api.router, prefix="/api/export", tags=["Export"])


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "AI Research Processor API",
        "version": "1.0.0"
    }


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "AI Research Processor Web API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=True
    )

