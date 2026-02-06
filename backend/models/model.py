from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime

class ModelConfig(BaseModel):
    epochs: int
    learning_rate: float
    batch_size: int

class ModelMetrics(BaseModel):
    training_config: ModelConfig
    epochs_completed: int
    best_val_accuracy: float
    best_val_loss: float
    final_train_accuracy: float
    final_val_accuracy: float
    test_accuracy: Optional[float] = None
    test_loss: Optional[float] = None
    class_metrics: Optional[Dict[str, Any]] = None

class TrainedModel(BaseModel):
    id: str
    name: str
    model_type: str
    status: str
    config: Optional[Dict[str, Any]] = None
    metrics: Optional[ModelMetrics] = None
    error: Optional[str] = None
    is_production: bool = False
    created_at: datetime
    completed_at: Optional[datetime] = None
    trained_by: Optional[str] = None
    model_path: Optional[str] = None

class TrainingRequest(BaseModel):
    model_type: str
    epochs: int
    learning_rate: float
    batch_size: int
    dataset_id: Optional[str] = Field(None, description="Optional dataset ID for training on real data")
    model_name: Optional[str] = Field(None, description="Optional custom model name")

class TrainingResponse(BaseModel):
    training_id: str
    message: str
    status: str
    estimated_time: str

