#!/usr/bin/env python3
"""
Startup script for the ITSM AI Agent
"""
import asyncio
import uvicorn
from config import get_settings
from utils.logging import setup_logging, get_logger

# Setup logging
logger = setup_logging()

async def startup():
    """Application startup tasks"""
    logger.info("Starting ITSM AI Agent...")
    
    # Validate configuration
    settings = get_settings()
    
    # Check required environment variables
    required_configs = [
        'AZURE_OPENAI_ENDPOINT',
        'AZURE_OPENAI_KEY',
        'COSMOS_ENDPOINT',
        'COSMOS_KEY'
    ]
    
    missing_configs = []
    for config in required_configs:
        if not getattr(settings, config.lower(), None):
            missing_configs.append(config)
    
    if missing_configs:
        logger.error(f"Missing required configuration: {', '.join(missing_configs)}")
        logger.error("Please check your environment variables or .env file")
        return False
    
    logger.info("Configuration validated successfully")
    return True

def main():
    """Main entry point"""
    # Run startup checks
    startup_success = asyncio.run(startup())
    
    if not startup_success:
        logger.error("Startup failed. Exiting...")
        return
    
    # Get settings
    settings = get_settings()
    
    # Configure uvicorn
    config = uvicorn.Config(
        "main:app",
        host="0.0.0.0",
        port=8000,
        log_level=settings.log_level.lower(),
        reload=settings.debug,
        workers=1 if settings.debug else 4,
        access_log=True
    )
    
    # Start server
    server = uvicorn.Server(config)
    logger.info("Starting server on http://0.0.0.0:8000")
    server.run()

if __name__ == "__main__":
    main()
