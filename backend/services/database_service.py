"""
Database service for ChromaDB status and operations.
"""
import sys
import logging
from typing import List, Optional
from datetime import datetime
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.core.chromadb_manager import ChromaDBManager
from models.database import DatabaseStatus, CollectionInfo, SourceBreakdown

logger = logging.getLogger(__name__)


class DatabaseService:
    """Service for managing ChromaDB operations."""
    
    def __init__(self):
        self.chroma_manager: Optional[ChromaDBManager] = None
    
    def _get_manager(self) -> ChromaDBManager:
        """Get or create ChromaDB manager."""
        if not self.chroma_manager:
            try:
                self.chroma_manager = ChromaDBManager()
                logger.info("✅ ChromaDB manager initialized")
            except Exception as e:
                logger.error(f"❌ Failed to initialize ChromaDB manager: {e}")
                raise
        return self.chroma_manager
    
    async def get_status(self) -> DatabaseStatus:
        """Get database status and statistics."""
        try:
            manager = self._get_manager()
            
            # Get collections
            collections = await self.get_collections()
            
            # Calculate total documents
            total_documents = sum(col.document_count for col in collections)
            
            # Get source breakdown (simplified - would need metadata analysis)
            source_breakdown = await self._get_source_breakdown(manager)
            
            return DatabaseStatus(
                is_connected=True,
                total_documents=total_documents,
                collections=collections,
                source_breakdown=source_breakdown,
                last_updated=datetime.utcnow()
            )
            
        except Exception as e:
            logger.error(f"❌ Failed to get database status: {e}")
            return DatabaseStatus(
                is_connected=False,
                total_documents=0,
                collections=[],
                source_breakdown=SourceBreakdown()
            )
    
    async def get_collections(self) -> List[CollectionInfo]:
        """Get list of collections."""
        try:
            manager = self._get_manager()
            
            # Get all collections
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
            logger.error(f"❌ Failed to get collections: {e}")
            return []
    
    async def _get_source_breakdown(self, manager: ChromaDBManager) -> SourceBreakdown:
        """Get breakdown of documents by source."""
        try:
            # This would require querying metadata
            # For now, return a placeholder
            # TODO: Implement actual source counting from metadata
            
            if not manager.collection:
                return SourceBreakdown()
            
            total = manager.collection.count()
            
            # Placeholder distribution
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
    
    async def check_health(self) -> bool:
        """Check database health."""
        try:
            manager = self._get_manager()
            
            # Try to perform a simple operation
            if manager.collection:
                manager.collection.count()
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"❌ Database health check failed: {e}")
            return False

