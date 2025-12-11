"""
Startup and shutdown handlers for the application
"""
import asyncio
import atexit
import signal
import sys
from typing import Optional
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

# Global references for cleanup
_enhanced_model_service = None
_model_manager = None

def set_services_for_cleanup(enhanced_model_service=None, model_manager=None):
    """Set services for cleanup on shutdown"""
    global _enhanced_model_service, _model_manager
    _enhanced_model_service = enhanced_model_service
    _model_manager = model_manager

async def cleanup_on_shutdown():
    """Cleanup function called on application shutdown"""
    logger.info("Starting application shutdown cleanup...")
    
    try:
        # Cleanup enhanced model service (auto-saved models)
        if _enhanced_model_service:
            logger.info("Cleaning up auto-saved models...")
            cleaned_count = await _enhanced_model_service.cleanup_auto_saved_models()
            logger.info(f"Cleaned up {cleaned_count} auto-saved models")
        
        # Cleanup model manager
        if _model_manager:
            logger.info("Cleaning up model manager...")
            await _model_manager.cleanup()
            logger.info("Model manager cleanup completed")
        
        logger.info("Application shutdown cleanup completed successfully")
        
    except Exception as e:
        logger.error(f"Error during shutdown cleanup: {str(e)}")

def setup_shutdown_handlers():
    """Setup shutdown signal handlers"""
    try:
        # Register cleanup function for normal exit
        atexit.register(lambda: asyncio.run(cleanup_on_shutdown()))
        
        # Register signal handlers for graceful shutdown
        def signal_handler(signum, frame):
            logger.info(f"Received signal {signum}, starting graceful shutdown...")
            asyncio.run(cleanup_on_shutdown())
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        logger.info("Shutdown handlers registered successfully")
        
    except Exception as e:
        logger.error(f"Failed to setup shutdown handlers: {str(e)}")

def register_enhanced_service_for_cleanup(enhanced_service):
    """Register enhanced model service for cleanup on shutdown"""
    global _enhanced_model_service
    _enhanced_model_service = enhanced_service
    logger.info("Enhanced model service registered for shutdown cleanup")

async def startup_initialization():
    """Initialize application on startup"""
    logger.info("Starting application initialization...")
    
    try:
        # Additional startup initialization can be added here
        logger.info("Application startup initialization completed")
        
    except Exception as e:
        logger.error(f"Error during startup initialization: {str(e)}")
        raise