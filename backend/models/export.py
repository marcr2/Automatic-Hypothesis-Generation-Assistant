"""
Export-related Pydantic models.
"""
from pydantic import BaseModel
from enum import Enum
from typing import Optional


class ExportFormat(str, Enum):
    """Supported export formats."""
    JSON = "json"
    EXCEL = "excel"
    PDF = "pdf"
    CSV = "csv"


class ExportRequest(BaseModel):
    """Request model for exporting hypothesis results."""
    job_id: str
    format: ExportFormat
    include_citations: bool = True
    include_scores: bool = True
    
    class Config:
        json_schema_extra = {
            "example": {
                "job_id": "gen_abc123",
                "format": "excel",
                "include_citations": True,
                "include_scores": True
            }
        }


class ExportResponse(BaseModel):
    """Response model for export request."""
    success: bool
    download_url: Optional[str] = None
    filename: str
    format: ExportFormat
    file_size_bytes: Optional[int] = None
    error_message: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "download_url": "/api/export/download/export_abc123.xlsx",
                "filename": "hypotheses_2025-11-19.xlsx",
                "format": "excel",
                "file_size_bytes": 45678
            }
        }

