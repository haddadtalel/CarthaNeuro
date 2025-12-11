"""
Metrics service for storing, retrieving, and analyzing training metrics
"""
import json
import os
import pickle
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
import hashlib

from src.models.metrics_models import (
    ModelMetrics, TrainingJob, ModelPerformanceReport, SavedModelMetadata,
    EpochMetrics, ModelComparison, MetricHistory, MetricType, ModelFramework
)
from ..utils.logger import setup_logger

logger = setup_logger(__name__)

class MetricsService:
    """Service for managing training metrics and model performance data"""
    
    def __init__(self, metrics_dir: Optional[Path] = None):
        """Initialize metrics service"""
        self.metrics_dir = metrics_dir or Path("metrics")
        self.metrics_dir.mkdir(parents=True, exist_ok=True)
        
        # Ensure subdirectories exist
        (self.metrics_dir / "training").mkdir(exist_ok=True)
        (self.metrics_dir / "reports").mkdir(exist_ok=True)
        (self.metrics_dir / "models").mkdir(exist_ok=True)
        (self.metrics_dir / "comparisons").mkdir(exist_ok=True)
        (self.metrics_dir / "history").mkdir(exist_ok=True)
        
        logger.info(f"Metrics service initialized with directory: {self.metrics_dir}")
    
    def save_training_metrics(self, metrics: ModelMetrics) -> str:
        """Save training metrics to file"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{metrics.model_name}_{timestamp}.json"
            filepath = self.metrics_dir / "training" / filename
            
            # Add performance report generation
            metrics_dict = metrics.dict()
            metrics_dict["performance_report"] = self._generate_performance_report(metrics).dict()
            
            with open(filepath, 'w') as f:
                json.dump(metrics_dict, f, indent=2, default=str)
            
            logger.info(f"Saved training metrics to {filepath}")
            return str(filepath)
            
        except Exception as e:
            logger.error(f"Failed to save training metrics: {str(e)}")
            raise
    
    def load_training_metrics(self, model_name: str) -> Optional[ModelMetrics]:
        """Load latest training metrics for a model"""
        try:
            training_dir = self.metrics_dir / "training"
            if not training_dir.exists():
                return None
            
            # Find latest metrics file for the model
            model_files = list(training_dir.glob(f"{model_name}_*.json"))
            if not model_files:
                return None
            
            latest_file = max(model_files, key=lambda f: f.stat().st_mtime)
            
            with open(latest_file, 'r') as f:
                data = json.load(f, object_hook=self._json_date_hook)
            
            return ModelMetrics.parse_obj(data)
            
        except Exception as e:
            logger.error(f"Failed to load training metrics for {model_name}: {str(e)}")
            return None
    
    def save_model_metadata(self, metadata: SavedModelMetadata) -> str:
        """Save model metadata"""
        try:
            filepath = self.metrics_dir / "models" / f"{metadata.model_name}.json"
            
            with open(filepath, 'w') as f:
                json.dump(metadata.dict(), f, indent=2, default=str)
            
            logger.info(f"Saved model metadata to {filepath}")
            return str(filepath)
            
        except Exception as e:
            logger.error(f"Failed to save model metadata: {str(e)}")
            raise
    
    def load_model_metadata(self, model_name: str) -> Optional[SavedModelMetadata]:
        """Load model metadata"""
        try:
            filepath = self.metrics_dir / "models" / f"{model_name}.json"
            
            if not filepath.exists():
                return None
            
            with open(filepath, 'r') as f:
                data = json.load(f, object_hook=self._json_date_hook)
            
            return SavedModelMetadata.parse_obj(data)
            
        except Exception as e:
            logger.error(f"Failed to load model metadata for {model_name}: {str(e)}")
            return None
    
    def create_training_job(self, job: TrainingJob) -> None:
        """Create or update a training job"""
        try:
            jobs_file = self.metrics_dir / "training_jobs.json"
            
            # Load existing jobs
            jobs = self._load_training_jobs()
            
            # Update or add job
            jobs[job.job_id] = job.dict()
            
            # Save back to file
            with open(jobs_file, 'w') as f:
                json.dump(jobs, f, indent=2, default=str)
            
            logger.info(f"Created/updated training job: {job.job_id}")
            
        except Exception as e:
            logger.error(f"Failed to create training job: {str(e)}")
            raise
    
    def update_training_job(self, job_id: str, **kwargs) -> Optional[TrainingJob]:
        """Update training job with new data"""
        try:
            jobs = self._load_training_jobs()
            
            if job_id not in jobs:
                logger.warning(f"Training job {job_id} not found")
                return None
            
            # Update job data
            job_data = jobs[job_id]
            for key, value in kwargs.items():
                if key in ['progress', 'current_epoch', 'status', 'last_update', 'current_metrics']:
                    job_data[key] = value
            
            jobs[job_id] = job_data
            
            # Save back to file
            jobs_file = self.metrics_dir / "training_jobs.json"
            with open(jobs_file, 'w') as f:
                json.dump(jobs, f, indent=2, default=str)
            
            return TrainingJob.parse_obj(job_data)
            
        except Exception as e:
            logger.error(f"Failed to update training job {job_id}: {str(e)}")
            return None
    
    def get_training_job(self, job_id: str) -> Optional[TrainingJob]:
        """Get training job by ID"""
        try:
            jobs = self._load_training_jobs()
            job_data = jobs.get(job_id)
            
            if job_data:
                return TrainingJob.parse_obj(job_data)
            return None
            
        except Exception as e:
            logger.error(f"Failed to get training job {job_id}: {str(e)}")
            return None
    
    def list_training_jobs(self, status: Optional[str] = None) -> List[TrainingJob]:
        """List all training jobs, optionally filtered by status"""
        try:
            jobs = self._load_training_jobs()
            result = []
            
            for job_data in jobs.values():
                job = TrainingJob.parse_obj(job_data)
                if status is None or job.status == status:
                    result.append(job)
            
            # Sort by start time, newest first
            result.sort(key=lambda j: j.start_time, reverse=True)
            return result
            
        except Exception as e:
            logger.error(f"Failed to list training jobs: {str(e)}")
            return []
    
    def get_model_history(self, model_name: str, metric_type: MetricType) -> Optional[MetricHistory]:
        """Get historical metrics for a specific model and metric type"""
        try:
            history_file = self.metrics_dir / "history" / f"{model_name}_{metric_type}.json"
            
            if not history_file.exists():
                return None
            
            with open(history_file, 'r') as f:
                data = json.load(f, object_hook=self._json_date_hook)
            
            return MetricHistory.parse_obj(data)
            
        except Exception as e:
            logger.error(f"Failed to get model history: {str(e)}")
            return None
    
    def create_metric_history(self, metrics: ModelMetrics) -> List[str]:
        """Create metric history from training metrics"""
        try:
            created_files = []
            
            # Create history for each metric type
            metric_mappings = {
                MetricType.ACCURACY: metrics.final_training_accuracy,
                MetricType.LOSS: metrics.final_training_loss,
                MetricType.VALIDATION_ACCURACY: metrics.final_validation_accuracy,
                MetricType.VALIDATION_LOSS: metrics.final_validation_loss,
                MetricType.LEARNING_RATE: metrics.learning_rate
            }
            
            for metric_type, value in metric_mappings.items():
                history = MetricHistory(
                    model_name=metrics.model_name,
                    metric_type=metric_type,
                    values=[value] if value is not None else [],
                    epochs=[metrics.epochs_completed],
                    timestamps=[datetime.now()],
                    framework=metrics.framework
                )
                
                # Append to existing history if it exists
                existing_history = self.get_model_history(metrics.model_name, metric_type)
                if existing_history:
                    history.values = existing_history.values + history.values
                    history.epochs = existing_history.epochs + history.epochs
                    history.timestamps = existing_history.timestamps + history.timestamps
                
                # Save history
                history_file = self.metrics_dir / "history" / f"{metrics.model_name}_{metric_type}.json"
                with open(history_file, 'w') as f:
                    json.dump(history.dict(), f, indent=2, default=str)
                
                created_files.append(str(history_file))
            
            logger.info(f"Created metric history files: {created_files}")
            return created_files
            
        except Exception as e:
            logger.error(f"Failed to create metric history: {str(e)}")
            raise
    
    def compare_models(self, model_names: List[str], metrics_to_compare: List[str]) -> ModelComparison:
        """Compare multiple models on specified metrics"""
        try:
            comparison_id = f"comparison_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            comparison_metrics = {}
            
            for model_name in model_names:
                metrics = self.load_training_metrics(model_name)
                if metrics:
                    model_comparison_data = {}
                    
                    for metric in metrics_to_compare:
                        if hasattr(metrics, metric):
                            value = getattr(metrics, metric)
                            if value is not None:
                                model_comparison_data[metric] = float(value)
                    
                    comparison_metrics[model_name] = model_comparison_data
            
            comparison = ModelComparison(
                comparison_id=comparison_id,
                name=f"Model Comparison - {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                model_names=model_names,
                comparison_metrics=comparison_metrics
            )
            
            # Save comparison
            comparison_file = self.metrics_dir / "comparisons" / f"{comparison_id}.json"
            with open(comparison_file, 'w') as f:
                json.dump(comparison.dict(), f, indent=2, default=str)
            
            logger.info(f"Created model comparison: {comparison_id}")
            return comparison
            
        except Exception as e:
            logger.error(f"Failed to compare models: {str(e)}")
            raise
    
    def get_best_model(self, metric: str, ascending: bool = False) -> Optional[SavedModelMetadata]:
        """Get the best model based on a specific metric"""
        try:
            models_dir = self.metrics_dir / "models"
            if not models_dir.exists():
                return None
            
            best_model = None
            best_value = float('inf') if ascending else float('-inf')
            
            for metadata_file in models_dir.glob("*.json"):
                try:
                    with open(metadata_file, 'r') as f:
                        data = json.load(f, object_hook=self._json_date_hook)
                    
                    metadata = SavedModelMetadata.parse_obj(data)
                    
                    if hasattr(metadata, metric):
                        value = getattr(metadata, metric)
                        if value is not None:
                            if (ascending and value < best_value) or (not ascending and value > best_value):
                                best_value = value
                                best_model = metadata
                
                except Exception as e:
                    logger.warning(f"Failed to process model metadata file {metadata_file}: {str(e)}")
                    continue
            
            return best_model
            
        except Exception as e:
            logger.error(f"Failed to get best model: {str(e)}")
            return None
    
    def generate_performance_report(self, model_name: str) -> Optional[ModelPerformanceReport]:
        """Generate comprehensive performance report for a model"""
        try:
            metrics = self.load_training_metrics(model_name)
            if not metrics:
                return None
            
            return self._generate_performance_report(metrics)
            
        except Exception as e:
            logger.error(f"Failed to generate performance report for {model_name}: {str(e)}")
            return None
    
    def _generate_performance_report(self, metrics: ModelMetrics) -> ModelPerformanceReport:
        """Generate performance report from model metrics"""
        try:
            # Calculate efficiency metrics
            time_per_epoch = metrics.total_training_time / metrics.epochs_completed if metrics.total_training_time else 0
            accuracy_improvement = metrics.final_validation_accuracy - (metrics.epoch_metrics[0].validation_accuracy if metrics.epoch_metrics else 0)
            
            # Generate recommendations
            recommendations = []
            potential_improvements = []
            
            if metrics.final_validation_accuracy < 0.85:
                recommendations.append("Consider increasing model complexity or training time")
                potential_improvements.append("Try data augmentation techniques")
            
            if metrics.final_validation_loss > metrics.final_training_loss * 1.5:
                recommendations.append("Model may be overfitting")
                potential_improvements.append("Add regularization techniques")
            
            if time_per_epoch > 60:  # More than 1 minute per epoch
                recommendations.append("Training is slow - consider reducing model size or batch size")
                potential_improvements.append("Use mixed precision training")
            
            # Performance trends
            performance_trends = {}
            if metrics.epoch_metrics:
                performance_trends["validation_accuracy"] = [em.validation_accuracy for em in metrics.epoch_metrics]
                performance_trends["training_loss"] = [em.training_loss for em in metrics.epoch_metrics]
            
            return ModelPerformanceReport(
                report_id=f"report_{metrics.model_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                model_name=metrics.model_name,
                overall_performance={
                    "accuracy": metrics.final_validation_accuracy,
                    "loss": metrics.final_validation_loss,
                    "precision": metrics.precision or 0,
                    "recall": metrics.recall or 0,
                    "f1_score": metrics.f1_score or 0
                },
                training_efficiency={
                    "epochs_completed": metrics.epochs_completed,
                    "total_time": metrics.total_training_time or 0,
                    "time_per_epoch": time_per_epoch,
                    "accuracy_improvement": accuracy_improvement
                },
                resource_utilization={
                    "gpu_memory_peak": metrics.gpu_memory_peak or 0,
                    "gpu_utilization_avg": metrics.gpu_utilization_avg or 0
                },
                recommendations=recommendations,
                potential_improvements=potential_improvements,
                performance_trends=performance_trends
            )
            
        except Exception as e:
            logger.error(f"Failed to generate performance report: {str(e)}")
            raise
    
    def _load_training_jobs(self) -> Dict[str, Any]:
        """Load training jobs from file"""
        jobs_file = self.metrics_dir / "training_jobs.json"
        
        if jobs_file.exists():
            with open(jobs_file, 'r') as f:
                return json.load(f, object_hook=self._json_date_hook)
        
        return {}
    
    def _json_date_hook(self, obj):
        """JSON object hook to handle datetime objects"""
        if isinstance(obj, dict):
            for key, value in obj.items():
                if isinstance(value, str) and self._is_iso_datetime(value):
                    try:
                        obj[key] = datetime.fromisoformat(value.replace('Z', '+00:00'))
                    except ValueError:
                        pass
        return obj
    
    def _is_iso_datetime(self, s: str) -> bool:
        """Check if string is ISO datetime format"""
        try:
            datetime.fromisoformat(s.replace('Z', '+00:00'))
            return True
        except ValueError:
            return False
    
    def cleanup_old_metrics(self, days_to_keep: int = 30) -> int:
        """Clean up metrics files older than specified days"""
        try:
            cutoff_time = datetime.now().timestamp() - (days_to_keep * 24 * 3600)
            cleaned_count = 0
            
            for subdir in self.metrics_dir.iterdir():
                if subdir.is_dir():
                    for file_path in subdir.rglob("*"):
                        if file_path.is_file() and file_path.stat().st_mtime < cutoff_time:
                            file_path.unlink()
                            cleaned_count += 1
            
            logger.info(f"Cleaned up {cleaned_count} old metrics files")
            return cleaned_count
            
        except Exception as e:
            logger.error(f"Failed to cleanup old metrics: {str(e)}")
            return 0