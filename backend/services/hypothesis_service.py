"""
Hypothesis generation service - wraps the existing enhanced_rag_with_chromadb.py for web API.

Handles service unavailability (ChromaDB, LLM) gracefully, providing user-friendly
error messages instead of crashing.
"""
import asyncio
import json
import os
import sys
import uuid
from datetime import datetime
from typing import Dict, Optional, List, Any
from pathlib import Path
import logging

from fastapi import WebSocket

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent))

from models.hypothesis import (
    HypothesisStatus,
    HypothesisResult,
    HypothesisItem,
    HypothesisScores,
    HypothesisCitation,
    GenerationStatus
)
from services.session_service import SessionService
from exceptions import ChromaDBUnavailableError, LLMUnavailableError, HypothesisGenerationError
from config import settings

logger = logging.getLogger(__name__)


class HypothesisJob:
    """Represents a hypothesis generation job."""
    
    def __init__(self, job_id: str, session_id: str, research_topic: str, num_hypotheses: int):
        self.job_id = job_id
        self.session_id = session_id
        self.research_topic = research_topic
        self.num_hypotheses = num_hypotheses
        self.status = GenerationStatus.PENDING
        self.progress = 0.0
        self.current_step = "Initializing..."
        self.hypotheses_generated = 0
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None
        self.error_message: Optional[str] = None
        self.result: Optional[HypothesisResult] = None
        self.task: Optional[asyncio.Task] = None


