"""
Configuration management for the web application backend.
"""
import os
from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Server Configuration
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    secret_key: str = "development-secret-key-please-change-in-production"
    session_timeout_hours: int = 2
    cleanup_interval_minutes: int = 30
    
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
    
    # Rate Limiting
    max_requests_per_minute: int = 10
    max_concurrent_generations: int = 3
    
    # Storage Paths
    embeddings_base_path: str = "../data/embeddings"
    temp_sessions_path: str = "./temp_sessions"
    logs_db_path: str = "./logs/sessions.db"
    config_path: str = "../config"
    
    class Config:
        env_file = ".env"
        case_sensitive = False
    
    def get_allowed_origins_list(self) -> List[str]:
        """Parse allowed origins from comma-separated string."""
        return [origin.strip() for origin in self.allowed_origins.split(",")]


# Global settings instance
settings = Settings()

