#!/usr/bin/env python3
"""
Test script for saved model loading and prediction functionality
"""

import asyncio
import sys
import os
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from models.saved_model_loader import initialize_saved_model_loader, get_saved_model_loader
from models.classifier_3d_cnn import Classifier3DCNN
from config.settings import settings
from PIL import Image
import numpy as np

async def test_saved_model_loading():
    """Test loading saved models"""
    print("🔄 Testing saved model loading...")
    
    try:
        # Initialize saved model loader
        loader = await initialize_saved_model_loader()
        
        # Load saved models
        results = await loader.load_saved_3d_cnn_models()
        
        print(f"✅ Loaded {len(results)} saved models")
        for model_name, result in results.items():
            if result.get("success"):
                print(f"  📁 {model_name}: {result.get('architecture', 'unknown')} architecture, "
                      f"validation accuracy: {result.get('validation_accuracy', 0):.3f}")
            else:
                print(f"  ❌ {model_name}: {result.get('error', 'Unknown error')}")
        
        return results
        
    except Exception as e:
        print(f"❌ Error loading saved models: {e}")
        return {}

async def test_saved_model_prediction():
    """Test prediction with saved models"""
    print("\n🔄 Testing saved model prediction...")
    
    try:
        loader = get_saved_model_loader()
        
        # Create a dummy image for testing
        dummy_image = np.random.rand(224, 224, 3).astype(np.float32)
        dummy_pil_image = Image.fromarray((dummy_image * 255).astype(np.uint8))
        
        # Get available models
        available_models = loader.get_available_saved_models()
        
        if not available_models:
            print("❌ No saved models available for prediction")
            return
        
        print(f"📋 Available models: {available_models}")
        
        # Test prediction with best model
        print(f"\n🎯 Testing prediction with best model...")
        result = await loader.predict_with_best_model(
            image_input=dummy_pil_image,
            patient_context="Test patient context"
        )
        
        if result.get("success"):
            prediction = result.get("prediction", {})
            print(f"✅ Prediction successful:")
            print(f"  🎯 Predicted class: {prediction.get('class', 'unknown')}")
            print(f"  📊 Confidence: {prediction.get('confidence', 0):.3f}")
            print(f"  📈 Model source: {result.get('model_source', 'unknown')}")
            
            saved_info = result.get("saved_model_info", {})
            if saved_info:
                print(f"  🏆 Training accuracy: {saved_info.get('training_config', {}).get('final_validation_accuracy', 'N/A')}")
        else:
            print(f"❌ Prediction failed: {result.get('error', 'Unknown error')}")
        
        return result
        
    except Exception as e:
        print(f"❌ Error testing prediction: {e}")
        return {}

async def test_specific_model_prediction():
    """Test prediction with a specific saved model"""
    print("\n🔄 Testing prediction with specific saved model...")
    
    try:
        loader = get_saved_model_loader()
        available_models = loader.get_available_saved_models()
        
        if not available_models:
            print("❌ No saved models available")
            return
        
        # Use the first available model
        model_name = available_models[0]
        
        # Create a dummy image for testing
        dummy_image = np.random.rand(224, 224, 3).astype(np.float32)
        dummy_pil_image = Image.fromarray((dummy_image * 255).astype(np.uint8))
        
        print(f"🎯 Testing prediction with model: {model_name}")
        
        result = await loader.predict_with_saved_model(
            model_name=model_name,
            image_input=dummy_pil_image,
            patient_context="Test patient context for specific model"
        )
        
        if result.get("success"):
            prediction = result.get("prediction", {})
            print(f"✅ Prediction successful with {model_name}:")
            print(f"  🎯 Predicted class: {prediction.get('class', 'unknown')}")
            print(f"  📊 Confidence: {prediction.get('confidence', 0):.3f}")
        else:
            print(f"❌ Prediction failed with {model_name}: {result.get('error', 'Unknown error')}")
        
        return result
        
    except Exception as e:
        print(f"❌ Error testing specific model prediction: {e}")
        return {}

def test_model_metadata():
    """Test getting model metadata"""
    print("\n🔄 Testing model metadata retrieval...")
    
    try:
        loader = get_saved_model_loader()
        
        # Get loaded models info
        models_info = loader.get_loaded_models_info()
        
        print(f"📋 Loaded models info:")
        for model_name, info in models_info.items():
            print(f"  📁 {model_name}:")
            print(f"    • Framework: {info.get('framework', 'unknown')}")
            print(f"    • Architecture: {info.get('architecture', 'unknown')}")
            print(f"    • Loaded at: {info.get('loaded_at', 'unknown')}")
            print(f"    • Model path: {info.get('model_path', 'unknown')}")
            
            training_config = info.get('training_config', {})
            if training_config:
                print(f"    • Training epochs: {training_config.get('epochs_completed', 'N/A')}")
                print(f"    • Final validation accuracy: {training_config.get('final_validation_accuracy', 'N/A')}")
        
        return models_info
        
    except Exception as e:
        print(f"❌ Error getting model metadata: {e}")
        return {}

async def main():
    """Main test function"""
    print("🚀 CarthaNeuro Saved Model Testing")
    print("=" * 50)
    
    # Initialize settings
    settings.initialize()
    
    try:
        # Test saved model loading
        loading_results = await test_saved_model_loading()
        
        # Test model metadata
        metadata_results = test_model_metadata()
        
        # Test prediction functionality
        prediction_result = await test_saved_model_prediction()
        
        # Test specific model prediction
        specific_result = await test_specific_model_prediction()
        
        print("\n" + "=" * 50)
        print("🎉 Testing completed!")
        
        # Summary
        success_count = 0
        total_tests = 4
        
        if loading_results:
            success_count += 1
        if metadata_results:
            success_count += 1
        if prediction_result and prediction_result.get("success"):
            success_count += 1
        if specific_result and specific_result.get("success"):
            success_count += 1
        
        print(f"📊 Test Results: {success_count}/{total_tests} tests passed")
        
        if success_count == total_tests:
            print("✅ All tests passed! Saved model functionality is working correctly.")
        else:
            print("⚠️  Some tests failed. Check the output above for details.")
        
    except Exception as e:
        print(f"❌ Fatal error during testing: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())