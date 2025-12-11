"""
Metrics API endpoints for training history, model performance, and detailed analytics
"""
from fastapi import APIRouter, HTTPException, Depends, Query, BackgroundTasks
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import time
from datetime import datetime, timedelta
from pathlib import Path

from src.services.metrics_service import MetricsService
from src.models.metrics_models import (
    ModelMetrics, TrainingJob, ModelPerformanceReport, SavedModelMetadata,
    ModelComparison, MetricType, ModelFramework, TrainingStatus
)
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

# Create router
metrics_router = APIRouter()

# Global model manager reference for metrics service
_model_manager = None

def set_model_manager(manager):
    """Set the global model manager instance for metrics service"""
    global _model_manager
    _model_manager = manager

def get_model_manager():
    """Dependency injection for model manager in metrics service"""
    global _model_manager
    if _model_manager is None:
        logger.warning("Model manager not initialized for metrics service")
        return None
    return _model_manager

# Initialize metrics service
metrics_service = MetricsService()

# Request/Response Models
class SaveModelRequest(BaseModel):
    """Request model for saving a Keras model with metrics"""
    model_name: str = Field(..., description="Name of the model to save")
    save_path: Optional[str] = Field(None, description="Custom save path")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional metadata")
    overwrite: bool = Field(default=False, description="Overwrite existing model")

class ModelMetricsResponse(BaseModel):
    """Response model for model metrics"""
    success: bool
    message: str
    model_name: str
    metrics: Optional[Dict[str, Any]] = None
    performance_report: Optional[Dict[str, Any]] = None
    timestamp: float

class TrainingJobsResponse(BaseModel):
    """Response model for training jobs list"""
    jobs: List[TrainingJob]
    total: int
    active: int
    completed: int
    failed: int

class ModelComparisonRequest(BaseModel):
    """Request model for model comparison"""
    model_names: List[str] = Field(..., description="Models to compare")
    metrics_to_compare: List[str] = Field(..., description="Metrics to compare on")
    comparison_name: Optional[str] = Field(None, description="Name for the comparison")

@metrics_router.get("/metrics/{model_name}", response_model=ModelMetricsResponse)
async def get_model_metrics(
    model_name: str,
    include_history: bool = Query(default=True, description="Include training history"),
    include_report: bool = Query(default=True, description="Include performance report")
):
    """
    Get detailed metrics for a specific model
    """
    try:
        # Load model metrics
        metrics = metrics_service.load_training_metrics(model_name)
        
        if not metrics:
            raise HTTPException(status_code=404, detail=f"Model metrics not found for: {model_name}")
        
        response_data = {
            "success": True,
            "message": f"Successfully retrieved metrics for {model_name}",
            "model_name": model_name,
            "timestamp": time.time()
        }
        
        # Include metrics data
        if include_history:
            response_data["metrics"] = metrics.dict()
        
        # Include performance report
        if include_report:
            report = metrics_service.generate_performance_report(model_name)
            if report:
                response_data["performance_report"] = report.dict()
        
        return response_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get model metrics for {model_name}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve metrics: {str(e)}")

@metrics_router.get("/jobs", response_model=TrainingJobsResponse)
async def get_training_jobs(
    status: Optional[TrainingStatus] = Query(None, description="Filter by job status"),
    limit: int = Query(default=50, ge=1, le=200, description="Maximum number of jobs to return"),
    offset: int = Query(default=0, ge=0, description="Number of jobs to skip")
):
    """
    Get training jobs with optional filtering and pagination
    """
    try:
        jobs = metrics_service.list_training_jobs(status.value if status else None)
        
        # Apply pagination
        paginated_jobs = jobs[offset:offset + limit]
        
        # Calculate statistics
        total = len(jobs)
        active = len([j for j in jobs if j.status in [TrainingStatus.PENDING, TrainingStatus.RUNNING]])
        completed = len([j for j in jobs if j.status == TrainingStatus.COMPLETED])
        failed = len([j for j in jobs if j.status == TrainingStatus.FAILED])
        
        return TrainingJobsResponse(
            jobs=paginated_jobs,
            total=total,
            active=active,
            completed=completed,
            failed=failed
        )
        
    except Exception as e:
        logger.error(f"Failed to get training jobs: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve training jobs: {str(e)}")

