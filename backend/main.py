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
from logging.handlers import RotatingFileHandler
from datetime import datetime

# Rate limiting
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from config import settings
from api import auth, hypothesis, database, export_api
from services.session_service import SessionService
from services.cleanup_service import CleanupService


def setup_logging():
    """
    Configure comprehensive logging with file handlers for debug and crash logs.
    
    Creates:
    - Console handler for INFO+ level messages
    - Debug log file with rotating handler (all messages when debug_mode is True)
    - Crash log file for ERROR+ level messages with full tracebacks
    """
    # Create logs directory if it doesn't exist
    os.makedirs(settings.log_dir, exist_ok=True)
    
    # Determine log level
    log_level = logging.DEBUG if settings.debug_mode else getattr(logging, settings.log_level.upper(), logging.INFO)
    
    # Root logger configuration
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)  # Capture all, filter at handler level
    
    # Clear any existing handlers
    root_logger.handlers.clear()
    
    # Log format
    detailed_format = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'
    )
    simple_format = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Console handler (INFO+ level, or DEBUG if debug_mode is enabled)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(simple_format)
    root_logger.addHandler(console_handler)
    
    # Debug log file handler (rotating, captures everything when debug mode is on)
    debug_log_path = os.path.join(settings.log_dir, 'debug.log')
    debug_handler = RotatingFileHandler(
        debug_log_path,
        maxBytes=settings.log_max_bytes,
        backupCount=settings.log_backup_count,
        encoding='utf-8'
    )
    debug_handler.setLevel(logging.DEBUG if settings.debug_mode else logging.INFO)
    debug_handler.setFormatter(detailed_format)
    root_logger.addHandler(debug_handler)
    
    # Crash/error log file handler (rotating, ERROR+ level only)
    crash_log_path = os.path.join(settings.log_dir, 'crash.log')
    crash_handler = RotatingFileHandler(
        crash_log_path,
        maxBytes=settings.log_max_bytes,
        backupCount=settings.log_backup_count,
        encoding='utf-8'
    )
    crash_handler.setLevel(logging.ERROR)
    crash_handler.setFormatter(detailed_format)
    root_logger.addHandler(crash_handler)
    
    # Log startup message
    startup_logger = logging.getLogger(__name__)
    startup_logger.info(f"Logging initialized - Level: {settings.log_level}, Debug Mode: {settings.debug_mode}")
    startup_logger.info(f"Log files: {debug_log_path}, {crash_log_path}")
    
    return startup_logger


# Set up logging
logger = setup_logging()

# Initialize rate limiter
# Uses IP address as the default key for rate limiting
limiter = Limiter(key_func=get_remote_address)

# Initialize services
session_service = SessionService()
cleanup_service = CleanupService()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events."""
    # Startup
    logger.info("=" * 60)
    logger.info("🚀 Starting AI Research Processor Web API")
    logger.info("=" * 60)
    logger.info(f"   API Host: {settings.api_host}")
    logger.info(f"   API Port: {settings.api_port}")
    logger.info(f"   Environment: {settings.environment}")
    logger.info(f"   Debug Mode: {settings.debug_mode}")
    logger.info(f"   Log Level: {settings.log_level}")
    logger.info(f"   Execution Mode: {settings.execution_mode}")
    logger.info(f"   ChromaDB: {settings.chroma_host}:{settings.chroma_port}")
    logger.info(f"   LLM Provider: {settings.llm_provider}")
    logger.info("=" * 60)
    
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

# Add rate limiter to app state
app.state.limiter = limiter

# Add rate limiting middleware
app.add_middleware(SlowAPIMiddleware)

# Add rate limit exceeded handler
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

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
    """Handle uncaught exceptions gracefully and log to crash log."""
    # Log detailed error information for debugging
    error_id = datetime.utcnow().strftime('%Y%m%d_%H%M%S_%f')
    logger.error(
        f"[ERROR_ID: {error_id}] Unhandled exception on {request.method} {request.url.path}: {exc}",
        exc_info=True
    )
    logger.error(f"[ERROR_ID: {error_id}] Request headers: {dict(request.headers)}")
    
    # Don't expose internal error types in production
    error_message = "An internal server error occurred"
    if settings.debug_mode:
        error_message = f"{error_message}. Error ID: {error_id}. Details: {str(exc)}"
    
    return JSONResponse(
        status_code=500,
        content={
            "detail": error_message,
            "error_id": error_id
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

