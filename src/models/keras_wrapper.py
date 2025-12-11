"""
Keras Model Wrapper for CarthaNeuro
Enables saving and loading models in Keras format for easier deployment
"""

import tensorflow as tf
import numpy as np
import json
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
import time
from datetime import datetime

from src.utils.logger import setup_logger
from src.config.settings import settings

logger = setup_logger(__name__)

class KerasModelWrapper:
    """
    Wrapper for Keras models with save/load functionality
    Works alongside PyTorch models for deployment flexibility
    """
    
    def __init__(self, model: tf.keras.Model, model_name: str, model_type: str):
        self.model = model
        self.model_name = model_name
        self.model_type = model_type
        self.created_at = time.time()
        self.class_names = settings.class_names
        self.num_classes = settings.num_classes
        
        # Compile model for inference (handle different Keras versions)
        try:
            # Check if model is already compiled
            if hasattr(self.model, 'compiled') and self.model.compiled:
                pass  # Already compiled
            elif hasattr(self.model, '_compile') and self.model._compile:
                pass  # Already compiled (older Keras versions)
            else:
                # Compile the model
                self.model.compile(
                    optimizer='adam',
                    loss='categorical_crossentropy',
                    metrics=['accuracy']
                )
        except Exception as e:
            # If compilation fails, try to continue anyway
            logger.warning(f"Model compilation warning for {model_name}: {str(e)}")
        
        logger.info(f"Keras model wrapper created for {model_name}")
    
    def predict(self, input_data, **kwargs) -> Dict[str, Any]:
        """
        Make prediction using the Keras model
        """
        try:
            start_time = time.time()
            
            # Ensure proper shape
            if len(input_data.shape) == 3:  # (height, width, channels)
                input_data = np.expand_dims(input_data, axis=0)  # Add batch dimension
            elif len(input_data.shape) == 4:  # (batch, height, width, channels)
                pass  # Already has batch dimension
            else:
                raise ValueError(f"Unexpected input shape: {input_data.shape}")
            
            # Make prediction
            predictions = self.model.predict(input_data, verbose=0)
            predicted_class = np.argmax(predictions[0])
            confidence = float(predictions[0][predicted_class])
            
            # Get all class probabilities
            class_probabilities = {
                class_name: float(prob) 
                for class_name, prob in zip(self.class_names, predictions[0])
            }
            
            return {
                "prediction": {
                    "class": self.class_names[predicted_class],
                    "class_id": int(predicted_class),
                    "confidence": confidence,
                    "probabilities": class_probabilities
                },
                "model_info": {
                    "model_name": self.model_name,
                    "model_type": self.model_type,
                    "framework": "keras",
                    "inference_time": time.time() - start_time
                },
                "metadata": {
                    "input_shape": list(input_data.shape),
                    "output_shape": list(predictions[0].shape),
                    "created_at": self.created_at
                }
            }
            
        except Exception as e:
            logger.error(f"Keras prediction failed: {str(e)}")
            return self._get_fallback_prediction()
    
    def save_model(self, save_path: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Save model in both .h5 and .keras formats with professional error handling
        
        This method saves the model in two formats:
        - .h5: Legacy format for maximum compatibility
        - .keras: Modern recommended format for TensorFlow 2.13+
        
        Args:
            save_path: Directory path where the model will be saved
            metadata: Additional metadata to include in the save operation
            
        Returns:
            Dict containing success status and save information
        """
        try:
            save_dir = Path(save_path)
            save_dir.mkdir(parents=True, exist_ok=True)
            
            saved_files = []
            save_errors = []
            
            # Professional model saving in both formats
            # Save in .h5 format (legacy format for compatibility)
            try:
                h5_model_path = save_dir / "model.h5"
                self.model.save(str(h5_model_path), save_format='h5')
                saved_files.append("model.h5")
                logger.info(f"Keras model saved in .h5 format to {h5_model_path}")
            except Exception as e:
                error_msg = f"Failed to save .h5 format: {str(e)}"
                save_errors.append(error_msg)
                logger.error(error_msg)
            
            # Save in .keras format (recommended modern format)
            try:
                keras_model_path = save_dir / "model.keras"
                self.model.save(str(keras_model_path), save_format='keras')
                saved_files.append("model.keras")
                logger.info(f"Keras model saved in .keras format to {keras_model_path}")
            except Exception as e:
                error_msg = f"Failed to save .keras format: {str(e)}"
                save_errors.append(error_msg)
                logger.error(error_msg)
            
            # Enhanced metadata for both formats
            metadata_info = {
                "model_name": self.model_name,
                "model_type": self.model_type,
                "framework": "keras",
                "class_names": self.class_names,
                "num_classes": self.num_classes,
                "created_at": self.created_at,
                "saved_at": time.time(),
                "input_shape": list(self.model.input_shape),
                "output_shape": list(self.model.output_shape),
                "total_params": self.model.count_params(),
                "save_formats": saved_files,
                "save_errors": save_errors,
                "professional_save": True,
                "multi_format_support": True,
                "tensorflow_version": tf.__version__,
                "metadata": metadata or {}
            }
            
            # Save comprehensive metadata
            metadata_path = save_dir / "metadata.json"
            with open(metadata_path, 'w') as f:
                json.dump(metadata_info, f, indent=2)
            saved_files.append("metadata.json")
            
            # Save class mapping
            classes_path = save_dir / "classes.txt"
            with open(classes_path, 'w') as f:
                for i, class_name in enumerate(self.class_names):
                    f.write(f"{i},{class_name}\n")
            saved_files.append("classes.txt")
            
            # Create a professional summary file
            summary_path = save_dir / "model_summary.txt"
            with open(summary_path, 'w') as f:
                f.write("CarthaNeuro - Professional Model Save Summary\n")
                f.write("=" * 50 + "\n\n")
                f.write(f"Model Name: {self.model_name}\n")
                f.write(f"Framework: Keras\n")
                f.write(f"Saved At: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Formats Saved: {', '.join(saved_files) if saved_files else 'None'}\n")
                f.write(f"Total Parameters: {metadata_info['total_params']}\n")
                f.write(f"Input Shape: {metadata_info['input_shape']}\n")
                f.write(f"Output Shape: {metadata_info['output_shape']}\n")
                f.write(f"TensorFlow Version: {metadata_info['tensorflow_version']}\n")
                f.write(f"Professional Save: {metadata_info['professional_save']}\n")
                f.write(f"Multi-Format Support: {metadata_info['multi_format_support']}\n")
                f.write(f"\nBoth .h5 and .keras formats available for maximum compatibility\n")
                if save_errors:
                    f.write(f"\nSave Errors:\n")
                    for error in save_errors:
                        f.write(f"  - {error}\n")
            saved_files.append("model_summary.txt")
            
            # Log final status
            if saved_files:
                logger.info(f"Successfully saved {self.model_name} with {len(saved_files)} files: {', '.join(saved_files)}")
            if save_errors:
                logger.warning(f"Model saved with {len(save_errors)} format error(s)")
            
            return {
                "success": len(saved_files) > 0,  # Success if at least one file was saved
                "message": f"Model saved successfully with {len(saved_files)} files",
                "model_path": str(save_dir),
                "files": saved_files,
                "save_errors": save_errors,
                "metadata": metadata_info
            }
            
        except Exception as e:
            logger.error(f"Failed to save Keras model: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "model_path": str(save_dir)
            }
    
    @classmethod
    def load_model(cls, load_path: str) -> 'KerasModelWrapper':
        """
        Load Keras model from path, supporting both .keras and .h5 formats
        
        This method attempts to load the model in the following order:
        1. .keras format (preferred modern format)
        2. .h5 format (legacy format for compatibility)
        
        Args:
            load_path: Directory path where the model is saved
            
        Returns:
            KerasModelWrapper instance with the loaded model
        """
        try:
            load_dir = Path(load_path)
            metadata_path = load_dir / "metadata.json"
            
            # Check for model files in both formats
            keras_model_path = load_dir / "model.keras"
            h5_model_path = load_dir / "model.h5"
            
            model_path = None
            loaded_format = None
            
            # Try .keras format first (preferred)
            if keras_model_path.exists():
                model_path = keras_model_path
                loaded_format = "keras"
                logger.info(f"Loading model from .keras format: {model_path}")
            # Fall back to .h5 format
            elif h5_model_path.exists():
                model_path = h5_model_path
                loaded_format = "h5"
                logger.info(f"Loading model from .h5 format: {model_path}")
            else:
                raise FileNotFoundError(f"No model file found in {load_dir}. Expected 'model.keras' or 'model.h5'")
            
            # Load metadata if available
            metadata_info = {}
            if metadata_path.exists():
                with open(metadata_path, 'r') as f:
                    metadata_info = json.load(f)
            else:
                logger.warning(f"Metadata file not found: {metadata_path}")
            
            # Load Keras model
            model = tf.keras.models.load_model(str(model_path))
            
            # Create wrapper
            wrapper = cls(
                model=model,
                model_name=metadata_info.get("model_name", "loaded_model"),
                model_type=metadata_info.get("model_type", "keras_classifier")
            )
            wrapper.created_at = metadata_info.get("created_at", time.time())
            wrapper.class_names = metadata_info.get("class_names", settings.class_names)
            wrapper.num_classes = metadata_info.get("num_classes", settings.num_classes)
            
            logger.info(f"Keras model loaded from {load_path} using {loaded_format} format")
            return wrapper
            
        except Exception as e:
            logger.error(f"Failed to load Keras model from {load_path}: {str(e)}")
            raise
    
    def _get_fallback_prediction(self) -> Dict[str, Any]:
        """Get fallback prediction when inference fails"""
        return {
            "prediction": {
                "class": "error",
                "class_id": -1,
                "confidence": 0.0,
                "probabilities": {cls: 0.0 for cls in self.class_names}
            },
            "model_info": {
                "model_name": self.model_name,
                "model_type": self.model_type,
                "framework": "keras",
                "error": "Prediction failed"
            },
            "metadata": {
                "fallback": True
            }
        }
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get comprehensive model information"""
        return {
            "model_name": self.model_name,
            "model_type": self.model_type,
            "framework": "keras",
            "created_at": self.created_at,
            "class_names": self.class_names,
            "num_classes": self.num_classes,
            "input_shape": list(self.model.input_shape),
            "output_shape": list(self.model.output_shape),
            "total_params": self.model.count_params(),
            "trainable_params": sum([tf.keras.backend.count_params(w) for w in self.model.trainable_weights]),
            "non_trainable_params": sum([tf.keras.backend.count_params(w) for w in self.model.non_trainable_weights])
        }

def create_keras_model(num_classes: int = 4, model_type: str = "simple_cnn") -> tf.keras.Model:
    """
    Create a Keras model for brain tumor classification
    """
    input_shape = (224, 224, 1)  # (height, width, channels)
    
    if model_type == "simple_cnn":
        # Simple CNN architecture
        model = tf.keras.Sequential([
            tf.keras.layers.Input(shape=input_shape),
            
            # Convolutional layers
            tf.keras.layers.Conv2D(32, (3, 3), activation='relu', padding='same'),
            tf.keras.layers.BatchNormalization(),
            tf.keras.layers.MaxPooling2D((2, 2)),
            tf.keras.layers.Dropout(0.25),
            
            tf.keras.layers.Conv2D(64, (3, 3), activation='relu', padding='same'),
            tf.keras.layers.BatchNormalization(),
            tf.keras.layers.MaxPooling2D((2, 2)),
            tf.keras.layers.Dropout(0.25),
            
            tf.keras.layers.Conv2D(128, (3, 3), activation='relu', padding='same'),
            tf.keras.layers.BatchNormalization(),
            tf.keras.layers.MaxPooling2D((2, 2)),
            tf.keras.layers.Dropout(0.25),
            
            # Global Average Pooling
            tf.keras.layers.GlobalAveragePooling2D(),
            
            # Dense layers
            tf.keras.layers.Dense(512, activation='relu'),
            tf.keras.layers.BatchNormalization(),
            tf.keras.layers.Dropout(0.5),
            
            tf.keras.layers.Dense(256, activation='relu'),
            tf.keras.layers.BatchNormalization(),
            tf.keras.layers.Dropout(0.5),
            
            # Output layer
            tf.keras.layers.Dense(num_classes, activation='softmax')
        ])
        
    elif model_type == "resnet50":
        # ResNet50 architecture
        base_model = tf.keras.applications.ResNet50(
            input_shape=input_shape,
            include_top=False,
            weights=None
        )
        
        model = tf.keras.Sequential([
            base_model,
            tf.keras.layers.GlobalAveragePooling2D(),
            tf.keras.layers.Dense(512, activation='relu'),
            tf.keras.layers.BatchNormalization(),
            tf.keras.layers.Dropout(0.5),
            tf.keras.layers.Dense(num_classes, activation='softmax')
        ])
        
    elif model_type == "efficientnet":
        # EfficientNet architecture
        base_model = tf.keras.applications.EfficientNetB0(
            input_shape=input_shape,
            include_top=False,
            weights=None
        )
        
        model = tf.keras.Sequential([
            base_model,
            tf.keras.layers.GlobalAveragePooling2D(),
            tf.keras.layers.Dense(512, activation='relu'),
            tf.keras.layers.BatchNormalization(),
            tf.keras.layers.Dropout(0.5),
            tf.keras.layers.Dense(num_classes, activation='softmax')
        ])
    
    else:
        raise ValueError(f"Unknown model type: {model_type}")
    
    return model

def list_saved_models(models_dir: Path) -> List[Dict[str, Any]]:
    """
    List all saved Keras models in the models directory, supporting both .keras and .h5 formats
    
    This function scans the models directory and returns information about all saved models,
    including their format, size, and metadata.
    
    Args:
        models_dir: Directory path containing saved models
        
    Returns:
        List of dictionaries containing model information, sorted by save date (newest first)
    """
    models = []
    models_dir.mkdir(parents=True, exist_ok=True)
    
    for model_dir in models_dir.iterdir():
        if model_dir.is_dir():
            metadata_path = model_dir / "metadata.json"
            if metadata_path.exists():
                try:
                    with open(metadata_path, 'r') as f:
                        metadata = json.load(f)
                    
                    # Determine which model format is available and get file size
                    keras_model_file = model_dir / "model.keras"
                    h5_model_file = model_dir / "model.h5"
                    
                    size_mb = 0
                    available_formats = []
                    
                    if keras_model_file.exists():
                        size_mb = keras_model_file.stat().st_size / (1024 * 1024)
                        available_formats.append("keras")
                    if h5_model_file.exists():
                        h5_size = h5_model_file.stat().st_size / (1024 * 1024)
                        size_mb = max(size_mb, h5_size)  # Use the larger file
                        available_formats.append("h5")
                    
                    models.append({
                        "model_name": metadata.get("model_name", model_dir.name),
                        "model_type": metadata.get("model_type", "unknown"),
                        "framework": metadata.get("framework", "keras"),
                        "saved_at": metadata.get("saved_at", 0),
                        "model_path": str(model_dir),
                        "size_mb": round(size_mb, 2),
                        "num_classes": metadata.get("num_classes", 0),
                        "total_params": metadata.get("total_params", 0),
                        "created_at": metadata.get("created_at", 0),
                        "available_formats": available_formats,
                        "save_formats": metadata.get("save_formats", available_formats),
                        "professional_save": metadata.get("professional_save", False),
                        "multi_format_support": metadata.get("multi_format_support", False)
                    })
                    
                except Exception as e:
                    logger.warning(f"Failed to read metadata for {model_dir}: {str(e)}")
    
    return sorted(models, key=lambda x: x.get("saved_at", 0), reverse=True)
