"""
LLM Client - Unified interface for Large Language Model interactions
Supports both Google Gemini API and local OpenAI-compatible endpoints
"""
import os
import json
import logging
from typing import Optional, Any
from openai import OpenAI

logger = logging.getLogger(__name__)


class LLMResponse:
    """Standardized response object for LLM generations"""
    
    def __init__(self, text: str, raw_response: Any = None):
        self.text = text
        self.raw_response = raw_response


class LLMClient:
    """
    Unified LLM client that supports multiple providers:
    - Google Gemini API
    - Local OpenAI-compatible LLM endpoints (vLLM, TGI, Ollama, LM Studio, etc.)
    
    Configuration is loaded from:
    1. Environment variables (highest priority)
    2. config/LLM_config.json (fallback)
    3. config/keys.json (for Gemini API key fallback)
    """
    
    def __init__(self, config_path: str = "config/LLM_config.json", keys_path: str = "config/keys.json"):
        """
        Initialize the LLM client with configuration.
        
        Args:
            config_path: Path to LLM configuration file
            keys_path: Path to API keys file (for backward compatibility)
        """
        self.config = self._load_config(config_path, keys_path)
        self.provider = self.config.get("provider", "gemini")
        self.api_base = self.config.get("api_base", "http://localhost:11434/v1")
        self.model_name = self.config.get("model_name", "llama3")
        self.api_key = self.config.get("api_key", "")
        self.gemini_client = None
        self.openai_client = None
        
        # Initialize the appropriate client
        self._initialize_client()
        
        logger.info(f"✅ LLMClient initialized - Provider: {self.provider}, Model: {self.model_name}")
    
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
                    llm_section = llm_config.get("llm", {})
                    config.update(llm_section)
                    logger.info(f"📄 Loaded LLM config from {config_path}")
            except Exception as e:
                logger.warning(f"⚠️ Failed to load config from {config_path}: {e}")
        
        # Load Gemini API key from keys.json for backward compatibility
        if os.path.exists(keys_path):
            try:
                with open(keys_path, 'r') as f:
                    keys = json.load(f)
                    if not config.get("api_key") and keys.get("GEMINI_API_KEY"):
                        config["api_key"] = keys["GEMINI_API_KEY"]
                        logger.info(f"📄 Loaded Gemini API key from {keys_path}")
            except Exception as e:
                logger.warning(f"⚠️ Failed to load keys from {keys_path}: {e}")
        
        # Override with environment variables (highest priority)
        if os.getenv("LLM_PROVIDER"):
            config["provider"] = os.getenv("LLM_PROVIDER")
        if os.getenv("LLM_API_BASE"):
            config["api_base"] = os.getenv("LLM_API_BASE")
        if os.getenv("LLM_MODEL_NAME"):
            config["model_name"] = os.getenv("LLM_MODEL_NAME")
        if os.getenv("GEMINI_API_KEY"):
            config["api_key"] = os.getenv("GEMINI_API_KEY")
        
        # Set defaults if not provided
        if "provider" not in config:
            config["provider"] = "gemini"
        if "model_name" not in config:
            config["model_name"] = "gemini-2.5-flash" if config["provider"] == "gemini" else "llama3"
        
        return config
    
    def _initialize_client(self):
        """Initialize the appropriate client based on provider"""
        try:
            if self.provider == "gemini":
                import google.generativeai as genai
                if not self.api_key:
                    logger.error("❌ Gemini API key not configured")
                    return
                genai.configure(api_key=self.api_key)
                self.gemini_client = genai
                logger.info("✅ Gemini client initialized")
            elif self.provider == "local":
                # Initialize OpenAI client with custom base URL
                self.openai_client = OpenAI(
                    base_url=self.api_base,
                    api_key="dummy"  # Most local servers don't require a real key
                )
                logger.info(f"✅ OpenAI-compatible client initialized: {self.api_base}")
            else:
                logger.error(f"❌ Unknown LLM provider: {self.provider}")
        except Exception as e:
            logger.error(f"❌ Failed to initialize {self.provider} client: {e}")
    
    def generate_content(self, prompt: str, model: Optional[str] = None) -> LLMResponse:
        """
        Generate content using the configured LLM provider.
        
        Args:
            prompt: Text prompt to send to the LLM
            model: Optional model name override
            
        Returns:
            LLMResponse object containing generated text
        """
        if self.provider == "gemini":
            return self._gemini_generate(prompt, model)
        elif self.provider == "local":
            return self._openai_generate(prompt, model)
        else:
            logger.error(f"❌ Unknown provider: {self.provider}")
            raise ValueError(f"Unknown LLM provider: {self.provider}")
    
    def _gemini_generate(self, prompt: str, model: Optional[str] = None) -> LLMResponse:
        """
        Generate content using Google Gemini API.
        
        Args:
            prompt: Text prompt
            model: Optional model name override
            
        Returns:
            LLMResponse object
        """
        if not self.gemini_client:
            logger.error("❌ Gemini client not initialized")
            raise RuntimeError("Gemini client not initialized")
        
        try:
            model_name = model or self.model_name or "gemini-2.5-flash"
            model_instance = self.gemini_client.GenerativeModel(model_name)
            response = model_instance.generate_content(prompt)
            return LLMResponse(text=response.text, raw_response=response)
        except Exception as e:
            logger.error(f"❌ Gemini generation error: {e}")
            raise
    
    def _openai_generate(self, prompt: str, model: Optional[str] = None) -> LLMResponse:
        """
        Generate content using OpenAI-compatible API.
        
        Args:
            prompt: Text prompt
            model: Optional model name override
            
        Returns:
            LLMResponse object
        """
        if not self.openai_client:
            logger.error("❌ OpenAI-compatible client not initialized")
            raise RuntimeError("OpenAI-compatible client not initialized")
        
        try:
            model_name = model or self.model_name or "llama3"
            response = self.openai_client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=4096
            )
            text = response.choices[0].message.content
            return LLMResponse(text=text, raw_response=response)
        except Exception as e:
            logger.error(f"❌ OpenAI-compatible generation error: {e}")
            raise
    
    def GenerativeModel(self, model_name: str):
        """
        Compatibility method that returns a model wrapper for the specified model.
        This mimics the Gemini API's GenerativeModel interface.
        
        Args:
            model_name: Name of the model to use
            
        Returns:
            ModelWrapper instance
        """
        return ModelWrapper(self, model_name)
    
    def get_config_info(self) -> dict:
        """
        Get current configuration information.
        
        Returns:
            Dictionary with configuration details
        """
        return {
            "provider": self.provider,
            "model_name": self.model_name,
            "api_base": self.api_base if self.provider == "local" else "Gemini API",
            "has_api_key": bool(self.api_key) if self.provider == "gemini" else "N/A",
            "is_initialized": self.gemini_client is not None or self.openai_client is not None
        }


class ModelWrapper:
    """
    Wrapper class to provide Gemini-like interface for any LLM provider.
    This ensures backward compatibility with existing code.
    """
    
    def __init__(self, llm_client: LLMClient, model_name: str):
        self.llm_client = llm_client
        self.model_name = model_name
    
    def generate_content(self, prompt: str) -> LLMResponse:
        """
        Generate content using the wrapped model.
        
        Args:
            prompt: Text prompt
            
        Returns:
            LLMResponse object
        """
        return self.llm_client.generate_content(prompt, model=self.model_name)


def get_llm_client() -> LLMClient:
    """
    Factory function to create and return an LLM client instance.
    
    Returns:
        Configured LLMClient instance
    """
    return LLMClient()

