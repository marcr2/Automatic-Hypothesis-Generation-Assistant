"""
Database-related Pydantic models.
"""
from pydantic import BaseModel
from typing import Dict, List, Optional
from datetime import datetime


class CollectionInfo(BaseModel):
    """Information about a ChromaDB collection."""
    name: str
    document_count: int
    metadata: Optional[Dict] = None


class SourceBreakdown(BaseModel):
    """Breakdown of documents by source."""
    pubmed: int = 0
    biorxiv: int = 0
    medrxiv: int = 0
    semantic_scholar: int = 0
    other: int = 0


class DatabaseStatus(BaseModel):
    """Status of the ChromaDB database."""
    is_connected: bool
    total_documents: int
    collections: List[CollectionInfo]
    source_breakdown: SourceBreakdown
    last_updated: Optional[datetime] = None
    error_message: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "is_connected": True,
                "total_documents": 125000,
                "collections": [
                    {
                        "name": "pubmed_papers",
                        "document_count": 125000
                    }
                ],
                "source_breakdown": {
                    "pubmed": 50000,
                    "biorxiv": 30000,
                    "medrxiv": 25000,
                    "semantic_scholar": 20000
                },
                "last_updated": "2025-11-19T08:00:00Z",
                "error_message": None
            }
        }

