"""
Detailed metrics models for training tracking and model performance analysis
"""
from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any, Union
from datetime import datetime
from enum import Enum

class ModelFramework(str, Enum):
    """Supported model frameworks"""
    PYTORCH = "pytorch"
    KERAS = "keras"
    TENSORFLOW = "tensorflow"

class TrainingStatus(str, Enum):
    """Training job status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"

class MetricType(str, Enum):
    """Types of metrics that can be tracked"""
    ACCURACY = "accuracy"
    LOSS = "loss"
    PRECISION = "precision"
    RECALL = "recall"
    F1_SCORE = "f1_score"
    ROC_AUC = "roc_auc"
    CONFUSION_MATRIX = "confusion_matrix"
    LEARNING_RATE = "learning_rate"
    GPU_MEMORY = "gpu_memory"
    CPU_USAGE = "cpu_usage"
    TRAINING_TIME = "training_time"

class EpochMetrics(BaseModel):
    """Metrics for a single training epoch"""
    epoch: int
    training_loss: float
    training_accuracy: float
    validation_loss: float
    validation_accuracy: float
    learning_rate: float
    training_time: float = Field(description="Time taken for this epoch in seconds")
    gpu_memory_used: Optional[float] = Field(default=None, description="GPU memory used in MB")
    cpu_usage: Optional[float] = Field(default=None, description="CPU usage percentage")
    timestamp: datetime = Field(default_factory=datetime.now)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class ModelMetrics(BaseModel):
    """Comprehensive model performance metrics"""
    model_name: str
    framework: ModelFramework
    architecture: str
    
    # Training configuration
    epochs_completed: int
    total_epochs: int
    batch_size: int
    learning_rate: float
    optimizer: str
    loss_function: str
    
    # Performance metrics
    final_training_loss: float
    final_training_accuracy: float
    final_validation_loss: float
    final_validation_accuracy: float
    best_validation_accuracy: float
    best_epoch: int
    
    # Additional metrics
    precision: Optional[float] = None
    recall: Optional[float] = None
    f1_score: Optional[float] = None
    roc_auc: Optional[float] = None
    confusion_matrix: Optional[List[List[int]]] = None
    
    # Model statistics
    total_parameters: Optional[int] = None
    model_size_mb: Optional[float] = None
    inference_time_ms: Optional[float] = None
    
    # Training metadata
    training_start_time: datetime
    training_end_time: Optional[datetime] = None
    total_training_time: Optional[float] = None  # in seconds
    gpu_utilization_avg: Optional[float] = None
    gpu_memory_peak: Optional[float] = None
    
    # Class-wise performance (for multi-class classification)
    class_wise_metrics: Optional[Dict[str, Dict[str, float]]] = None
    
    # Training history
    epoch_metrics: List[EpochMetrics] = Field(default_factory=list)
    
    # Additional metadata
    dataset_name: Optional[str] = None
    dataset_size: Optional[int] = None
    class_distribution: Optional[Dict[str, int]] = None
    
    # Saving information
    is_saved: bool = False
    saved_path: Optional[str] = None
    saved_timestamp: Optional[datetime] = None
    metadata_file_path: Optional[str] = None

class TrainingJob(BaseModel):
    """Training job tracking"""
    job_id: str
    model_name: str
    model_type: str
    framework: ModelFramework
    status: TrainingStatus
    progress: float = Field(ge=0, le=100)
    
    # Configuration
    epochs: int
    batch_size: int
    learning_rate: float
    validation_split: float
    
    # Tracking
    start_time: datetime = Field(default_factory=datetime.now)
    estimated_end_time: Optional[datetime] = None
    current_epoch: int = 0
    last_update: datetime = Field(default_factory=datetime.now)
    
    # Results
    current_metrics: Optional[ModelMetrics] = None
    error_message: Optional[str] = None
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class ModelComparison(BaseModel):
    """Model comparison for analysis"""
    comparison_id: str
    name: str
    description: Optional[str] = None
    model_names: List[str]
    comparison_metrics: Dict[str, Dict[str, float]] = Field(
        description="Model performance comparison by metric"
    )
    created_at: datetime = Field(default_factory=datetime.now)

class MetricHistory(BaseModel):
    """Historical metric tracking for visualization"""
    model_name: str
    metric_type: MetricType
    values: List[float]
    epochs: List[int]
    timestamps: List[datetime]
    framework: ModelFramework

class ModelPerformanceReport(BaseModel):
    """Comprehensive model performance report"""
    report_id: str
    model_name: str
    generated_at: datetime = Field(default_factory=datetime.now)
    
    # Summary statistics
    overall_performance: Dict[str, float]
    training_efficiency: Dict[str, float]
    resource_utilization: Dict[str, float]
    
    # Recommendations
    recommendations: List[str] = Field(default_factory=list)
    potential_improvements: List[str] = Field(default_factory=list)
    
    # Performance trends
    performance_trends: Dict[str, List[float]] = Field(default_factory=dict)
    
    # Comparison with baseline (if available)
    baseline_comparison: Optional[Dict[str, float]] = None

class SavedModelMetadata(BaseModel):
    """Metadata for saved models"""
    model_name: str
    model_path: str
    metadata_path: str
    framework: ModelFramework
    
    # Model details
    architecture: str
    input_shape: Optional[List[int]] = None
    output_shape: Optional[List[int]] = None
    total_parameters: Optional[int] = None
    
    # Performance metrics
    accuracy: float
    loss: float
    precision: Optional[float] = None
    recall: Optional[float] = None
    f1_score: Optional[float] = None
    
    # Training details
    epochs_trained: int
    training_time: float  # in seconds
    final_learning_rate: float
    
    # Dataset information
    dataset_name: Optional[str] = None
    class_names: Optional[List[str]] = None
    num_classes: int
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.now)
    last_modified: datetime = Field(default_factory=datetime.now)
    
    # Additional metadata
    description: Optional[str] = None
    version: str = "1.0"
    tags: List[str] = Field(default_factory=list)
    
    # File information
    model_size_mb: Optional[float] = None
    checksum: Optional[str] = None
    
    # Usage statistics
    prediction_count: int = 0
    last_prediction: Optional[datetime] = None