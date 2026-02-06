// User Types
export interface User {
  id: string;
  email: string;
  username: string;
  full_name?: string;
  role: 'admin' | 'doctor';
  is_active: boolean;
  created_at: string;
}

export interface Doctor {
  id: string;
  username: string;
  full_name?: string;
  email?: string;
}

export interface LoginCredentials {
  username: string;
  password: string;
}

export interface RegisterData {
  email: string;
  username: string;
  password: string;
  full_name?: string;
  role?: 'doctor' | 'user';
}

export interface AuthResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  user: User;
}

export interface TokenData {
  user_id: string;
  role: string;
  exp: number;
}

// Consultation Types
export interface ConsultationFormData {
  // Patient Identity
  patient_full_name: string;
  patient_reference_id?: string;

  // Demographics
  age: number;
  gender: 'male' | 'female' | 'other';
  
  // Medical History
  family_history_ad: boolean;
  diabetes: boolean;
  hypertension: boolean;
  heart_disease: boolean;
  stroke_history: boolean;
  smoking: boolean;
  alcohol_use: boolean;
  
  // Cognitive Symptoms (0-3 scale)
  memory_complaints: number;
  difficulty_concentrating: number;
  problem_solving_difficulty: number;
  mood_changes: number;
  confusion: number;
  personality_changes: number;
  disorientation: number;
  difficulty_with_daily_tasks: number;
  
  // Additional Information
  symptoms_duration_months: number;
  previous_ad_evaluation: boolean;
  current_medications?: string;
  notes?: string;
}

export interface ConsultationResponse {
  consultation_id: string;
  risk_score: number;
  message: string;
}

// MRI Upload Types
export interface MRIUploadResponse {
  mri_id: string;
  validation: {
    valid: boolean;
    message: string;
    details?: Record<string, any>;
  };
  file_path: string;
  message: string;
}

// Prediction Types
export type DiseaseClass = 
  | "No Alzheimer's Disease"
  | "Mild Cognitive Impairment"
  | "Early Stage Alzheimer's"
  | "Moderate Stage Alzheimer's";

export interface PredictionRequest {
  patient_id: string;
  patient_full_name: string;
  mri_image_id: string;
  consultation_id?: string;
  model_type?: string;
}

export interface PredictionResponse {
  _id: string;
  prediction_id: string;
  patient_id: string;
  patient_full_name: string;
  disease_class: DiseaseClass;
  probability: number;
  confidence: 'Very High' | 'High' | 'Moderate' | 'Low' | 'Very Low';
  factors: {
    image_analysis_weight: number;
    consultation_risk_score: number;
    final_confidence: number;
    contribution_image: number;
    contribution_consultation: number;
  };
  recommendations: string;
  model_used: string;
  created_at: string;
  doctor?: Doctor;
}

// Alias for backwards compatibility
export type Prediction = PredictionResponse;

// Model Types
export interface ModelConfig {
  epochs: number;
  learning_rate: number;
  batch_size: number;
}

export interface ModelMetrics {
  training_config: ModelConfig;
  epochs_completed: number;
  best_val_accuracy: number;
  best_val_loss: number;
  final_train_accuracy: number;
  final_val_accuracy: number;
  test_accuracy?: number;
  test_loss?: number;
}

export interface TrainedModel {
  _id: string;
  name: string;
  model_type: string;
  status: string;
  config?: {
    epochs?: number;
    learning_rate?: number;
    batch_size?: number;
    dataset_id?: string;
  };
  metrics?: any;
  error?: string;
  is_production: boolean;
  created_at: string;
  completed_at?: string;
  trained_by?: string;
  model_path?: string;
}

export interface TrainingRequest {
  model_type: 'efficientnet' | 'resnet';
  epochs: number;
  learning_rate: number;
  batch_size: number;
  dataset_id?: string;
}

export interface TrainingResponse {
  training_id: string;
  message: string;
  status: string;
  estimated_time: string;
}

// Dataset Types
export interface Dataset {
  _id: string;
  name: string;
  description: string;
  path: string;
  file_count: number;
  size_bytes: number;
  size_mb: number;
  uploaded_by: string;
  is_active: boolean;
  created_at: string;
}

// Dashboard Types
export interface DashboardStats {
  users: {
    total: number;
    active: number;
    admins: number;
    doctors: number;
    recent_registrations: number;
  };
  predictions: {
    total: number;
    today: number;
    by_class: Record<string, number>;
  };
  datasets: {
    total: number;
    total_size_mb: number;
  };
  models: {
    total: number;
    trained: number;
    production_model?: string;
  };
}

export interface ActivityItem {
  id: string;
  type: string;
  user_id?: string;
  patient_id?: string;
  result?: string;
  confidence?: number;
  timestamp: string;
}

// API Error Type
export interface ApiError {
  detail: string | ValidationError[];
  status_code?: number;
}

// Pydantic Validation Error
export interface ValidationError {
  type: string;
  loc: (string | number)[];
  msg: string;
  input: any;
  ctx?: {
    reason?: string;
    [key: string]: any;
  };
  url: string;
}

