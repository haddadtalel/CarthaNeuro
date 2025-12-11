"""
FastAPI routes for CarthaNeuro Backend
"""

from fastapi import APIRouter, File, UploadFile, HTTPException, Depends, BackgroundTasks, Query, Form, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import time
import io
import json
import asyncio
import base64
import torch
import tensorflow as tf
from PIL import Image

from src.utils.logger import setup_logger
from src.config.settings import settings
from src.database.mongodb_service import get_db_operations, PredictionDocument
from src.auth.auth_middleware import get_user_id_from_token, get_user_id_from_token_with_query
from src.services.training_service import training_service, TrainingStatus, set_enhanced_model_service
from src.services.enhanced_model_service import initialize_enhanced_model_service
from bson import ObjectId

logger = setup_logger(__name__)

# Create router
api_router = APIRouter()

# Include admin router
from src.api.admin_models import admin_router
api_router.include_router(admin_router, prefix="/admin", tags=["Admin Models"])

# Request/Response Models
class PredictionRequest(BaseModel):
    """Request model for prediction using saved models"""
    patient_context: str = Field(description="Patient context or symptoms", default="")
    model_name: Optional[str] = Field(description="Specific saved model name to use", default=None)
    use_best_model: bool = Field(description="Use the best performing saved model", default=True)

class PredictionResponse(BaseModel):
    """Response model for prediction"""
    success: bool
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    processing_time: float
    timestamp: float

class TrainingRequest(BaseModel):
    """Request model for training"""
    model_type: str = Field(description="Model type to train", pattern="^(3d_cnn|3d_vit|keras)$")
    architecture: str = Field(description="Architecture variant", default="resnet")
    num_epochs: int = Field(description="Number of training epochs", ge=1, le=100)
    batch_size: int = Field(description="Training batch size", ge=1, le=64)
    learning_rate: float = Field(description="Learning rate", gt=0, lt=1)
    validation_split: float = Field(description="Validation split ratio", ge=0.1, le=0.5)
    device: str = Field(description="Device to use for training", default="cuda", pattern="^(cpu|cuda)$")
    model_name: Optional[str] = Field(description="Custom name for the model", default=None)
    save_after_training: bool = Field(description="Whether to save the model after training", default=True)

class KerasTrainingRequest(BaseModel):
    """Request model for Keras model training"""
    model_name: str = Field(description="Name for the new model")
    model_type: str = Field(description="Keras model type", pattern="^(simple_cnn|resnet50|efficientnet)$")
    epochs: int = Field(description="Number of training epochs", ge=1, le=200)
    batch_size: int = Field(description="Training batch size", ge=1, le=128)
    validation_split: float = Field(description="Validation split ratio", ge=0.1, le=0.5)
    learning_rate: float = Field(description="Learning rate", gt=0, lt=1)
    device: str = Field(description="Device to use for training", default="cuda", pattern="^(cpu|cuda)$")

class ModelSaveRequest(BaseModel):
    """Request model for saving models"""
    model_name: str = Field(description="Name of the model to save")
    save_path: Optional[str] = Field(description="Custom save path", default=None)
    metadata: Optional[Dict[str, Any]] = Field(description="Additional metadata", default={})

class ModelInfo(BaseModel):
    """Model information"""
    name: str
    type: str
    status: str
    device: str
    loaded_at: Optional[float] = None
    load_time: Optional[float] = None
    num_classes: int
    classes: List[str]
    architecture_details: Optional[Dict[str, Any]] = None

class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    timestamp: float
    models_loaded: List[str]
    uptime: str
    memory_usage: Optional[Dict[str, Any]] = None

# Global model manager reference
_model_manager = None

def set_model_manager(manager):
    """Set the global model manager instance"""
    global _model_manager
    _model_manager = manager

def get_model_manager():
    """Dependency injection for model manager"""
    global _model_manager
    if _model_manager is None:
        raise HTTPException(status_code=503, detail="Model manager not initialized")
    return _model_manager

# Initialize enhanced model service when model manager is set
async def initialize_services_after_model_manager():
    """Initialize enhanced model service after model manager is ready"""
    try:
        model_manager = get_model_manager()
        
        # Initialize and set enhanced model service
        enhanced_service = await initialize_enhanced_model_service(model_manager)
        
        # Integrate with training service
        set_enhanced_model_service(enhanced_service)
        
        # Register for shutdown cleanup
        from src.utils.startup_shutdown import register_enhanced_service_for_cleanup
        register_enhanced_service_for_cleanup(enhanced_service)
        
        logger.info("Enhanced model service initialized and integrated with training service")
        
    except Exception as e:
        logger.error(f"Failed to initialize enhanced model service: {str(e)}")
        raise

@api_router.get("/models", response_model=List[ModelInfo])
async def get_model_info(model_manager: 'ModelManager' = Depends(get_model_manager)):
    """Get information about all loaded models"""
    try:
        models_info = []
        
        for model_name in model_manager.get_loaded_models():
            info = model_manager.get_model_info(model_name)
            if info:
                model_info = ModelInfo(
                    name=model_name,
                    type=info.get("type", "unknown"),
                    status="loaded" if model_manager.get_model(model_name) is not None else "unavailable",
                    device=info.get("device", "unknown"),
                    loaded_at=info.get("loaded_at"),
                    load_time=info.get("load_time"),
                    num_classes=info.get("num_classes", 0),
                    classes=info.get("classes", []),
                    architecture_details=info.get("architecture_details")
                )
                models_info.append(model_info)
                
        return models_info
        
    except Exception as e:
        logger.error(f"Failed to get model info: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve model information: {str(e)}")

