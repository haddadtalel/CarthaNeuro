"""
MongoDB Database Service for CarthaNeuro Backend
Handles all database operations using Motor (async MongoDB driver)
"""

import motor.motor_asyncio
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
from bson import ObjectId
from pydantic import BaseModel, field_validator, ValidationInfo
from pydantic_core import core_schema
import logging

from src.config.settings import settings
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

class PyObjectId(ObjectId):
    @classmethod
    def __get_pydantic_core_schema__(cls, source_type, handler):
        def validate(value):
            if isinstance(value, ObjectId):
                return value
            if not ObjectId.is_valid(value):
                raise ValueError("Invalid objectid")
            return ObjectId(value)
        
        return core_schema.no_info_plain_validator_function(
            validate,
            serialization=core_schema.to_string_ser_schema(),
        )

    @classmethod
    def __get_pydantic_json_schema__(cls, schema, handler):
        json_schema = handler(schema)
        json_schema.update(type="string")
        return json_schema

class MongoDBService:
    """MongoDB database service with async operations"""
    
    def __init__(self):
        self.client = None
        self.database = None
        self.initialized = False
        
    async def initialize(self):
        """Initialize MongoDB connection"""
        if self.initialized:
            return
            
        try:
            # Create MongoDB client with connection options (SSL handshake fix)
            self.client = motor.motor_asyncio.AsyncIOMotorClient(
                settings.mongodb_connection_string,
                maxPoolSize=settings.mongodb_max_pool_size,
                minPoolSize=settings.mongodb_min_pool_size,
                serverSelectionTimeoutMS=settings.mongodb_server_selection_timeout,
                retryWrites=True,
                w="majority",
                tls=True,
                tlsAllowInvalidCertificates=True,
                socketTimeoutMS=20000,
                connectTimeoutMS=20000,
                heartbeatFrequencyMS=10000
            )
            
            # Get database
            self.database = self.client[settings.mongodb_database_name]
            
            # Test connection
            await self.client.admin.command('ping')
            
            # Initialize collections
            await self._initialize_collections()
            
            self.initialized = True
            logger.info(f"MongoDB connection established to {settings.mongodb_database_name}")
            
        except Exception as e:
            logger.error(f"Failed to initialize MongoDB: {str(e)}")
            raise
    
    async def _initialize_collections(self):
        """Initialize database collections with indexes"""
        try:
            # Users collection indexes
            await self.database.users.create_index("email", unique=True)
            await self.database.users.create_index("username", unique=True)
            await self.database.users.create_index("created_at")
            
            # Datasets collection indexes
            await self.database.datasets.create_index("user_id")
            await self.database.datasets.create_index("dataset_name")
            await self.database.datasets.create_index("upload_date")
            await self.database.datasets.create_index([("metadata.class_label", 1)])
            
            # Models collection indexes
            await self.database.models.create_index("user_id")
            await self.database.models.create_index("model_name", unique=True)
            await self.database.models.create_index("model_type")
            await self.database.models.create_index("created_at")
            
            # Training sessions collection indexes
            await self.database.training_sessions.create_index("model_id")
            await self.database.training_sessions.create_index("user_id")
            await self.database.training_sessions.create_index("start_time")
            
            # Predictions collection indexes
            await self.database.predictions.create_index("user_id")
            await self.database.predictions.create_index("model_id")
            await self.database.predictions.create_index("prediction_time")
            await self.database.predictions.create_index("file_upload_id")
            
            # File metadata collection indexes
            await self.database.file_metadata.create_index("upload_id")
            await self.database.file_metadata.create_index("file_path")
            await self.database.file_metadata.create_index("user_id")
            await self.database.file_metadata.create_index("upload_date")
            
            logger.info("MongoDB collections and indexes initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize collections: {str(e)}")
            raise
    
    async def close(self):
        """Close MongoDB connection"""
        if self.client:
            self.client.close()
            self.initialized = False
            logger.info("MongoDB connection closed")

# Global database service instance
db_service = MongoDBService()

