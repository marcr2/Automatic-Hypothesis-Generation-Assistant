"""
Database status and management API endpoints.

These endpoints handle ChromaDB unavailability gracefully, returning
appropriate error responses (503) when the database is down instead of
crashing the entire application.
"""
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse
import logging

from models.database import DatabaseStatus, CollectionInfo, SourceBreakdown
from api.auth import require_session
from services.database_service import DatabaseService

logger = logging.getLogger(__name__)
router = APIRouter()

# Initialize database service
database_service = DatabaseService()


@router.get("/status", response_model=DatabaseStatus)
async def get_database_status(session_id: str = Depends(require_session)):
    """
    Get ChromaDB database status and statistics.
    
    Returns status information even if ChromaDB is unavailable,
    with is_connected=False and an error message explaining the issue.
    
    - Connection status
    - Total document count
    - Collection information
    - Source breakdown
    - Error message (if any)
    """
    try:
        status = await database_service.get_status()
        return status
        
    except Exception as e:
        logger.error(f"❌ Database status error: {e}", exc_info=True)
        # Return a status object even on error
        return DatabaseStatus(
            is_connected=False,
            total_documents=0,
            collections=[],
            source_breakdown=SourceBreakdown(),
            error_message=f"Failed to get database status: {str(e)}"
        )


@router.get("/collections")
async def get_collections(session_id: str = Depends(require_session)):
    """
    Get list of available ChromaDB collections.
    
    Returns an empty list if ChromaDB is unavailable, along with
    an error message explaining the issue.
    
    - Collection names
    - Document counts
    - Metadata
    """
    try:
        if not database_service.chromadb_available:
            connection_info = database_service.get_connection_info()
            return JSONResponse(
                status_code=503,
                content={
                    "collections": [],
                    "error": "ChromaDB is currently unavailable",
                    "details": connection_info.get("last_error"),
                    "connection": {
                        "host": connection_info.get("host"),
                        "port": connection_info.get("port")
                    }
                }
            )
        
        collections = await database_service.get_collections()
        return {"collections": collections}
        
    except Exception as e:
        logger.error(f"❌ Collections retrieval error: {e}", exc_info=True)
        return JSONResponse(
            status_code=503,
            content={
                "collections": [],
                "error": "Failed to get collections",
                "details": str(e)
            }
        )


@router.get("/health")
async def check_database_health(session_id: str = Depends(require_session)):
    """
    Check database connectivity and health.
    
    Returns 503 Service Unavailable if ChromaDB is down, with details
    about the connection failure.
    
    - Tests ChromaDB connection
    - Verifies data accessibility
    - Returns health status with error details if unhealthy
    """
    try:
        is_healthy, error_message = await database_service.check_health()
        
        if not is_healthy:
            connection_info = database_service.get_connection_info()
            return JSONResponse(
                status_code=503,
                content={
                    "status": "unhealthy",
                    "message": "ChromaDB database is unavailable",
                    "error": error_message,
                    "connection": {
                        "host": connection_info.get("host"),
                        "port": connection_info.get("port"),
                        "execution_mode": connection_info.get("execution_mode")
                    },
                    "suggestion": "Please check that ChromaDB server is running and accessible"
                }
            )
        
        return {
            "status": "healthy",
            "message": "Database is accessible",
            "connection": database_service.get_connection_info()
        }
        
    except Exception as e:
        logger.error(f"❌ Health check error: {e}", exc_info=True)
        return JSONResponse(
            status_code=503,
            content={
                "status": "error",
                "message": "Health check failed",
                "error": str(e)
            }
        )


@router.post("/reconnect")
async def reconnect_database(session_id: str = Depends(require_session)):
    """
    Force a reconnection attempt to ChromaDB.
    
    Useful when ChromaDB was temporarily down and is now available again.
    """
    try:
        # Reset the connection to force a retry
        database_service.reset_connection()
        
        # Try to connect
        is_healthy, error_message = await database_service.check_health()
        
        if is_healthy:
            return {
                "status": "success",
                "message": "Successfully reconnected to ChromaDB",
                "connection": database_service.get_connection_info()
            }
        else:
            return JSONResponse(
                status_code=503,
                content={
                    "status": "failed",
                    "message": "Failed to reconnect to ChromaDB",
                    "error": error_message,
                    "connection": database_service.get_connection_info()
                }
            )
            
    except Exception as e:
        logger.error(f"❌ Reconnection error: {e}", exc_info=True)
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": "Reconnection attempt failed",
                "error": str(e)
            }
        )


@router.get("/connection-info")
async def get_connection_info(session_id: str = Depends(require_session)):
    """
    Get information about the current ChromaDB connection state.
    
    Returns connection details including host, port, and any errors.
    """
    return database_service.get_connection_info()
