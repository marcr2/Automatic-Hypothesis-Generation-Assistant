"""
Configuration Loader - Centralized configuration management
Loads settings from environment variables and config files with proper precedence
Supports machine profiles for distributed deployments
"""
import os
import json
import logging
import socket
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
    
    def __init__(self, config_path: str = "config/LLM_config.json", keys_path: str = "config/keys.json", profile: Optional[str] = None):
        """
        Initialize configuration loader.
        
        Args:
            config_path: Path to main configuration file
            keys_path: Path to API keys file
            profile: Machine profile name (m3, mystery, or auto-detect)
        """
        self.config_path = config_path
        self.keys_path = keys_path
        self.profile = profile or os.getenv("MACHINE_PROFILE", "auto")
        self.machine_name = None
        self._config = self._load_all_config()
    
    def _load_all_config(self) -> Dict[str, Any]:
        """
        Load configuration from all sources with proper precedence.
        
        Priority (highest to lowest):
        1. Environment variables
        2. Machine profile (deploy/*/config_*.json)
        3. Base config (config/LLM_config.json)
        4. API keys (config/keys.json)
        5. Default values
        
        Returns:
            Complete configuration dictionary
        """
        config = {
            "execution_mode": "local",
            "llm": {},
            "embeddings": {},
            "chromadb": {},
            "paths": {},
            "resources": {}
        }
        
        # Load from base LLM_config.json
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r') as f:
                    file_config = json.load(f)
                    config.update(file_config)
                    logger.info(f"📄 Loaded base configuration from {self.config_path}")
            except Exception as e:
                logger.warning(f"⚠️ Failed to load {self.config_path}: {e}")
        
        # Load machine profile (if specified or auto-detected)
        profile_config = self._load_machine_profile()
        if profile_config:
            # Deep merge profile config into base config
            for key, value in profile_config.items():
                if isinstance(value, dict) and key in config:
                    config[key].update(value)
                else:
                    config[key] = value
            self.machine_name = profile_config.get("machine_name")
            logger.info(f"✅ Loaded machine profile: {self.machine_name}")
        
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
        
        # Override with environment variables (highest priority)
        config = self._apply_env_overrides(config)
        
        return config
    
    def _load_machine_profile(self) -> Optional[Dict[str, Any]]:
        """
        Load machine-specific profile configuration.
        
        Returns:
            Profile configuration dictionary or None
        """
        profile_name = self.profile
        
        # Auto-detect profile if requested
        if profile_name == "auto":
            profile_name = self._detect_machine_profile()
            if not profile_name:
                return None
        
        # Skip if no profile specified
        if not profile_name or profile_name == "none":
            return None
        
        # Build profile config path
        profile_path = f"deploy/{profile_name}/config_{profile_name}.json"
        
        if not os.path.exists(profile_path):
            logger.warning(f"⚠️ Machine profile not found: {profile_path}")
            return None
        
        try:
            with open(profile_path, 'r') as f:
                profile_config = json.load(f)
                logger.info(f"📄 Loaded machine profile from {profile_path}")
                return profile_config
        except Exception as e:
            logger.error(f"❌ Failed to load machine profile {profile_path}: {e}")
            return None
    
    def _detect_machine_profile(self) -> Optional[str]:
        """
        Auto-detect machine profile based on hostname or environment.
        
        Returns:
            Profile name (m3, mystery) or None
        """
        # Check environment variable first
        env_profile = os.getenv("MACHINE_PROFILE")
        if env_profile and env_profile != "auto":
            return env_profile
        
        # Detect based on hostname
        hostname = socket.gethostname().lower()
        
        if "m3" in hostname:
            logger.info(f"🔍 Auto-detected profile: m3 (hostname: {hostname})")
            return "m3"
        elif "mystery" in hostname:
            logger.info(f"🔍 Auto-detected profile: mystery (hostname: {hostname})")
            return "mystery"
        
        # Check if specific services are running to infer machine role
        # This is a fallback detection method
        try:
            import requests
            # Try to detect vLLM server (M3)
            try:
                response = requests.get("http://localhost:11434/v1/models", timeout=1)
                if response.status_code == 200:
                    logger.info(f"🔍 Auto-detected profile: m3 (vLLM server found)")
                    return "m3"
            except:
                pass
            
            # Try to detect ChromaDB server (Mystery)
            try:
                response = requests.get("http://localhost:8000/api/v1/heartbeat", timeout=1)
                if response.status_code == 200:
                    logger.info(f"🔍 Auto-detected profile: mystery (ChromaDB server found)")
                    return "mystery"
            except:
                pass
        except ImportError:
            pass
        
        logger.info("ℹ️ Could not auto-detect machine profile")
        return None
    
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
        
        # Machine profile
        if self.machine_name:
            print(f"\nMachine Profile: {self.machine_name.upper()}")
        else:
            print(f"\nMachine Profile: Not configured (using default)")
        
        print(f"Execution Mode: {self.execution_mode.upper()}")
        
        # ChromaDB configuration
        chromadb_config = self.get_chromadb_config()
        print(f"\nChromaDB:")
        if self.is_distributed or self.execution_mode == "chromadb_server":
            if self.execution_mode == "chromadb_server":
                print(f"   Mode: Server")
                print(f"   Host: {chromadb_config.get('host', '0.0.0.0')}")
                print(f"   Port: {chromadb_config.get('port', '8000')}")
                print(f"   Directory: {chromadb_config.get('persist_directory', 'Not configured')}")
            else:
                print(f"   Mode: Remote (HttpClient)")
                print(f"   Host: {chromadb_config.get('host', 'Not configured')}")
                print(f"   Port: {chromadb_config.get('port', 'Not configured')}")
        else:
            print(f"   Mode: Local (PersistentClient)")
            print(f"   Directory: {chromadb_config.get('persist_directory', './data/vector_db/chroma_db')}")
        
        # LLM configuration
        llm_config = self.get_llm_config()
        if llm_config:
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
        if embeddings_config:
            print(f"\nEmbeddings:")
            print(f"   Provider: {embeddings_config.get('provider', 'google')}")
            print(f"   Model: {embeddings_config.get('model_name', 'text-embedding-004')}")
            if embeddings_config.get('provider') == 'local':
                print(f"   API Base: {embeddings_config.get('api_base', 'Not configured')}")
            else:
                print(f"   API: Google text-embedding-004")
                print(f"   Has Key: {'Yes' if embeddings_config.get('google_api_key') else 'No'}")
        
        # Paths configuration
        paths_config = self._config.get("paths", {})
        if paths_config:
            print(f"\nData Paths:")
            for path_name, path_value in paths_config.items():
                print(f"   {path_name}: {path_value}")
        
        # Resources configuration
        resources_config = self._config.get("resources", {})
        if resources_config:
            print(f"\nResources:")
            for resource_name, resource_value in resources_config.items():
                print(f"   {resource_name}: {resource_value}")
        
        print("\n" + "="*60 + "\n")


