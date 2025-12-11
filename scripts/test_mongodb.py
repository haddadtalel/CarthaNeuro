"""
Test script for MongoDB integration in CarthaNeuro
Tests all major database operations and API integrations
"""

import asyncio
import time
import sys
from pathlib import Path

# Add the src directory to the Python path
sys.path.append(str(Path(__file__).parent.parent / "src"))

from src.database.mongodb_service import (
    db_service, 
    get_db_operations, 
    UserDocument, 
    DatasetDocument, 
    ModelDocument, 
    PredictionDocument, 
    FileMetadataDocument
)
from bson import ObjectId
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

async def test_mongodb_connection():
    """Test MongoDB connection"""
    try:
        logger.info("Testing MongoDB connection...")
        await db_service.initialize()
        await db_service.client.admin.command('ping')
        logger.info("✓ MongoDB connection successful")
        return True
    except Exception as e:
        logger.error(f"✗ MongoDB connection failed: {str(e)}")
        return False

async def test_user_operations():
    """Test user CRUD operations"""
    try:
        logger.info("Testing user operations...")
        db_ops = get_db_operations()
        
        # Create test user
        test_user = UserDocument(
            username="test_user",
            email="test@example.com",
            first_name="Test",
            last_name="User"
        )
        
        user_id = await db_ops.create_user(test_user)
        logger.info(f"✓ Created test user with ID: {user_id}")
        
        # Get user by ID
        retrieved_user = await db_ops.get_user_by_id(user_id)
        if retrieved_user and retrieved_user.username == "test_user":
            logger.info("✓ User retrieval by ID successful")
        else:
            logger.error("✗ User retrieval by ID failed")
            return False
        
        # Get user by email
        email_user = await db_ops.get_user_by_email("test@example.com")
        if email_user and email_user.user_id == user_id:
            logger.info("✓ User retrieval by email successful")
        else:
            logger.error("✗ User retrieval by email failed")
            return False
        
        # Update user
        update_success = await db_ops.update_user(user_id, {"last_name": "Updated"})
        if update_success:
            updated_user = await db_ops.get_user_by_id(user_id)
            if updated_user.last_name == "Updated":
                logger.info("✓ User update successful")
            else:
                logger.error("✗ User update verification failed")
                return False
        
        return True
        
    except Exception as e:
        logger.error(f"✗ User operations test failed: {str(e)}")
        return False

async def test_dataset_operations():
    """Test dataset CRUD operations"""
    try:
        logger.info("Testing dataset operations...")
        db_ops = get_db_operations()
        
        # Create test dataset
        test_dataset = DatasetDocument(
            user_id=ObjectId("000000000000000000000001"),
            dataset_name="test_dataset",
            file_count=10,
            total_size_bytes=1024000,
            class_distribution={"glioma": 5, "meningioma": 3, "notumor": 2},
            upload_id="test_upload_123",
            metadata={"test": True}
        )
        
        dataset_id = await db_ops.create_dataset(test_dataset)
        logger.info(f"✓ Created test dataset with ID: {dataset_id}")
        
        # Get datasets by user
        user_datasets = await db_ops.get_datasets_by_user("000000000000000000000001")
        if any(d.dataset_name == "test_dataset" for d in user_datasets):
            logger.info("✓ Dataset retrieval by user successful")
        else:
            logger.error("✗ Dataset retrieval by user failed")
            return False
        
        # Get dataset by upload ID
        upload_dataset = await db_ops.get_dataset_by_upload_id("test_upload_123")
        if upload_dataset and upload_dataset.dataset_id == dataset_id:
            logger.info("✓ Dataset retrieval by upload ID successful")
        else:
            logger.error("✗ Dataset retrieval by upload ID failed")
            return False
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Dataset operations test failed: {str(e)}")
        return False

async def test_model_operations():
    """Test model CRUD operations"""
    try:
        logger.info("Testing model operations...")
        db_ops = get_db_operations()
        
        # Create test model
        test_model = ModelDocument(
            user_id=ObjectId("000000000000000000000001"),
            model_name="test_model",
            model_type="keras_simple_cnn",
            framework="keras",
            architecture="simple_cnn",
            parameters={"epochs": 10, "batch_size": 32},
            performance_metrics={"accuracy": 0.95, "loss": 0.1}
        )
        
        model_id = await db_ops.create_model(test_model)
        logger.info(f"✓ Created test model with ID: {model_id}")
        
        # Get models by user
        user_models = await db_ops.get_models_by_user("000000000000000000000001")
        if any(m.model_name == "test_model" for m in user_models):
            logger.info("✓ Model retrieval by user successful")
        else:
            logger.error("✗ Model retrieval by user failed")
            return False
        
        # Get model by name
        name_model = await db_ops.get_model_by_name("test_model")
        if name_model and name_model.model_id == model_id:
            logger.info("✓ Model retrieval by name successful")
        else:
            logger.error("✗ Model retrieval by name failed")
            return False
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Model operations test failed: {str(e)}")
        return False

async def test_prediction_operations():
    """Test prediction CRUD operations"""
    try:
        logger.info("Testing prediction operations...")
        db_ops = get_db_operations()
        
        # Create test prediction
        test_prediction = PredictionDocument(
            user_id=ObjectId("000000000000000000000001"),
            model_id=ObjectId("000000000000000000000002"),
            predicted_class="glioma",
            confidence_score=0.85,
            prediction_details={"class_probabilities": [0.1, 0.85, 0.03, 0.02]},
            patient_context="Patient with headache and vision problems",
            processing_time_seconds=2.5,
            metadata={"test": True}
        )
        
        prediction_id = await db_ops.create_prediction(test_prediction)
        logger.info(f"✓ Created test prediction with ID: {prediction_id}")
        
        # Get predictions by user
        user_predictions = await db_ops.get_predictions_by_user("000000000000000000000001", limit=10)
        if any(p.prediction_id == prediction_id for p in user_predictions):
            logger.info("✓ Prediction retrieval by user successful")
        else:
            logger.error("✗ Prediction retrieval by user failed")
            return False
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Prediction operations test failed: {str(e)}")
        return False

