"""
Custom exceptions for the AHGA backend application.

These exceptions provide specific error types for different failure scenarios,
allowing for graceful error handling and user-friendly error messages.
"""


class AHGABaseException(Exception):
    """Base exception for all AHGA application errors."""
    
    def __init__(self, message: str, details: str = None):
        self.message = message
        self.details = details
        super().__init__(self.message)
    
    def to_dict(self) -> dict:
        """Convert exception to dictionary for JSON response."""
        result = {"error": self.message}
        if self.details:
            result["details"] = self.details
        return result


class ChromaDBUnavailableError(AHGABaseException):
    """
    Raised when ChromaDB is unavailable or connection fails.
    
    This exception allows the application to continue running even when
    ChromaDB is down, returning appropriate error messages to users
    trying to access ChromaDB-dependent features.
    """
    
    def __init__(
        self, 
        message: str = "ChromaDB database is currently unavailable",
        details: str = None,
        host: str = None,
        port: int = None
    ):
        self.host = host
        self.port = port
        
        if host and port and not details:
            details = f"Failed to connect to ChromaDB at {host}:{port}"
        
        super().__init__(message, details)
    
    def to_dict(self) -> dict:
        """Convert exception to dictionary for JSON response."""
        result = super().to_dict()
        if self.host and self.port:
            result["connection"] = {"host": self.host, "port": self.port}
        return result


class ChromaDBOperationError(AHGABaseException):
    """
    Raised when a ChromaDB operation fails (but connection is available).
    
    This covers scenarios like failed queries, collection errors, etc.
    """
    
    def __init__(
        self,
        operation: str,
        message: str = "ChromaDB operation failed",
        details: str = None
    ):
        self.operation = operation
        if not details:
            details = f"Failed during operation: {operation}"
        super().__init__(message, details)
    
    def to_dict(self) -> dict:
        """Convert exception to dictionary for JSON response."""
        result = super().to_dict()
        result["operation"] = self.operation
        return result


class LLMUnavailableError(AHGABaseException):
    """
    Raised when the LLM service is unavailable.
    """
    
    def __init__(
        self,
        message: str = "LLM service is currently unavailable",
        details: str = None,
        provider: str = None
    ):
        self.provider = provider
        if provider and not details:
            details = f"LLM provider '{provider}' is not responding"
        super().__init__(message, details)


class HypothesisGenerationError(AHGABaseException):
    """
    Raised when hypothesis generation fails.
    """
    
    def __init__(
        self,
        message: str = "Failed to generate hypothesis",
        details: str = None,
        stage: str = None
    ):
        self.stage = stage
        if stage and not details:
            details = f"Generation failed at stage: {stage}"
        super().__init__(message, details)


class SessionError(AHGABaseException):
    """
    Raised for session-related errors.
    """
    
    def __init__(
        self,
        message: str = "Session error occurred",
        details: str = None,
        session_id: str = None
    ):
        self.session_id = session_id
        super().__init__(message, details)

