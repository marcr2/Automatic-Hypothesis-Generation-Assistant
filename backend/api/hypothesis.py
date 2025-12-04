"""
Hypothesis generation API endpoints.
"""
from fastapi import APIRouter, HTTPException, Depends, WebSocket, WebSocketDisconnect, Request
from typing import Dict
import logging
import asyncio

from slowapi import Limiter
from slowapi.util import get_remote_address

from models.hypothesis import (
    HypothesisGenerateRequest,
    HypothesisGenerateResponse,
    HypothesisStatus,
    HypothesisResult,
    GenerationStatus
)
from services.hypothesis_service import HypothesisService
from services.session_service import SessionService
from api.auth import require_session, get_session_id
from config import settings

logger = logging.getLogger(__name__)
router = APIRouter()

# Initialize services
hypothesis_service = HypothesisService()
session_service = SessionService()

# Rate limiter - will use the app's limiter
limiter = Limiter(key_func=get_remote_address)


def get_session_key(request: Request) -> str:
    """
    Get rate limiting key based on session ID.
    Falls back to IP address if no session.
    """
    # Try to get session ID from cookie
    session_id = request.cookies.get("session_id")
    if session_id:
        return f"session:{session_id}"
    
    # Try Authorization header
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        return f"session:{auth_header.replace('Bearer ', '')}"
    
    # Fall back to IP
    return f"ip:{get_remote_address(request)}"


@router.post("/generate", response_model=HypothesisGenerateResponse)
@limiter.limit(f"{settings.max_generations_per_hour}/hour", key_func=get_session_key)
async def generate_hypotheses(
    request: Request,
    request_data: HypothesisGenerateRequest,
    session_id: str = Depends(require_session)
):
    """
    Start hypothesis generation job.
    
    - Validates request
    - Creates generation job
    - Returns job ID for status tracking
    
    Rate limited to 5 requests per hour per session (configurable).
    """
    try:
        logger.info(f"📝 Hypothesis generation requested by session: {session_id}")
        logger.info(f"   Topic: {request_data.research_topic}")
        logger.info(f"   Count: {request_data.num_hypotheses}")
        
        job_id = await hypothesis_service.start_generation(
            session_id=session_id,
            research_topic=request_data.research_topic,
            num_hypotheses=request_data.num_hypotheses,
            advanced_options=request_data.advanced_options
        )
        
        return HypothesisGenerateResponse(
            job_id=job_id,
            status=GenerationStatus.PENDING,
            message="Hypothesis generation job created"
        )
        
    except ValueError as e:
        logger.error(f"❌ Validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"❌ Generation error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to start hypothesis generation")


@router.get("/status/{job_id}", response_model=HypothesisStatus)
async def get_generation_status(
    job_id: str,
    session_id: str = Depends(require_session)
):
    """
    Get status of a hypothesis generation job.
    
    - Returns current progress
    - Shows current step
    - Indicates completion or errors
    """
    try:
        status = await hypothesis_service.get_status(session_id, job_id)
        
        if not status:
            raise HTTPException(status_code=404, detail="Job not found")
        
        return status
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Status check error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get job status")


@router.get("/results/{job_id}", response_model=HypothesisResult)
async def get_generation_results(
    job_id: str,
    session_id: str = Depends(require_session)
):
    """
    Get results of a completed hypothesis generation job.
    
    - Returns all generated hypotheses
    - Includes scores and citations
    - Only available for completed jobs
    """
    try:
        result = await hypothesis_service.get_results(session_id, job_id)
        
        if not result:
            raise HTTPException(status_code=404, detail="Results not found")
        
        if result.status != GenerationStatus.COMPLETED:
            raise HTTPException(
                status_code=400,
                detail=f"Job not completed yet. Current status: {result.status}"
            )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Results retrieval error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to get results")


@router.post("/cancel/{job_id}")
async def cancel_generation(
    job_id: str,
    session_id: str = Depends(require_session)
):
    """
    Cancel a running hypothesis generation job.
    
    - Stops generation process
    - Cleans up resources
    - Returns partial results if available
    """
    try:
        success = await hypothesis_service.cancel_job(session_id, job_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Job not found or already completed")
        
        return {"message": "Job cancelled successfully", "job_id": job_id}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Cancellation error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to cancel job")


@router.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    """
    WebSocket endpoint for real-time progress updates.
    
    - Validates session before accepting connection
    - Sends progress updates during generation
    - Provides status messages
    - Notifies on completion or errors
    
    Security: Session must be valid to establish WebSocket connection.
    """
    # Security: Validate session exists and is valid BEFORE accepting connection
    session = await session_service.get_session(session_id)
    
    if not session:
        logger.warning(f"WebSocket rejected: Invalid session ID {session_id[:8]}...")
        await websocket.close(code=4001, reason="Invalid session")
        return
    
    if not session.is_valid():
        logger.warning(f"WebSocket rejected: Expired session {session_id[:8]}...")
        await websocket.close(code=4002, reason="Session expired")
        return
    
    # Session is valid, accept the connection
    await websocket.accept()
    logger.info(f"🔌 WebSocket connected: {session_id[:8]}...")
    
    try:
        # Register websocket for this session
        await hypothesis_service.register_websocket(session_id, websocket)
        
        # Keep connection alive and handle messages
        while True:
            try:
                # Wait for client messages (heartbeat, etc.)
                data = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
                
                # Handle ping/pong
                if data == "ping":
                    await websocket.send_text("pong")
                    
            except asyncio.TimeoutError:
                # Send heartbeat
                await websocket.send_json({"type": "heartbeat"})
                
                # Periodically re-validate session
                session = await session_service.get_session(session_id)
                if not session or not session.is_valid():
                    logger.info(f"🔌 WebSocket closing: Session expired {session_id[:8]}...")
                    await websocket.close(code=4002, reason="Session expired")
                    break
                
    except WebSocketDisconnect:
        logger.info(f"🔌 WebSocket disconnected: {session_id[:8]}...")
    except Exception as e:
        logger.error(f"❌ WebSocket error: {e}", exc_info=True)
    finally:
        # Unregister websocket
        await hypothesis_service.unregister_websocket(session_id)