# Global configuration instance
_global_config: Optional[ExecutionConfig] = None


def load_execution_config(force_reload: bool = False, profile: Optional[str] = None) -> ExecutionConfig:
    """
    Load or return cached execution configuration.
    
    Args:
        force_reload: Force reloading configuration from files
        profile: Machine profile name (m3, mystery, auto, or none)
        
    Returns:
        ExecutionConfig instance
    """
    global _global_config
    
    if _global_config is None or force_reload:
        _global_config = ExecutionConfig(profile=profile)
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


def get_machine_profile() -> Optional[str]:
    """
    Get current machine profile name.
    
    Returns:
        Machine profile name or None
    """
    config = load_execution_config()
    return config.machine_name


def list_available_profiles() -> list:
    """
    List available machine profiles.
    
    Returns:
        List of available profile names
    """
    profiles = []
    deploy_dir = "deploy"
    
    if os.path.exists(deploy_dir):
        for item in os.listdir(deploy_dir):
            profile_path = os.path.join(deploy_dir, item)
            config_file = os.path.join(profile_path, f"config_{item}.json")
            if os.path.isdir(profile_path) and os.path.exists(config_file):
                profiles.append(item)
    
    return profiles


def validate_profile(profile_name: str) -> bool:
    """
    Validate that a machine profile exists and is properly configured.
    
    Args:
        profile_name: Profile name to validate
        
    Returns:
        True if valid, False otherwise
    """
    if not profile_name or profile_name in ["auto", "none"]:
        return True
    
    profile_path = f"deploy/{profile_name}/config_{profile_name}.json"
    
    if not os.path.exists(profile_path):
        logger.error(f"❌ Profile configuration not found: {profile_path}")
        return False
    
    try:
        with open(profile_path, 'r') as f:
            config = json.load(f)
            
            # Validate required fields
            if "machine_name" not in config:
                logger.error(f"❌ Profile missing 'machine_name' field")
                return False
            
            if "execution_mode" not in config:
                logger.error(f"❌ Profile missing 'execution_mode' field")
                return False
            
            logger.info(f"✅ Profile '{profile_name}' is valid")
            return True
    except Exception as e:
        logger.error(f"❌ Failed to validate profile {profile_name}: {e}")
        return False

