"""
MongoDB Database Initialization Script for CarthaNeuro
Sets up collections, indexes, and creates default system users
"""

import asyncio
import logging
from datetime import datetime
from bson import ObjectId

from src.config.settings import settings
from src.database.mongodb_service import db_service, get_db_operations, UserDocument
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

async def initialize_database():
    """Initialize MongoDB database with collections and default data"""
    try:
        # Initialize MongoDB connection
        await db_service.initialize()
        logger.info("MongoDB connection established successfully")
        
        # Get database operations
        db_ops = get_db_operations()
        
        # Create system users if they don't exist
        await _create_system_users(db_ops)
        
        # Create default datasets if needed
        await _create_default_datasets(db_ops)
        
        # Create default models if needed
        await _create_default_models(db_ops)
        
        logger.info("Database initialization completed successfully")
        
    except Exception as e:
        logger.error(f"Database initialization failed: {str(e)}")
        raise

async def _create_system_users(db_ops):
    """Create default system users"""
    try:
        # Check if system user already exists
        existing_user = await db_ops.get_user_by_email("system@carthaneuro.com")
        if not existing_user:
            system_user = UserDocument(
                username="system",
                email="system@carthaneuro.com",
                first_name="System",
                last_name="Admin",
                role="system_admin",
                is_active=True,
                preferences={
                    "system_user": True,
                    "created_by": "initialization_script"
                }
            )
            user_id = await db_ops.create_user(system_user)
            logger.info(f"System user created with ID: {user_id}")
            
            # Create demo user for testing
            demo_user = UserDocument(
                username="demo_user",
                email="demo@carthaneuro.com",
                first_name="Demo",
                last_name="User",
                role="user",
                is_active=True,
                preferences={
                    "demo_user": True
                }
            )
            user_id = await db_ops.create_user(demo_user)
            logger.info(f"Demo user created with ID: {user_id}")
        else:
            logger.info("System users already exist")
            
    except Exception as e:
        logger.error(f"Failed to create system users: {str(e)}")

async def _create_default_datasets(db_ops):
    """Create default dataset references"""
    try:
        # This would typically reference existing datasets on disk
        # For now, just log that we're ready to track datasets
        logger.info("Default datasets tracking ready")
        
    except Exception as e:
        logger.error(f"Failed to create default datasets: {str(e)}")

async def _create_default_models(db_ops):
    """Create default model records for loaded models"""
    try:
        from bson import ObjectId
        
        # Create entries for the default models that get loaded
        system_user = await db_ops.get_user_by_email("system@carthaneuro.com")
        if system_user:
            user_id = ObjectId(system_user.user_id)
            
            # Define default models
            default_models = [
                {
                    "model_name": "3d_cnn_classifier",
                    "model_type": "3d_cnn",
                    "framework": "pytorch",
                    "architecture": "resnet",
                    "parameters": {
                        "num_classes": 4,
                        "pretrained": True,
                        "model_type": "resnet"
                    }
                },
                {
                    "model_name": "3d_vit_classifier", 
                    "model_type": "3d_vit",
                    "framework": "pytorch",
                    "architecture": "vit",
                    "parameters": {
                        "num_classes": 4,
                        "pretrained": True
                    }
                },
                {
                    "model_name": "multimodal_llm",
                    "model_type": "multimodal_llm",
                    "framework": "transformers",
                    "architecture": "llava",
                    "parameters": {
                        "model_name": settings.multimodal_model_name,
                        "max_new_tokens": settings.max_new_tokens,
                        "temperature": settings.temperature
                    }
                }
            ]
            
            for model_data in default_models:
                existing_model = await db_ops.get_model_by_name(model_data["model_name"])
                if not existing_model:
                    from src.database.mongodb_service import ModelDocument
                    
                    model_doc = ModelDocument(
                        user_id=user_id,
                        model_name=model_data["model_name"],
                        model_type=model_data["model_type"],
                        framework=model_data["framework"],
                        architecture=model_data["architecture"],
                        parameters=model_data["parameters"],
                        metadata={
                            "is_default_model": True,
                            "created_by": "initialization_script"
                        }
                    )
                    
                    model_id = await db_ops.create_model(model_doc)
                    logger.info(f"Default model {model_data['model_name']} created with ID: {model_id}")
                else:
                    logger.info(f"Default model {model_data['model_name']} already exists")
                    
    except Exception as e:
        logger.error(f"Failed to create default models: {str(e)}")

