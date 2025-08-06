"""
Logging utilities for the ITSM AI Agent
"""
import logging
import sys
from typing import Optional
from config import get_settings

settings = get_settings()


def setup_logging(
    level: Optional[str] = None,
    format_string: Optional[str] = None
) -> logging.Logger:
    """
    Setup logging configuration
    
    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        format_string: Custom format string for log messages
    
    Returns:
        Configured logger instance
    """
    # Set log level
    log_level = level or settings.log_level
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)
    
    # Set format
    if format_string is None:
        format_string = (
            "%(asctime)s - %(name)s - %(levelname)s - "
            "%(filename)s:%(lineno)d - %(message)s"
        )
    
    # Configure logging
    logging.basicConfig(
        level=numeric_level,
        format=format_string,
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler("agent.log", mode="a")
        ]
    )
    
    # Create logger
    logger = logging.getLogger("itsm_agent")
    
    # Set third-party loggers to WARNING to reduce noise
    logging.getLogger("azure").setLevel(logging.WARNING)
    logging.getLogger("openai").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger with the specified name
    
    Args:
        name: Logger name
        
    Returns:
        Logger instance
    """
    return logging.getLogger(f"itsm_agent.{name}")


# Global logger instance
logger = setup_logging()