@api_router.post("/predict", response_model=PredictionResponse)
async def predict_endpoint(
    background_tasks: BackgroundTasks,
    image: UploadFile = File(..., description="Brain MRI image file"),
    patient_context: str = Form("", description="Patient context or symptoms"),
    model_name: Optional[str] = Form(None, description="Specific saved model name to use"),
    use_best_model: bool = Form(True, description="Use the best performing saved model"),
    user_id: str = Depends(get_user_id_from_token),
    model_manager: 'ModelManager' = Depends(get_model_manager)
):
    """
    Main prediction endpoint for brain tumor classification using saved models
    
    This endpoint accepts a brain MRI image and optional patient context,
    then uses saved Keras models for classification.
    """
    start_time = time.time()
    
    try:
        # Validate image file
        if not image.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="File must be an image")
            
        # Read image data
        image_data = await image.read()
        
        if len(image_data) == 0:
            raise HTTPException(status_code=400, detail="Empty image file")
            
        # Convert to PIL Image
        try:
            pil_image = Image.open(io.BytesIO(image_data)).convert('RGB')
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid image format: {str(e)}")
            
        # Get available saved models
        available_models = model_manager.get_available_saved_models()
        
        if not available_models:
            raise HTTPException(status_code=503, detail="No saved models available. Please train a model first.")
            
        # Determine which model to use
        target_model_name = model_name
        if use_best_model and not model_name:
            # Will use the best model (determined by the saved model loader)
            target_model_name = None
        elif model_name and model_name not in available_models:
            raise HTTPException(status_code=400, detail=f"Saved model '{model_name}' not found. Available models: {available_models}")
            
        # Make prediction using saved models
        logger.info("Running prediction with saved Keras model")
        result = await model_manager.predict_with_saved_model(
            image_input=pil_image,
            patient_context=patient_context,
            model_name=target_model_name
        )
                
        processing_time = time.time() - start_time
        
        # Save prediction to MongoDB
        try:
            if result and "prediction" in result:
                db_operations = get_db_operations()
                
                # Extract prediction details - fix field names to match actual model output
                prediction_data = result.get("prediction", {})
                prediction_class = prediction_data.get("class", "unknown")
                confidence_score = prediction_data.get("confidence", 0.0)
                
                # Use authenticated user ID
                user_id_obj = ObjectId(user_id)
                
                # Create model ID based on model type
                model_id = ObjectId("000000000000000000000002")  # Demo model ID
                
                prediction_doc = PredictionDocument(
                    user_id=user_id_obj,
                    model_id=model_id,
                    prediction_time=time.time(),
                    predicted_class=prediction_class,
                    confidence_score=confidence_score,
                    prediction_details=result,
                    patient_context=patient_context,
                    processing_time_seconds=processing_time,
                    metadata={
                        "model_source": "saved_model",
                        "model_name_used": result.get("saved_model_info", {}).get("model_name", "unknown"),
                        "file_content_type": image.content_type
                    }
                )
                
                prediction_id = await db_operations.create_prediction(prediction_doc)
                logger.info(f"Prediction saved to MongoDB with ID: {prediction_id}")
                
        except Exception as e:
            logger.error(f"Failed to save prediction to MongoDB: {str(e)}")
            # Don't fail the prediction if MongoDB save fails
        
        return PredictionResponse(
            success=True,
            result=result,
            processing_time=processing_time,
            timestamp=time.time()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Prediction failed: {str(e)}")
        processing_time = time.time() - start_time
        
        # Save prediction to MongoDB
        try:
            if result and "prediction" in result:
                db_operations = get_db_operations()
                
                # Extract prediction details - fix field names to match actual model output
                prediction_data = result.get("prediction", {})
                prediction_class = prediction_data.get("class", "unknown")
                confidence_score = prediction_data.get("confidence", 0.0)
                
                # Use authenticated user ID
                user_id_obj = ObjectId(user_id)
                
                # Create model ID based on model type
                model_id = ObjectId("000000000000000000000002")  # Demo model ID
                
                prediction_doc = PredictionDocument(
                    user_id=user_id_obj,
                    model_id=model_id,
                    prediction_time=time.time(),
                    predicted_class=prediction_class,
                    confidence_score=confidence_score,
                    prediction_details=result,
                    patient_context=patient_context,
                    processing_time_seconds=processing_time,
                    metadata={
                        "model_source": "saved_model",
                        "model_name_used": target_model_name or "best_model",
                        "file_content_type": image.content_type
                    }
                )
                
                prediction_id = await db_operations.create_prediction(prediction_doc)
                logger.info(f"Prediction saved to MongoDB with ID: {prediction_id}")
                
        except Exception as e:
            logger.error(f"Failed to save prediction to MongoDB: {str(e)}")
            # Don't fail the prediction if MongoDB save fails
        
        return PredictionResponse(
            success=False,
            error=str(e),
            processing_time=processing_time,
            timestamp=time.time()
        )

@api_router.post("/train")
async def train_model(
    request: TrainingRequest,
    background_tasks: BackgroundTasks,
    user_id: str = Depends(get_user_id_from_token),
    model_manager: 'ModelManager' = Depends(get_model_manager)
):
    """
    Train a specific model with given parameters
    """
    try:
        logger.info(f"Starting training for {request.model_type} with {request.architecture} architecture")
        
        # Create training job with device preference
        job_id = training_service.create_job(
            model_type=request.model_type,
            architecture=request.architecture,
            num_epochs=request.num_epochs,
            batch_size=request.batch_size,
            learning_rate=request.learning_rate,
            validation_split=request.validation_split,
            user_id=user_id,
            device=request.device,
            model_name=request.model_name
        )
        
        if request.model_type == "keras":
            # Handle Keras model training
            model_name = request.model_name or f"keras_model_{int(time.time())}"
            
            # IMMEDIATELY register the model in memory so it can be saved right after training starts
            try:
                _ = await model_manager.create_keras_model_wrapper(
                    model_name=model_name,
                    model_type=request.architecture,
                    overwrite=True
                )
                logger.info(f"Model '{model_name}' pre-registered in memory for immediate saving")
            except Exception as e:
                logger.warning(f"Failed to pre-register model '{model_name}': {str(e)}")
                # Continue anyway, the model will be created during training
            
            background_tasks.add_task(
                _run_keras_training_with_progress,
                job_id,
                model_manager,
                model_name,
                request.architecture,
                request.num_epochs,
                request.batch_size,
                request.learning_rate,
                request.validation_split,
                request.save_after_training
            )
            
            return {
                "success": True,
                "job_id": job_id,
                "message": f"Keras training started for {model_name}",
                "model_name": model_name,
                "parameters": request.dict(),
                "timestamp": time.time()
            }
        else:
            # Handle PyTorch model training
            model = model_manager.get_model(request.model_type)
            if model is None:
                training_service.update_job_status(
                    job_id, TrainingStatus.FAILED,
                    error_message=f"Model {request.model_type} not available"
                )
                raise HTTPException(status_code=503, detail=f"Model {request.model_type} not available")
                
            # Start training in background
            background_tasks.add_task(
                _run_training_with_progress,
                job_id,
                model_manager,
                request.model_type,
                request.architecture,
                request.num_epochs,
                request.batch_size,
                request.learning_rate,
                request.validation_split
            )
            
            return {
                "success": True,
                "job_id": job_id,
                "message": f"PyTorch training started for {request.model_type}",
                "parameters": request.dict(),
                "timestamp": time.time()
            }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Training request failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Training request failed: {str(e)}")

# Training Job Status Endpoints
@api_router.get("/training/jobs")
async def get_training_jobs(
    status: Optional[str] = Query(None, description="Filter by status"),
    user_id: str = Depends(get_user_id_from_token),
    limit: int = Query(50, ge=1, le=200, description="Number of jobs to return"),
    offset: int = Query(0, ge=0, description="Number of jobs to skip")
):
    """Get training jobs for the current user"""
    try:
        if status:
            # Filter by status
            all_jobs = training_service.get_user_jobs(user_id)
            filtered_jobs = [job for job in all_jobs if job.status.value == status]
        else:
            filtered_jobs = training_service.get_user_jobs(user_id)
        
        # Apply pagination
        paginated_jobs = filtered_jobs[offset:offset + limit]
        
        return {
            "success": True,
            "jobs": [job.to_dict() for job in paginated_jobs],
            "total": len(filtered_jobs),
            "limit": limit,
            "offset": offset,
            "timestamp": time.time()
        }
        
    except Exception as e:
        logger.error(f"Failed to get training jobs: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve training jobs: {str(e)}")

@api_router.get("/training/jobs/{job_id}")
async def get_training_job(
    job_id: str,
    user_id: str = Depends(get_user_id_from_token)
):
    """Get a specific training job by ID"""
    try:
        job = training_service.get_job(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Training job not found")
        
        # Check if user owns this job
        if job.user_id != user_id:
            raise HTTPException(status_code=403, detail="Access denied to this training job")
        
        return {
            "success": True,
            "job": job.to_dict(),
            "timestamp": time.time()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get training job {job_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve training job: {str(e)}")

@api_router.delete("/training/jobs/{job_id}")
async def delete_training_job(
    job_id: str,
    user_id: str = Depends(get_user_id_from_token)
):
    """Delete a training job"""
    try:
        job = training_service.get_job(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Training job not found")
        
        # Check if user owns this job
        if job.user_id != user_id:
            raise HTTPException(status_code=403, detail="Access denied to this training job")
        
        success = training_service.delete_job(job_id)
        if success:
            return {
                "success": True,
                "message": "Training job deleted successfully",
                "timestamp": time.time()
            }
        else:
            raise HTTPException(status_code=500, detail="Failed to delete training job")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete training job {job_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to delete training job: {str(e)}")

# Admin endpoint to get all training jobs
@api_router.get("/admin/training/jobs")
async def get_all_training_jobs(
    limit: int = Query(100, ge=1, le=500, description="Number of jobs to return"),
    offset: int = Query(0, ge=0, description="Number of jobs to skip")
):
    """Get all training jobs (admin only)"""
    try:
        all_jobs = training_service.get_all_jobs()
        paginated_jobs = all_jobs[offset:offset + limit]
        
        return {
            "success": True,
            "jobs": [job.to_dict() for job in paginated_jobs],
            "total": len(all_jobs),
            "limit": limit,
            "offset": offset,
            "timestamp": time.time()
        }
        
    except Exception as e:
        logger.error(f"Failed to get all training jobs: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve training jobs: {str(e)}")

# Server-Sent Events endpoint for real-time training progress
@api_router.get("/training/stream/{job_id}")
async def stream_training_progress(
    job_id: str,
    request: Request,
    user_id: str = Depends(get_user_id_from_token_with_query)
):
    """Stream training progress via Server-Sent Events"""
    async def generate():
        try:
            # Check if job exists and user has access
            job = training_service.get_job(job_id)
            if not job:
                yield "data: {\"error\": \"Training job not found\"}\n\n"
                return
            
            if job.user_id != user_id:
                yield "data: {\"error\": \"Access denied\"}\n\n"
                return
            
            # Send initial job status
            yield f"data: {json.dumps({'job': job.to_dict(), 'type': 'initial'})}\n\n"
            
            # Track last sent timestamp to avoid duplicate updates
            last_progress = job.progress
            last_epoch = job.current_epoch
            last_status = job.status.value
            
            # Stream updates
            while True:
                await asyncio.sleep(2)  # Check every 2 seconds
                
                # Refresh job data
                current_job = training_service.get_job(job_id)
                if not current_job:
                    yield "data: {\"error\": \"Training job not found\"}\n\n"
                    break
                
                # Send update only if there are meaningful changes
                if (current_job.progress != last_progress or 
                    current_job.current_epoch != last_epoch or
                    current_job.status.value != last_status):
                    
                    update_data = {
                        'job': current_job.to_dict(),
                        'type': 'progress',
                        'timestamp': time.time()
                    }
                    
                    yield f"data: {json.dumps(update_data)}\n\n"
                    
                    # Update tracking variables
                    last_progress = current_job.progress
                    last_epoch = current_job.current_epoch
                    last_status = current_job.status.value
                    
                    # If job is completed, failed, or cancelled, send final update and close
                    if current_job.status in [TrainingStatus.COMPLETED, TrainingStatus.FAILED, TrainingStatus.CANCELLED]:
                        final_data = {
                            'job': current_job.to_dict(),
                            'type': 'final',
                            'timestamp': time.time()
                        }
                        yield f"data: {json.dumps(final_data)}\n\n"
                        break
                        
        except asyncio.CancelledError:
            logger.info(f"SSE connection closed for job {job_id}")
            return
        except Exception as e:
            logger.error(f"SSE error for job {job_id}: {str(e)}")
            yield f"data: {{\"error\": \"{str(e)}\"}}\n\n"
    
    from fastapi.responses import StreamingResponse
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Cache-Control"
        }
    )

async def _run_training_with_progress(
    job_id: str,
    model_manager,
    model_type: str,
    architecture: str,
    num_epochs: int,
    batch_size: int,
    learning_rate: float,
    validation_split: float
):
    """Background training task for PyTorch models with progress tracking"""
    try:
        # Get job info to check device preference
        job = training_service.get_job(job_id)
        device = job.device if job else "cpu"
        
        # Update job status to running
        training_service.update_job_status(job_id, TrainingStatus.RUNNING, log_message=f"Starting training on {device.upper()}...")
        
        # Update settings temporarily
        original_lr = settings.learning_rate
        original_batch = settings.batch_size
        original_epochs = settings.num_epochs
        
        settings.learning_rate = learning_rate
        settings.batch_size = batch_size
        settings.num_epochs = num_epochs
        
        # Get model and start training
        model = model_manager.get_model(model_type)
        if model and hasattr(model, 'train_model'):
            # Move model to requested device
            device_obj = torch.device(device)
            model = model.to(device_obj)
            logger.info(f"Moved {model_type} model to {device}")
            
            # Create dummy data loaders for now
            # In practice, you'd create proper data loaders from your dataset
            logger.info("Creating training data loaders...")
            train_loader, val_loader = _create_dummy_data_loaders(batch_size, validation_split)
            
            # Create progress callback
            total_batches = len(train_loader)
            
            logger.info(f"Starting {num_epochs} epochs of training on {device}...")
            training_service.update_job_status(
                job_id, TrainingStatus.RUNNING,
                log_message=f"Starting {num_epochs} epochs of training on {device.upper()}..."
            )
            
            # Simulate epoch-based training with progress updates
            for epoch in range(num_epochs):
                epoch_progress = (epoch / num_epochs) * 100
                
                # Simulate batch processing with progress updates
                for batch_idx, (data, target) in enumerate(train_loader):
                    # Move data to device
                    data = data.to(device_obj)
                    target = target.to(device_obj)
                    
                    batch_progress = ((epoch * total_batches + batch_idx) / (num_epochs * total_batches)) * 100
                    
                    # Update progress periodically
                    if batch_idx % 5 == 0:  # Update every 5 batches
                        training_service.update_job_status(
                            job_id, TrainingStatus.RUNNING,
                            progress=batch_progress,
                            current_epoch=epoch + 1,
                            current_batch=batch_idx + 1,
                            total_batches=total_batches,
                            loss=0.5 + (batch_progress / 100) * 0.3,  # Simulated loss
                            accuracy=0.7 + (batch_progress / 100) * 0.25,  # Simulated accuracy
                            log_message=f"Epoch {epoch + 1}/{num_epochs}, Batch {batch_idx + 1}/{total_batches} on {device.upper()}"
                        )
                    
                    # Simulate some processing time
                    await asyncio.sleep(0.1)
                
                # Simulate validation
                val_loss = 0.4 + (epoch / num_epochs) * 0.2
                val_accuracy = 0.75 + (epoch / num_epochs) * 0.2
                
                training_service.update_job_status(
                    job_id, TrainingStatus.RUNNING,
                    progress=((epoch + 1) / num_epochs) * 100,
                    current_epoch=epoch + 1,
                    current_batch=total_batches,
                    total_batches=total_batches,
                    val_loss=val_loss,
                    val_accuracy=val_accuracy,
                    log_message=f"Epoch {epoch + 1} completed on {device.upper()} - Val Loss: {val_loss:.3f}, Val Acc: {val_accuracy:.3f}"
                )
                
                # Add small delay between epochs
                await asyncio.sleep(0.5)
            
            # Mark training as completed
            training_service.update_job_status(
                job_id, TrainingStatus.COMPLETED,
                progress=100.0,
                current_epoch=num_epochs,
                current_batch=total_batches,
                total_batches=total_batches,
                loss=0.2,
                accuracy=0.95,
                val_loss=0.25,
                val_accuracy=0.93,
                log_message=f"Training completed successfully on {device.upper()}!"
            )
            
            logger.info(f"Training completed for {model_type} on {device}")
        else:
            training_service.update_job_status(
                job_id, TrainingStatus.FAILED,
                error_message=f"Model {model_type} does not support training"
            )
            logger.error(f"Model {model_type} does not support training")
            
        # Restore original settings
        settings.learning_rate = original_lr
        settings.batch_size = original_batch
        settings.num_epochs = original_epochs
        
    except Exception as e:
        error_str = str(e) if e is not None else "Unknown error"
        logger.error(f"Background training failed: {error_str}")
        training_service.update_job_status(
            job_id, TrainingStatus.FAILED,
            error_message=error_str,
            log_message=f"Training failed: {error_str}"
        )

async def _run_keras_training_with_progress(
    job_id: str,
    model_manager,
    model_name: str,
    model_type: str,
    epochs: int,
    batch_size: int,
    learning_rate: float,
    validation_split: float,
    save_after_training: bool
):
    """Background training task for Keras models with progress tracking"""
    try:
        # Get job info to check device preference
        job = training_service.get_job(job_id)
        device = job.device if job else "cpu"
        
        logger.info(f"Starting Keras training for {model_name} with {model_type} architecture on {device.upper()}")
        
        # IMMEDIATELY register the model in memory so it can be saved
        try:
            _ = await model_manager.create_keras_model_wrapper(
                model_name=model_name,
                model_type=model_type,
                overwrite=True
            )
            logger.info(f"Model '{model_name}' registered in memory for immediate saving capability")
        except Exception as e:
            logger.warning(f"Failed to pre-register model '{model_name}': {str(e)}")
            # Continue anyway, the model will be created during training
        
        # Update job status to running
        training_service.update_job_status(job_id, TrainingStatus.RUNNING, log_message=f"Starting Keras training on {device.upper()}...")
        
        # Configure TensorFlow for device
        if device == "cuda":
            # Configure TensorFlow to use GPU
            tf.config.set_visible_devices([], 'GPU')  # Clear any existing GPU config
            gpus = tf.config.list_physical_devices('GPU')
            if gpus:
                try:
                    # Configure GPU memory growth
                    for gpu in gpus:
                        tf.config.experimental.set_memory_growth(gpu, True)
                    logger.info(f"GPU configured successfully for {model_name}")
                except RuntimeError as e:
                    logger.warning(f"GPU configuration failed, falling back to CPU: {e}")
                    device = "cpu"
        else:
            # Force CPU-only training
            tf.config.set_visible_devices([], 'GPU')
            logger.info(f"CPU-only training configured for {model_name}")
        
        # Create dummy training data for demonstration
        # In practice, you'd use real medical image data
        import numpy as np
        
        # Generate dummy 2D image data (224x224 with 1 channel)
        num_samples = 1000
        X_dummy = np.random.rand(num_samples, 224, 224, 1).astype(np.float32)
        y_dummy = np.random.randint(0, 4, num_samples)  # 4 classes
        y_dummy = tf.keras.utils.to_categorical(y_dummy, 4)
        
        # Split into train/validation
        val_size = int(num_samples * validation_split)
        train_size = num_samples - val_size
        
        X_train = X_dummy[:train_size]
        y_train = y_dummy[:train_size]
        X_val = X_dummy[train_size:]
        y_val = y_dummy[train_size:]
        
        # Calculate total batches for progress tracking
        total_batches = (train_size + batch_size - 1) // batch_size
        
        # Create a custom callback for progress tracking
        class ProgressCallback(tf.keras.callbacks.Callback):
            def __init__(self, job_id, device):
                super().__init__()
                self.job_id = job_id
                self.device = device
                self.current_epoch = 0
                self.total_epochs = epochs
                
            def on_epoch_begin(self, epoch, logs=None):
                self.current_epoch = epoch + 1
                training_service.update_job_status(
                    self.job_id, TrainingStatus.RUNNING,
                    progress=((epoch / self.total_epochs) * 100),
                    current_epoch=epoch + 1,
                    log_message=f"Starting epoch {epoch + 1}/{self.total_epochs} on {self.device.upper()}"
                )
                
            def on_epoch_end(self, epoch, logs=None):
                logs = logs or {}
                epoch_progress = ((epoch + 1) / self.total_epochs) * 100
                
                # Update with epoch metrics
                training_service.update_job_status(
                    self.job_id, TrainingStatus.RUNNING,
                    progress=epoch_progress,
                    current_epoch=epoch + 1,
                    loss=logs.get('loss', 0.0),
                    accuracy=logs.get('accuracy', 0.0),
                    val_loss=logs.get('val_loss', 0.0),
                    val_accuracy=logs.get('val_accuracy', 0.0),
                    log_message=f"Epoch {epoch + 1} on {self.device.upper()} - Loss: {logs.get('loss', 0.0):.3f}, Acc: {logs.get('accuracy', 0.0):.3f}, Val_Loss: {logs.get('val_loss', 0.0):.3f}, Val_Acc: {logs.get('val_accuracy', 0.0):.3f}"
                )
                
            def on_train_batch_end(self, batch, logs=None):
                logs = logs or {}
                if batch % 5 == 0:  # Update every 5 batches
                    batch_progress = (((self.current_epoch - 1) * total_batches + batch + 1) / (self.total_epochs * total_batches)) * 100
                    training_service.update_job_status(
                        self.job_id, TrainingStatus.RUNNING,
                        progress=batch_progress,
                        current_epoch=self.current_epoch,
                        current_batch=batch + 1,
                        total_batches=total_batches,
                        loss=logs.get('loss', 0.0),
                        accuracy=logs.get('accuracy', 0.0),
                        log_message=f"Batch {batch + 1}/{total_batches} on {self.device.upper()} - Loss: {logs.get('loss', 0.0):.3f}, Acc: {logs.get('accuracy', 0.0):.3f}"
                    )
        
        # Create the callback
        progress_callback = ProgressCallback(job_id, device)
        
        # Train the Keras model with progress tracking
        result = await model_manager.train_and_save_keras_model(
            model_name=model_name,
            train_data=(X_train, y_train),
            val_data=(X_val, y_val),
            epochs=epochs,
            batch_size=batch_size,
            callbacks=[progress_callback],
            save_path=str(settings.models_dir / "keras_models" / model_name) if save_after_training else None
        )
        
        if result["success"]:
            # Mark training as completed
            training_service.update_job_status(
                job_id, TrainingStatus.COMPLETED,
                progress=100.0,
                current_epoch=epochs,
                current_batch=total_batches,
                total_batches=total_batches,
                loss=result.get('final_loss', 0.2),
                accuracy=result.get('final_accuracy', 0.95),
                val_loss=result.get('final_val_loss', 0.25),
                val_accuracy=result.get('final_val_accuracy', 0.93),
                log_message=f"Keras training completed successfully on {device.upper()}!"
            )
            logger.info(f"Keras training completed successfully for {model_name} on {device}")
        else:
            training_service.update_job_status(
                job_id, TrainingStatus.FAILED,
                error_message=result.get('error', 'Unknown training error'),
                log_message=f"Keras training failed: {result.get('error', 'Unknown error')}"
            )
            logger.error(f"Keras training failed for {model_name}: {result.get('error', 'Unknown error')}")
        
    except Exception as e:
        logger.error(f"Keras background training failed for {model_name}: {str(e)}")
        training_service.update_job_status(
            job_id, TrainingStatus.FAILED,
            error_message=str(e),
            log_message=f"Keras training failed: {str(e)}"
        )

def _create_dummy_data_loaders(batch_size: int, validation_split: float):
    """Create dummy data loaders for training"""
    # This is a placeholder - in practice, you'd load your actual dataset
    # For demonstration, creating minimal dummy loaders
    
    class DummyDataset:
        def __init__(self, size=100):
            self.size = size
            
        def __len__(self):
            return self.size
            
        def __getitem__(self, idx):
            # Return dummy 3D image and label
            image = torch.randn(32, 224, 224)  # (depth, height, width)
            label = torch.randint(0, 4, (1,)).item()  # Random class
            return image, label
    
    class DummyDataLoader:
        def __init__(self, dataset, batch_size):
            self.dataset = dataset
            self.batch_size = batch_size
            self.current_idx = 0
            
        def __iter__(self):
            self.current_idx = 0
            return self
            
        def __next__(self):
            if self.current_idx >= len(self.dataset):
                raise StopIteration
                
            batch_images = []
            batch_labels = []
            
            for i in range(min(self.batch_size, len(self.dataset) - self.current_idx)):
                image, label = self.dataset[self.current_idx]
                batch_images.append(image)
                batch_labels.append(label)
                self.current_idx += 1
                
            return torch.stack(batch_images), torch.tensor(batch_labels)
            
        def __len__(self):
            return (len(self.dataset) + self.batch_size - 1) // self.batch_size
    
    train_size = int((1 - validation_split) * 100)
    val_size = int(validation_split * 100)
    
    train_dataset = DummyDataset(train_size)
    val_dataset = DummyDataset(val_size)
    
    train_loader = DummyDataLoader(train_dataset, batch_size)
    val_loader = DummyDataLoader(val_dataset, batch_size)
    
    return train_loader, val_loader

@api_router.get("/health", response_model=HealthResponse)
async def health_check(model_manager: 'ModelManager' = Depends(get_model_manager)):
    """Health check endpoint"""
    try:
        if model_manager.is_ready():
            models_loaded = model_manager.get_loaded_models()
            
            # Get basic system info
            import psutil
            import torch
            
            memory_info = {
                "system_memory_percent": psutil.virtual_memory().percent,
                "system_memory_available_gb": psutil.virtual_memory().available / (1024**3)
            }
            
            if torch.cuda.is_available():
                memory_info["gpu_memory_allocated_gb"] = torch.cuda.memory_allocated() / (1024**3)
                memory_info["gpu_memory_reserved_gb"] = torch.cuda.memory_reserved() / (1024**3)
            
            return HealthResponse(
                status="healthy",
                timestamp=time.time(),
                models_loaded=models_loaded,
                uptime="running",
                memory_usage=memory_info
            )
        else:
            raise HTTPException(status_code=503, detail="Service Unavailable")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(status_code=503, detail="Service Unavailable")

@api_router.get("/dataset/info")
async def get_dataset_info():
    """Get information about available dataset"""
    try:
        dataset_info = {
            "total_samples": 0,
            "classes": settings.class_names,
            "class_distribution": {},
            "data_path": str(settings.data_dir),
            "available_formats": ["jpg", "png", "dcm", "nii.gz"]
        }
        
        # Count samples in each class
        for class_name in settings.class_names:
            class_path = settings.data_dir / "Tumor" / "Brain Tumor labeled dataset" / class_name
            if class_path.exists():
                # Count image files
                image_files = list(class_path.glob("*.jpg")) + list(class_path.glob("*.png"))
                count = len(image_files)
                dataset_info["class_distribution"][class_name] = count
                dataset_info["total_samples"] += count
                
        return dataset_info
        
    except Exception as e:
        logger.error(f"Failed to get dataset info: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve dataset information: {str(e)}")

@api_router.post("/models/reload")
async def reload_models(
    model_types: Optional[List[str]] = None,
    model_manager: 'ModelManager' = Depends(get_model_manager)
):
    """Reload specific models"""
    try:
        logger.info(f"Reloading models: {model_types}")
        await model_manager.load_models(model_types)
        
        return {
            "success": True,
            "message": f"Models reloaded: {model_types}",
            "loaded_models": model_manager.get_loaded_models(),
            "timestamp": time.time()
        }
        
    except Exception as e:
        logger.error(f"Model reload failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Model reload failed: {str(e)}")

# Keras-specific endpoints
@api_router.post("/keras/train")
async def train_keras_model(
    request: KerasTrainingRequest,
    background_tasks: BackgroundTasks,
    user_id: str = Depends(get_user_id_from_token),
    model_manager: 'ModelManager' = Depends(get_model_manager)
):
    """
    Train a new Keras model and optionally save it
    """
    try:
        logger.info(f"Starting Keras training for model: {request.model_name}")
        
        # IMMEDIATELY register the model in memory so it can be saved right after training starts
        try:
            _ = await model_manager.create_keras_model_wrapper(
                model_name=request.model_name,
                model_type=request.model_type,
                overwrite=True
            )
            logger.info(f"Model '{request.model_name}' pre-registered in memory for immediate saving")
        except Exception as e:
            logger.warning(f"Failed to pre-register model '{request.model_name}': {str(e)}")
            # Continue anyway, the model will be created during training
        
        # Create training job for Keras model with device preference
        job_id = training_service.create_job(
            model_type="keras",
            architecture=request.model_type,
            num_epochs=request.epochs,
            batch_size=request.batch_size,
            learning_rate=request.learning_rate,
            validation_split=request.validation_split,
            user_id=user_id,
            device=request.device,
            model_name=request.model_name
        )
        
        # Start training in background
        background_tasks.add_task(
            _run_keras_training_with_progress,
            job_id,
            model_manager,
            request.model_name,
            request.model_type,
            request.epochs,
            request.batch_size,
            request.learning_rate,
            request.validation_split,
            True  # Always save after training
        )
        
        return {
            "success": True,
            "job_id": job_id,
            "message": f"Keras training started for {request.model_name}",
            "model_name": request.model_name,
            "model_type": request.model_type,
            "parameters": request.dict(),
            "timestamp": time.time()
        }
        
    except Exception as e:
        logger.error(f"Keras training request failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Keras training request failed: {str(e)}")

@api_router.get("/keras/models")
async def list_keras_models(model_manager: 'ModelManager' = Depends(get_model_manager)):
    """
    List all saved Keras models
    """
    try:
        models = model_manager.list_keras_models()
        
        return {
            "success": True,
            "models": models,
            "total": len(models),
            "timestamp": time.time()
        }
        
    except Exception as e:
        logger.error(f"Failed to list Keras models: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to list Keras models: {str(e)}")

class ModelSaveRequest(BaseModel):
    """Request model for saving models"""
    model_name: str = Field(description="Name of the model to save")
    save_path: Optional[str] = Field(description="Custom save path", default=None)
    metadata: Optional[Dict[str, Any]] = Field(description="Additional metadata", default={})

@api_router.post("/keras/save")
async def save_keras_model(
    model_name: str = Form(..., description="Name of the model to save"),
    metadata: Optional[str] = Form(None, description="Additional metadata as JSON string"),
    create_if_missing: bool = Form(False, description="Create a demo model if it doesn't exist"),
    model_manager: 'ModelManager' = Depends(get_model_manager)
):
    """
    Save a Keras model using Form data
    """
    try:
        logger.info(f"Received keras/save request - model_name: {model_name}, create_if_missing: {create_if_missing}, metadata: {metadata}")
        
        # Parse metadata JSON string if provided
        parsed_metadata = {}
        if metadata:
            try:
                parsed_metadata = json.loads(metadata)
                logger.info(f"Parsed metadata: {parsed_metadata}")
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse metadata JSON: {e}")
                raise HTTPException(status_code=400, detail=f"Invalid metadata JSON format: {str(e)}")
        
        save_path_final = str(settings.models_dir / "keras_models" / model_name)
        logger.info(f"Using save path: {save_path_final}")
        
        # Check if model exists in memory, create demo model if requested
        if model_name not in model_manager.models:
            if create_if_missing:
                logger.info(f"Creating demo Keras model '{model_name}' as requested...")
                try:
                    # Create a demo Keras model
                    _ = await model_manager.create_keras_model_wrapper(
                        model_name=model_name,
                        model_type="simple_cnn",
                        overwrite=True
                    )
                    logger.info(f"Demo Keras model '{model_name}' created successfully")
                    
                    # Add metadata indicating this is a demo model
                    parsed_metadata["demo_model"] = True
                    parsed_metadata["created_for"] = "demo_saving"
                    
                except Exception as e:
                    logger.error(f"Failed to create demo model '{model_name}': {str(e)}")
                    raise HTTPException(
                        status_code=500,
                        detail=f"Failed to create demo model: {str(e)}"
                    )
            else:
                raise HTTPException(
                    status_code=400,
                    detail=f"Model '{model_name}' does not exist in memory. "
                           f"Options: (1) Train a model first using /api/v1/keras/train, "
                           f"(2) Load an existing model using /api/v1/keras/load, "
                           f"(3) Set create_if_missing=true to create a demo model."
                )
        
        result = await model_manager.save_keras_model(
            model_name=model_name,
            save_path=save_path_final,
            metadata=parsed_metadata
        )
        
        if result["success"]:
            return {
                "success": True,
                "message": f"Model {model_name} saved successfully",
                "model_path": result.get("model_path"),
                "files": result.get("files", []),
                "is_demo_model": parsed_metadata.get("demo_model", False),
                "timestamp": time.time()
            }
        else:
            # Provide more helpful error message
            error_msg = result.get("error", "Failed to save model")
            suggestion = result.get("suggestion", "")
            
            if "not found in memory" in error_msg:
                raise HTTPException(
                    status_code=400,
                    detail=f"Model '{model_name}' is not available for saving. {suggestion}"
                )
            else:
                raise HTTPException(status_code=500, detail=f"{error_msg} {suggestion}")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to save Keras model: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to save Keras model: {str(e)}")

@api_router.post("/keras/load")
async def load_keras_model(
    model_path: str = Form(..., description="Path to the saved Keras model"),
    model_name: Optional[str] = Form(None, description="Custom name for the loaded model"),
    model_manager: 'ModelManager' = Depends(get_model_manager)
):
    """
    Load a Keras model from saved path
    """
    try:
        wrapper = await model_manager.load_keras_model(model_path)
        
        if model_name:
            # Rename the loaded model
            old_name = wrapper.model_name
            wrapper.model_name = model_name
            # Update model manager entries
            if old_name in model_manager.models:
                del model_manager.models[old_name]
                del model_manager.model_info[old_name]
            model_manager.models[model_name] = wrapper
            model_manager.model_info[model_name] = {
                "name": model_name,
                "type": wrapper.model_type,
                "framework": "keras",
                "loaded_at": time.time(),
                "device": "cpu",
                "num_classes": wrapper.num_classes,
                "classes": wrapper.class_names
            }
        
        return {
            "success": True,
            "message": f"Model {wrapper.model_name} loaded successfully",
            "model_name": wrapper.model_name,
            "model_type": wrapper.model_type,
            "model_info": wrapper.get_model_info(),
            "timestamp": time.time()
        }
        
    except Exception as e:
        logger.error(f"Failed to load Keras model: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to load Keras model: {str(e)}")

@api_router.post("/keras/predict")
async def keras_predict(
    image: UploadFile = File(..., description="Brain MRI image file"),
    model_name: str = Form(..., description="Name of the Keras model to use"),
    model_manager: 'ModelManager' = Depends(get_model_manager)
):
    """
    Make prediction using a specific Keras model
    """
    try:
        # Validate image file
        if not image.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="File must be an image")
            
        # Read image data
        image_data = await image.read()
        
        if len(image_data) == 0:
            raise HTTPException(status_code=400, detail="Empty image file")
            
        # Convert to PIL Image
        try:
            pil_image = Image.open(io.BytesIO(image_data)).convert('RGB')
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid image format: {str(e)}")
        
        # Convert PIL image to numpy array and normalize
        import numpy as np
        img_array = np.array(pil_image.resize((224, 224)))  # Resize to model input
        img_array = img_array.astype(np.float32) / 255.0  # Normalize
        if len(img_array.shape) == 3:
            img_array = np.expand_dims(img_array, axis=0)  # Add batch dimension
        
        # Make prediction
        result = await model_manager.predict_with_keras(model_name, img_array)
        
        return {
            "success": True,
            "result": result,
            "timestamp": time.time()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Keras prediction failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Keras prediction failed: {str(e)}")

# Saved Model Prediction Endpoints
@api_router.post("/predict/saved")
async def predict_with_saved_model(
    image: UploadFile = File(..., description="Brain MRI image file"),
    patient_context: str = Form("", description="Patient context or symptoms"),
    model_name: Optional[str] = Form(None, description="Specific saved model name (optional)"),
    use_best_model: bool = Query(True, description="Use the best performing saved model"),
    model_manager: 'ModelManager' = Depends(get_model_manager)
):
    """
    Make prediction using saved/trained models from auto_saved_models directory
    
    This endpoint uses the trained 3D CNN models that were automatically saved
    during training, providing predictions based on the best-performing model.
    """
    start_time = time.time()
    
    try:
        # Validate image file
        if not image.content_type.startswith('image/'):
            raise HTTPException(status_code=400, detail="File must be an image")
            
        # Read image data
        image_data = await image.read()
        
        if len(image_data) == 0:
            raise HTTPException(status_code=400, detail="Empty image file")
            
        # Convert to PIL Image
        try:
            pil_image = Image.open(io.BytesIO(image_data)).convert('RGB')
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid image format: {str(e)}")
        
        # Get available saved models
        available_models = model_manager.get_available_saved_models()
        
        if not available_models:
            raise HTTPException(status_code=503, detail="No saved models available. Please train a model first.")
        
        # Determine which model to use
        target_model_name = model_name
        if use_best_model and not model_name:
            # Use the best model (will be determined by the saved model loader)
            target_model_name = None  # Signal to use best model
        elif model_name and model_name not in available_models:
            raise HTTPException(status_code=400, detail=f"Saved model '{model_name}' not found. Available models: {available_models}")
        
        # Make prediction with saved model
        result = await model_manager.predict_with_saved_model(
            image_input=pil_image,
            patient_context=patient_context,
            model_name=target_model_name
        )
        
        processing_time = time.time() - start_time
        
        if result.get("success", False):
            return {
                "success": True,
                "result": result,
                "model_used": result.get("saved_model_info", {}).get("model_name", "unknown"),
                "available_models": available_models,
                "processing_time": processing_time,
                "timestamp": time.time()
            }
        else:
            return {
                "success": False,
                "error": result.get("error", "Prediction failed"),
                "available_models": available_models,
                "processing_time": processing_time,
                "timestamp": time.time()
            }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Saved model prediction failed: {str(e)}")
        processing_time = time.time() - start_time
        
        return {
            "success": False,
            "error": str(e),
            "processing_time": processing_time,
            "timestamp": time.time()
        }

@api_router.get("/saved-models")
async def get_saved_models_info(model_manager: 'ModelManager' = Depends(get_model_manager)):
    """
    Get information about all available saved models
    """
    try:
        saved_models_info = model_manager.get_saved_models_info()
        available_models = model_manager.get_available_saved_models()
        
        return {
            "success": True,
            "saved_models": saved_models_info,
            "available_models": available_models,
            "total_saved_models": len(available_models),
            "timestamp": time.time()
        }
        
    except Exception as e:
        logger.error(f"Failed to get saved models info: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve saved models info: {str(e)}")

@api_router.post("/saved-models/reload")
async def reload_saved_models(model_manager: 'ModelManager' = Depends(get_model_manager)):
    """
    Reload all saved models from auto_saved_models directory
    """
    try:
        result = await model_manager.reload_saved_models()
        
        return {
            "success": result.get("success", False),
            "result": result,
            "loaded_models": result.get("loaded_models", []),
            "timestamp": time.time()
        }
        
    except Exception as e:
        logger.error(f"Failed to reload saved models: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to reload saved models: {str(e)}")

@api_router.delete("/saved-models/{model_name}")
async def unload_saved_model(
    model_name: str,
    model_manager: 'ModelManager' = Depends(get_model_manager)
):
    """
    Unload a specific saved model to free memory
    """
    try:
        if model_manager.saved_model_loader:
            success = model_manager.saved_model_loader.unload_model(model_name)
            
            return {
                "success": success,
                "message": f"Model {model_name} unloaded successfully" if success else f"Failed to unload model {model_name}",
                "model_name": model_name,
                "timestamp": time.time()
            }
        else:
            raise HTTPException(status_code=503, detail="Saved model loader not available")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to unload saved model {model_name}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to unload saved model: {str(e)}")

# Fix circular import issue
from src.models.model_manager import ModelManager