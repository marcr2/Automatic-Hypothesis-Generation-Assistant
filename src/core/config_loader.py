"""
Configuration Loader - Centralized configuration management
Loads settings from environment variables and config files with proper precedence
"""
import os
import json
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class ExecutionConfig:
    """
    Centralized configuration for distributed system execution.
    
    Configuration hierarchy (highest to lowest priority):
    1. Environment variables
    2. config/LLM_config.json
    3. config/keys.json (for API keys)
    4. Default values
    """
    
    def __init__(self, config_path: str = "config/LLM_config.json", keys_path: str = "config/keys.json"):
        """
        Initialize configuration loader.
        
        Args:
            config_path: Path to main configuration file
            keys_path: Path to API keys file
        """
        self.config_path = config_path
        self.keys_path = keys_path
        self._config = self._load_all_config()
    
    def _load_all_config(self) -> Dict[str, Any]:
        """
        Load configuration from all sources with proper precedence.
        
        Returns:
            Complete configuration dictionary
        """
        config = {
            "execution_mode": "local",
            "llm": {},
            "embeddings": {},
            "chromadb": {}
        }
        
        # Load from LLM_config.json
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r') as f:
                    file_config = json.load(f)
                    config.update(file_config)
                    logger.info(f"📄 Loaded configuration from {self.config_path}")
            except Exception as e:
                logger.warning(f"⚠️ Failed to load {self.config_path}: {e}")
        
        # Load API keys from keys.json
        if os.path.exists(self.keys_path):
            try:
                with open(self.keys_path, 'r') as f:
                    keys = json.load(f)
                    # Merge keys into config sections
                    if "GEMINI_API_KEY" in keys and not config["llm"].get("api_key"):
                        config["llm"]["api_key"] = keys["GEMINI_API_KEY"]
                    if "GOOGLE_API_KEY" in keys and not config["embeddings"].get("google_api_key"):
                        config["embeddings"]["google_api_key"] = keys["GOOGLE_API_KEY"]
                    logger.info(f"📄 Loaded API keys from {self.keys_path}")
            except Exception as e:
                logger.warning(f"⚠️ Failed to load {self.keys_path}: {e}")
        
        # Override with environment variables
        config = self._apply_env_overrides(config)
        
        return config
    
    def _apply_env_overrides(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply environment variable overrides to configuration.
        
        Args:
            config: Base configuration dictionary
            
        Returns:
            Configuration with environment overrides applied
        """
        # Execution mode
        if os.getenv("EXECUTION_MODE"):
            config["execution_mode"] = os.getenv("EXECUTION_MODE")
        
        # ChromaDB configuration
        if os.getenv("CHROMA_HOST"):
            config["chromadb"]["host"] = os.getenv("CHROMA_HOST")
        if os.getenv("CHROMA_PORT"):
            config["chromadb"]["port"] = int(os.getenv("CHROMA_PORT"))
        
        # LLM configuration
        if os.getenv("LLM_PROVIDER"):
            config["llm"]["provider"] = os.getenv("LLM_PROVIDER")
        if os.getenv("LLM_API_BASE"):
            config["llm"]["api_base"] = os.getenv("LLM_API_BASE")
        if os.getenv("LLM_MODEL_NAME"):
            config["llm"]["model_name"] = os.getenv("LLM_MODEL_NAME")
        if os.getenv("GEMINI_API_KEY"):
            config["llm"]["api_key"] = os.getenv("GEMINI_API_KEY")
        
        # Embeddings configuration
        if os.getenv("EMBEDDINGS_PROVIDER"):
            config["embeddings"]["provider"] = os.getenv("EMBEDDINGS_PROVIDER")
        if os.getenv("EMBEDDINGS_API_BASE"):
            config["embeddings"]["api_base"] = os.getenv("EMBEDDINGS_API_BASE")
        if os.getenv("EMBEDDINGS_MODEL_NAME"):
            config["embeddings"]["model_name"] = os.getenv("EMBEDDINGS_MODEL_NAME")
        if os.getenv("GOOGLE_API_KEY"):
            config["embeddings"]["google_api_key"] = os.getenv("GOOGLE_API_KEY")
        
        return config
    
    @property
    def execution_mode(self) -> str:
        """Get execution mode: 'local' or 'distributed'"""
        return self._config.get("execution_mode", "local")
    
    @property
    def is_distributed(self) -> bool:
        """Check if running in distributed mode"""
        return self.execution_mode == "distributed"
    
    @property
    def is_local(self) -> bool:
        """Check if running in local mode"""
        return self.execution_mode == "local"
    
    def get_chromadb_config(self) -> Dict[str, Any]:
        """
        Get ChromaDB configuration.
        
        Returns:
            ChromaDB configuration dictionary
        """
        return self._config.get("chromadb", {})
    
    def get_llm_config(self) -> Dict[str, Any]:
        """
        Get LLM configuration.
        
        Returns:
            LLM configuration dictionary
        """
        return self._config.get("llm", {})
    
    def get_embeddings_config(self) -> Dict[str, Any]:
        """
        Get embeddings configuration.
        
        Returns:
            Embeddings configuration dictionary
        """
        return self._config.get("embeddings", {})
    
    def get_full_config(self) -> Dict[str, Any]:
        """
        Get complete configuration.
        
        Returns:
            Full configuration dictionary
        """
        return self._config.copy()
    
    def display_config(self):
        """Display current configuration in a readable format"""
        print("\n" + "="*60)
        print("DISTRIBUTED SYSTEM CONFIGURATION")
        print("="*60)
        
        print(f"\nExecution Mode: {self.execution_mode.upper()}")
        
        # ChromaDB configuration
        chromadb_config = self.get_chromadb_config()
        print(f"\nChromaDB:")
        if self.is_distributed:
            print(f"   Mode: Remote (HttpClient)")
            print(f"   Host: {chromadb_config.get('host', 'Not configured')}")
            print(f"   Port: {chromadb_config.get('port', 'Not configured')}")
        else:
            print(f"   Mode: Local (PersistentClient)")
            print(f"   Directory: {chromadb_config.get('persist_directory', './data/vector_db/chroma_db')}")
        
        # LLM configuration
        llm_config = self.get_llm_config()
        print(f"\nLLM:")
        print(f"   Provider: {llm_config.get('provider', 'gemini')}")
        print(f"   Model: {llm_config.get('model_name', 'gemini-2.5-flash')}")
        if llm_config.get('provider') == 'local':
            print(f"   API Base: {llm_config.get('api_base', 'Not configured')}")
        else:
            print(f"   API: Google Gemini")
            print(f"   Has Key: {'Yes' if llm_config.get('api_key') else 'No'}")
        
        # Embeddings configuration
        embeddings_config = self.get_embeddings_config()
        print(f"\nEmbeddings:")
        print(f"   Provider: {embeddings_config.get('provider', 'google')}")
        print(f"   Model: {embeddings_config.get('model_name', 'text-embedding-004')}")
        if embeddings_config.get('provider') == 'local':
            print(f"   API Base: {embeddings_config.get('api_base', 'Not configured')}")
        else:
            print(f"   API: Google text-embedding-004")
            print(f"   Has Key: {'Yes' if embeddings_config.get('google_api_key') else 'No'}")
        
        print("\n" + "="*60 + "\n")


# Global configuration instance
_global_config: Optional[ExecutionConfig] = None


def load_execution_config(force_reload: bool = False) -> ExecutionConfig:
    """
    Load or return cached execution configuration.
    
    Args:
        force_reload: Force reloading configuration from files
        
    Returns:
        ExecutionConfig instance
    """
    global _global_config
    
    if _global_config is None or force_reload:
        _global_config = ExecutionConfig()
        logger.info("✅ Execution configuration loaded")
    
    return _global_config


def get_execution_mode() -> str:
    """
    Get current execution mode.
    
    Returns:
        'local' or 'distributed'
    """
    config = load_execution_config()
    return config.execution_mode


def is_distributed_mode() -> bool:
    """
    Check if running in distributed mode.
    
    Returns:
        True if distributed mode, False otherwise
    """
    config = load_execution_config()
    return config.is_distributed


def is_local_mode() -> bool:
    """
    Check if running in local mode.
    
    Returns:
        True if local mode, False otherwise
    """
    config = load_execution_config()
    return config.is_local


def get_chromadb_config() -> Dict[str, Any]:
    """
    Get ChromaDB configuration.
    
    Returns:
        ChromaDB configuration dictionary
    """
    config = load_execution_config()
    return config.get_chromadb_config()


def get_llm_config() -> Dict[str, Any]:
    """
    Get LLM configuration.
    
    Returns:
        LLM configuration dictionary
    """
    config = load_execution_config()
    return config.get_llm_config()


def get_embeddings_config() -> Dict[str, Any]:
    """
    Get embeddings configuration.
    
    Returns:
        Embeddings configuration dictionary
    """
    config = load_execution_config()
    return config.get_embeddings_config()


def display_configuration():
    """Display current system configuration"""
    config = load_execution_config()
    config.display_config()

