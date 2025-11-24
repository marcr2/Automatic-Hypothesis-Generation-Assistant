"""
Authentication API endpoints.
"""
from fastapi import APIRouter, HTTPException, Depends, Request, Response
from fastapi.security import HTTPBearer
from typing import Optional
import logging

from models.auth import LoginRequest, LoginResponse, SessionInfo
from services.session_service import SessionService

logger = logging.getLogger(__name__)
router = APIRouter()
security = HTTPBearer(auto_error=False)

# Initialize session service
session_service = SessionService()


async def get_session_id(request: Request) -> Optional[str]:
    """Extract session ID from cookie or Authorization header."""
    # Try cookie first
    session_id = request.cookies.get("session_id")
    if session_id:
        return session_id
    
    # Try Authorization header
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        return auth_header.replace("Bearer ", "")
    
    return None


@router.post("/login", response_model=LoginResponse)
async def login(request: Request, login_data: LoginRequest, response: Response):
    """
    Create a new session for a user.
    
    - Simple username-based authentication (password optional for demo mode)
    - Creates ephemeral session
    - Returns session token
    """
    try:
        # Get client information
        client_ip = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "unknown")
        
        # Create session
        session = await session_service.create_session(
            username=login_data.username,
            ip_address=client_ip,
            user_agent=user_agent
        )
        
        # Set session cookie
        response.set_cookie(
            key="session_id",
            value=session.session_id,
            httponly=True,
            secure=False,  # Set to True in production with HTTPS
            samesite="lax",
            max_age=session.timeout_seconds
        )
        
        logger.info(f"✅ Session created for user: {login_data.username} (IP: {client_ip})")
        
        return LoginResponse(
            session_id=session.session_id,
            expires_at=session.expires_at,
            message=f"Welcome, {login_data.username}!"
        )
        
    except Exception as e:
        logger.error(f"❌ Login error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to create session")


@router.post("/logout")
async def logout(request: Request, response: Response):
    """
    End a session and cleanup data.
    
    - Removes session
    - Cleans up temporary files
    - Clears session cookie
    """
    session_id = await get_session_id(request)
    
    if not session_id:
        raise HTTPException(status_code=401, detail="No active session")
    
    try:
        # End session
        await session_service.end_session(session_id, logout_type="manual")
        
        # Clear cookie
        response.delete_cookie("session_id")
        
        logger.info(f"✅ Session ended: {session_id}")
        
        return {"message": "Logged out successfully"}
        
    except Exception as e:
        logger.error(f"❌ Logout error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to end session")


@router.get("/session", response_model=SessionInfo)
async def get_session_info(request: Request):
    """
    Get current session information.
    
    - Validates session
    - Returns session details
    - Returns time remaining
    """
    session_id = await get_session_id(request)
    
    if not session_id:
        raise HTTPException(status_code=401, detail="No active session")
    
    session = await session_service.get_session(session_id)
    
    if not session:
        raise HTTPException(status_code=401, detail="Invalid or expired session")
    
    if not session.is_valid():
        await session_service.end_session(session_id, logout_type="expired")
        raise HTTPException(status_code=401, detail="Session expired")
    
    return SessionInfo(
        session_id=session.session_id,
        created_at=session.created_at,
        expires_at=session.expires_at,
        is_valid=True,
        time_remaining_minutes=session.get_remaining_minutes()
    )


async def require_session(request: Request) -> str:
    """Dependency to require valid session."""
    session_id = await get_session_id(request)
    
    if not session_id:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    session = await session_service.get_session(session_id)
    
    if not session or not session.is_valid():
        raise HTTPException(status_code=401, detail="Invalid or expired session")
    
    # Update last activity
    await session_service.update_activity(session_id)
    
    return session_id

