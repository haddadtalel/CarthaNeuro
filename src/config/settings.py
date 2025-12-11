"""
Configuration management for CarthaNeuro Backend
"""

from pydantic_settings import BaseSettings
from typing import List, Optional
import os
from pathlib import Path

class Settings(BaseSettings):
    """Application settings"""
    
    # Application
    environment: str = "development"
    debug: bool = True
    host: str = "0.0.0.0"
    port: int = 8000
    
    # CORS
    allowed_origins: List[str] = [
        "http://localhost:3000",
        "http://localhost:3001", 
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001"
    ]
    
    # Paths
    project_root: Path = Path(r"C:\Users\Talel\Desktop\CarthaNeruo\carthaneuro\Back-end")
    data_dir: Path = project_root / "data"
    models_dir: Path = project_root / "models"
    logs_dir: Path = project_root / "logs"
    cache_dir: Path = project_root / "cache"
    
    # Model Configuration
    default_model_type: str = "resnet"  # resnet, densenet, vit
    multimodal_model_name: str = "llava-hf/llava-1.5-7b-hf"  # or "Qwen/Qwen2-VL-7B-Instruct"
    
    # Training
    batch_size: int = 8
    learning_rate: float = 1e-4
    num_epochs: int = 50
    validation_split: float = 0.2
    test_split: float = 0.1
    
    # Image processing
    image_size: int = 224
    num_slices: int = 32  # For 3D volume creation
    normalize: bool = True
    
    # LLM Configuration
    max_new_tokens: int = 512
    temperature: float = 0.1
    do_sample: bool = True
    
    # Classification
    num_classes: int = 4
    class_names: List[str] = ["glioma", "meningioma", "notumor", "pituitary"]
    
    # Logging
    log_level: str = "INFO"
    log_file: str = "carthaneuro.log"
    
    # Security
    api_key_header: str = "X-API-Key"
    
    # MongoDB Configuration
    mongodb_connection_string: str = "mongodb+srv://talelhaddad5_db_user:2X1WvWZNEC1JKYEl@carthaneruodatabase.5e3bkdw.mongodb.net/?appName=CarthaNeruoDataBase"
    mongodb_database_name: str = "carthaneuro_db"
    mongodb_max_pool_size: int = 50
    mongodb_min_pool_size: int = 5
    mongodb_server_selection_timeout: int = 5000
    
    # JWT Configuration
    jwt_secret_key: str = "your-super-secret-jwt-key-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30
    jwt_refresh_token_expire_days: int = 7
    
    # GPU settings
    use_gpu: bool = True
    device: str = "cuda" if use_gpu else "cpu"
    
    class Config:
        env_file = ".env"
        case_sensitive = False

# Create global settings instance
settings = Settings()

# Ensure directories exist
for directory in [settings.data_dir, settings.models_dir, settings.logs_dir, settings.cache_dir]:
    directory.mkdir(parents=True, exist_ok=True)