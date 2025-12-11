"""
CarthaNeuro FastAPI Backend
Multimodal AI system for brain tumor analysis combining LLM with 3D CNN classification
"""

from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import uvicorn
import logging
from pathlib import Path

from src.config.settings import settings
from src.utils.logger import setup_logger
from src.api.routes import api_router
from src.api.data_upload import data_router
from src.api.auth import auth_router
from src.api.metrics import metrics_router
from src.api.admin_models import admin_router
from src.models.model_manager import ModelManager
from src.database.mongodb_service import db_service, get_db_operations

# Setup logging
logger = setup_logger(__name__)

# Global model manager instance
model_manager = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """FastAPI lifespan context manager for startup and shutdown events"""
    global model_manager
    
    # Startup
    logger.info("Starting CarthaNeuro FastAPI Backend...")
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"Debug mode: {settings.debug}")
    
    try:
        # Initialize model manager
        model_manager = ModelManager()
        await model_manager.initialize()
        logger.info("Model manager initialized successfully")
        
        # Initialize MongoDB database service
        await db_service.initialize()
        logger.info("MongoDB database service initialized successfully")
        
        # Load models
        await model_manager.load_models()
        logger.info("All models loaded successfully")
        
        # Set model manager for API routes
        from src.api.routes import api_router, set_model_manager, initialize_services_after_model_manager
        from src.api.data_upload import data_router, set_model_manager as set_data_model_manager
        from src.api.metrics import metrics_router, set_model_manager as set_metrics_model_manager
        set_model_manager(model_manager)
        set_data_model_manager(model_manager)
        set_metrics_model_manager(model_manager)
        
        # Initialize enhanced model service and integrate with training service
        await initialize_services_after_model_manager()
        logger.info("Enhanced model service initialized and integrated with training service")
        
        yield
        
    except Exception as e:
        logger.error(f"Failed to initialize models: {str(e)}")
        raise
    finally:
        # Shutdown
        logger.info("Shutting down CarthaNeuro FastAPI Backend...")
        if model_manager:
            await model_manager.cleanup()
        # Close MongoDB connection
        await db_service.close()

# Create FastAPI app
app = FastAPI(
    title="CarthaNeuro Backend",
    description="Keras-based AI system for brain tumor analysis using saved models",
    version="1.0.0",
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(auth_router, prefix="/api/v1/auth")
app.include_router(api_router, prefix="/api/v1")
app.include_router(data_router, prefix="/api/v1/data")
app.include_router(metrics_router, prefix="/api/v1/metrics")
app.include_router(admin_router, prefix="/api/v1/admin")

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "name": "CarthaNeuro Backend",
        "version": "1.0.0",
        "status": "running",
        "models": ["saved_keras_classifier"]
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        if model_manager and model_manager.is_ready():
            return {
                "status": "healthy",
                "models_loaded": model_manager.get_loaded_models(),
                "uptime": "running"
            }
        else:
            raise HTTPException(status_code=503, detail="Service Unavailable")
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(status_code=503, detail="Service Unavailable")

if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level="info" if not settings.debug else "debug"
    )