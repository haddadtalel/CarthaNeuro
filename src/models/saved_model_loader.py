"""
Saved Model Loader for CarthaNeuro Backend
Handles loading and prediction with auto-saved models
"""

import json
import asyncio
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime

from src.utils.logger import setup_logger
from src.config.settings import settings
from src.models.keras_wrapper import KerasModelWrapper

logger = setup_logger(__name__)

class SavedModelLoader:
    """Handles loading and prediction with saved Keras models"""
    
    def __init__(self):
        self.loaded_models: Dict[str, KerasModelWrapper] = {}
        self.model_metadata: Dict[str, Dict[str, Any]] = {}
        self.auto_save_dir = Path("auto_saved_models")
        self.keras_models_dir = Path("models/keras_models")
        
    async def load_saved_keras_models(self) -> Dict[str, Dict[str, Any]]:
        """
        Load all available Keras models from both auto_saved_models and keras_models directories
        
        Returns:
            Dict with model loading results
        """
        results = {}
        loaded_count = 0
        
        try:
            # Load from auto_saved_models directory first
            if self.auto_save_dir.exists():
                logger.info("Loading models from auto_saved_models directory...")
                for model_dir in self.auto_save_dir.iterdir():
                    if model_dir.is_dir():
                        model_name = model_dir.name
                        logger.info(f"Loading auto-saved Keras model: {model_name}")
                        
                        try:
                            result = await self._load_model_from_directory(model_dir)
                            results[model_name] = result
                            if result.get("success"):
                                loaded_count += 1
                                logger.info(f"✅ Successfully loaded auto-saved model: {model_name}")
                            else:
                                logger.warning(f"❌ Failed to load auto-saved model {model_name}: {result.get('error')}")
                        except Exception as e:
                            error_msg = f"Exception loading auto-saved model {model_name}: {e}"
                            logger.error(error_msg)
                            results[model_name] = {"success": False, "error": error_msg}
            else:
                logger.warning("Auto-saved models directory not found")
                
            # Also load from keras_models directory (for static models like 'real')
            if self.keras_models_dir.exists():
                logger.info("Loading models from keras_models directory...")
                keras_models_found = 0
                
                for model_dir in self.keras_models_dir.iterdir():
                    if model_dir.is_dir():
                        # Check for model files
                        has_keras_model = (model_dir / "model.keras").exists()
                        has_h5_model = (model_dir / "model.h5").exists()
                        has_any_model = has_keras_model or has_h5_model
                        
                        if has_any_model:
                            model_name = model_dir.name
                            keras_models_found += 1
                            logger.info(f"Loading static Keras model: {model_name} (keras: {has_keras_model}, h5: {has_h5_model})")
                            
                            try:
                                result = await self._load_keras_model_from_directory(model_dir)
                                results[model_name] = result
                                if result.get("success"):
                                    loaded_count += 1
                                    logger.info(f"✅ Successfully loaded static model: {model_name}")
                                else:
                                    logger.warning(f"❌ Failed to load static model {model_name}: {result.get('error')}")
                            except Exception as e:
                                error_msg = f"Exception loading static model {model_name}: {e}"
                                logger.error(error_msg)
                                results[model_name] = {"success": False, "error": error_msg}
                        else:
                            logger.debug(f"Skipping directory {model_dir.name} - no model files found")
                
                if keras_models_found == 0:
                    logger.warning("No model files found in keras_models directory")
            else:
                logger.warning("Keras models directory not found")
                    
            logger.info(f"Model loading completed: {loaded_count} models loaded successfully out of {len(results)} attempted")
            if loaded_count > 0:
                logger.info(f"Loaded models: {list(self.loaded_models.keys())}")
            else:
                logger.warning("No models were successfully loaded!")
                
            return results
            
        except Exception as e:
            logger.error(f"Failed to load saved Keras models: {str(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return results
    
    async def _load_model_from_directory(self, model_dir: Path) -> Dict[str, Any]:
        """
        Load a Keras model from its saved directory
        
        Args:
            model_dir: Path to the model directory
            
        Returns:
            Dict with loading result information
        """
        try:
            # Read metadata
            metadata_file = model_dir / "auto_save_metadata.json"
            
            if not metadata_file.exists():
                return {
                    "success": False,
                    "error": "Metadata file not found",
                    "model_path": str(model_dir)
                }
                
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)
                
            # Check if this is a Keras model
            if metadata.get("framework") != "keras":
                return {
                    "success": False,
                    "error": f"Unsupported framework: {metadata.get('framework')}. Expected keras.",
                    "model_path": str(model_dir)
                }
                
            # Get training metadata
            training_metadata = metadata.get("training_metadata", {}).get("completion_data", {})
            
            # Look for Keras model files (.h5)
            model_files = list(model_dir.glob("*.h5")) + list(model_dir.glob("*.keras"))
            
            if not model_files:
                # Check if there's a saved model in the directory with different patterns
                model_files = []
                for pattern in ["model.h5", "model.keras", "trained_model.h5", "trained_model.keras"]:
                    found_files = list(model_dir.glob(pattern))
                    model_files.extend(found_files)
                    
            if model_files:
                # Load the Keras model
                model_file = model_files[0]  # Take the first found model file
                logger.info(f"Loading Keras model from: {model_file}")
                
                # Load the Keras model
                import tensorflow as tf
                keras_model = tf.keras.models.load_model(str(model_file))
                
                # Create a wrapper for the loaded model
                wrapper = KerasModelWrapper(
                    model=keras_model,
                    model_name=model_dir.name,
                    model_type=f"keras_{training_metadata.get('architecture', 'custom')}"
                )
                
            else:
                return {
                    "success": False,
                    "error": "No Keras model files (.h5 or .keras) found in directory",
                    "model_path": str(model_dir),
                    "files_found": [f.name for f in model_dir.iterdir() if f.is_file()]
                }
                
            # Store the loaded model
            model_name = model_dir.name
            self.loaded_models[model_name] = wrapper
            self.model_metadata[model_name] = {
                "model_path": str(model_dir),
                "metadata": metadata,
                "training_config": training_metadata,
                "loaded_at": datetime.now().isoformat(),
                "device": "cpu"  # Keras handles device automatically
            }
            
            logger.info(f"Successfully loaded Keras model: {model_name}")
            return {
                "success": True,
                "model_name": model_name,
                "model_path": str(model_dir),
                "framework": metadata.get("framework"),
                "architecture": training_metadata.get("architecture", "custom"),
                "validation_accuracy": training_metadata.get("final_validation_accuracy", 0.0),
                "training_epochs": training_metadata.get("epochs_completed", 0),
                "loaded_at": self.model_metadata[model_name]["loaded_at"],
                "files_found": [f.name for f in model_dir.iterdir() if f.is_file()]
            }
            
        except Exception as e:
            logger.error(f"Failed to load Keras model from {model_dir}: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "model_path": str(model_dir)
            }
    
    async def _load_keras_model_from_directory(self, model_dir: Path) -> Dict[str, Any]:
        """
        Load a Keras model from the keras_models directory format
        
        Args:
            model_dir: Path to the model directory
            
        Returns:
            Dict with loading result information
        """
        try:
            # Look for model files with enhanced detection
            keras_model_file = model_dir / "model.keras"
            h5_model_file = model_dir / "model.h5"
            
            model_file = None
            model_format = None
            
            # Prefer .keras format, fallback to .h5
            if keras_model_file.exists():
                model_file = keras_model_file
                model_format = "keras"
                logger.info(f"Found .keras model file: {model_file}")
            elif h5_model_file.exists():
                model_file = h5_model_file
                model_format = "h5"
                logger.info(f"Found .h5 model file: {model_file}")
            else:
                # Check for any model files in the directory
                model_files = list(model_dir.glob("*.keras")) + list(model_dir.glob("*.h5"))
                if model_files:
                    model_file = model_files[0]  # Take the first found model
                    model_format = "keras" if model_file.suffix == ".keras" else "h5"
                    logger.info(f"Found model file: {model_file}")
                else:
                    return {
                        "success": False,
                        "error": "No Keras model files (.keras or .h5) found",
                        "model_path": str(model_dir),
                        "files_in_dir": [f.name for f in model_dir.iterdir() if f.is_file()]
                    }
                    
            # Load metadata if available
            metadata_file = model_dir / "metadata.json"
            metadata = {}
            if metadata_file.exists():
                with open(metadata_file, 'r') as f:
                    metadata = json.load(f)
                logger.info(f"Loaded metadata for {model_dir.name}: {metadata.get('model_type', 'unknown')}")
            else:
                logger.warning(f"No metadata.json found for {model_dir.name}")
                    
            # Load the Keras model with enhanced error handling
            try:
                import tensorflow as tf
                logger.info(f"Loading Keras model from: {model_file}")
                
                # Try loading with custom objects if needed
                keras_model = tf.keras.models.load_model(
                    str(model_file),
                    compile=False  # Don't compile to avoid optimizer issues
                )
                
                logger.info(f"Successfully loaded {model_format} model")
                
            except Exception as tf_error:
                logger.error(f"TensorFlow loading failed: {tf_error}")
                # Try alternative loading methods
                try:
                    # Try loading as SavedModel format
                    keras_model = tf.keras.models.load_model(str(model_file))
                    logger.info("Successfully loaded with alternative method")
                except Exception as alt_error:
                    logger.error(f"Alternative loading also failed: {alt_error}")
                    return {
                        "success": False,
                        "error": f"Failed to load model with both methods. Primary: {tf_error}, Alternative: {alt_error}",
                        "model_path": str(model_file),
                        "model_format": model_format
                    }
            
            # Create a wrapper for the loaded model with enhanced info
            wrapper = KerasModelWrapper(
                model=keras_model,
                model_name=model_dir.name,
                model_type=metadata.get("model_type", "keras_classifier")
            )
            
            # Store the loaded model
            model_name = model_dir.name
            self.loaded_models[model_name] = wrapper
            self.model_metadata[model_name] = {
                "model_path": str(model_dir),
                "model_file": str(model_file),
                "model_format": model_format,
                "metadata": metadata,
                "training_config": metadata.get("training_config", {}),
                "class_names": metadata.get("class_names", []),
                "num_classes": metadata.get("num_classes", 0),
                "loaded_at": datetime.now().isoformat(),
                "device": "cpu",  # Keras handles device automatically
                "source": "keras_models_directory",
                "model_info": {
                    "input_shape": getattr(keras_model, 'input_shape', None),
                    "output_shape": getattr(keras_model, 'output_shape', None),
                    "name": getattr(keras_model, 'name', model_name)
                }
            }
            
            logger.info(f"Successfully loaded and registered Keras model: {model_name}")
            return {
                "success": True,
                "model_name": model_name,
                "model_path": str(model_dir),
                "model_file": str(model_file),
                "model_format": model_format,
                "framework": metadata.get("framework", "keras"),
                "model_type": metadata.get("model_type", "custom"),
                "class_names": metadata.get("class_names", []),
                "num_classes": metadata.get("num_classes", 0),
                "loaded_at": self.model_metadata[model_name]["loaded_at"],
                "source": "keras_models_directory"
            }
            
        except Exception as e:
            logger.error(f"Failed to load Keras model from {model_dir}: {str(e)}")
            import traceback
            logger.error(f"Traceback: {traceback.format_exc()}")
            return {
                "success": False,
                "error": str(e),
                "model_path": str(model_dir),
                "traceback": traceback.format_exc()
            }
    
    async def predict_with_saved_model(
        self,
        model_name: str,
        image_input,
        patient_context: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Make prediction using a loaded saved Keras model
        
        Args:
            model_name: Name of the saved model
            image_input: Input image (PIL Image, numpy array, or path)
            patient_context: Optional patient context (ignored for Keras models)
            
        Returns:
            Prediction results
        """
        try:
            # Get the loaded model
            wrapper = self.loaded_models.get(model_name)
            if wrapper is None:
                return {
                    "success": False,
                    "error": f"Model {model_name} not loaded. Available models: {list(self.loaded_models.keys())}",
                    "available_models": list(self.loaded_models.keys())
                }
                
            # Get model metadata
            metadata = self.model_metadata.get(model_name, {})
            
            # Make prediction
            import time
            start_time = time.time()
            
            # Preprocess image input for Keras model
            if hasattr(image_input, 'convert'):  # PIL Image
                import numpy as np
                from PIL import Image
                
                # Convert to grayscale if RGB to match model's expected input shape
                if image_input.mode == 'RGB':
                    image_input = image_input.convert('L')  # Convert to grayscale
                
                # Convert PIL image to numpy array and resize
                img_array = np.array(image_input.resize((224, 224)))
                img_array = img_array.astype(np.float32) / 255.0  # Normalize
                
                # Ensure 1 channel for grayscale images
                if len(img_array.shape) == 2:  # (height, width)
                    img_array = np.expand_dims(img_array, axis=-1)  # Add channel dimension -> (height, width, 1)
                elif len(img_array.shape) == 3:
                    # If still 3D, ensure it's 1 channel
                    if img_array.shape[-1] == 3 and img_array.ndim == 3:  # RGB
                        img_array = np.expand_dims(img_array[:, :, 0], axis=-1)  # Take first channel
                    elif img_array.shape[-1] == 1:  # Already grayscale with channel dim
                        pass
                    else:
                        # Unexpected format, take first channel
                        img_array = img_array[:, :, 0]
                        img_array = np.expand_dims(img_array, axis=-1)
                
                if len(img_array.shape) == 3:
                    img_array = np.expand_dims(img_array, axis=0)  # Add batch dimension
                
                image_input = img_array
            
            # Use the wrapper's predict method
            result = wrapper.predict(image_input)
            
            # Add saved model specific metadata
            result["model_source"] = "saved_model"
            result["saved_model_info"] = {
                "model_name": model_name,
                "training_config": metadata.get("training_config", {}),
                "loaded_at": metadata.get("loaded_at"),
                "original_save_path": metadata.get("model_path")
            }
            
            processing_time = time.time() - start_time
            if "model_info" in result:
                result["model_info"]["inference_time"] = processing_time
                result["model_info"]["total_processing_time"] = processing_time
            else:
                result["model_info"] = {
                    "inference_time": processing_time,
                    "total_processing_time": processing_time
                }
            
            logger.info(f"Saved Keras model prediction completed for {model_name} in {processing_time:.3f}s")
            return result
            
        except Exception as e:
            logger.error(f"Prediction failed with saved Keras model {model_name}: {str(e)}")
            return {
                "success": False,
                "error": f"Prediction failed: {str(e)}",
                "model_name": model_name
            }
    
    def get_loaded_models_info(self) -> Dict[str, Dict[str, Any]]:
        """Get information about all loaded saved models"""
        return {
            name: {
                "model_name": name,
                "loaded_at": info.get("loaded_at"),
                "training_config": info.get("training_config", {}),
                "model_path": info.get("model_path"),
                "framework": info.get("metadata", {}).get("framework"),
                "architecture": info.get("training_config", {}).get("architecture")
            }
            for name, info in self.model_metadata.items()
        }
    
    def get_available_saved_models(self) -> List[str]:
        """Get list of available saved models"""
        return list(self.loaded_models.keys())
    
    async def predict_with_best_model(
        self, 
        image_input, 
        patient_context: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Predict using the best available saved model (highest validation accuracy)
        
        Args:
            image_input: Input image
            patient_context: Optional patient context
            
        Returns:
            Prediction results from the best model
        """
        if not self.loaded_models:
            return {
                "success": False,
                "error": "No saved models available for prediction"
            }
            
        # Find the model with highest validation accuracy
        best_model_name = None
        best_accuracy = -1
        
        for model_name, metadata in self.model_metadata.items():
            training_config = metadata.get("training_config", {})
            accuracy = training_config.get("final_validation_accuracy", 0.0)
            
            if accuracy > best_accuracy:
                best_accuracy = accuracy
                best_model_name = model_name
                
        if best_model_name:
            logger.info(f"Using best saved model: {best_model_name} (validation accuracy: {best_accuracy:.3f})")
            return await self.predict_with_saved_model(best_model_name, image_input, patient_context)
        else:
            # Fallback to any available model
            fallback_model = list(self.loaded_models.keys())[0]
            logger.info(f"Using fallback saved model: {fallback_model}")
            return await self.predict_with_saved_model(fallback_model, image_input, patient_context)
    
    def unload_model(self, model_name: str) -> bool:
        """
        Unload a specific saved model to free memory
        
        Args:
            model_name: Name of the model to unload
            
        Returns:
            True if successfully unloaded
        """
        try:
            if model_name in self.loaded_models:
                del self.loaded_models[model_name]
                del self.model_metadata[model_name]
                logger.info(f"Unloaded saved model: {model_name}")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to unload model {model_name}: {str(e)}")
            return False
    
    async def cleanup(self):
        """Cleanup all loaded models"""
        logger.info("Cleaning up saved model loader...")
        self.loaded_models.clear()
        self.model_metadata.clear()
        logger.info("Saved model loader cleanup completed")


# Global saved model loader instance
_saved_model_loader = None

def get_saved_model_loader() -> SavedModelLoader:
    """Get or create the global saved model loader instance"""
    global _saved_model_loader
    if _saved_model_loader is None:
        _saved_model_loader = SavedModelLoader()
    return _saved_model_loader

async def initialize_saved_model_loader() -> SavedModelLoader:
    """Initialize the global saved model loader"""
    global _saved_model_loader
    _saved_model_loader = SavedModelLoader()
    
    # Load all available saved Keras models
    await _saved_model_loader.load_saved_keras_models()
    
    return _saved_model_loader