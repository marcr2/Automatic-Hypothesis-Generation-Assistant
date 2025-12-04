"""
Session management service for handling user sessions and ephemeral data.

Security: Uses cryptographically secure session token generation.
"""
import os
import shutil
import secrets
import re
from datetime import datetime, timedelta
from typing import Dict, Optional
from dataclasses import dataclass
import aiosqlite
import logging
from pathlib import Path

from config import settings

logger = logging.getLogger(__name__)

# Session ID format: 43 characters of URL-safe base64 (256 bits of entropy)
SESSION_ID_LENGTH = 32  # bytes, produces 43 character token
SESSION_ID_PATTERN = re.compile(r'^[A-Za-z0-9_-]{43}$')


@dataclass
class Session:
    """Session data class."""
    session_id: str
    username: str
    created_at: datetime
    expires_at: datetime
    ip_address: str
    user_agent: str
    timeout_seconds: int
    
    def is_valid(self) -> bool:
        """Check if session is still valid."""
        return datetime.utcnow() < self.expires_at
    
    def get_remaining_minutes(self) -> int:
        """Get remaining time in minutes."""
        if not self.is_valid():
            return 0
        remaining = self.expires_at - datetime.utcnow()
        return int(remaining.total_seconds() / 60)


class SessionService:
    """Service for managing user sessions."""
    
    def __init__(self):
        self.sessions: Dict[str, Session] = {}
        self.db_path = settings.logs_db_path
        self._ensure_db()
    
    def _ensure_db(self):
        """Ensure database and tables exist."""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        # Database will be created on first connection
    
    async def _init_db(self):
        """Initialize database tables."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    id TEXT PRIMARY KEY,
                    username TEXT,
                    ip_address TEXT,
                    user_agent TEXT,
                    created_at TIMESTAMP,
                    ended_at TIMESTAMP,
                    logout_type TEXT
                )
            """)
            await db.execute("""
                CREATE TABLE IF NOT EXISTS actions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT,
                    action_type TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    metadata TEXT
                )
            """)
            await db.commit()
    
    @staticmethod
    def is_valid_session_id(session_id: str) -> bool:
        """
        Validate session ID format.
        
        Security: Ensures session IDs match expected format to prevent
        injection attacks and identify invalid/forged session IDs.
        """
        if not session_id or not isinstance(session_id, str):
            return False
        return bool(SESSION_ID_PATTERN.match(session_id))
    
    async def create_session(
        self,
        username: str,
        ip_address: str,
        user_agent: str
    ) -> Session:
        """
        Create a new session with cryptographically secure session ID.
        
        Security: Uses secrets.token_urlsafe() for unpredictable session IDs.
        """
        await self._init_db()
        
        # Generate cryptographically secure session ID
        # 32 bytes = 256 bits of entropy, encoded as URL-safe base64 (43 chars)
        session_id = secrets.token_urlsafe(SESSION_ID_LENGTH)
        created_at = datetime.utcnow()
        timeout_seconds = settings.session_timeout_hours * 3600
        expires_at = created_at + timedelta(seconds=timeout_seconds)
        
        session = Session(
            session_id=session_id,
            username=username,
            created_at=created_at,
            expires_at=expires_at,
            ip_address=ip_address,
            user_agent=user_agent,
            timeout_seconds=timeout_seconds
        )
        
        # Store in memory
        self.sessions[session_id] = session
        
        # Create session directory
        session_dir = os.path.join(settings.temp_sessions_path, session_id)
        os.makedirs(session_dir, exist_ok=True)
        os.makedirs(os.path.join(session_dir, "exports"), exist_ok=True)
        os.makedirs(os.path.join(session_dir, "results"), exist_ok=True)
        
        # Log to database
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "INSERT INTO sessions (id, username, ip_address, user_agent, created_at) VALUES (?, ?, ?, ?, ?)",
                (session_id, username, ip_address, user_agent, created_at)
            )
            await db.commit()
        
        logger.info(f"✅ Session created: {session_id} for {username}")
        return session
    
    async def get_session(self, session_id: str) -> Optional[Session]:
        """
        Get session by ID.
        
        Security: Validates session ID format before lookup.
        """
        # Validate session ID format to prevent attacks
        if not self.is_valid_session_id(session_id):
            logger.warning(f"Invalid session ID format attempted: {session_id[:20] if session_id else 'None'}...")
            return None
        
        return self.sessions.get(session_id)
    
    async def update_activity(self, session_id: str):
        """Update session last activity (could extend timeout if needed)."""
        session = self.sessions.get(session_id)
        if session:
            # Optional: Extend session on activity
            # session.expires_at = datetime.utcnow() + timedelta(seconds=session.timeout_seconds)
            pass
    
    async def end_session(self, session_id: str, logout_type: str = "manual"):
        """End a session and cleanup resources."""
        session = self.sessions.get(session_id)
        
        if not session:
            logger.warning(f"⚠️ Attempted to end non-existent session: {session_id}")
            return
        
        # Remove from memory
        del self.sessions[session_id]
        
        # Cleanup session directory
        session_dir = os.path.join(settings.temp_sessions_path, session_id)
        if os.path.exists(session_dir):
            try:
                shutil.rmtree(session_dir)
                logger.info(f"🗑️ Cleaned up session directory: {session_id}")
            except Exception as e:
                logger.error(f"❌ Error cleaning up session {session_id}: {e}")
        
        # Log to database
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute(
                    "UPDATE sessions SET ended_at = ?, logout_type = ? WHERE id = ?",
                    (datetime.utcnow(), logout_type, session_id)
                )
                await db.commit()
        except Exception as e:
            logger.error(f"❌ Error logging session end: {e}")
        
        logger.info(f"✅ Session ended: {session_id} ({logout_type})")
    
    async def log_action(self, session_id: str, action_type: str, metadata: Optional[str] = None):
        """Log a session action."""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute(
                    "INSERT INTO actions (session_id, action_type, metadata) VALUES (?, ?, ?)",
                    (session_id, action_type, metadata)
                )
                await db.commit()
        except Exception as e:
            logger.error(f"❌ Error logging action: {e}")
    
    async def cleanup_expired_sessions(self):
        """Cleanup all expired sessions."""
        expired_sessions = [
            session_id
            for session_id, session in self.sessions.items()
            if not session.is_valid()
        ]
        
        for session_id in expired_sessions:
            await self.end_session(session_id, logout_type="expired")
        
        if expired_sessions:
            logger.info(f"🧹 Cleaned up {len(expired_sessions)} expired sessions")
    
    def get_session_path(self, session_id: str) -> str:
        """Get the file system path for a session."""
        return os.path.join(settings.temp_sessions_path, session_id)

