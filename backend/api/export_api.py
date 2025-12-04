"""
Export API endpoints for downloading hypothesis results.
"""
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import FileResponse
import logging
import os

from models.export import ExportRequest, ExportResponse, ExportFormat
from services.export_service import ExportService
from api.auth import require_session

logger = logging.getLogger(__name__)
router = APIRouter()

# Initialize export service
export_service = ExportService()


@router.post("/create", response_model=ExportResponse)
async def create_export(
    export_request: ExportRequest,
    session_id: str = Depends(require_session)
):
    """
    Create an export file for hypothesis results.
    
    - Supports JSON, Excel, PDF, CSV formats
    - Returns download URL
    - Files are temporary and cleaned up with session
    """
    try:
        logger.info(f"📦 Export requested: {export_request.format} for job {export_request.job_id}")
        
        export_response = await export_service.create_export(
            session_id=session_id,
            job_id=export_request.job_id,
            format=export_request.format,
            include_citations=export_request.include_citations,
            include_scores=export_request.include_scores
        )
        
        return export_response
        
    except ValueError as e:
        logger.error(f"❌ Export validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"❌ Export creation error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to create export")


@router.get("/download/{filename}")
async def download_export(
    filename: str,
    session_id: str = Depends(require_session)
):
    """
    Download an export file.
    
    - Validates session ownership
    - Validates filename to prevent path traversal
    - Returns file for download
    - Sets appropriate content type
    """
    try:
        # Security: Validate filename at API level as well
        safe_filename = os.path.basename(filename)
        if safe_filename != filename or not safe_filename:
            raise HTTPException(status_code=400, detail="Invalid filename")
        
        # Only allow specific file extensions
        allowed_extensions = {".json", ".xlsx", ".pdf", ".csv"}
        file_extension = os.path.splitext(safe_filename)[1].lower()
        if file_extension not in allowed_extensions:
            raise HTTPException(status_code=400, detail="Invalid file type")
        
        file_path = await export_service.get_export_file(session_id, safe_filename)
        
        if not file_path or not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="Export file not found")
        
        # Determine media type based on extension
        media_type_map = {
            ".json": "application/json",
            ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            ".pdf": "application/pdf",
            ".csv": "text/csv"
        }
        
        media_type = media_type_map.get(file_extension, "application/octet-stream")
        
        return FileResponse(
            path=file_path,
            media_type=media_type,
            filename=safe_filename
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Download error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to download file")

