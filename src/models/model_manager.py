"""
Model Manager for CarthaNeuro Backend
Handles loading, caching, and management of all AI models
"""

import tensorflow as tf
import asyncio
from typing import Dict, Any, Optional, List
from pathlib import Path
import pickle
import time
from concurrent.futures import ThreadPoolExecutor

from src.utils.logger import setup_logger
from src.config.settings import settings
from src.models.classifier_3d_cnn import Classifier3DCNN
from src.models.classifier_3d_vit import Classifier3DViT
from src.models.keras_wrapper import KerasModelWrapper, create_keras_model, list_saved_models
from src.models.saved_model_loader import initialize_saved_model_loader, get_saved_model_loader

logger = setup_logger(__name__)

class ModelManager:
    """Manages all AI models in the application"""
    
    def __init__(self):
        self.models: Dict[str, Any] = {}
        self.model_info: Dict[str, Dict[str, Any]] = {}
        self._executor = ThreadPoolExecutor(max_workers=2)
    def __init__(self):
        self.models: Dict[str, Any] = {}
        self.model_info: Dict[str, Dict[str, Any]] = {}
        self._executor = ThreadPoolExecutor(max_workers=2)
        self._initialized = False
        self._loading = False
        self.saved_model_loader = None
        self._initialized = False
        self._loading = False
        
    async def initialize(self):
        """Initialize the model manager"""
        if self._initialized or self._loading:
            return
            
        self._loading = True
        logger.info("Initializing ModelManager...")
        
        try:
            # Create model directories
            for model_type in ["3d_cnn", "3d_vit"]:
                (settings.models_dir / model_type).mkdir(parents=True, exist_ok=True)
            
            # Create Keras models directory
            (settings.models_dir / "keras_models").mkdir(parents=True, exist_ok=True)
            
            # Initialize saved model loader
            self.saved_model_loader = await initialize_saved_model_loader()
            logger.info("Saved model loader initialized successfully")
                
            self._initialized = True
            logger.info("ModelManager initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize ModelManager: {str(e)}")
            raise
        finally:
            self._loading = False
            
    async def load_models(self, model_types: Optional[List[str]] = None):
        """
        Load all required models
        
        Args:
            model_types: List of model types to load. If None, loads all models
        """
        if not self._initialized:
            await self.initialize()
            
        if model_types is None:
            model_types = ["3d_cnn", "3d_vit"]
            
        logger.info(f"Loading models: {model_types}")
        
        # Load models concurrently for better performance
        tasks = []
        for model_type in model_types:
            if model_type == "3d_cnn":
                tasks.append(self._load_3d_cnn())
            elif model_type == "3d_vit":
                tasks.append(self._load_3d_vit())
                
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
            
        logger.info(f"Successfully loaded models: {list(self.models.keys())}")
        
    async def _load_3d_cnn(self):
        """Load 3D CNN classifier model"""
        try:
            logger.info("Loading 3D CNN classifier model...")
            start_time = time.time()
            
            loop = asyncio.get_event_loop()
            model = await loop.run_in_executor(
                self._executor,
                self._create_3d_cnn
            )
            
            self.models["3d_cnn"] = model
            self.model_info["3d_cnn"] = {
                "name": "3D ResNet Classifier",
                "type": "3d_cnn",
                "loaded_at": time.time(),
                "load_time": time.time() - start_time,
                "device": str(next(model.parameters()).device) if hasattr(model, 'parameters') else "cpu",
                "num_classes": settings.num_classes,
                "classes": settings.class_names
            }
            
            logger.info(f"3D CNN loaded in {time.time() - start_time:.2f}s")
            
        except Exception as e:
            logger.error(f"Failed to load 3D CNN: {str(e)}")
            self.models["3d_cnn"] = None
            
    def _create_3d_cnn(self) -> Classifier3DCNN:
        """Create 3D CNN instance (runs in thread pool)"""
        return Classifier3DCNN(
            num_classes=settings.num_classes,
            model_type="resnet",  # or "densenet"
            device=settings.device,
            pretrained=True
        )
        
    async def _load_3d_vit(self):
        """Load 3D Vision Transformer model"""
        try:
            logger.info("Loading 3D Vision Transformer model...")
            start_time = time.time()
            
            loop = asyncio.get_event_loop()
            model = await loop.run_in_executor(
                self._executor,
                self._create_3d_vit
            )
            
            self.models["3d_vit"] = model
            self.model_info["3d_vit"] = {
                "name": "3D Vision Transformer",
                "type": "3d_vit",
                "loaded_at": time.time(),
                "load_time": time.time() - start_time,
                "device": str(next(model.parameters()).device) if hasattr(model, 'parameters') else "cpu",
                "num_classes": settings.num_classes,
                "classes": settings.class_names
            }
            
            logger.info(f"3D Vision Transformer loaded in {time.time() - start_time:.2f}s")
            
        except Exception as e:
            logger.error(f"Failed to load 3D Vision Transformer: {str(e)}")
            self.models["3d_vit"] = None
            
    def _create_3d_vit(self) -> Classifier3DViT:
        """Create 3D ViT instance (runs in thread pool)"""
        return Classifier3DViT(
            num_classes=settings.num_classes,
            device=settings.device,
            pretrained=True
        )
        
    def is_ready(self) -> bool:
        """Check if models are ready for inference"""
        return self._initialized and len(self.models) > 0
        
    def get_loaded_models(self) -> List[str]:
        """Get list of loaded model names"""
        return [name for name, model in self.models.items() if model is not None]
        
    def get_model(self, model_name: str) -> Optional[Any]:
        """Get a specific model by name"""
        return self.models.get(model_name)
        
    def get_model_info(self, model_name: str) -> Optional[Dict[str, Any]]:
        """Get information about a specific model"""
        return self.model_info.get(model_name)
    
    async def create_keras_model_wrapper(
        self, 
        model_name: str, 
        model_type: str = "simple_cnn",
        overwrite: bool = False
    ) -> KerasModelWrapper:
        """
        Create and register a new Keras model wrapper
        
        Args:
            model_name: Name for the new model
            model_type: Type of Keras model to create
            overwrite: Whether to overwrite existing model
        """
        try:
            # Check if model already exists
            if model_name in self.models and not overwrite:
                raise ValueError(f"Model {model_name} already exists. Use overwrite=True to replace it.")
            
            # Create Keras model
            keras_model = create_keras_model(
                num_classes=settings.num_classes,
                model_type=model_type
            )
            
            # Create wrapper
            wrapper = KerasModelWrapper(
                model=keras_model,
                model_name=model_name,
                model_type=f"keras_{model_type}"
            )
            
            # Register the model
            self.models[model_name] = wrapper
            self.model_info[model_name] = {
                "name": model_name,
                "type": f"keras_{model_type}",
                "framework": "keras",
                "loaded_at": time.time(),
                "device": "cpu",  # Keras runs on CPU/GPU automatically
                "num_classes": settings.num_classes,
                "classes": settings.class_names
            }
            
            logger.info(f"Keras model wrapper created for {model_name}")
            return wrapper
            
        except Exception as e:
            logger.error(f"Failed to create Keras model wrapper: {str(e)}")
            raise
    
    async def train_and_save_keras_model(
        self,
        model_name: str,
        train_data: Any,
        val_data: Any,
        epochs: int = 10,
        batch_size: int = 32,
        save_path: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Train a Keras model and save it
        
        Args:
            model_name: Name for the model
            train_data: Training data
            val_data: Validation data
            epochs: Number of training epochs
            batch_size: Training batch size
            save_path: Path to save the model (optional)
            **kwargs: Additional training parameters
        """
        try:
            # Get or create model wrapper
            wrapper = None
            if model_name in self.models:
                wrapper = self.models[model_name]
            else:
                wrapper = await self.create_keras_model_wrapper(model_name)
            
            # Prepare save path
            if save_path is None:
                save_path = str(settings.models_dir / "keras_models" / model_name)
            
            logger.info(f"Starting training for Keras model: {model_name}")
            
            # Train the model
            history = wrapper.model.fit(
                train_data,
                validation_data=val_data,
                epochs=epochs,
                batch_size=batch_size,
                verbose=1,
                **kwargs
            )
            
            # Save the trained model
            save_result = wrapper.save_model(save_path, {
                "training_history": history.history,
                "epochs": epochs,
                "batch_size": batch_size,
                "training_timestamp": time.time()
            })
            
            logger.info(f"Training completed for {model_name}")
            
            return {
                "success": True,
                "model_name": model_name,
                "save_result": save_result,
                "training_history": history.history,
                "final_loss": float(history.history['loss'][-1]) if history.history['loss'] else None,
                "final_accuracy": float(history.history['accuracy'][-1]) if history.history['accuracy'] else None
            }
            
        except Exception as e:
            logger.error(f"Training and saving failed for {model_name}: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def save_keras_model(self, model_name: str, save_path: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Save a Keras model
        
        Args:
            model_name: Name of the model to save
            save_path: Path to save the model
            metadata: Additional metadata to save
        """
        try:
            # Check if model exists in memory
            if model_name not in self.models:
                return {
                    "success": False,
                    "error": f"Model '{model_name}' not found in memory. Models must be trained and loaded before saving.",
                    "suggestion": "Train a new model first or load an existing model from disk."
                }
            
            wrapper = self.models[model_name]
            if not isinstance(wrapper, KerasModelWrapper):
                return {
                    "success": False,
                    "error": f"Model '{model_name}' is not a Keras model",
                    "suggestion": "Only Keras models can be saved using this endpoint."
                }
            
            result = wrapper.save_model(save_path, metadata)
            logger.info(f"Keras model {model_name} saved to {save_path}")
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to save Keras model {model_name}: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "suggestion": "Ensure the model is properly trained and loaded before saving."
            }
    
    def list_keras_models(self) -> List[Dict[str, Any]]:
        """
        List all saved Keras models
        """
        try:
            models_dir = settings.models_dir / "keras_models"
            return list_saved_models(models_dir)
        except Exception as e:
            logger.error(f"Failed to list Keras models: {str(e)}")
            return []
    
    async def load_keras_model(self, model_path: str) -> KerasModelWrapper:
        """
        Load a Keras model from saved path
        
        Args:
            model_path: Path to the saved model directory
        """
        try:
            wrapper = KerasModelWrapper.load_model(model_path)
            
            # Register the loaded model
            self.models[wrapper.model_name] = wrapper
            self.model_info[wrapper.model_name] = {
                "name": wrapper.model_name,
                "type": wrapper.model_type,
                "framework": "keras",
                "loaded_at": time.time(),
                "device": "cpu",
                "num_classes": wrapper.num_classes,
                "classes": wrapper.class_names
            }
            
            logger.info(f"Keras model {wrapper.model_name} loaded from {model_path}")
            return wrapper
            
        except Exception as e:
            logger.error(f"Failed to load Keras model from {model_path}: {str(e)}")
            raise
    
    async def predict_with_keras(self, model_name: str, input_data: Any) -> Dict[str, Any]:
        """
        Make prediction with a Keras model
        
        Args:
            model_name: Name of the Keras model
            input_data: Input data for prediction
        """
        try:
            if model_name not in self.models:
                raise ValueError(f"Keras model {model_name} not found")
            
            wrapper = self.models[model_name]
            if not isinstance(wrapper, KerasModelWrapper):
                raise ValueError(f"Model {model_name} is not a Keras model")
            
            # Run prediction in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(
                self._executor,
                lambda: wrapper.predict(input_data)
            )
            
        except Exception as e:
            logger.error(f"Keras prediction failed for {model_name}: {str(e)}")
            raise
        
    async def predict(self, model_name: str, *args, **kwargs):
        """Make prediction with a specific model"""
        model = self.get_model(model_name)
        if model is None:
            raise ValueError(f"Model {model_name} not available")
            
        # Run inference in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self._executor,
            lambda: model.predict(*args, **kwargs)
        )
    
    async def predict_with_saved_model(self, image_input, patient_context: Optional[str] = None, model_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Make prediction using saved models
        
        Args:
            image_input: Input image
            patient_context: Optional patient context
            model_name: Specific model name to use (optional)
            
        Returns:
            Prediction results from saved model
        """
        try:
            if self.saved_model_loader is None:
                return {
                    "success": False,
                    "error": "Saved model loader not initialized"
                }
            
            if model_name:
                return await self.saved_model_loader.predict_with_saved_model(model_name, image_input, patient_context)
            else:
                return await self.saved_model_loader.predict_with_best_model(image_input, patient_context)
                
        except Exception as e:
            logger.error(f"Saved model prediction failed: {str(e)}")
            return {
                "success": False,
                "error": f"Prediction failed: {str(e)}"
            }
    
    def get_saved_models_info(self) -> Dict[str, Dict[str, Any]]:
        """Get information about all loaded saved models"""
        if self.saved_model_loader:
            return self.saved_model_loader.get_loaded_models_info()
        return {}
    
    def get_available_saved_models(self) -> List[str]:
        """Get list of available saved models"""
        if self.saved_model_loader:
            return self.saved_model_loader.get_available_saved_models()
        return []
    
    async def reload_saved_models(self) -> Dict[str, Dict[str, Any]]:
        """
        Reload all saved models
        
        Returns:
            Dict with reload results
        """
        try:
            if self.saved_model_loader is None:
                return {"success": False, "error": "Saved model loader not initialized"}
            
            # Clean up existing models
            await self.saved_model_loader.cleanup()
            
            # Reinitialize and load models
            self.saved_model_loader = await initialize_saved_model_loader()
            
            results = await self.saved_model_loader.load_saved_keras_models()
            
            return {
                "success": True,
                "results": results,
                "loaded_models": self.get_available_saved_models()
            }
            
        except Exception as e:
            logger.error(f"Failed to reload saved models: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    async def predict(self, model_name: str, *args, **kwargs):
        """Make prediction with a specific model"""
        model = self.get_model(model_name)
        if model is None:
            raise ValueError(f"Model {model_name} not available")
            
        # Run inference in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self._executor,
            lambda: model.predict(*args, **kwargs)
        )
        
    async def cleanup(self):
        """Cleanup resources"""
        logger.info("Cleaning up ModelManager...")
        
        # Clear models from memory
        for model_name, model in self.models.items():
            if model is not None and hasattr(model, 'cleanup'):
                try:
                    await asyncio.get_event_loop().run_in_executor(
                        self._executor,
                        model.cleanup
                    )
                except Exception as e:
                    logger.warning(f"Error cleaning up model {model_name}: {str(e)}")
                    
        self.models.clear()
        self.model_info.clear()
        
        # Cleanup saved model loader
        if self.saved_model_loader:
            await self.saved_model_loader.cleanup()
        
        # Shutdown executor
        self._executor.shutdown(wait=True)
        
        logger.info("ModelManager cleanup completed")