@metrics_router.get("/jobs/{job_id}", response_model=TrainingJob)
async def get_training_job(job_id: str):
    """
    Get a specific training job by ID
    """
    try:
        job = metrics_service.get_training_job(job_id)
        
        if not job:
            raise HTTPException(status_code=404, detail=f"Training job not found: {job_id}")
        
        return job
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get training job {job_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve training job: {str(e)}")

@metrics_router.post("/compare", response_model=ModelComparison)
async def compare_models(request: ModelComparisonRequest):
    """
    Compare multiple models on specified metrics
    """
    try:
        if len(request.model_names) < 2:
            raise HTTPException(status_code=400, detail="At least 2 models required for comparison")
        
        comparison = metrics_service.compare_models(
            model_names=request.model_names,
            metrics_to_compare=request.metrics_to_compare
        )
        
        return comparison
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to compare models: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to compare models: {str(e)}")

@metrics_router.get("/models/best")
async def get_best_model(
    metric: str = Query(..., description="Metric to optimize"),
    ascending: bool = Query(default=False, description="True for ascending (minimize), False for descending (maximize)"),
    framework: Optional[ModelFramework] = Query(None, description="Filter by framework")
):
    """
    Get the best model based on a specific metric
    """
    try:
        best_model = metrics_service.get_best_model(metric=metric, ascending=ascending)
        
        if not best_model:
            return {
                "success": True,
                "message": f"No models found for metric: {metric}",
                "metric": metric,
                "ascending": ascending,
                "framework": framework.value if framework else None,
                "best_model": None,
                "timestamp": time.time()
            }
        
        # Filter by framework if specified
        if framework and best_model.framework != framework:
            return {
                "success": True,
                "message": f"No {framework.value} models found for metric: {metric}",
                "metric": metric,
                "ascending": ascending,
                "framework": framework.value,
                "best_model": None,
                "timestamp": time.time()
            }
        
        return {
            "success": True,
            "message": f"Best model found for metric: {metric}",
            "metric": metric,
            "ascending": ascending,
            "framework": best_model.framework.value if best_model.framework else None,
            "best_model": best_model.dict(),
            "timestamp": time.time()
        }
        
    except Exception as e:
        logger.error(f"Failed to get best model: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve best model: {str(e)}")

@metrics_router.get("/reports/{model_name}", response_model=ModelPerformanceReport)
async def get_model_performance_report(model_name: str):
    """
    Get comprehensive performance report for a model
    """
    try:
        report = metrics_service.generate_performance_report(model_name)
        
        if not report:
            raise HTTPException(status_code=404, detail=f"No performance report found for: {model_name}")
        
        return report
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get performance report for {model_name}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve performance report: {str(e)}")



@metrics_router.post("/models/save", response_model=Dict[str, Any])
async def save_model_for_prediction(
    request: SaveModelRequest,
    background_tasks: BackgroundTasks
):
    """
    Save a Keras model in the correct format for prediction use
    """
    try:
        # Check if model exists in metrics
        existing_metrics = metrics_service.load_training_metrics(request.model_name)
        
        if not existing_metrics and not request.overwrite:
            raise HTTPException(status_code=404, detail=f"No training metrics found for model: {request.model_name}")
        
        # Create model directory structure for prediction use
        model_dir = Path(request.save_path or f"models/keras_models/{request.model_name}")
        model_dir.mkdir(parents=True, exist_ok=True)
        
        # Get the model from the global model manager
        model_manager = get_model_manager()
        if model_manager is None or request.model_name not in model_manager.models:
            raise HTTPException(status_code=404, detail=f"Model {request.model_name} not found in model manager")
        
        # Get the Keras wrapper
        wrapper = model_manager.models[request.model_name]
        if not hasattr(wrapper, 'model'):
            raise HTTPException(status_code=400, detail=f"Model {request.model_name} is not a Keras model")
        
        keras_model = wrapper.model
        
        # Save the model in both formats for maximum compatibility
        saved_files = []
        
        # Save in .keras format (recommended for TF 2.14+)
        try:
            keras_path = model_dir / f"{request.model_name}.keras"
            keras_model.save(str(keras_path))  # No save_format needed for modern Keras
            saved_files.append(str(keras_path))
            logger.info(f"Model saved in .keras format: {keras_path}")
        except Exception as e:
            logger.warning(f"Failed to save .keras format: {e}")
        
        # Save in .h5 format (legacy compatibility)
        try:
            h5_path = model_dir / f"{request.model_name}.h5"
            keras_model.save(str(h5_path), save_format='h5')
            saved_files.append(str(h5_path))
            logger.info(f"Model saved in .h5 format: {h5_path}")
        except Exception as e:
            logger.warning(f"Failed to save .h5 format: {e}")
        
        # Create comprehensive metadata for prediction use
        metadata = SavedModelMetadata(
            model_name=request.model_name,
            model_path=str(model_dir),
            metadata_path=str(model_dir / "metadata.json"),
            framework=ModelFramework.KERAS,
            architecture="custom",
            accuracy=existing_metrics.final_validation_accuracy if existing_metrics else 0.0,
            loss=existing_metrics.final_validation_loss if existing_metrics else 0.0,
            precision=existing_metrics.precision,
            recall=existing_metrics.recall,
            f1_score=existing_metrics.f1_score,
            epochs_trained=existing_metrics.epochs_completed if existing_metrics else 0,
            training_time=existing_metrics.total_training_time or 0.0,
            final_learning_rate=existing_metrics.learning_rate or 0.001,
            num_classes=len(existing_metrics.class_distribution) if existing_metrics and existing_metrics.class_distribution else 4,
            class_names=list(existing_metrics.class_distribution.keys()) if existing_metrics and existing_metrics.class_distribution else ["glioma", "meningioma", "notumor", "pituitary"],
            description=request.metadata.get("description", f"Model {request.model_name} trained with Keras - Ready for prediction"),
            tags=request.metadata.get("tags", ["keras", "brain-tumor-classification", "prediction-ready"])
        )
        
        # Save metadata
        metadata_path = metrics_service.save_model_metadata(metadata)
        
        # Create prediction-specific model info
        model_info = {
            "model_name": request.model_name,
            "saved_for_prediction": True,
            "saved_formats": [Path(f).suffix for f in saved_files],
            "model_directory": str(model_dir),
            "prediction_ready": True,
            "input_shape": str(getattr(keras_model, 'input_shape', 'unknown')),
            "output_shape": str(getattr(keras_model, 'output_shape', 'unknown')),
            "total_params": getattr(keras_model, 'count_params', lambda: 0)(),
            "class_names": metadata.class_names,
            "metadata_path": metadata_path,
            "saved_files": saved_files,
            "timestamp": time.time()
        }
        
        # Save prediction-specific info
        info_path = model_dir / "prediction_info.json"
        import json
        with open(info_path, 'w') as f:
            json.dump(model_info, f, indent=2)
        
        # Add background task for cleanup if needed
        background_tasks.add_task(_cleanup_old_model_files, request.model_name)
        
        return {
            "success": True,
            "message": f"Model {request.model_name} saved successfully for prediction",
            "model_name": request.model_name,
            "model_directory": str(model_dir),
            "saved_files": saved_files,
            "prediction_info_path": str(info_path),
            "metadata_path": metadata_path,
            "prediction_ready": True,
            "timestamp": time.time()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to save model for prediction {request.model_name}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to save model for prediction: {str(e)}")

@metrics_router.delete("/cleanup")
async def cleanup_old_metrics(
    days_to_keep: int = Query(default=30, ge=1, le=365, description="Days to keep old metrics")
):
    """
    Clean up old metrics files
    """
    try:
        cleaned_count = metrics_service.cleanup_old_metrics(days_to_keep)
        
        return {
            "success": True,
            "message": f"Cleaned up {cleaned_count} old metrics files",
            "cleaned_count": cleaned_count,
            "days_to_keep": days_to_keep,
            "timestamp": time.time()
        }
        
    except Exception as e:
        logger.error(f"Failed to cleanup old metrics: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to cleanup metrics: {str(e)}")

@metrics_router.get("/dashboard")
async def get_dashboard_metrics():
    """
    Get dashboard summary metrics
    """
    try:
        # Get all training jobs
        all_jobs = metrics_service.list_training_jobs()
        
        # Get recent models
        recent_models = []
        models_dir = metrics_service.metrics_dir / "models"
        if models_dir.exists():
            for metadata_file in list(models_dir.glob("*.json"))[-5:]:  # Last 5 models
                try:
                    with open(metadata_file, 'r') as f:
                        import json
                        data = json.load(f, object_hook=_json_date_hook)
                    metadata = SavedModelMetadata.parse_obj(data)
                    recent_models.append(metadata)
                except Exception as e:
                    logger.warning(f"Failed to load model metadata from {metadata_file}: {e}")
                    continue
        
        # Calculate statistics
        stats = {
            "total_jobs": len(all_jobs),
            "active_jobs": len([j for j in all_jobs if j.status in [TrainingStatus.PENDING, TrainingStatus.RUNNING]]),
            "completed_jobs": len([j for j in all_jobs if j.status == TrainingStatus.COMPLETED]),
            "failed_jobs": len([j for j in all_jobs if j.status == TrainingStatus.FAILED]),
            "total_models": len(recent_models),
            "best_accuracy": 0.0,
            "avg_training_time": 0.0
        }
        
        # Calculate best accuracy
        if recent_models:
            stats["best_accuracy"] = max([m.accuracy for m in recent_models])
            stats["avg_training_time"] = sum([m.training_time for m in recent_models]) / len(recent_models)
        
        return {
            "success": True,
            "statistics": stats,
            "recent_models": [m.dict() for m in recent_models],
            "recent_jobs": [j.dict() for j in all_jobs[:5]],
            "timestamp": time.time()
        }
        
    except Exception as e:
        logger.error(f"Failed to get dashboard metrics: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve dashboard metrics: {str(e)}")

# Helper functions
async def _cleanup_old_model_files(model_name: str):
    """Enhanced background task to clean up old model files with better error handling"""
    try:
        logger.info(f"Starting cleanup of old model files for {model_name}")
        
        # Import necessary modules
        import shutil
        import time
        from pathlib import Path
        
        # Define cleanup paths
        models_base_dir = Path("models/keras_models")
        auto_save_dir = Path("auto_saved_models")
        metrics_dir = Path("metrics/models")
        
        cleaned_files = []
        errors_count = 0
        
        # Clean up old auto-saved models for this model name
        if auto_save_dir.exists():
            logger.debug(f"Scanning auto-save directory: {auto_save_dir}")
            try:
                auto_save_paths = list(auto_save_dir.glob(f"{model_name}_*"))
                logger.debug(f"Found {len(auto_save_paths)} auto-save paths for {model_name}")
                
                for auto_save_path in auto_save_paths:
                    try:
                        if auto_save_path.is_dir():
                            # Verify directory is not currently in use by checking for lock files
                            lock_files = list(auto_save_path.glob("*.lock"))
                            if lock_files:
                                logger.info(f"Skipping cleanup of {auto_save_path} - appears to be in use (lock files found)")
                                continue
                            
                            shutil.rmtree(auto_save_path)
                            cleaned_files.append(str(auto_save_path))
                            logger.info(f"Removed auto-saved model directory: {auto_save_path}")
                        elif auto_save_path.is_file():
                            # Clean up orphaned files too
                            auto_save_path.unlink()
                            cleaned_files.append(str(auto_save_path))
                            logger.info(f"Removed auto-saved model file: {auto_save_path}")
                    except PermissionError as e:
                        logger.warning(f"Permission denied removing {auto_save_path}: {e}")
                        errors_count += 1
                    except Exception as e:
                        logger.warning(f"Failed to remove auto-saved path {auto_save_path}: {e}")
                        errors_count += 1
            except Exception as e:
                logger.error(f"Error scanning auto-save directory: {e}")
                errors_count += 1
        
        # Clean up old model directories in the main models directory (keep only the latest 3)
        if models_base_dir.exists():
            logger.debug(f"Scanning models directory: {models_base_dir}")
            try:
                model_dirs = [d for d in models_base_dir.iterdir()
                             if d.is_dir() and d.name.startswith(model_name)]
                
                # Sort by modification time (newest first)
                model_dirs.sort(key=lambda x: x.stat().st_mtime, reverse=True)
                
                logger.debug(f"Found {len(model_dirs)} model directories for {model_name}, keeping latest 3")
                
                # Keep only the latest 3, remove the rest
                for old_dir in model_dirs[3:]:
                    try:
                        # Check if directory is in use
                        lock_files = list(old_dir.glob("*.lock"))
                        if lock_files:
                            logger.info(f"Skipping cleanup of {old_dir} - appears to be in use (lock files found)")
                            continue
                        
                        # Additional safety check - ensure directory exists and is accessible
                        if not old_dir.exists():
                            logger.warning(f"Directory {old_dir} no longer exists, skipping")
                            continue
                        
                        shutil.rmtree(old_dir)
                        cleaned_files.append(str(old_dir))
                        logger.info(f"Removed old model directory: {old_dir}")
                    except PermissionError as e:
                        logger.warning(f"Permission denied removing {old_dir}: {e}")
                        errors_count += 1
                    except Exception as e:
                        logger.warning(f"Failed to remove old model directory {old_dir}: {e}")
                        errors_count += 1
            except Exception as e:
                logger.error(f"Error scanning models directory: {e}")
                errors_count += 1
        
        # Clean up orphaned metadata files
        if metrics_dir.exists():
            logger.debug(f"Scanning metrics directory: {metrics_dir}")
            try:
                metadata_files = list(metrics_dir.glob(f"{model_name}_*.json"))
                logger.debug(f"Found {len(metadata_files)} metadata files for {model_name}")
                
                for metadata_file in metadata_files:
                    try:
                        # Check if file is locked
                        if metadata_file.suffix == '.lock':
                            continue
                        
                        # Verify file exists and is accessible
                        if not metadata_file.exists():
                            logger.warning(f"Metadata file {metadata_file} no longer exists, skipping")
                            continue
                        
                        metadata_file.unlink()
                        cleaned_files.append(str(metadata_file))
                        logger.info(f"Removed orphaned metadata file: {metadata_file}")
                    except PermissionError as e:
                        logger.warning(f"Permission denied removing {metadata_file}: {e}")
                        errors_count += 1
                    except Exception as e:
                        logger.warning(f"Failed to remove metadata file {metadata_file}: {e}")
                        errors_count += 1
            except Exception as e:
                logger.error(f"Error scanning metrics directory: {e}")
                errors_count += 1
        
        # Clean up any temporary files in the model directories
        temp_patterns = ["*.tmp", "*.temp", "__pycache__", "*.pyc"]
        for pattern in temp_patterns:
            for model_dir in models_base_dir.glob(f"{model_name}/*") if models_base_dir.exists() else []:
                if model_dir.is_dir():
                    try:
                        temp_items = list(model_dir.glob(pattern))
                        for temp_item in temp_items:
                            if temp_item.is_dir():
                                shutil.rmtree(temp_item)
                            else:
                                temp_item.unlink()
                            cleaned_files.append(str(temp_item))
                            logger.debug(f"Removed temporary file: {temp_item}")
                    except Exception as e:
                        logger.warning(f"Failed to clean temp files in {model_dir}: {e}")
                        errors_count += 1
        
        # Summary logging
        if cleaned_files:
            logger.info(f"Cleanup completed for {model_name}. Removed {len(cleaned_files)} items, {errors_count} errors")
            logger.debug(f"Cleaned files: {cleaned_files}")
        else:
            logger.info(f"Cleanup completed for {model_name}. No old files found to remove")
        
        # Add cleanup success metric
        cleanup_success = len(cleaned_files) > 0 and errors_count == 0
        if cleanup_success:
            logger.info(f"✅ Cleanup successful for {model_name}")
        else:
            logger.warning(f"⚠️  Cleanup completed with issues for {model_name}: {len(cleaned_files)} cleaned, {errors_count} errors")
        
    except Exception as e:
        logger.error(f"Critical failure in cleanup process for {model_name}: {str(e)}")
        # Don't re-raise to prevent background task from crashing

def _json_date_hook(obj):
    """JSON object hook to handle datetime objects"""
    if isinstance(obj, dict):
        for key, value in obj.items():
            if isinstance(value, str) and _is_iso_datetime(value):
                try:
                    obj[key] = datetime.fromisoformat(value.replace('Z', '+00:00'))
                except ValueError:
                    pass
    return obj

def _is_iso_datetime(s: str) -> bool:
    """Check if string is ISO datetime format"""
    try:
        datetime.fromisoformat(s.replace('Z', '+00:00'))
        return True
    except ValueError:
        return False