async def test_file_metadata_operations():
    """Test file metadata CRUD operations"""
    try:
        logger.info("Testing file metadata operations...")
        db_ops = get_db_operations()
        
        # Create test file metadata
        test_file = FileMetadataDocument(
            user_id=ObjectId("000000000000000000000001"),
            upload_id="test_upload_123",
            original_filename="brain_scan.jpg",
            file_path="/uploads/test/brain_scan.jpg",
            file_size_bytes=2048000,
            file_type="image",
            class_label="glioma",
            metadata={"test": True}
        )
        
        file_id = await db_ops.create_file_metadata(test_file)
        logger.info(f"✓ Created test file metadata with ID: {file_id}")
        
        # Get files by upload ID
        upload_files = await db_ops.get_files_by_upload_id("test_upload_123")
        if any(f.file_id == file_id for f in upload_files):
            logger.info("✓ File metadata retrieval by upload ID successful")
        else:
            logger.error("✗ File metadata retrieval by upload ID failed")
            return False
        
        return True
        
    except Exception as e:
        logger.error(f"✗ File metadata operations test failed: {str(e)}")
        return False

async def test_api_integration_simulation():
    """Simulate API integration scenarios"""
    try:
        logger.info("Testing API integration simulation...")
        db_ops = get_db_operations()
        
        # Simulate file upload scenario
        upload_id = "simulated_upload_456"
        
        # 1. Create dataset record
        dataset = DatasetDocument(
            user_id=ObjectId("000000000000000000000001"),
            dataset_name="simulated_dataset",
            file_count=5,
            total_size_bytes=10240000,
            class_distribution={"glioma": 3, "meningioma": 2},
            upload_id=upload_id,
            status="uploaded"
        )
        
        dataset_id = await db_ops.create_dataset(dataset)
        logger.info(f"✓ Simulated dataset creation: {dataset_id}")
        
        # 2. Create file metadata records
        files = ["scan1.jpg", "scan2.jpg", "scan3.jpg", "scan4.jpg", "scan5.jpg"]
        for i, filename in enumerate(files):
            file_meta = FileMetadataDocument(
                user_id=ObjectId("000000000000000000000001"),
                upload_id=upload_id,
                original_filename=filename,
                file_path=f"/uploads/{upload_id}/{filename}",
                file_size_bytes=2048000,
                file_type="image",
                class_label="glioma" if i < 3 else "meningioma"
            )
            file_id = await db_ops.create_file_metadata(file_meta)
        
        logger.info("✓ Simulated file metadata creation")
        
        # 3. Simulate prediction scenario
        prediction = PredictionDocument(
            user_id=ObjectId("000000000000000000000001"),
            model_id=ObjectId("000000000000000000000002"),
            input_file_upload_id=upload_id,
            predicted_class="glioma",
            confidence_score=0.92,
            prediction_details={
                "class_probabilities": [0.92, 0.05, 0.02, 0.01],
                "analysis_type": "multimodal_llm_plus_classification"
            },
            patient_context="Simulated patient context for testing",
            processing_time_seconds=3.2,
            metadata={
                "simulation": True,
                "api_test": True
            }
        )
        
        prediction_id = await db_ops.create_prediction(prediction)
        logger.info(f"✓ Simulated prediction creation: {prediction_id}")
        
        # 4. Verify data retrieval
        retrieved_dataset = await db_ops.get_dataset_by_upload_id(upload_id)
        retrieved_files = await db_ops.get_files_by_upload_id(upload_id)
        retrieved_predictions = await db_ops.get_predictions_by_upload_id(upload_id)
        
        if (retrieved_dataset and 
            len(retrieved_files) == 5 and 
            len(retrieved_predictions) == 1):
            logger.info("✓ API integration simulation successful")
            return True
        else:
            logger.error("✗ API integration simulation verification failed")
            return False
        
    except Exception as e:
        logger.error(f"✗ API integration simulation failed: {str(e)}")
        return False

async def run_all_tests():
    """Run all database tests"""
    logger.info("Starting MongoDB integration tests...")
    
    tests = [
        ("MongoDB Connection", test_mongodb_connection),
        ("User Operations", test_user_operations),
        ("Dataset Operations", test_dataset_operations),
        ("Model Operations", test_model_operations),
        ("Prediction Operations", test_prediction_operations),
        ("File Metadata Operations", test_file_metadata_operations),
        ("API Integration Simulation", test_api_integration_simulation)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        logger.info(f"\n--- Running {test_name} Test ---")
        try:
            result = await test_func()
            if result:
                passed += 1
                logger.info(f"✓ {test_name} test PASSED")
            else:
                logger.error(f"✗ {test_name} test FAILED")
        except Exception as e:
            logger.error(f"✗ {test_name} test FAILED with exception: {str(e)}")
    
    # Summary
    logger.info(f"\n=== Test Results ===")
    logger.info(f"Passed: {passed}/{total}")
    logger.info(f"Success Rate: {(passed/total)*100:.1f}%")
    
    if passed == total:
        logger.info("🎉 All tests PASSED! MongoDB integration is working correctly.")
        return True
    else:
        logger.error(f"❌ {total-passed} tests FAILED. Please check the logs above.")
        return False

if __name__ == "__main__":
    asyncio.run(run_all_tests())