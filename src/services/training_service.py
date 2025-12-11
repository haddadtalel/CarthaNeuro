"""
Training job tracking service for CarthaNeuro with auto-saving integration
"""
import asyncio
import time
import uuid
from datetime import datetime
from enum import Enum
from typing import Dict, Optional, List, Any
from threading import Lock
import logging

logger = logging.getLogger(__name__)

# Enhanced model service for auto-saving integration
_enhanced_model_service = None

def set_enhanced_model_service(service):
    """Set the enhanced model service for training integration"""
    global _enhanced_model_service
    _enhanced_model_service = service

def get_enhanced_model_service():
    """Get the enhanced model service"""
    global _enhanced_model_service
    return _enhanced_model_service

class TrainingStatus(Enum):
    """Training job status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class TrainingJob:
    """Training job data model"""
    def __init__(
        self,
        job_id: str,
        model_type: str,
        architecture: str,
        num_epochs: int,
        batch_size: int,
        learning_rate: float,
        validation_split: float,
        user_id: str,
        device: str = "cpu",
        created_at: Optional[float] = None,
        model_name: Optional[str] = None
    ):
        self.job_id = job_id
        self.model_type = model_type
        self.architecture = architecture
        self.num_epochs = num_epochs
        self.batch_size = batch_size
        self.learning_rate = learning_rate
        self.validation_split = validation_split
        self.user_id = user_id
        self.device = device  # Store user's device preference
        self.created_at = created_at or time.time()
        self.model_name = model_name or f"{model_type}_model_{job_id[:8]}"  # Auto-generate if not provided
        self.framework = model_type  # Store framework type
        self.started_at: Optional[float] = None
        self.completed_at: Optional[float] = None
        self.status = TrainingStatus.PENDING
        self.progress = 0.0
        self.current_epoch = 0
        self.current_batch = 0
        self.total_batches = 0
        self.loss = 0.0
        self.accuracy = 0.0
        self.val_loss = 0.0
        self.val_accuracy = 0.0
        self.error_message: Optional[str] = None
        self.logs: List[str] = []

    def to_dict(self) -> Dict:
        """Convert job to dictionary for API responses"""
        return {
            "job_id": self.job_id,
            "model_type": self.model_type,
            "architecture": self.architecture,
            "num_epochs": self.num_epochs,
            "batch_size": self.batch_size,
            "learning_rate": self.learning_rate,
            "validation_split": self.validation_split,
            "user_id": self.user_id,
            "status": self.status.value,
            "progress": self.progress,
            "current_epoch": self.current_epoch,
            "current_batch": self.current_batch,
            "total_batches": self.total_batches,
            "loss": self.loss,
            "accuracy": self.accuracy,
            "val_loss": self.val_loss,
            "val_accuracy": self.val_accuracy,
            "error_message": self.error_message,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "device": self.device,
            "model_name": self.model_name,
            "framework": self.framework,
            "logs": self.logs
        }

class TrainingService:
    """Service for managing training jobs"""
    
    def __init__(self):
        self._jobs: Dict[str, TrainingJob] = {}
        self._lock = Lock()
        logger.info("TrainingService initialized")
    
    def create_job(
        self,
        model_type: str,
        architecture: str,
        num_epochs: int,
        batch_size: int,
        learning_rate: float,
        validation_split: float,
        user_id: str,
        device: str = "cpu",
        model_name: Optional[str] = None
    ) -> str:
        """Create a new training job"""
        job_id = str(uuid.uuid4())
        
        # Validate device and apply fallback if GPU not available
        import torch
        if device == "cuda" and not torch.cuda.is_available():
            device = "cpu"
            logger.warning(f"GPU requested but not available for job {job_id}, falling back to CPU")
        
        with self._lock:
            job = TrainingJob(
                job_id=job_id,
                model_type=model_type,
                architecture=architecture,
                num_epochs=num_epochs,
                batch_size=batch_size,
                learning_rate=learning_rate,
                validation_split=validation_split,
                user_id=user_id,
                device=device,
                model_name=model_name
            )
            self._jobs[job_id] = job
        
        logger.info(f"Created training job {job_id} for model {model_type} ({architecture}) - "
                   f"Epochs: {num_epochs}, Batch: {batch_size}, LR: {learning_rate}, Device: {device}, User: {user_id}")
        logger.info(f"Training job {job_id} is now PENDING and ready to start")
        return job_id
    
    def get_job(self, job_id: str) -> Optional[TrainingJob]:
        """Get job by ID"""
        with self._lock:
            return self._jobs.get(job_id)
    
    def get_user_jobs(self, user_id: str) -> List[TrainingJob]:
        """Get all jobs for a user"""
        with self._lock:
            return [job for job in self._jobs.values() if job.user_id == user_id]
    
    def get_all_jobs(self) -> List[TrainingJob]:
        """Get all jobs (for admin)"""
        with self._lock:
            return list(self._jobs.values())
    
    def update_job_status(
        self,
        job_id: str,
        status: TrainingStatus,
        progress: Optional[float] = None,
        current_epoch: Optional[int] = None,
        current_batch: Optional[int] = None,
        total_batches: Optional[int] = None,
        loss: Optional[float] = None,
        accuracy: Optional[float] = None,
        val_loss: Optional[float] = None,
        val_accuracy: Optional[float] = None,
        error_message: Optional[str] = None,
        log_message: Optional[str] = None,
        trained_model: Optional[Any] = None
    ) -> bool:
        """Update job status and metrics"""
        with self._lock:
            job = self._jobs.get(job_id)
            if not job:
                logger.warning(f"Job {job_id} not found for update")
                return False
            
            # Update status
            if status != job.status:
                old_status = job.status.value
                job.status = status
                if status == TrainingStatus.RUNNING and job.started_at is None:
                    job.started_at = time.time()
                    logger.info(f"Training job {job_id} STARTED - Status changed from {old_status} to RUNNING")
                elif status in [TrainingStatus.COMPLETED, TrainingStatus.FAILED, TrainingStatus.CANCELLED]:
                    job.completed_at = time.time()
                    logger.info(f"Training job {job_id} FINISHED - Status changed from {old_status} to {status.value}")
                    if status == TrainingStatus.COMPLETED:
                        total_time = job.completed_at - job.started_at if job.started_at else 0
                        logger.info(f"Training job {job_id} completed successfully in {total_time:.1f} seconds - "
                                   f"Final metrics - Loss: {job.loss:.4f}, Accuracy: {job.accuracy:.4f}, "
                                   f"Val Loss: {job.val_loss:.4f}, Val Accuracy: {job.val_accuracy:.4f}")
                        
                        # Trigger auto-save integration if enhanced model service is available
                        enhanced_service = get_enhanced_model_service()
                        if enhanced_service:
                            try:
                                # Create completion data for auto-save
                                completion_data = {
                                    "job_id": job_id,
                                    "model_name": getattr(job, 'model_name', f"model_{job_id[:8]}"),
                                    "framework": getattr(job, 'framework', 'keras'),
                                    "architecture": job.architecture,
                                    "epochs_completed": job.current_epoch,
                                    "total_epochs": job.num_epochs,
                                    "batch_size": job.batch_size,
                                    "learning_rate": job.learning_rate,
                                    "optimizer": "adam",  # Default, can be made configurable
                                    "loss_function": "categorical_crossentropy",
                                    "final_training_loss": job.loss or 0.0,
                                    "final_training_accuracy": job.accuracy or 0.0,
                                    "final_validation_loss": job.val_loss or 0.0,
                                    "final_validation_accuracy": job.val_accuracy or 0.0,
                                    "best_validation_accuracy": job.val_accuracy or 0.0,
                                    "best_epoch": job.current_epoch,
                                    "start_time": job.started_at,
                                    "training_time": total_time,
                                    "user_id": job.user_id
                                }
                                
                                # Run auto-save in background to avoid blocking
                                asyncio.create_task(
                                    enhanced_service.integrate_with_training_service(completion_data, trained_model)
                                )
                                
                                logger.info(f"Auto-save integration triggered for completed job {job_id}")
                                
                            except Exception as e:
                                logger.error(f"Failed to trigger auto-save for job {job_id}: {str(e)}")
                        
                    elif status == TrainingStatus.FAILED:
                        logger.error(f"Training job {job_id} failed - Error: {error_message or 'Unknown error'}")
                    elif status == TrainingStatus.CANCELLED:
                        logger.warning(f"Training job {job_id} was cancelled by user")
            
            # Update progress and metrics
            if progress is not None:
                job.progress = max(0.0, min(100.0, progress))
            if current_epoch is not None:
                job.current_epoch = current_epoch
            if current_batch is not None:
                job.current_batch = current_batch
            if total_batches is not None:
                job.total_batches = total_batches
            if loss is not None:
                job.loss = loss
            if accuracy is not None:
                job.accuracy = accuracy
            if val_loss is not None:
                job.val_loss = val_loss
            if val_accuracy is not None:
                job.val_accuracy = val_accuracy
            if error_message is not None:
                job.error_message = error_message
            
            # Add log message if provided
            if log_message:
                timestamp = datetime.fromtimestamp(time.time()).strftime("%Y-%m-%d %H:%M:%S")
                log_entry = f"[{timestamp}] {log_message}"
                job.logs.append(log_entry)
                # Keep only last 100 log entries
                if len(job.logs) > 100:
                    job.logs = job.logs[-100:]
                
                # Also log to the application logger for backend visibility
                if status == TrainingStatus.RUNNING:
                    progress_val = progress if progress is not None else job.progress
                    epoch_str = f"{job.current_epoch}/{getattr(job, 'num_epochs', '?')}"
                    logger.info(f"🔄 Training Job {job_id} - Progress: {progress_val:.1f}% - Epoch: {epoch_str} - {log_message}")
                    # Log detailed metrics if available and not None
                    if (job.loss is not None and job.accuracy is not None and 
                        job.val_loss is not None and job.val_accuracy is not None and
                        (job.loss > 0 or job.accuracy > 0)):
                        logger.info(f"📊 Training Job {job_id} - Metrics: Loss: {job.loss:.4f}, Accuracy: {job.accuracy:.4f}, Val_Loss: {job.val_loss:.4f}, Val_Accuracy: {job.val_accuracy:.4f}")
                else:
                    logger.info(f"✅ Training Job {job_id} - Status: {status.value} - {log_message}")
                    if status == TrainingStatus.COMPLETED:
                        # Ensure all metrics are not None before formatting
                        loss_val = job.loss if job.loss is not None else 0.0
                        accuracy_val = job.accuracy if job.accuracy is not None else 0.0
                        val_loss_val = job.val_loss if job.val_loss is not None else 0.0
                        val_accuracy_val = job.val_accuracy if job.val_accuracy is not None else 0.0
                        
                        logger.info(f"🎉 Training Job {job_id} COMPLETED - Final Metrics: Loss: {loss_val:.4f}, Accuracy: {accuracy_val:.4f}, Val_Loss: {val_loss_val:.4f}, Val_Accuracy: {val_accuracy_val:.4f}")
                        logger.info(f"💾 Training Job {job_id} - Model ready for saving!")
            
            logger.debug(f"Updated job {job_id}: status={status.value}, progress={job.progress:.1f}%")
            return True
    
    def delete_job(self, job_id: str) -> bool:
        """Delete a job"""
        with self._lock:
            if job_id in self._jobs:
                del self._jobs[job_id]
                logger.info(f"Deleted training job {job_id}")
                return True
            return False
    
    def cleanup_old_jobs(self, days_to_keep: int = 7) -> int:
        """Clean up old completed/failed jobs"""
        cutoff_time = time.time() - (days_to_keep * 24 * 60 * 60)
        jobs_to_delete = []
        
        with self._lock:
            for job_id, job in self._jobs.items():
                if (job.status in [TrainingStatus.COMPLETED, TrainingStatus.FAILED, TrainingStatus.CANCELLED] 
                    and job.completed_at and job.completed_at < cutoff_time):
                    jobs_to_delete.append(job_id)
            
            for job_id in jobs_to_delete:
                del self._jobs[job_id]
        
        if jobs_to_delete:
            logger.info(f"Cleaned up {len(jobs_to_delete)} old training jobs")
        
        return len(jobs_to_delete)

# Global training service instance
training_service = TrainingService()