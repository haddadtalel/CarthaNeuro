"""
Logging configuration for CarthaNeuro Backend
"""

import logging
import sys
from pathlib import Path
from typing import Optional
from loguru import logger as loguru_logger

from src.config.settings import settings

class InterceptHandler(logging.Handler):
    """Intercept standard logging and redirect to loguru"""
    
    def emit(self, record):
        # Get corresponding Loguru level if it exists
        try:
            level = loguru_logger.level(record.levelname).name
        except ValueError:
            level = record.levelno
            
        # Find caller from where originated the logged message
        frame, depth = logging.currentframe(), 2
        while frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1
            
        loguru_logger.opt(
            depth=depth,
            exception=record.exc_info
        ).log(level, record.getMessage())

def setup_logger(name: Optional[str] = None) -> loguru_logger:
    """
    Setup logger with console and file outputs
    
    Args:
        name: Logger name
        
    Returns:
        Configured logger instance
    """
    # Remove default handler
    loguru_logger.remove()
    
    # Add console handler with colors
    loguru_logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
               "<level>{level: <8}</level> | "
               "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
               "<level>{message}</level>",
        level=settings.log_level,
        colorize=True,
        backtrace=True,
        diagnose=True
    )
    
    # Add file handler
    loguru_logger.add(
        settings.logs_dir / settings.log_file,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}",
        level=settings.log_level,
        rotation="10 MB",
        retention="30 days",
        compression="zip",
        backtrace=True,
        diagnose=True
    )
    
    # Configure standard library logging
    logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)
    
    # Set logging levels for specific modules
    for log_name, log_level in [
        ("uvicorn", "INFO"),
        ("fastapi", "INFO"),
        ("torch", "WARNING"),
        ("transformers", "WARNING"),
        ("PIL", "WARNING"),
    ]:
        logging.getLogger(log_name).setLevel(getattr(logging, log_level))
    
    return loguru_logger