class HypothesisService:
    """Service for managing hypothesis generation."""
    
    def __init__(self):
        self.session_service = SessionService()
        self.jobs: Dict[str, HypothesisJob] = {}
        self.websockets: Dict[str, WebSocket] = {}
    
    async def start_generation(
        self,
        session_id: str,
        research_topic: str,
        num_hypotheses: int,
        advanced_options: Optional[Dict[str, Any]] = None
    ) -> str:
        """Start a new hypothesis generation job."""
        # Create job
        job_id = f"gen_{uuid.uuid4().hex[:12]}"
        job = HypothesisJob(job_id, session_id, research_topic, num_hypotheses)
        self.jobs[job_id] = job
        
        # Start generation task
        job.task = asyncio.create_task(
            self._run_generation(job, advanced_options)
        )
        
        # Log action
        await self.session_service.log_action(
            session_id,
            "hypothesis_generation_started",
            json.dumps({"job_id": job_id, "topic": research_topic})
        )
        
        return job_id
    
    async def _run_generation(self, job: HypothesisJob, advanced_options: Optional[Dict[str, Any]]):
        """Run the hypothesis generation process."""
        try:
            job.status = GenerationStatus.IN_PROGRESS
            job.started_at = datetime.utcnow()
            await self._send_update(job)
            
            # Import here to avoid circular imports and load heavy modules only when needed
            from src.ai.enhanced_rag_with_chromadb import EnhancedRAGSystem
            
            job.current_step = "Initializing RAG system..."
            job.progress = 10.0
            await self._send_update(job)
            
            # Initialize RAG system
            rag_system = EnhancedRAGSystem()
            
            job.current_step = "Searching literature database..."
            job.progress = 20.0
            await self._send_update(job)
            
            # Generate hypotheses
            # This is a simplified integration - you'll need to adapt based on actual API
            hypotheses = await self._generate_hypotheses_sync(
                rag_system,
                job.research_topic,
                job.num_hypotheses,
                job
            )
            
            job.current_step = "Finalizing results..."
            job.progress = 95.0
            await self._send_update(job)
            
            # Create result
            job.result = HypothesisResult(
                job_id=job.job_id,
                status=GenerationStatus.COMPLETED,
                research_topic=job.research_topic,
                hypotheses=hypotheses,
                total_count=len(hypotheses),
                generated_at=datetime.utcnow(),
                metadata={"num_requested": job.num_hypotheses}
            )
            
            # Save result to session directory
            await self._save_result(job)
            
            job.status = GenerationStatus.COMPLETED
            job.progress = 100.0
            job.current_step = "Complete!"
            job.completed_at = datetime.utcnow()
            await self._send_update(job)
            
            logger.info(f"✅ Hypothesis generation completed: {job.job_id}")
            
        except asyncio.CancelledError:
            job.status = GenerationStatus.CANCELLED
            job.error_message = "Job was cancelled"
            job.current_step = "Cancelled"
            await self._send_update(job)
            logger.info(f"⚠️ Hypothesis generation cancelled: {job.job_id}")
        
        except ChromaDBUnavailableError as e:
            # ChromaDB is unavailable - provide user-friendly message
            job.status = GenerationStatus.FAILED
            job.error_message = f"Database unavailable: {e.message}"
            if e.details:
                job.error_message += f" ({e.details})"
            job.current_step = "Failed - Database unavailable"
            job.completed_at = datetime.utcnow()
            await self._send_update(job)
            logger.error(f"❌ Hypothesis generation failed (ChromaDB unavailable): {job.job_id} - {e.message}")
        
        except LLMUnavailableError as e:
            # LLM service is unavailable - provide user-friendly message
            job.status = GenerationStatus.FAILED
            job.error_message = f"AI service unavailable: {e.message}"
            if e.details:
                job.error_message += f" ({e.details})"
            job.current_step = "Failed - AI service unavailable"
            job.completed_at = datetime.utcnow()
            await self._send_update(job)
            logger.error(f"❌ Hypothesis generation failed (LLM unavailable): {job.job_id} - {e.message}")
        
        except HypothesisGenerationError as e:
            # Generation-specific error - provide user-friendly message
            job.status = GenerationStatus.FAILED
            job.error_message = e.message
            if e.details:
                job.error_message += f": {e.details}"
            job.current_step = f"Failed - {e.stage if e.stage else 'Generation error'}"
            job.completed_at = datetime.utcnow()
            await self._send_update(job)
            logger.error(f"❌ Hypothesis generation failed: {job.job_id} - {e.message}")
            
        except Exception as e:
            # Unexpected error - log full details but provide generic message
            job.status = GenerationStatus.FAILED
            job.error_message = f"An unexpected error occurred: {str(e)}"
            job.current_step = "Failed - Unexpected error"
            job.completed_at = datetime.utcnow()
            await self._send_update(job)
            logger.error(f"❌ Hypothesis generation failed (unexpected): {job.job_id} - {e}", exc_info=True)
    
    async def _generate_hypotheses_sync(
        self,
        rag_system: Any,
        research_topic: str,
        num_hypotheses: int,
        job: HypothesisJob
    ) -> List[HypothesisItem]:
        """Generate hypotheses using the RAG system (run in executor to avoid blocking)."""
        # Import the adapter
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from adapters.rag_adapter import RAGAdapter
        
        # Create session output directory
        session_path = self.session_service.get_session_path(job.session_id)
        output_dir = os.path.join(session_path, "results")
        
        # Initialize adapter
        adapter = RAGAdapter(job.session_id, output_dir)
        
        # Progress callback
        def progress_callback(progress: float, step: str, count: int):
            job.progress = progress
            job.current_step = step
            job.hypotheses_generated = count
            # Send update asynchronously
            asyncio.create_task(self._send_update(job))
        
        # Generate hypotheses using adapter
        hypotheses = await adapter.generate_hypotheses(
            research_topic=research_topic,
            num_hypotheses=num_hypotheses,
            progress_callback=progress_callback
        )
        
        return hypotheses
    
    async def _save_result(self, job: HypothesisJob):
        """Save result to session directory."""
        session_path = self.session_service.get_session_path(job.session_id)
        results_dir = os.path.join(session_path, "results")
        os.makedirs(results_dir, exist_ok=True)
        
        result_file = os.path.join(results_dir, f"{job.job_id}.json")
        
        with open(result_file, 'w') as f:
            json.dump(job.result.model_dump(), f, indent=2, default=str)
    
    async def _send_update(self, job: HypothesisJob):
        """Send progress update via WebSocket if connected."""
        websocket = self.websockets.get(job.session_id)
        
        if websocket:
            try:
                status_dict = {
                    "type": "progress",
                    "job_id": job.job_id,
                    "status": job.status.value,
                    "progress": job.progress,
                    "current_step": job.current_step,
                    "hypotheses_generated": job.hypotheses_generated,
                    "total_hypotheses": job.num_hypotheses
                }
                
                # Include error message if job failed
                if job.status == GenerationStatus.FAILED and job.error_message:
                    status_dict["error_message"] = job.error_message
                    status_dict["type"] = "error"
                
                await websocket.send_json(status_dict)
            except Exception as e:
                logger.warning(f"⚠️ Failed to send WebSocket update: {e}")
    
    async def get_status(self, session_id: str, job_id: str) -> Optional[HypothesisStatus]:
        """Get status of a job."""
        job = self.jobs.get(job_id)
        
        if not job or job.session_id != session_id:
            return None
        
        return HypothesisStatus(
            job_id=job.job_id,
            status=job.status,
            progress=job.progress,
            current_step=job.current_step,
            hypotheses_generated=job.hypotheses_generated,
            total_hypotheses=job.num_hypotheses,
            started_at=job.started_at,
            completed_at=job.completed_at,
            error_message=job.error_message
        )
    
    async def get_results(self, session_id: str, job_id: str) -> Optional[HypothesisResult]:
        """Get results of a completed job."""
        job = self.jobs.get(job_id)
        
        if not job or job.session_id != session_id:
            return None
        
        return job.result
    
    async def cancel_job(self, session_id: str, job_id: str) -> bool:
        """Cancel a running job."""
        job = self.jobs.get(job_id)
        
        if not job or job.session_id != session_id:
            return False
        
        if job.status in [GenerationStatus.COMPLETED, GenerationStatus.FAILED, GenerationStatus.CANCELLED]:
            return False
        
        if job.task:
            job.task.cancel()
        
        return True
    
    async def register_websocket(self, session_id: str, websocket: WebSocket):
        """Register a WebSocket for a session."""
        self.websockets[session_id] = websocket
    
    async def unregister_websocket(self, session_id: str):
        """Unregister a WebSocket for a session."""
        if session_id in self.websockets:
            del self.websockets[session_id]

