"""
Background cleanup service for expired sessions.
"""
import asyncio
import logging
from typing import Optional

from config import settings
from services.session_service import SessionService

logger = logging.getLogger(__name__)


class CleanupService:
    """Background service for cleaning up expired sessions."""
    
    def __init__(self):
        self.session_service = SessionService()
        self.cleanup_task: Optional[asyncio.Task] = None
        self.running = False
    
    async def start(self):
        """Start the cleanup service."""
        if self.running:
            logger.warning("⚠️ Cleanup service already running")
            return
        
        self.running = True
        self.cleanup_task = asyncio.create_task(self._cleanup_loop())
        logger.info("✅ Cleanup service started")
    
    async def stop(self):
        """Stop the cleanup service."""
        if not self.running:
            return
        
        self.running = False
        
        if self.cleanup_task:
            self.cleanup_task.cancel()
            try:
                await self.cleanup_task
            except asyncio.CancelledError:
                pass
        
        logger.info("✅ Cleanup service stopped")
    
    async def _cleanup_loop(self):
        """Main cleanup loop."""
        interval_seconds = settings.cleanup_interval_minutes * 60
        
        while self.running:
            try:
                await asyncio.sleep(interval_seconds)
                
                if not self.running:
                    break
                
                logger.info("🧹 Running session cleanup...")
                await self.session_service.cleanup_expired_sessions()
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"❌ Error in cleanup loop: {e}", exc_info=True)
                # Continue running despite errors
                await asyncio.sleep(60)  # Wait a minute before retry

