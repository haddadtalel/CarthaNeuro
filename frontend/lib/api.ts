import axios, { AxiosInstance, AxiosError } from 'axios';
import type { ApiError } from '@/types';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001/api';

class ApiClient {
  private client: AxiosInstance;
  private static instance: ApiClient;

  private constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      headers: {
        'Content-Type': 'application/json',
      },
      timeout: 30000,
    });

    // Request interceptor to add auth token
    this.client.interceptors.request.use(
      (config) => {
        const token = typeof window !== 'undefined' ? localStorage.getItem('access_token') : null;
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error) => {
        return Promise.reject(error);
      }
    );

    // Response interceptor for error handling
    this.client.interceptors.response.use(
      (response) => response,
      (error: AxiosError<ApiError>) => {
        if (error.response?.status === 401) {
          // Token expired or invalid - try to refresh
          if (typeof window !== 'undefined') {
            localStorage.removeItem('access_token');
            localStorage.removeItem('user');
            window.location.href = '/login';
          }
        }
        return Promise.reject(error);
      }
    );
  }

  public static getInstance(): ApiClient {
    if (!ApiClient.instance) {
      ApiClient.instance = new ApiClient();
    }
    return ApiClient.instance;
  }

  // Auth endpoints
  async login(username: string, password: string) {
    const formData = new URLSearchParams();
    formData.append('username', username);
    formData.append('password', password);
    
    return this.client.post('/auth/login', formData, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    });
  }

  async register(data: {
    email: string;
    username: string;
    password: string;
    full_name?: string;
    role?: string;
  }) {
    return this.client.post('/auth/register', data);
  }

  async getCurrentUser() {
    return this.client.get('/auth/me');
  }

  async refreshToken(refreshToken: string) {
    return this.client.post('/auth/token/refresh', { refresh_token: refreshToken });
  }

  // User endpoints
  async getUsers(params?: { skip?: number; limit?: number; role?: string }) {
    return this.client.get('/users', { params });
  }

  async getUser(userId: string) {
    return this.client.get(`/users/${userId}`);
  }

  async createUser(data: {
    username: string;
    email: string;
    full_name?: string;
    password?: string;
    role?: string;
    is_active?: boolean;
  }) {
    return this.client.post('/users', data);
  }

  async updateUser(userId: string, data: any) {
    return this.client.put(`/users/${userId}`, data);
  }

  async deleteUser(userId: string) {
    return this.client.delete(`/users/${userId}`);
  }

  async activateUser(userId: string) {
    return this.client.post(`/users/${userId}/activate`);
  }

  async getUserStats() {
    return this.client.get('/users/count/stats');
  }

  // Prediction endpoints
  async createConsultation(data: any) {
    return this.client.post('/predictions/consultation', data);
  }

  async getConsultation(consultationId: string) {
    return this.client.get(`/predictions/consultation/${consultationId}`);
  }

  async uploadMRI(file: File, patientId: string, consultationId?: string) {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('patient_id', patientId);
    if (consultationId) {
      formData.append('consultation_id', consultationId);
    }

    return this.client.post('/predictions/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  }

  async createPrediction(data: {
    patient_id: string;
    mri_image_id: string;
    consultation_id?: string;
    model_type?: string;
  }) {
    return this.client.post('/predictions/predict', data);
  }

  async getPrediction(predictionId: string) {
    return this.client.get(`/predictions/results/${predictionId}`);
  }

  async getPatientPredictions(patientId: string, limit?: number) {
    return this.client.get(`/predictions/patient/${patientId}`, { params: { limit } });
  }

  async getPredictionHistory(skip?: number, limit?: number) {
    return this.client.get('/predictions/history', { params: { skip, limit } });
  }

  async getPredictionStats() {
    return this.client.get('/predictions/stats');
  }

  async downloadReport(predictionId: string): Promise<Blob> {
    const token = typeof window !== 'undefined' ? localStorage.getItem('access_token') : null;
    const response = await fetch(`${API_BASE_URL}/predictions/report/${predictionId}`, {
      headers: {
        'Authorization': token ? `Bearer ${token}` : '',
      },
    });
    
    if (!response.ok) {
      throw new Error('Failed to download report');
    }
    
    return response.blob();
  }

  // Model endpoints
  async getModels(skip?: number, limit?: number) {
    return this.client.get('/models', { params: { skip, limit } });
  }

  async getProductionModel() {
    return this.client.get('/models/production');
  }

  async setProductionModel(modelId: string) {
    // Validate modelId before sending
    if (!modelId || modelId === 'undefined' || modelId === 'null') {
      console.error('Invalid modelId passed to setProductionModel:', modelId);
      throw new Error('Invalid model ID: ' + modelId);
    }
    console.log('Calling set-production API with modelId:', modelId);
    return this.client.post(`/models/set-production/${modelId}`);
  }

  async trainModel(data: {
    model_type: string;
    epochs: number;
    learning_rate: number;
    batch_size: number;
    dataset_id?: string;
    model_name?: string;
  }) {
    // Send as JSON to ensure proper type handling
    return this.client.post('/models/train', {
      model_type: data.model_type,
      epochs: Number(data.epochs),
      learning_rate: Number(data.learning_rate),
      batch_size: Number(data.batch_size),
      dataset_id: data.dataset_id || null,
      model_name: data.model_name || null,
    });
  }


  async getTrainingStatus(trainingId: string) {
    return this.client.get(`/models/training/${trainingId}`);
  }

  async getModelDetails(modelId: string) {
    return this.client.get(`/models/${modelId}`);
  }

  async deleteModel(modelId: string) {
    return this.client.delete(`/models/${modelId}`);
  }

  async getModelMetrics(modelId: string) {
    return this.client.get(`/models/${modelId}/metrics`);
  }

  async importModel(data: {
    name: string;
    model_type: string;
    model_path: string;
    config?: Record<string, any>;
    metrics?: Record<string, any>;
  }) {
    return this.client.post('/models/import', data);
  }

  // Dataset endpoints
  async getDatasets(skip?: number, limit?: number) {
    return this.client.get('/datasets', { params: { skip, limit } });
  }

  async uploadDataset(formData: FormData) {
    return this.client.post('/datasets/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    });
  }

  async getDatasetDetails(datasetId: string) {
    return this.client.get(`/datasets/${datasetId}`);
  }

  async deleteDataset(datasetId: string) {
    return this.client.delete(`/datasets/${datasetId}`);
  }

  async getDatasetPreview(datasetId: string) {
    return this.client.get(`/datasets/${datasetId}/preview`);
  }

  // Admin endpoints
  async getDashboardStats() {
    return this.client.get('/admin/dashboard');
  }

  async getRecentActivity(limit?: number) {
    return this.client.get('/admin/activity', { params: { limit } });
  }

  async getSystemHealth() {
    return this.client.get('/admin/system-health');
  }

  async getUserActivity(userId?: string, limit?: number) {
    return this.client.get('/admin/users/activity', { params: { user_id: userId, limit } });
  }

  async getPredictionsAnalysis(startDate?: string, endDate?: string) {
    return this.client.get('/admin/predictions/analysis', { params: { start_date: startDate, end_date: endDate } });
  }

  async getPredictionsAdmin(skip?: number, limit?: number) {
    return this.client.get('/admin/predictions', { params: { skip, limit } });
  }
}

export const api = ApiClient.getInstance();
export default api;