# Data Models for MongoDB Documents
class UserDocument(BaseModel):
    user_id: Optional[PyObjectId] = None
    username: str
    email: str
    password_hash: Optional[str] = None  # Hashed password
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    created_at: datetime = datetime.now()
    updated_at: datetime = datetime.now()
    is_active: bool = True
    role: str = "user"
    preferences: Dict[str, Any] = {}
    last_login: Optional[datetime] = None
    is_email_verified: bool = False
    
    class Config:
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

class DatasetDocument(BaseModel):
    dataset_id: Optional[PyObjectId] = None
    user_id: PyObjectId
    dataset_name: str
    description: Optional[str] = None
    upload_date: datetime = datetime.now()
    file_count: int = 0
    total_size_bytes: int = 0
    class_distribution: Dict[str, int] = {}
    file_paths: List[str] = []
    upload_id: str  # For tracking upload sessions
    metadata: Dict[str, Any] = {}
    status: str = "uploaded"  # uploaded, processing, ready, error
    
    class Config:
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

class ModelDocument(BaseModel):
    model_id: Optional[PyObjectId] = None
    user_id: PyObjectId
    model_name: str
    model_type: str  # 3d_cnn, 3d_vit, keras_simple_cnn, etc.
    framework: str  # pytorch, keras
    architecture: Optional[str] = None
    created_at: datetime = datetime.now()
    updated_at: datetime = datetime.now()
    parameters: Dict[str, Any] = {}
    performance_metrics: Dict[str, Any] = {}
    model_file_path: Optional[str] = None
    model_size_bytes: Optional[int] = None
    training_config: Dict[str, Any] = {}
    metadata: Dict[str, Any] = {}
    is_active: bool = True
    
    class Config:
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

class TrainingSessionDocument(BaseModel):
    session_id: Optional[PyObjectId] = None
    model_id: PyObjectId
    user_id: PyObjectId
    start_time: datetime = datetime.now()
    end_time: Optional[datetime] = None
    status: str = "running"  # running, completed, failed, stopped
    epochs_completed: int = 0
    total_epochs: int
    batch_size: int
    learning_rate: float
    training_metrics: Dict[str, Any] = {}
    validation_metrics: Dict[str, Any] = {}
    training_time_seconds: Optional[float] = None
    error_message: Optional[str] = None
    checkpoint_files: List[str] = []
    
    class Config:
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

class PredictionDocument(BaseModel):
    prediction_id: Optional[PyObjectId] = None
    user_id: PyObjectId
    model_id: PyObjectId
    input_file_path: Optional[str] = None
    input_file_upload_id: Optional[str] = None
    prediction_time: datetime = datetime.now()
    predicted_class: str
    confidence_score: float
    prediction_details: Dict[str, Any] = {}
    patient_context: Optional[str] = None
    processing_time_seconds: float
    model_version: Optional[str] = None
    metadata: Dict[str, Any] = {}
    
    class Config:
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

class FileMetadataDocument(BaseModel):
    file_id: Optional[PyObjectId] = None
    user_id: PyObjectId
    upload_id: str
    original_filename: str
    file_path: str
    file_size_bytes: int
    file_type: str  # image, zip, etc.
    upload_date: datetime = datetime.now()
    class_label: Optional[str] = None
    file_hash: Optional[str] = None
    metadata: Dict[str, Any] = {}
    is_processed: bool = False
    
    class Config:
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

