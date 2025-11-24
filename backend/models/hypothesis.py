"""
Hypothesis generation-related Pydantic models.
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class GenerationStatus(str, Enum):
    """Status of hypothesis generation."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class HypothesisGenerateRequest(BaseModel):
    """Request model for hypothesis generation."""
    research_topic: str = Field(..., min_length=5, max_length=500)
    num_hypotheses: int = Field(default=10, ge=1, le=50)
    advanced_options: Optional[Dict[str, Any]] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "research_topic": "UBR-5 role in cancer immunotherapy",
                "num_hypotheses": 10,
                "advanced_options": {
                    "focus_areas": ["molecular mechanisms", "clinical applications"]
                }
            }
        }


class HypothesisGenerateResponse(BaseModel):
    """Response model for hypothesis generation request."""
    job_id: str
    status: GenerationStatus
    message: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "job_id": "gen_abc123",
                "status": "pending",
                "message": "Hypothesis generation job created"
            }
        }


class HypothesisStatus(BaseModel):
    """Status model for hypothesis generation job."""
    job_id: str
    status: GenerationStatus
    progress: float = Field(ge=0.0, le=100.0)
    current_step: str
    hypotheses_generated: int = 0
    total_hypotheses: int = 0
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "job_id": "gen_abc123",
                "status": "in_progress",
                "progress": 45.5,
                "current_step": "Generating hypothesis 5/10",
                "hypotheses_generated": 5,
                "total_hypotheses": 10,
                "started_at": "2025-11-19T10:05:00Z"
            }
        }


class HypothesisCitation(BaseModel):
    """Citation information for a hypothesis."""
    title: str
    authors: List[str]
    journal: Optional[str] = None
    year: Optional[int] = None
    doi: Optional[str] = None
    pmid: Optional[str] = None
    url: Optional[str] = None


class HypothesisScores(BaseModel):
    """Scoring information for a hypothesis."""
    novelty: float = Field(ge=0.0, le=5.0)
    accuracy: float = Field(ge=0.0, le=5.0)
    relevancy: float = Field(ge=0.0, le=5.0)
    feasibility: Optional[float] = Field(default=None, ge=0.0, le=5.0)
    overall: float = Field(ge=0.0, le=5.0)


class HypothesisItem(BaseModel):
    """Individual hypothesis with metadata."""
    id: int
    hypothesis_text: str
    rationale: str
    scores: HypothesisScores
    citations: List[HypothesisCitation]
    key_concepts: List[str]
    experimental_approach: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": 1,
                "hypothesis_text": "UBR-5 modulates PD-L1 expression through ubiquitination...",
                "rationale": "Based on literature showing UBR-5's role in protein degradation...",
                "scores": {
                    "novelty": 4.5,
                    "accuracy": 4.0,
                    "relevancy": 5.0,
                    "feasibility": 3.5,
                    "overall": 4.25
                },
                "citations": [],
                "key_concepts": ["ubiquitination", "PD-L1", "immune checkpoint"]
            }
        }


class HypothesisResult(BaseModel):
    """Complete result of hypothesis generation."""
    job_id: str
    status: GenerationStatus
    research_topic: str
    hypotheses: List[HypothesisItem]
    total_count: int
    generated_at: datetime
    metadata: Optional[Dict[str, Any]] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "job_id": "gen_abc123",
                "status": "completed",
                "research_topic": "UBR-5 role in cancer immunotherapy",
                "hypotheses": [],
                "total_count": 10,
                "generated_at": "2025-11-19T10:15:00Z"
            }
        }