async def check_database_health():
    """Check database health and connectivity"""
    try:
        await db_service.initialize()
        
        # Test basic operations
        db_ops = get_db_operations()
        
        # Check collections exist
        collections = await db_service.database.list_collection_names()
        required_collections = ['users', 'datasets', 'models', 'predictions', 'training_sessions', 'file_metadata']
        
        missing_collections = [col for col in required_collections if col not in collections]
        if missing_collections:
            logger.warning(f"Missing collections: {missing_collections}")
        else:
            logger.info("All required collections exist")
        
        # Test user operations
        user_count = await db_ops.users.count_documents({})
        logger.info(f"Total users in database: {user_count}")
        
        # Test dataset operations  
        dataset_count = await db_ops.datasets.count_documents({})
        logger.info(f"Total datasets in database: {dataset_count}")
        
        # Test model operations
        model_count = await db_ops.models.count_documents({})
        logger.info(f"Total models in database: {model_count}")
        
        logger.info("Database health check completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"Database health check failed: {str(e)}")
        return False

async def cleanup_test_data():
    """Clean up test data (use with caution!)"""
    try:
        await db_service.initialize()
        db_ops = get_db_operations()
        
        # Only clean up test data (not production data)
        test_result = await db_ops.users.delete_many({
            "email": {"$regex": "@test\\.|@demo\\.", "$options": "i"}
        })
        logger.info(f"Cleaned up {test_result.deleted_count} test users")
        
        test_datasets = await db_ops.datasets.delete_many({
            "dataset_name": {"$regex": "test|demo", "$options": "i"}
        })
        logger.info(f"Cleaned up {test_datasets.deleted_count} test datasets")
        
        test_models = await db_ops.models.delete_many({
            "model_name": {"$regex": "test|demo", "$options": "i"}
        })
        logger.info(f"Cleaned up {test_models.deleted_count} test models")
        
        test_predictions = await db_ops.predictions.delete_many({
            "metadata.test_data": True
        })
        logger.info(f"Cleaned up {test_predictions.deleted_count} test predictions")
        
        logger.info("Test data cleanup completed")
        
    except Exception as e:
        logger.error(f"Failed to cleanup test data: {str(e)}")

async def export_database_stats():
    """Export database statistics"""
    try:
        await db_service.initialize()
        db_ops = get_db_operations()
        
        stats = {}
        
        # User statistics
        stats["users"] = {
            "total": await db_ops.users.count_documents({}),
            "active": await db_ops.users.count_documents({"is_active": True}),
            "by_role": {}
        }
        
        # Get user roles breakdown
        async for role_doc in db_ops.users.aggregate([
            {"$group": {"_id": "$role", "count": {"$sum": 1}}}
        ]):
            stats["users"]["by_role"][role_doc["_id"]] = role_doc["count"]
        
        # Dataset statistics
        stats["datasets"] = {
            "total": await db_ops.datasets.count_documents({}),
            "ready": await db_ops.datasets.count_documents({"status": "ready"}),
            "processing": await db_ops.datasets.count_documents({"status": "processing"}),
            "total_files": 0,
            "total_size_bytes": 0
        }
        
        # Get dataset file statistics
        async for dataset_doc in db_ops.datasets.find({}, {"file_count": 1, "total_size_bytes": 1}):
            stats["datasets"]["total_files"] += dataset_doc.get("file_count", 0)
            stats["datasets"]["total_size_bytes"] += dataset_doc.get("total_size_bytes", 0)
        
        # Model statistics
        stats["models"] = {
            "total": await db_ops.models.count_documents({}),
            "active": await db_ops.models.count_documents({"is_active": True}),
            "by_framework": {},
            "by_type": {}
        }
        
        # Get model breakdown
        async for model_doc in db_ops.models.aggregate([
            {"$group": {"_id": "$framework", "count": {"$sum": 1}}}
        ]):
            stats["models"]["by_framework"][model_doc["_id"]] = model_doc["count"]
            
        async for model_doc in db_ops.models.aggregate([
            {"$group": {"_id": "$model_type", "count": {"$sum": 1}}}
        ]):
            stats["models"]["by_type"][model_doc["_id"]] = model_doc["count"]
        
        # Prediction statistics
        stats["predictions"] = {
            "total": await db_ops.predictions.count_documents({}),
            "recent_24h": await db_ops.predictions.count_documents({
                "prediction_time": {"$gte": datetime.utcnow().timestamp() - 86400}
            }),
            "by_model": {}
        }
        
        # Get prediction breakdown by model
        async for pred_doc in db_ops.predictions.aggregate([
            {"$group": {"_id": "$model_id", "count": {"$sum": 1}}}
        ]):
            stats["predictions"]["by_model"][str(pred_doc["_id"])] = pred_doc["count"]
        
        logger.info("Database statistics exported successfully")
        return stats
        
    except Exception as e:
        logger.error(f"Failed to export database statistics: {str(e)}")
        return {}

if __name__ == "__main__":
    import sys
    
    async def main():
        if len(sys.argv) > 1:
            command = sys.argv[1]
            
            if command == "init":
                await initialize_database()
            elif command == "health":
                await check_database_health()
            elif command == "cleanup_test":
                await cleanup_test_data()
            elif command == "stats":
                stats = await export_database_stats()
                print("Database Statistics:")
                print(f"Users: {stats.get('users', {})}")
                print(f"Datasets: {stats.get('datasets', {})}")
                print(f"Models: {stats.get('models', {})}")
                print(f"Predictions: {stats.get('predictions', {})}")
            else:
                print("Available commands: init, health, cleanup_test, stats")
        else:
            await initialize_database()
    
    asyncio.run(main())