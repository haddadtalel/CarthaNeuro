from pydantic import BaseModel
from typing import Optional, List, Dict
from datetime import datetime

class Dataset(BaseModel):
    id: str
    name: str
    description: str
    path: str
    file_count: int
    size_bytes: int
    size_mb: float
    uploaded_by: str
    is_active: bool = True
    created_at: datetime
    # New fields for dataset analysis
    total_images: int = 0
    classes: List[str] = []
    class_distribution: Dict[str, int] = {}
    file_format: str = ""
    # Train/Test split fields
    has_train_test_split: bool = False
    train_count: int = 0
    test_count: int = 0
    train_distribution: Dict[str, int] = {}
    test_distribution: Dict[str, int] = {}
    # Frontend compatibility fields
    image_count: int = 0
    status: str = "ready"
    image_extensions: List[str] = []

class DatasetCreate(BaseModel):
    name: str
    description: str
    uploaded_by: str

