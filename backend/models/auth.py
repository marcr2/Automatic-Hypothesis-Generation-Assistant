"""
Authentication-related Pydantic models.
"""
from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class LoginRequest(BaseModel):
    """Request model for login."""
    username: str
    password: Optional[str] = None  # Optional for demo mode
    
    class Config:
        json_schema_extra = {
            "example": {
                "username": "researcher",
                "password": "optional"
            }
        }


class LoginResponse(BaseModel):
    """Response model for successful login."""
    session_id: str
    expires_at: datetime
    message: str = "Login successful"
    
    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "abc123-def456-ghi789",
                "expires_at": "2025-11-19T12:00:00Z",
                "message": "Login successful"
            }
        }


class SessionInfo(BaseModel):
    """Session information model."""
    session_id: str
    created_at: datetime
    expires_at: datetime
    is_valid: bool
    time_remaining_minutes: int
    
    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "abc123-def456-ghi789",
                "created_at": "2025-11-19T10:00:00Z",
                "expires_at": "2025-11-19T12:00:00Z",
                "is_valid": True,
                "time_remaining_minutes": 85
            }
        }

