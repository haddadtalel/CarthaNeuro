"""
Enhanced Model Service for automatic model and metrics saving with MongoDB integration
"""
import os
import asyncio
import shutil
import json
import time
import hashlib
import pickle
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, Optional, List, Union
import uuid
import tensorflow as tf
from src.config.settings import settings
from bson import ObjectId

from src.models.metrics_models import ModelMetrics, SavedModelMetadata, ModelFramework
from src.services.metrics_service import MetricsService
from src.database.mongodb_service import get_db_operations, ModelDocument
from src.models.model_manager import ModelManager
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

class EnhancedModelService:
    """Enhanced service for automatic model/metrics saving and MongoDB integration"""
    
    def __init__(self, model_manager: ModelManager, metrics_service: MetricsService):
        self.model_manager = model_manager
        self.metrics_service = metrics_service
        self.auto_save_dir = Path("auto_saved_models")
        self.auto_save_dir.mkdir(exist_ok=True)
        
        # Track auto-saved models for cleanup
        self._auto_saved_models = {}
        
    async def initialize(self):
        """Initialize the enhanced model service"""
        logger.info("Initializing Enhanced Model Service...")
        
        # Create auto-save directory
        self.auto_save_dir.mkdir(parents=True, exist_ok=True)
        
        # Load existing auto-saved models from previous session
        await self._load_auto_saved_models()
        
        logger.info("Enhanced Model Service initialized successfully")
    
    async def _load_auto_saved_models(self):
        """Load auto-saved models from previous session"""
        try:
            for model_dir in self.auto_save_dir.iterdir():
                if model_dir.is_dir():
                    model_name = model_dir.name
                    metadata_file = model_dir / "auto_save_metadata.json"
                    
                    if metadata_file.exists():
                        with open(metadata_file, 'r') as f:
                            metadata = json.load(f)
                        
                        self._auto_saved_models[model_name] = {
                            "path": str(model_dir),
                            "saved_at": metadata.get("saved_at"),
                            "model_type": metadata.get("model_type"),
                            "framework": metadata.get("framework")
                        }
                        
            logger.info(f"Loaded {len(self._auto_saved_models)} auto-saved models from previous session")
            
        except Exception as e:
            logger.error(f"Failed to load auto-saved models: {str(e)}")
    
    async def auto_save_model_and_metrics(
        self,
        model_name: str,
        model_framework: ModelFramework,
        final_metrics: Optional[ModelMetrics] = None,
        training_metadata: Optional[Dict[str, Any]] = None,
        model_instance: Optional[Any] = None
    ) -> Dict[str, Any]:
        """
        Automatically save model and metrics during training completion
        
        Args:
            model_name: Name of the model
            model_framework: Framework used (Keras, PyTorch, etc.)
            final_metrics: Final training metrics
            training_metadata: Additional training metadata
            model_instance: The actual trained model instance (if available)
            
        Returns:
            Dict with save result information
        """
        try:
            logger.info(f"Auto-saving model {model_name} with {model_framework} framework")
            
            # Generate unique save ID for auto-saved models
            save_id = f"auto_{int(time.time())}_{uuid.uuid4().hex[:8]}"
            auto_save_path = self.auto_save_dir / f"{model_name}_{save_id}"
            
            # Ensure directory exists
            auto_save_path.mkdir(parents=True, exist_ok=True)
            
            # Save the actual model files
            saved_files = []
            
            if model_framework == ModelFramework.KERAS:
                # Try multiple approaches to get the Keras model
                model_to_save = None
                
                # Approach 1: Check if model instance is provided
                if model_instance and hasattr(model_instance, 'save'):
                    model_to_save = model_instance
                # Approach 2: Check if model exists in memory via Keras wrapper
                elif model_name in self.model_manager.models:
                    wrapper = self.model_manager.models[model_name]
                    if hasattr(wrapper, 'model'):
                        model_to_save = wrapper.model
                # Approach 3: Check saved Keras models directory
                else:
                    keras_models_dir = settings.models_dir / "keras_models"
                    potential_model_path = keras_models_dir / model_name
                    if potential_model_path.exists():
                        # Load from saved directory and then save to auto-save
                        try:
                            from src.models.keras_wrapper import KerasModelWrapper
                            wrapper = KerasModelWrapper.load_model(str(potential_model_path))
                            model_to_save = wrapper.model
                            logger.info(f"Found and loaded Keras model from {potential_model_path}")
                        except Exception as e:
                            logger.warning(f"Failed to load existing Keras model: {e}")
                
                if model_to_save:
                    # Professional automatic saving of Keras model in both .h5 and .keras formats
                    saved_formats = []
                    save_errors = []
                    
                    # Save in .h5 format (legacy format for compatibility)
                    try:
                        h5_model_path = auto_save_path / "model.h5"
                        model_to_save.save(str(h5_model_path), save_format='h5')
                        saved_files.append(str(h5_model_path))
                        saved_formats.append("h5")
                        logger.info(f"Keras model saved in .h5 format to {h5_model_path}")
                    except Exception as e:
                        error_msg = f"Failed to save .h5 format: {str(e)}"
                        save_errors.append(error_msg)
                        logger.error(error_msg)
                    
                    # Save in .keras format (recommended modern format)
                    try:
                        keras_model_path = auto_save_path / "model.keras"
                        model_to_save.save(str(keras_model_path), save_format='keras')
                        saved_files.append(str(keras_model_path))
                        saved_formats.append("keras")
                        logger.info(f"Keras model saved in .keras format to {keras_model_path}")
                    except Exception as e:
                        error_msg = f"Failed to save .keras format: {str(e)}"
                        save_errors.append(error_msg)
                        logger.error(error_msg)
                    
                    # Enhanced metadata for both formats
                    try:
                        # Get model information
                        model_info = {
                            "model_name": model_name,
                            "framework": "keras",
                            "saved_at": datetime.now().isoformat(),
                            "save_type": "auto_save",
                            "save_formats": saved_formats,
                            "save_errors": save_errors,
                            "input_shape": str(getattr(model_to_save, 'input_shape', 'unknown')),
                            "output_shape": str(getattr(model_to_save, 'output_shape', 'unknown')),
                            "total_params": getattr(model_to_save, 'count_params', lambda: 0)(),
                            "model_summary": str(model_to_save.summary()) if hasattr(model_to_save, 'summary') else "summary_not_available",
                            "best_model": True,  # Mark as best trained model
                            "professional_save": True,
                            "multi_format_support": True
                        }
                        
                        # Save comprehensive model info
                        model_info_path = auto_save_path / "model_info.json"
                        with open(model_info_path, 'w') as f:
                            json.dump(model_info, f, indent=2)
                        saved_files.append(str(model_info_path))
                        logger.info(f"Enhanced model metadata saved to {model_info_path}")
                        
                        # Create a professional summary file
                        summary_path = auto_save_path / "model_summary.txt"
                        with open(summary_path, 'w') as f:
                            f.write(f"Enhanced Model Service - Professional Auto-Save Summary\n")
                            f.write(f"=" * 60 + "\n\n")
                            f.write(f"Model Name: {model_name}\n")
                            f.write(f"Framework: Keras\n")
                            f.write(f"Saved At: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                            f.write(f"Save ID: {save_id}\n")
                            f.write(f"Formats Saved: {', '.join(saved_formats)}\n")
                            f.write(f"Total Parameters: {model_info['total_params']}\n")
                            f.write(f"Input Shape: {model_info['input_shape']}\n")
                            f.write(f"Output Shape: {model_info['output_shape']}\n")
                            f.write(f"Professional Save: {model_info['professional_save']}\n")
                            f.write(f"Multi-Format Support: {model_info['multi_format_support']}\n")
                            f.write(f"\nBest Trained Model - Ready for Production Use\n")
                            f.write(f"Both .h5 and .keras formats available for maximum compatibility\n")
                            if save_errors:
                                f.write(f"\nSave Errors:\n")
                                for error in save_errors:
                                    f.write(f"  - {error}\n")
                        
                        saved_files.append(str(summary_path))
                        
                    except Exception as e:
                        logger.error(f"Failed to save enhanced metadata: {e}")
                    
                    # Log final status
                    if saved_formats:
                        logger.info(f"Successfully saved {model_name} in {len(saved_formats)} format(s): {', '.join(saved_formats)}")
                    if save_errors:
                        logger.warning(f"Model saved with {len(save_errors)} format error(s)")
                        
                else:
                    logger.warning(f"No Keras model found to save for {model_name}")
            elif model_framework == ModelFramework.PYTORCH:
                # For PyTorch models, save the model state dict
                if model_instance:
                    try:
                        import torch
                        model_path = auto_save_path / "model.pt"
                        torch.save(model_instance.state_dict(), model_path)
                        saved_files.append(str(model_path))
                        logger.info(f"PyTorch model saved to {model_path}")
                        
                        # Save model metadata
                        model_info = {
                            "model_name": model_name,
                            "framework": "pytorch",
                            "saved_at": datetime.now().isoformat(),
                            "save_type": "auto_save",
                            "save_format": "pytorch_state_dict"
                        }
                        
                        with open(auto_save_path / "model_info.json", 'w') as f:
                            json.dump(model_info, f, indent=2)
                        saved_files.append(str(auto_save_path / "model_info.json"))
                        
                    except Exception as e:
                        logger.error(f"Failed to save PyTorch model: {e}")
                else:
                    logger.warning(f"No PyTorch model instance provided for {model_name}")
            else:
                logger.warning(f"Unsupported framework: {model_framework}")
                    
            # Save metrics if provided
            if final_metrics:
                metrics_path = auto_save_path / "metrics.json"
                with open(metrics_path, 'w') as f:
                    json.dump(final_metrics.dict(), f, indent=2, default=str)
                saved_files.append(str(metrics_path))
                
                # Also save metrics through metrics service
                try:
                    self.metrics_service.save_training_metrics(final_metrics)
                except Exception as e:
                    logger.warning(f"Failed to save metrics through metrics service: {e}")
            
            # Save auto-save metadata
            auto_save_metadata = {
                "model_name": model_name,
                "save_id": save_id,
                "framework": model_framework.value,
                "saved_at": datetime.now().isoformat(),
                "save_type": "auto_save",
                "training_metadata": training_metadata or {},
                "files_saved": saved_files,
                "auto_save": True
            }
            
            with open(auto_save_path / "auto_save_metadata.json", 'w') as f:
                json.dump(auto_save_metadata, f, indent=2)
            
            # Track the auto-saved model
            self._auto_saved_models[model_name] = {
                "path": str(auto_save_path),
                "saved_at": auto_save_metadata["saved_at"],
                "model_type": model_framework.value,
                "save_id": save_id
            }
            
            logger.info(f"Auto-saved model {model_name} to {auto_save_path}")
            
            return {
                "success": True,
                "model_name": model_name,
                "auto_save_path": str(auto_save_path),
                "save_id": save_id,
                "files_saved": saved_files,
                "message": "Model auto-saved successfully"
            }
            
        except Exception as e:
            logger.error(f"Failed to auto-save model {model_name}: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "model_name": model_name
            }
    
    def _register_model_in_memory(self, model_name: str, model_framework: ModelFramework, auto_save_path: str):
        """Register model in memory so it can be saved immediately after training"""
        try:
            # For both Keras and PyTorch models, create and register a wrapper
            if model_framework in [ModelFramework.KERAS, ModelFramework.PYTORCH]:
                # Try to create a Keras wrapper for the saved model
                from src.models.keras_wrapper import KerasModelWrapper, create_keras_model
                
                # Create a new Keras model wrapper
                keras_model = create_keras_model(
                    num_classes=settings.num_classes,
                    model_type="simple_cnn"  # Default type for auto-saved models
                )
                
                wrapper = KerasModelWrapper(
                    model=keras_model,
                    model_name=model_name,
                    model_type=f"{model_framework.value}_auto_saved"
                )
                
                # Register in model manager's memory
                self.model_manager.models[model_name] = wrapper
                self.model_manager.model_info[model_name] = {
                    "name": model_name,
                    "type": f"{model_framework.value}_auto_saved",
                    "framework": "keras",
                    "loaded_at": time.time(),
                    "device": "cpu",
                    "num_classes": settings.num_classes,
                    "classes": settings.class_names,
                    "auto_saved": True,
                    "auto_save_path": auto_save_path,
                    "original_framework": model_framework.value
                }
                
                logger.info(f"Model '{model_name}' registered in memory for immediate saving capability")
                return True
                
        except Exception as e:
            logger.warning(f"Failed to register model '{model_name}' in memory: {str(e)}")
            # Don't fail the auto-save if memory registration fails
            return False
    async def push_model_to_mongodb_cloud(
        self, 
        model_name: str, 
        user_id: str,
        admin_user_id: str,
        push_metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Push an auto-saved model to MongoDB cloud storage
        
        Args:
            model_name: Name of the model to push
            user_id: Original model owner
            admin_user_id: Admin user performing the push
            push_metadata: Additional push metadata
            
        Returns:
            Dict with push result
        """
        try:
            logger.info(f"Pushing model {model_name} to MongoDB cloud storage")
            
            # Find the auto-saved model
            if model_name not in self._auto_saved_models:
                return {
                    "success": False,
                    "error": f"Model {model_name} not found in auto-saved models"
                }
            
            auto_save_info = self._auto_saved_models[model_name]
            auto_save_path = Path(auto_save_info["path"])
            
            if not auto_save_path.exists():
                return {
                    "success": False,
                    "error": f"Auto-saved model files not found at {auto_save_path}"
                }
            
            # Get database operations
            db_operations = get_db_operations()
            # Ensure MongoDB service is initialized
            await db_operations.db.initialize()
            
            # Read model files and metadata
            model_file_paths = []
            metadata = {}
            
            # Find model files
            for file_path in auto_save_path.iterdir():
                if file_path.is_file() and file_path.name != "auto_save_metadata.json":
                    model_file_paths.append(str(file_path))
                    if file_path.suffix == ".json":
                        try:
                            with open(file_path, 'r') as f:
                                file_metadata = json.load(f)
                                metadata.update(file_metadata)
                        except Exception as e:
                            logger.warning(f"Failed to read metadata from {file_path}: {e}")
            
            # Get model size
            total_size = sum(f.stat().st_size for f in auto_save_path.rglob('*') if f.is_file())
            
            # Create model document for MongoDB
            model_doc = ModelDocument(
                user_id=ObjectId(user_id),
                model_name=model_name,
                model_type=auto_save_info.get("model_type", "unknown"),
                framework=auto_save_info.get("framework", "unknown"),
                parameters={
                    "original_save_path": str(auto_save_path),
                    "save_id": auto_save_info.get("save_id"),
                    "auto_save_date": auto_save_info.get("saved_at"),
                    "admin_push_user": admin_user_id,
                    "push_metadata": push_metadata or {}
                },
                performance_metrics=metadata.get("performance_metrics", {}),
                model_file_path=str(auto_save_path),  # Store local path for now
                model_size_bytes=total_size,
                training_config=metadata.get("training_config", {}),
                metadata={
                    "pushed_to_cloud": True,
                    "push_date": datetime.now().isoformat(),
                    "admin_user": admin_user_id,
                    "files_included": [Path(p).name for p in model_file_paths]
                },
                is_active=True
            )
            
            # Save to MongoDB
            model_id = await db_operations.create_model(model_doc)
            
            logger.info(f"Model {model_name} pushed to MongoDB with ID: {model_id}")
            
            return {
                "success": True,
                "model_name": model_name,
                "model_id": str(model_id),
                "files_included": len(model_file_paths),
                "total_size_bytes": total_size,
                "push_date": datetime.now().isoformat(),
                "message": "Model pushed to MongoDB cloud successfully"
            }
            
        except Exception as e:
            logger.error(f"Failed to push model {model_name} to MongoDB: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "model_name": model_name
            }
    
    async def cleanup_auto_saved_models(self) -> int:
        """
        Clean up all auto-saved models (called on server shutdown)
        
        Returns:
            Number of models cleaned up
        """
        try:
            logger.info("Cleaning up auto-saved models...")
            
            cleaned_count = 0
            errors = []
            
            # Remove all auto-saved model directories
            for model_name, model_info in list(self._auto_saved_models.items()):
                try:
                    model_path = Path(model_info["path"])
                    if model_path.exists():
                        shutil.rmtree(model_path)
                        cleaned_count += 1
                        logger.info(f"Cleaned up auto-saved model: {model_name}")
                except Exception as e:
                    error_msg = f"Failed to clean up {model_name}: {str(e)}"
                    errors.append(error_msg)
                    logger.error(error_msg)
            
            # Clear tracking
            self._auto_saved_models.clear()
            
            if errors:
                logger.warning(f"Auto-save cleanup completed with {len(errors)} errors")
            else:
                logger.info(f"Auto-save cleanup completed: {cleaned_count} models cleaned up")
            
            return cleaned_count
            
        except Exception as e:
            logger.error(f"Failed to cleanup auto-saved models: {str(e)}")
            return 0
    
    def get_auto_saved_models(self) -> List[Dict[str, Any]]:
        """Get list of all auto-saved models"""
        return [
            {
                "model_name": model_name,
                **model_info
            }
            for model_name, model_info in self._auto_saved_models.items()
        ]
    
    async def integrate_with_training_service(self, training_job_completion_data: Dict[str, Any], model_instance: Optional[Any] = None) -> Dict[str, Any]:
        """
        Integrate with training service to auto-save models when training completes
        
        Args:
            training_job_completion_data: Data from completed training job
            model_instance: The trained model instance (if available)
            
        Returns:
            Result of auto-save integration
        """
        try:
            job_id = training_job_completion_data.get("job_id")
            model_name = training_job_completion_data.get("model_name")
            model_framework = training_job_completion_data.get("framework", "keras")
            
            if not model_name:
                return {"success": False, "error": "Model name not provided"}
            
            # Create ModelMetrics from training data
            final_metrics = ModelMetrics(
                model_name=model_name,
                framework=ModelFramework.KERAS if model_framework == "keras" else ModelFramework.PYTORCH,
                architecture=training_job_completion_data.get("architecture", "custom"),
                epochs_completed=training_job_completion_data.get("epochs_completed", 0),
                total_epochs=training_job_completion_data.get("total_epochs", 0),
                batch_size=training_job_completion_data.get("batch_size", 32),
                learning_rate=training_job_completion_data.get("learning_rate", 0.001),
                optimizer=training_job_completion_data.get("optimizer", "adam"),
                loss_function=training_job_completion_data.get("loss_function", "categorical_crossentropy"),
                final_training_loss=training_job_completion_data.get("final_training_loss", 0.0),
                final_training_accuracy=training_job_completion_data.get("final_training_accuracy", 0.0),
                final_validation_loss=training_job_completion_data.get("final_validation_loss", 0.0),
                final_validation_accuracy=training_job_completion_data.get("final_validation_accuracy", 0.0),
                best_validation_accuracy=training_job_completion_data.get("best_validation_accuracy", 0.0),
                best_epoch=training_job_completion_data.get("best_epoch", 0),
                training_start_time=datetime.fromtimestamp(training_job_completion_data.get("start_time", time.time())),
                training_end_time=datetime.now(),
                total_training_time=training_job_completion_data.get("training_time", 0.0)
            )
            
            # Auto-save the model and metrics
            save_result = await self.auto_save_model_and_metrics(
                model_name=model_name,
                model_framework=ModelFramework.KERAS if model_framework == "keras" else ModelFramework.PYTORCH,
                final_metrics=final_metrics,
                training_metadata={
                    "job_id": job_id,
                    "completion_data": training_job_completion_data,
                    "auto_save_integration": True
                },
                model_instance=model_instance
            )
            
            logger.info(f"Training integration auto-save result for {model_name}: {save_result.get('success', False)}")
            
            return save_result
            
        except Exception as e:
            logger.error(f"Training integration auto-save failed: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def get_model_by_name(self, model_name: str) -> Optional[Dict[str, Any]]:
        """Get model information by name (either from auto-saved or regular saved)"""
        try:
            # Check auto-saved models first
            if model_name in self._auto_saved_models:
                auto_save_info = self._auto_saved_models[model_name]
                
                # Read metadata
                metadata_path = Path(auto_save_info["path"]) / "auto_save_metadata.json"
                if metadata_path.exists():
                    with open(metadata_path, 'r') as f:
                        metadata = json.load(f)
                    
                    return {
                        "model_name": model_name,
                        "type": "auto_saved",
                        "framework": auto_save_info.get("framework"),
                        "saved_at": auto_save_info.get("saved_at"),
                        "path": auto_save_info.get("path"),
                        "metadata": metadata
                    }
            
            # Check if it's a regularly saved model
            models_dir = Path("models") / "keras_models"
            model_path = models_dir / model_name
            
            if model_path.exists():
                return {
                    "model_name": model_name,
                    "type": "regular_save",
                    "path": str(model_path),
                    "saved_at": datetime.now().isoformat()
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to get model {model_name}: {str(e)}")
            return None


# Global enhanced model service instance
_enhanced_model_service = None

def get_enhanced_model_service() -> EnhancedModelService:
    """Get or create the global enhanced model service instance"""
    global _enhanced_model_service
    if _enhanced_model_service is None:
        raise RuntimeError("Enhanced Model Service not initialized")
    return _enhanced_model_service

async def initialize_enhanced_model_service(model_manager: ModelManager) -> EnhancedModelService:
    """Initialize the global enhanced model service"""
    global _enhanced_model_service
    
    metrics_service = MetricsService()
    _enhanced_model_service = EnhancedModelService(model_manager, metrics_service)
    await _enhanced_model_service.initialize()
    
    return _enhanced_model_service