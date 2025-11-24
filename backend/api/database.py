"""
Database status and management API endpoints.
"""
from fastapi import APIRouter, HTTPException, Depends
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
    
    - Connection status
    - Total document count
    - Collection information
    - Source breakdown
    """
    try:
        status = await database_service.get_status()
        return status
        
    except Exception as e:
        logger.error(f"❌ Database status error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get database status")


@router.get("/collections")
async def get_collections(session_id: str = Depends(require_session)):
    """
    Get list of available ChromaDB collections.
    
    - Collection names
    - Document counts
    - Metadata
    """
    try:
        collections = await database_service.get_collections()
        return {"collections": collections}
        
    except Exception as e:
        logger.error(f"❌ Collections retrieval error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get collections")


@router.get("/health")
async def check_database_health(session_id: str = Depends(require_session)):
    """
    Check database connectivity and health.
    
    - Tests ChromaDB connection
    - Verifies data accessibility
    - Returns health status
    """
    try:
        is_healthy = await database_service.check_health()
        
        if not is_healthy:
            raise HTTPException(status_code=503, detail="Database unhealthy")
        
        return {"status": "healthy", "message": "Database is accessible"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Health check error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Health check failed")

