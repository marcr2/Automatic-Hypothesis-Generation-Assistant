"""
Configuration management for the web application backend.

SECURITY NOTE: The SECRET_KEY must be set via environment variable in production.
Generate a secure key with: openssl rand -hex 32
"""
import os
import secrets
import logging
from pydantic_settings import BaseSettings
from typing import List

logger = logging.getLogger(__name__)

# Insecure default key - only used in development
_INSECURE_DEFAULT_KEY = "dev-only-insecure-key-do-not-use-in-production"


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Server Configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    secret_key: str = _INSECURE_DEFAULT_KEY
    session_timeout_hours: int = 2
    cleanup_interval_minutes: int = 30
    
    # Environment mode
    environment: str = "development"  # "development" or "production"
    
    # CORS Settings
    allowed_origins: str = "http://localhost:3000,http://127.0.0.1:3000"
    
    # ChromaDB Configuration
    execution_mode: str = "distributed"
    chroma_host: str = "localhost"
    chroma_port: int = 8000
    
    # LLM Configuration
    llm_provider: str = "local"
    llm_api_base: str = "http://localhost:11434/v1"
    llm_model_name: str = "llama3"
    
    # Embeddings Configuration
    embeddings_provider: str = "local"
    embeddings_api_base: str = "http://localhost:11434/v1"
    embeddings_model_name: str = "nomic-embed-text"
    
    # API Keys (if using Gemini)
    gemini_api_key: str = ""
    google_api_key: str = ""
    
    # Rate Limiting Configuration
    max_requests_per_minute: int = 60  # General API rate limit per IP
    max_generations_per_hour: int = 5  # Hypothesis generation rate limit per session
    login_rate_limit: int = 10  # Login attempts per minute per IP
    max_concurrent_generations: int = 3
    
    # Storage Paths
    embeddings_base_path: str = "../data/embeddings"
    temp_sessions_path: str = "./temp_sessions"
    logs_db_path: str = "./logs/sessions.db"
    config_path: str = "../config"
    
    # Logging Configuration
    debug_mode: bool = False
    log_level: str = "INFO"
    log_dir: str = "./logs"
    log_max_bytes: int = 10485760  # 10MB
    log_backup_count: int = 5
    
    class Config:
        env_file = ".env"
        case_sensitive = False
    
    def get_allowed_origins_list(self) -> List[str]:
        """Parse allowed origins from comma-separated string."""
        return [origin.strip() for origin in self.allowed_origins.split(",")]
    
    def validate_security(self) -> bool:
        """
        Validate security-critical settings.
        
        Returns:
            True if security settings are valid
            
        Raises:
            ValueError: If security settings are invalid in production
        """
        is_production = self.environment.lower() == "production"
        is_insecure_key = (
            self.secret_key == _INSECURE_DEFAULT_KEY or 
            "development" in self.secret_key.lower() or
            "insecure" in self.secret_key.lower() or
            len(self.secret_key) < 32
        )
        
        if is_production and is_insecure_key:
            raise ValueError(
                "SECURITY ERROR: SECRET_KEY must be set to a secure random value in production!\n"
                "Generate one with: openssl rand -hex 32\n"
                "Then set it: export SECRET_KEY=your_generated_key"
            )
        
        if is_insecure_key:
            logger.warning(
                "SECURITY WARNING: Using insecure default SECRET_KEY. "
                "This is only acceptable in development. "
                "Set SECRET_KEY environment variable for production."
            )
        
        return True


# Global settings instance
settings = Settings()

# Validate security on import (will raise in production if misconfigured)
try:
    settings.validate_security()
except ValueError as e:
    logger.error(str(e))
    # In production, we should fail fast
    if settings.environment.lower() == "production":
        raise