# CRUD Operations
class DatabaseOperations:
    """Database CRUD operations"""
    
    def __init__(self, db_service: MongoDBService):
        self.db = db_service
        self._users = None
        self._datasets = None
        self._models = None
        self._training_sessions = None
        self._predictions = None
        self._file_metadata = None
    
    @property
    def users(self):
        if self._users is None:
            if self.db.database is None:
                raise RuntimeError("Database not initialized. Call db_service.initialize() first.")
            self._users = self.db.database.users
        return self._users
    
    @property
    def datasets(self):
        if self._datasets is None:
            if self.db.database is None:
                raise RuntimeError("Database not initialized. Call db_service.initialize() first.")
            self._datasets = self.db.database.datasets
        return self._datasets
    
    @property
    def models(self):
        if self._models is None:
            if self.db.database is None:
                raise RuntimeError("Database not initialized. Call db_service.initialize() first.")
            self._models = self.db.database.models
        return self._models
    
    @property
    def training_sessions(self):
        if self._training_sessions is None:
            if self.db.database is None:
                raise RuntimeError("Database not initialized. Call db_service.initialize() first.")
            self._training_sessions = self.db.database.training_sessions
        return self._training_sessions
    
    @property
    def predictions(self):
        if self._predictions is None:
            if self.db.database is None:
                raise RuntimeError("Database not initialized. Call db_service.initialize() first.")
            self._predictions = self.db.database.predictions
        return self._predictions
    
    @property
    def file_metadata(self):
        if self._file_metadata is None:
            if self.db.database is None:
                raise RuntimeError("Database not initialized. Call db_service.initialize() first.")
            self._file_metadata = self.db.database.file_metadata
        return self._file_metadata
    
    # User Operations
    async def create_user(self, user_data: UserDocument) -> str:
        """Create a new user"""
        user_dict = user_data.dict(exclude={"user_id"})
        user_dict["created_at"] = datetime.now()
        user_dict["updated_at"] = datetime.now()
        result = await self.users.insert_one(user_dict)
        return str(result.inserted_id)
    
    async def get_user_by_id(self, user_id: str) -> Optional[UserDocument]:
        """Get user by ID"""
        user = await self.users.find_one({"_id": ObjectId(user_id)})
        if user:
            user["user_id"] = str(user["_id"])
            return UserDocument(**user)
        return None
    
    async def get_user_by_email(self, email: str) -> Optional[UserDocument]:
        """Get user by email"""
        user = await self.users.find_one({"email": email})
        if user:
            user["user_id"] = str(user["_id"])
            return UserDocument(**user)
        return None
    
    async def update_user(self, user_id: str, update_data: Dict[str, Any]) -> bool:
        """Update user data"""
        update_data["updated_at"] = datetime.now()
        result = await self.users.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": update_data}
        )
        return result.modified_count > 0
    
    # Dataset Operations
    async def create_dataset(self, dataset_data: DatasetDocument) -> str:
        """Create a new dataset record"""
        dataset_dict = dataset_data.dict(exclude={"dataset_id"})
        dataset_dict["upload_date"] = datetime.now()
        result = await self.datasets.insert_one(dataset_dict)
        return str(result.inserted_id)
    
    async def get_datasets_by_user(self, user_id: str) -> List[DatasetDocument]:
        """Get all datasets for a user"""
        cursor = self.datasets.find({"user_id": ObjectId(user_id)})
        datasets = []
        async for doc in cursor:
            doc["dataset_id"] = str(doc["_id"])
            datasets.append(DatasetDocument(**doc))
        return datasets
    
    async def get_dataset_by_upload_id(self, upload_id: str) -> Optional[DatasetDocument]:
        """Get dataset by upload ID"""
        dataset = await self.datasets.find_one({"upload_id": upload_id})
        if dataset:
            dataset["dataset_id"] = str(dataset["_id"])
            return DatasetDocument(**dataset)
        return None
    
    async def update_dataset(self, dataset_id: str, update_data: Dict[str, Any]) -> bool:
        """Update dataset information"""
        result = await self.datasets.update_one(
            {"_id": ObjectId(dataset_id)},
            {"$set": update_data}
        )
        return result.modified_count > 0
    
    # Model Operations
    async def create_model(self, model_data: ModelDocument) -> str:
        """Create a new model record"""
        model_dict = model_data.dict(exclude={"model_id"})
        model_dict["created_at"] = datetime.now()
        model_dict["updated_at"] = datetime.now()
        result = await self.models.insert_one(model_dict)
        return str(result.inserted_id)
    
    async def get_models_by_user(self, user_id: str) -> List[ModelDocument]:
        """Get all models for a user"""
        cursor = self.models.find({"user_id": ObjectId(user_id), "is_active": True})
        models = []
        async for doc in cursor:
            doc["model_id"] = str(doc["_id"])
            models.append(ModelDocument(**doc))
        return models
    
    async def get_model_by_name(self, model_name: str) -> Optional[ModelDocument]:
        """Get model by name"""
        model = await self.models.find_one({"model_name": model_name, "is_active": True})
        if model:
            model["model_id"] = str(model["_id"])
            return ModelDocument(**model)
        return None
    
    async def update_model(self, model_id: str, update_data: Dict[str, Any]) -> bool:
        """Update model information"""
        update_data["updated_at"] = datetime.now()
        result = await self.models.update_one(
            {"_id": ObjectId(model_id)},
            {"$set": update_data}
        )
        return result.modified_count > 0
    
    # Training Session Operations
    async def create_training_session(self, session_data: TrainingSessionDocument) -> str:
        """Create a new training session"""
        session_dict = session_data.dict(exclude={"session_id"})
        session_dict["start_time"] = datetime.now()
        result = await self.training_sessions.insert_one(session_dict)
        return str(result.inserted_id)
    
    async def update_training_session(self, session_id: str, update_data: Dict[str, Any]) -> bool:
        """Update training session"""
        result = await self.training_sessions.update_one(
            {"_id": ObjectId(session_id)},
            {"$set": update_data}
        )
        return result.modified_count > 0
    
    async def get_training_sessions_by_model(self, model_id: str) -> List[TrainingSessionDocument]:
        """Get training sessions for a model"""
        cursor = self.training_sessions.find({"model_id": ObjectId(model_id)})
        sessions = []
        async for doc in cursor:
            doc["session_id"] = str(doc["_id"])
            sessions.append(TrainingSessionDocument(**doc))
        return sessions
    
    # Prediction Operations
    async def create_prediction(self, prediction_data: PredictionDocument) -> str:
        """Create a new prediction record"""
        prediction_dict = prediction_data.dict(exclude={"prediction_id"})
        prediction_dict["prediction_time"] = datetime.now()
        result = await self.predictions.insert_one(prediction_dict)
        return str(result.inserted_id)
    
    async def get_predictions_by_user(self, user_id: str, limit: int = 50) -> List[PredictionDocument]:
        """Get predictions for a user"""
        cursor = self.predictions.find({"user_id": ObjectId(user_id)}).sort("prediction_time", -1).limit(limit)
        predictions = []
        async for doc in cursor:
            doc["prediction_id"] = str(doc["_id"])
            predictions.append(PredictionDocument(**doc))
        return predictions
    
    async def get_predictions_by_upload_id(self, upload_id: str) -> List[PredictionDocument]:
        """Get predictions by file upload ID"""
        cursor = self.predictions.find({"input_file_upload_id": upload_id})
        predictions = []
        async for doc in cursor:
            doc["prediction_id"] = str(doc["_id"])
            predictions.append(PredictionDocument(**doc))
        return predictions
    
    # File Metadata Operations
    async def create_file_metadata(self, file_data: FileMetadataDocument) -> str:
        """Create file metadata record"""
        file_dict = file_data.dict(exclude={"file_id"})
        file_dict["upload_date"] = datetime.now()
        result = await self.file_metadata.insert_one(file_dict)
        return str(result.inserted_id)
    
    async def get_files_by_upload_id(self, upload_id: str) -> List[FileMetadataDocument]:
        """Get files by upload ID"""
        cursor = self.file_metadata.find({"upload_id": upload_id})
        files = []
        async for doc in cursor:
            doc["file_id"] = str(doc["_id"])
            files.append(FileMetadataDocument(**doc))
        return files
    
    async def update_file_metadata(self, file_id: str, update_data: Dict[str, Any]) -> bool:
        """Update file metadata"""
        result = await self.file_metadata.update_one(
            {"_id": ObjectId(file_id)},
            {"$set": update_data}
        )
        return result.modified_count > 0

# Global database operations instance
db_operations = None

def get_db_operations() -> DatabaseOperations:
    """Get database operations instance"""
    global db_operations
    if db_operations is None:
        db_operations = DatabaseOperations(db_service)
    return db_operations

# Database utilities
def convert_object_ids(data: Dict[str, Any]) -> Dict[str, Any]:
    """Convert ObjectId fields to strings for JSON serialization"""
    if isinstance(data, dict):
        for key, value in data.items():
            if isinstance(value, ObjectId):
                data[key] = str(value)
            elif isinstance(value, dict):
                convert_object_ids(value)
            elif isinstance(value, list):
                for item in value:
                    if isinstance(item, dict):
                        convert_object_ids(item)
    return data