"""
Database service for ChromaDB status and operations.

Handles ChromaDB connections gracefully - if ChromaDB is unavailable,
the service will return appropriate error states instead of crashing.
"""
import sys
import logging
from typing import List, Optional, Tuple
from datetime import datetime
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent))

from models.database import DatabaseStatus, CollectionInfo, SourceBreakdown
from exceptions import ChromaDBUnavailableError, ChromaDBOperationError
from config import settings

logger = logging.getLogger(__name__)


class DatabaseService:
    """
    Service for managing ChromaDB operations.
    
    This service handles ChromaDB unavailability gracefully, allowing the
    rest of the application to continue functioning even when the database
    is down.
    """
    
    def __init__(self):
        self._chroma_manager = None
        self._connection_error: Optional[str] = None
        self._last_connection_attempt: Optional[datetime] = None
        self._connection_retry_interval = 30  # seconds
    
    @property
    def chromadb_available(self) -> bool:
        """Check if ChromaDB is currently available."""
        manager, error = self._get_manager_safe()
        return manager is not None and error is None
    
    def _should_retry_connection(self) -> bool:
        """Check if we should retry connecting to ChromaDB."""
        if self._last_connection_attempt is None:
            return True
        
        elapsed = (datetime.utcnow() - self._last_connection_attempt).total_seconds()
        return elapsed >= self._connection_retry_interval
    
    def _get_manager_safe(self) -> Tuple[Optional['ChromaDBManager'], Optional[str]]:
        """
        Safely get or create ChromaDB manager.
        
        Returns:
            Tuple of (manager, error_message). If successful, error_message is None.
            If failed, manager is None and error_message contains the reason.
        """
        # Return cached manager if available
        if self._chroma_manager is not None:
            return self._chroma_manager, None
        
        # Return cached error if we shouldn't retry yet
        if self._connection_error and not self._should_retry_connection():
            return None, self._connection_error
        
        # Try to connect
        self._last_connection_attempt = datetime.utcnow()
        
        try:
            # Import here to avoid import errors if chromadb is not installed
            from src.core.chromadb_manager import ChromaDBManager
            
            logger.info(f"🔄 Attempting to connect to ChromaDB at {settings.chroma_host}:{settings.chroma_port}")
            self._chroma_manager = ChromaDBManager()
            self._connection_error = None
            logger.info("✅ ChromaDB manager initialized successfully")
            return self._chroma_manager, None
            
        except ConnectionError as e:
            error_msg = f"ChromaDB connection failed: {e}"
            logger.warning(f"⚠️ {error_msg}")
            self._connection_error = error_msg
            self._chroma_manager = None
            return None, error_msg
            
        except Exception as e:
            error_msg = f"ChromaDB initialization failed: {e}"
            logger.error(f"❌ {error_msg}", exc_info=True)
            self._connection_error = error_msg
            self._chroma_manager = None
            return None, error_msg
    
    def reset_connection(self):
        """Reset the connection to force a retry on next access."""
        self._chroma_manager = None
        self._connection_error = None
        self._last_connection_attempt = None
        logger.info("🔄 ChromaDB connection reset, will retry on next access")
    
    async def get_status(self) -> DatabaseStatus:
        """
        Get database status and statistics.
        
        Returns a status object even if ChromaDB is unavailable,
        with is_connected=False and an error message.
        """
        manager, error = self._get_manager_safe()
        
        if manager is None:
            logger.debug(f"ChromaDB unavailable: {error}")
            return DatabaseStatus(
                is_connected=False,
                total_documents=0,
                collections=[],
                source_breakdown=SourceBreakdown(),
                error_message=error
            )
        
        try:
            # Get collections
            collections = await self.get_collections()
            
            # Calculate total documents
            total_documents = sum(col.document_count for col in collections)
            
            # Get source breakdown
            source_breakdown = await self._get_source_breakdown(manager)
            
            return DatabaseStatus(
                is_connected=True,
                total_documents=total_documents,
                collections=collections,
                source_breakdown=source_breakdown,
                last_updated=datetime.utcnow()
            )
            
        except Exception as e:
            logger.error(f"❌ Failed to get database status: {e}", exc_info=True)
            return DatabaseStatus(
                is_connected=False,
                total_documents=0,
                collections=[],
                source_breakdown=SourceBreakdown(),
                error_message=str(e)
            )
    
    async def get_collections(self) -> List[CollectionInfo]:
        """Get list of collections."""
        manager, error = self._get_manager_safe()
        
        if manager is None:
            logger.debug(f"Cannot get collections - ChromaDB unavailable: {error}")
            return []
        
        try:
            collections_data = []
            
            # Try to get the main collection
            if manager.collection:
                count = manager.collection.count()
                collections_data.append(
                    CollectionInfo(
                        name=manager.collection_name,
                        document_count=count,
                        metadata={}
                    )
                )
            
            return collections_data
            
        except Exception as e:
            logger.error(f"❌ Failed to get collections: {e}", exc_info=True)
            return []
    
    async def _get_source_breakdown(self, manager) -> SourceBreakdown:
        """Get breakdown of documents by source."""
        try:
            if not manager.collection:
                return SourceBreakdown()
            
            total = manager.collection.count()
            
            # Placeholder distribution
            # TODO: Implement actual source counting from metadata
            return SourceBreakdown(
                pubmed=int(total * 0.4),
                biorxiv=int(total * 0.25),
                medrxiv=int(total * 0.2),
                semantic_scholar=int(total * 0.15),
                other=0
            )
            
        except Exception as e:
            logger.error(f"❌ Failed to get source breakdown: {e}")
            return SourceBreakdown()
    
    async def check_health(self) -> Tuple[bool, Optional[str]]:
        """
        Check database health.
        
        Returns:
            Tuple of (is_healthy, error_message)
        """
        manager, error = self._get_manager_safe()
        
        if manager is None:
            return False, error
        
        try:
            # Try to perform a simple operation
            if manager.collection:
                manager.collection.count()
                return True, None
            
            return False, "No collection available"
            
        except Exception as e:
            error_msg = f"Health check failed: {e}"
            logger.error(f"❌ {error_msg}", exc_info=True)
            return False, error_msg
    
    def get_connection_info(self) -> dict:
        """Get information about the current connection state."""
        return {
            "host": settings.chroma_host,
            "port": settings.chroma_port,
            "execution_mode": settings.execution_mode,
            "is_connected": self._chroma_manager is not None,
            "last_error": self._connection_error,
            "last_connection_attempt": self._last_connection_attempt.isoformat() if self._last_connection_attempt else None
        }
