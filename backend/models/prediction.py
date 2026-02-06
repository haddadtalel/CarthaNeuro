from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime

class ConsultationFormData(BaseModel):
    patient_full_name: str
    patient_reference_id: Optional[str] = None
    age: int
    gender: str
    family_history_ad: bool
    diabetes: bool
    hypertension: bool
    heart_disease: bool
    stroke_history: bool
    smoking: bool
    alcohol_use: bool
    memory_complaints: int
    difficulty_concentrating: int
    problem_solving_difficulty: int
    mood_changes: int
    confusion: int
    personality_changes: int
    disorientation: int
    difficulty_with_daily_tasks: int
    symptoms_duration_months: int
    previous_ad_evaluation: bool
    current_medications: Optional[str] = None
    notes: Optional[str] = None

class ConsultationResponse(BaseModel):
    consultation_id: str
    risk_score: float
    message: str

class PredictionRequest(BaseModel):
    patient_id: str
    patient_full_name: str
    mri_image_id: str
    consultation_id: Optional[str] = None
    model_type: Optional[str] = None

class PredictionResponse(BaseModel):
    prediction_id: str
    patient_id: str
    patient_full_name: str
    disease_class: str
    probability: float
    confidence: str
    factors: Dict[str, Any]
    recommendations: str
    model_used: str
    created_at: datetime
    doctor: Optional[Dict[str, Any]] = None