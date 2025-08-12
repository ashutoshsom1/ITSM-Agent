"""
Error handling utilities for the ITSM AI Agent
"""
from typing import Dict, Any, Optional
from fastapi import HTTPException, status
from utils.logging import get_logger

logger = get_logger("error_handler")


class AgentError(Exception):
    """Base exception for agent-related errors"""
    
    def __init__(self, message: str, error_code: str = "AGENT_ERROR", details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)


class MemoryError(AgentError):
    """Exception for memory-related errors"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "MEMORY_ERROR", details)


class OpenAIError(AgentError):
    """Exception for OpenAI-related errors"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "OPENAI_ERROR", details)


class VisionError(AgentError):
    """Exception for vision analysis errors"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "VISION_ERROR", details)


class HumanHandoffError(AgentError):
    """Exception for human handoff errors"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "HANDOFF_ERROR", details)


class ValidationError(AgentError):
    """Exception for validation errors"""
    
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, "VALIDATION_ERROR", details)


def handle_agent_error(error: AgentError) -> HTTPException:
    """
    Convert agent errors to HTTP exceptions
    
    Args:
        error: Agent error instance
        
    Returns:
        HTTPException with appropriate status code and message
    """
    logger.error(f"Agent error: {error.error_code} - {error.message}", extra={"details": error.details})
    
    # Map error types to HTTP status codes
    status_mapping = {
        "MEMORY_ERROR": status.HTTP_500_INTERNAL_SERVER_ERROR,
        "OPENAI_ERROR": status.HTTP_502_BAD_GATEWAY,
        "VISION_ERROR": status.HTTP_502_BAD_GATEWAY,
        "HANDOFF_ERROR": status.HTTP_503_SERVICE_UNAVAILABLE,
        "VALIDATION_ERROR": status.HTTP_400_BAD_REQUEST,
        "AGENT_ERROR": status.HTTP_500_INTERNAL_SERVER_ERROR,
    }
    
    status_code = status_mapping.get(error.error_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    return HTTPException(
        status_code=status_code,
        detail={
            "error": error.error_code,
            "message": error.message,
            "details": error.details
        }
    )


def handle_generic_error(error: Exception) -> HTTPException:
    """
    Handle generic exceptions
    
    Args:
        error: Generic exception
        
    Returns:
        HTTPException with 500 status code
    """
    logger.error(f"Unexpected error: {str(error)}", exc_info=True)
    
    return HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail={
            "error": "INTERNAL_ERROR",
            "message": "An unexpected error occurred. Please try again later.",
            "details": {}
        }
    )


async def safe_execute(func, *args, **kwargs):
    """
    Safely execute a function with error handling
    
    Args:
        func: Function to execute
        *args: Function arguments
        **kwargs: Function keyword arguments
        
    Returns:
        Function result or raises appropriate HTTPException
    """
    try:
        if hasattr(func, '__call__'):
            if hasattr(func, '__await__'):
                return await func(*args, **kwargs)
            else:
                return func(*args, **kwargs)
        else:
            raise ValueError("Provided object is not callable")
    except AgentError as e:
        raise handle_agent_error(e)
    except Exception as e:
        raise handle_generic_error(e)


def validate_required_fields(data: Dict[str, Any], required_fields: list) -> None:
    """
    Validate that required fields are present in data
    
    Args:
        data: Data dictionary to validate
        required_fields: List of required field names
        
    Raises:
        ValidationError: If any required fields are missing
    """
    missing_fields = [field for field in required_fields if field not in data or data[field] is None]
    
    if missing_fields:
        raise ValidationError(
            f"Missing required fields: {', '.join(missing_fields)}",
            {"missing_fields": missing_fields}
        )
