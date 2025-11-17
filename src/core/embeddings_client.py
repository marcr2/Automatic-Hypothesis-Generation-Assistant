"""
Embeddings Client - Unified interface for generating embeddings
Supports both Google API and local OpenAI-compatible endpoints
"""
import os
import json
import logging
import requests
import httpx
from typing import List, Optional

logger = logging.getLogger(__name__)


class EmbeddingsClient:
    """
    Unified embeddings client that supports multiple providers:
    - Google text-embedding-004 API
    - Local OpenAI-compatible embedding endpoints (vLLM, TGI, Ollama, etc.)
    
    Configuration is loaded from:
    1. Environment variables (highest priority)
    2. config/LLM_config.json (fallback)
    3. config/keys.json (for Google API key fallback)
    """
    
    def __init__(self, config_path: str = "config/LLM_config.json", keys_path: str = "config/keys.json"):
        """
        Initialize the embeddings client with configuration.
        
        Args:
            config_path: Path to LLM configuration file
            keys_path: Path to API keys file (for backward compatibility)
        """
        self.config = self._load_config(config_path, keys_path)
        self.provider = self.config.get("provider", "google")
        self.api_base = self.config.get("api_base", "http://localhost:8001/v1")
        self.model_name = self.config.get("model_name", "nomic-embed-text")
        self.google_api_key = self.config.get("google_api_key", "")
        
        logger.info(f"✅ EmbeddingsClient initialized - Provider: {self.provider}, Model: {self.model_name}")
    
    def _load_config(self, config_path: str, keys_path: str) -> dict:
        """
        Load configuration from environment variables and config files.
        Environment variables take precedence over config files.
        
        Returns:
            Configuration dictionary
        """
        config = {}
        
        # Load from config file first
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    llm_config = json.load(f)
                    embeddings_config = llm_config.get("embeddings", {})
                    config.update(embeddings_config)
                    logger.info(f"📄 Loaded embeddings config from {config_path}")
            except Exception as e:
                logger.warning(f"⚠️ Failed to load config from {config_path}: {e}")
        
        # Load Google API key from keys.json for backward compatibility
        if os.path.exists(keys_path):
            try:
                with open(keys_path, 'r') as f:
                    keys = json.load(f)
                    if not config.get("google_api_key") and keys.get("GOOGLE_API_KEY"):
                        config["google_api_key"] = keys["GOOGLE_API_KEY"]
                        logger.info(f"📄 Loaded Google API key from {keys_path}")
            except Exception as e:
                logger.warning(f"⚠️ Failed to load keys from {keys_path}: {e}")
        
        # Override with environment variables (highest priority)
        if os.getenv("EMBEDDINGS_PROVIDER"):
            config["provider"] = os.getenv("EMBEDDINGS_PROVIDER")
        if os.getenv("EMBEDDINGS_API_BASE"):
            config["api_base"] = os.getenv("EMBEDDINGS_API_BASE")
        if os.getenv("EMBEDDINGS_MODEL_NAME"):
            config["model_name"] = os.getenv("EMBEDDINGS_MODEL_NAME")
        if os.getenv("GOOGLE_API_KEY"):
            config["google_api_key"] = os.getenv("GOOGLE_API_KEY")
        
        # Set defaults if not provided
        if "provider" not in config:
            config["provider"] = "google"
        if "model_name" not in config:
            config["model_name"] = "text-embedding-004" if config["provider"] == "google" else "nomic-embed-text"
        
        return config
    
    def get_embedding(self, text: str, retry_count: int = 0) -> Optional[List[float]]:
        """
        Get embedding vector for the given text using the configured provider.
        
        Args:
            text: Text to embed
            retry_count: Current retry attempt (for internal use)
            
        Returns:
            Embedding vector as list of floats, or None on error
        """
        if not text or not text.strip():
            logger.warning("⚠️ Empty text provided for embedding")
            return None
        
        try:
            if self.provider == "google":
                return self._get_google_embedding(text, retry_count)
            elif self.provider == "local":
                return self._get_local_embedding(text, retry_count)
            else:
                logger.error(f"❌ Unknown embeddings provider: {self.provider}")
                return None
        except Exception as e:
            logger.error(f"❌ Error getting embedding: {e}")
            return None
    
    def _get_google_embedding(self, text: str, retry_count: int = 0) -> Optional[List[float]]:
        """
        Get embedding from Google's text-embedding-004 API.
        
        Args:
            text: Text to embed
            retry_count: Current retry attempt
            
        Returns:
            Embedding vector or None on error
        """
        if not self.google_api_key:
            logger.error("❌ Google API key not configured")
            return None
        
        url = f"https://generativelanguage.googleapis.com/v1beta/models/text-embedding-004:embedContent?key={self.google_api_key}"
        headers = {"Content-Type": "application/json"}
        data = {
            "model": "models/text-embedding-004",
            "content": {"parts": [{"text": text}]}
        }
        
        try:
            response = requests.post(url, headers=headers, json=data, timeout=30)
            
            if response.status_code == 429:
                if retry_count < 3:
                    logger.warning(f"⚠️ Rate limited (attempt {retry_count + 1}/3). Waiting 60s...")
                    import time
                    time.sleep(60)
                    return self._get_google_embedding(text, retry_count + 1)
                else:
                    logger.error("❌ Max retries reached for rate limit")
                    return None
            
            response.raise_for_status()
            return response.json()["embedding"]["values"]
            
        except requests.exceptions.Timeout:
            logger.warning(f"⚠️ Timeout for text: {text[:50]}...")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"❌ Network error getting embedding: {e}")
            return None
        except Exception as e:
            logger.error(f"❌ Error parsing embedding response: {e}")
            return None
    
    def _get_local_embedding(self, text: str, retry_count: int = 0) -> Optional[List[float]]:
        """
        Get embedding from local OpenAI-compatible endpoint.
        
        Args:
            text: Text to embed
            retry_count: Current retry attempt
            
        Returns:
            Embedding vector or None on error
        """
        if not self.api_base:
            logger.error("❌ Local embeddings API base URL not configured")
            return None
        
        # Construct the embeddings endpoint
        url = f"{self.api_base.rstrip('/')}/embeddings"
        headers = {"Content-Type": "application/json"}
        data = {
            "model": self.model_name,
            "input": text
        }
        
        try:
            # Use httpx for better async support in the future
            with httpx.Client(timeout=30.0) as client:
                response = client.post(url, headers=headers, json=data)
                
                if response.status_code == 429:
                    if retry_count < 3:
                        logger.warning(f"⚠️ Rate limited (attempt {retry_count + 1}/3). Waiting 5s...")
                        import time
                        time.sleep(5)
                        return self._get_local_embedding(text, retry_count + 1)
                    else:
                        logger.error("❌ Max retries reached for rate limit")
                        return None
                
                response.raise_for_status()
                result = response.json()
                
                # Handle OpenAI-compatible response format
                if "data" in result and len(result["data"]) > 0:
                    return result["data"][0]["embedding"]
                elif "embedding" in result:
                    return result["embedding"]
                else:
                    logger.error(f"❌ Unexpected response format: {result}")
                    return None
                    
        except httpx.TimeoutException:
            logger.warning(f"⚠️ Timeout for text: {text[:50]}...")
            return None
        except httpx.HTTPError as e:
            logger.error(f"❌ HTTP error getting embedding: {e}")
            return None
        except Exception as e:
            logger.error(f"❌ Error getting local embedding: {e}")
            return None
    
    def get_embeddings_batch(self, texts: List[str]) -> List[Optional[List[float]]]:
        """
        Get embeddings for a batch of texts.
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List of embedding vectors (None for failed embeddings)
        """
        embeddings = []
        for text in texts:
            embedding = self.get_embedding(text)
            embeddings.append(embedding)
        return embeddings
    
    def get_config_info(self) -> dict:
        """
        Get current configuration information.
        
        Returns:
            Dictionary with configuration details
        """
        return {
            "provider": self.provider,
            "model_name": self.model_name,
            "api_base": self.api_base if self.provider == "local" else "Google API",
            "has_api_key": bool(self.google_api_key) if self.provider == "google" else "N/A"
        }


def get_embeddings_client() -> EmbeddingsClient:
    """
    Factory function to create and return an embeddings client instance.
    
    Returns:
        Configured EmbeddingsClient instance
    """
    return EmbeddingsClient()

