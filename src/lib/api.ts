/**
 * API utilities for communicating with the CarthaNeuro backend
 */
import axios, { AxiosError, InternalAxiosRequestConfig, AxiosResponse } from 'axios';

// Type definitions
export interface ApiError {
  message: string;
  status?: number;
  field?: string;
}

export interface ModelInfo {
  name: string;
  type: string;
  status: string;
  device: string;
  num_classes: number;
  classes?: string[];
  loaded_at?: number;
  load_time?: number;
}

export interface KerasModelInfo {
  model_name: string;
  model_type: string;
  framework: string;
  size_mb: number;
  num_classes?: number;
  classes?: string[];
  created_at: number;
}

export interface HealthResponse {
  status: string;
  models_loaded: string[];
  uptime: string;
  memory_usage?: {
    system_memory_percent?: number;
    gpu_memory_allocated_gb?: number;
  };
}

export interface DatasetInfo {
  name?: string;
  path?: string;
  total_samples: number;
  classes?: string[];
  class_distribution: Record<string, number>;
  available_formats?: string[];
  last_updated?: string;
  status?: string;
}

// Create axios instance
const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to add auth token
api.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error: AxiosError) => {
    return Promise.reject(error);
  }
);

// Response interceptor to handle token refresh
api.interceptors.response.use(
  (response: AxiosResponse) => {
    return response;
  },
  async (error: AxiosError) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean };
    
    if (error.response?.status === 401 && originalRequest && !originalRequest._retry) {
      originalRequest._retry = true;
      
      try {
        const refreshToken = localStorage.getItem('refresh_token');
        if (refreshToken) {
          const response = await axios.post(
            `${process.env.NEXT_PUBLIC_BACKEND_URL}/api/v1/auth/refresh`,
            { refresh_token: refreshToken }
          );
          
          const { access_token } = response.data;
          localStorage.setItem('access_token', access_token);
          
          // Retry original request
          originalRequest.headers.Authorization = `Bearer ${access_token}`;
          return api(originalRequest);
        }
      } catch {
        // Refresh failed, redirect to login
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        localStorage.removeItem('user');
        window.location.href = '/login';
      }
    }
    
    return Promise.reject(error);
  }
);

// CarthaNeuro API class for frontend-backend communication
export class CarthaNeuroApi {
  private static async handleResponse<T>(response: AxiosResponse<T>): Promise<T> {
    return response.data;
  }

  private static async handleError(error: unknown): Promise<never> {
    if (axios.isAxiosError(error)) {
      // Handle validation errors from FastAPI/Pydantic
      if (error.response?.status === 422) {
        const detail = error.response?.data?.detail;
        if (Array.isArray(detail)) {
          // Format validation errors nicely
          const errorMessages = detail.map(err => {
            const field = err.loc?.[err.loc.length - 1] || 'unknown field';
            const message = err.msg || 'Validation error';
            return `${field}: ${message}`;
          });
          throw new Error(`Validation failed: ${errorMessages.join(', ')}`);
        } else if (typeof detail === 'string') {
          throw new Error(detail);
        }
      }
      
      const message = error.response?.data?.detail || error.response?.data?.message || error.message;
      throw new Error(message);
    }
    throw error instanceof Error ? error : new Error('Unknown error');
  }

  static async healthCheck(): Promise<HealthResponse> {
    try {
      const response = await api.get('/api/v1/health');
      return this.handleResponse(response);
    } catch (error) {
      return this.handleError(error);
    }
  }

  static async getModels(): Promise<ModelInfo[]> {
    try {
      const response = await api.get('/api/v1/models');
      return this.handleResponse(response);
    } catch (error) {
      return this.handleError(error);
    }
  }

  static async getKerasModels(): Promise<{ models: KerasModelInfo[] }> {
    try {
      const response = await api.get('/api/v1/keras/models');
      return this.handleResponse(response);
    } catch (error) {
      return this.handleError(error);
    }
  }

  static async getDatasetInfo(): Promise<DatasetInfo> {
    try {
      const response = await api.get('/api/v1/data/datasets');
      return this.handleResponse(response);
    } catch (error) {
      return this.handleError(error);
    }
  }

  static async reloadModels(modelTypes?: string[]): Promise<void> {
    try {
      const response = await api.post('/api/v1/models/reload', { model_types: modelTypes });
      return this.handleResponse(response);
    } catch (error) {
      return this.handleError(error);
    }
  }

  static async cleanupTempUploads(): Promise<void> {
    try {
      const response = await api.delete('/api/v1/data/cleanup');
      return this.handleResponse(response);
    } catch (error) {
      return this.handleError(error);
    }
  }

  static async trainModel(data: {
    model_type: string;
    architecture: string;
    num_epochs: number;
    batch_size: number;
    learning_rate: number;
    validation_split: number;
    device?: string;
    model_name?: string;
    save_after_training?: boolean;
  }): Promise<any> {
    try {
      const response = await api.post('/api/v1/train', data);
      return this.handleResponse(response);
    } catch (error) {
      return this.handleError(error);
    }
  }

  // Training job tracking endpoints
  static async getTrainingJobs(status?: string, limit = 50, offset = 0): Promise<any> {
    try {
      const params: any = { limit, offset };
      if (status) params.status = status;
      
      const response = await api.get('/api/v1/training/jobs', { params });
      return this.handleResponse(response);
    } catch (error) {
      return this.handleError(error);
    }
  }

  static async getTrainingJob(jobId: string): Promise<any> {
    try {
      const response = await api.get(`/api/v1/training/jobs/${jobId}`);
      return this.handleResponse(response);
    } catch (error) {
      return this.handleError(error);
    }
  }

  static async deleteTrainingJob(jobId: string): Promise<any> {
    try {
      const response = await api.delete(`/api/v1/training/jobs/${jobId}`);
      return this.handleResponse(response);
    } catch (error) {
      return this.handleError(error);
    }
  }

  // Server-Sent Events for real-time progress
  static createTrainingProgressStream(jobId: string): EventSource {
    const token = localStorage.getItem('access_token');
    const baseURL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000';
    const url = `${baseURL}/api/v1/training/stream/${jobId}`;
    
    // Create EventSource with headers (note: EventSource doesn't support custom headers directly)
    // We'll need to pass the token as a query parameter for this implementation
    const tokenUrl = token ? `${url}?token=${token}` : url;
    return new EventSource(tokenUrl);
  }

  static async trainKerasModel(data: {
    model_name: string;
    model_type: string;
    epochs: number;
    batch_size: number;
    validation_split: number;
    learning_rate: number;
    device?: string;
  }): Promise<any> {
    try {
      const response = await api.post('/api/v1/keras/train', data);
      return this.handleResponse(response);
    } catch (error) {
      return this.handleError(error);
    }
  }

  static async predict(data: {
    image: File;
    patientContext?: string;
    modelType?: string;
    modelName?: string;
    useLlm?: boolean;
  }): Promise<any> {
    try {
      const formData = new FormData();
      formData.append('image', data.image);
      
      if (data.patientContext) {
        formData.append('patient_context', data.patientContext);
      }
      
      if (data.modelType) {
        formData.append('model_type', data.modelType);
      }
      
      if (data.modelName) {
        formData.append('model_name', data.modelName);
      }
      
      if (data.useLlm !== undefined) {
        formData.append('use_llm', data.useLlm.toString());
      }
      
      const response = await api.post('/api/v1/predict', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      return this.handleResponse(response);
    } catch (error) {
      return this.handleError(error);
    }
  }

  static async loadKerasModel(model_path: string, model_name?: string): Promise<any> {
    try {
      const formData = new FormData();
      formData.append('model_path', model_path);
      if (model_name) {
        formData.append('model_name', model_name);
      }
      
      const response = await api.post('/api/v1/keras/load', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      return this.handleResponse(response);
    } catch (error) {
      return this.handleError(error);
    }
  }

  static async saveKerasModel(data: {
    model_name: string;
    save_path?: string;
    metadata?: any;
    create_if_missing?: boolean;
  }): Promise<any> {
    try {
      const formData = new FormData();
      formData.append('model_name', data.model_name);
      
      if (data.save_path) {
        formData.append('save_path', data.save_path);
      }
      
      if (data.metadata) {
        // Convert metadata object to JSON string as expected by backend
        formData.append('metadata', JSON.stringify(data.metadata));
      }
      
      if (data.create_if_missing !== undefined) {
        formData.append('create_if_missing', data.create_if_missing.toString());
      }
      
      const response = await api.post('/api/v1/keras/save', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      return this.handleResponse(response);
    } catch (error) {
      return this.handleError(error);
    }
  }

  static async getKPI(): Promise<any> {
    try {
      const response = await api.get('/api/v1/kpi');
      return this.handleResponse(response);
    } catch (error) {
      return this.handleError(error);
    }
  }

  static async kerasPredict(file: any, model_name?: string): Promise<any> {
    try {
      const formData = new FormData();
      formData.append('file', file);
      if (model_name) {
        formData.append('model_name', model_name);
      }
      
      const response = await api.post('/api/v1/keras/predict', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      return this.handleResponse(response);
    } catch (error) {
      return this.handleError(error);
    }
  }

  // Metrics API endpoints
  static async getModelMetrics(modelName: string, includeHistory = true, includeReport = true): Promise<any> {
    try {
      const response = await api.get(`/api/v1/metrics/${modelName}`, {
        params: { include_history: includeHistory, include_report: includeReport }
      });
      return this.handleResponse(response);
    } catch (error) {
      return this.handleError(error);
    }
  }

  // Fast metrics fetch with shorter timeout for auto-fetch scenarios
  static async getModelMetricsQuick(modelName: string, includeHistory = true, includeReport = true): Promise<any> {
    try {
      const response = await api.get(`/api/v1/metrics/${modelName}`, {
        params: { include_history: includeHistory, include_report: includeReport },
        timeout: 3000 // Shorter timeout for quick fetch
      });
      return this.handleResponse(response);
    } catch (error) {
      // Don't throw error for timeout, just return null to trigger fallback
      if (axios.isAxiosError(error) && error.code === 'ECONNABORTED') {
        return null;
      }
      return this.handleError(error);
    }
  }



  static async compareModels(modelNames: string[], metricsToCompare: string[], comparisonName?: string): Promise<any> {
    try {
      const response = await api.post('/api/v1/metrics/compare', {
        model_names: modelNames,
        metrics_to_compare: metricsToCompare,
        comparison_name: comparisonName
      });
      return this.handleResponse(response);
    } catch (error) {
      return this.handleError(error);
    }
  }

  static async getBestModel(metric: string, ascending = false, framework?: string): Promise<any> {
    try {
      const params: any = { metric, ascending };
      if (framework) params.framework = framework;
      
      const response = await api.get('/api/v1/metrics/models/best', { params });
      return this.handleResponse(response);
    } catch (error) {
      return this.handleError(error);
    }
  }

  static async getModelPerformanceReport(modelName: string): Promise<any> {
    try {
      const response = await api.get(`/api/v1/metrics/reports/${modelName}`);
      return this.handleResponse(response);
    } catch (error) {
      return this.handleError(error);
    }
  }

  static async saveModelWithMetrics(modelName: string, savePath?: string, metadata?: any, overwrite = false): Promise<any> {
    try {
      const response = await api.post('/api/v1/metrics/models/save', {
        model_name: modelName,
        save_path: savePath,
        metadata: metadata || {},
        overwrite
      });
      return this.handleResponse(response);
    } catch (error) {
      return this.handleError(error);
    }
  }

  static async cleanupOldMetrics(daysToKeep = 30): Promise<any> {
    try {
      const response = await api.delete('/api/v1/metrics/cleanup', {
        params: { days_to_keep: daysToKeep }
      });
      return this.handleResponse(response);
    } catch (error) {
      return this.handleError(error);
    }
  }

  static async getDashboardMetrics(): Promise<any> {
    try {
      const response = await api.get('/api/v1/metrics/dashboard');
      return this.handleResponse(response);
    } catch (error) {
      return this.handleError(error);
    }
  }

  // Admin API endpoints for enhanced model management
  static async getAutoSavedModels(): Promise<any> {
    try {
      const response = await api.get('/api/v1/admin/models/auto-saved');
      return this.handleResponse(response);
    } catch (error) {
      return this.handleError(error);
    }
  }

  static async pushModelToCloud(data: {
    model_name: string;
    user_id: string;
    push_metadata?: any;
    confirm: boolean;
  }): Promise<any> {
    try {
      const response = await api.post('/api/v1/admin/models/push-to-cloud', data);
      return this.handleResponse(response);
    } catch (error) {
      return this.handleError(error);
    }
  }

  static async cleanupAutoSavedModels(): Promise<any> {
    try {
      const response = await api.delete('/api/v1/admin/models/cleanup-auto-saved');
      return this.handleResponse(response);
    } catch (error) {
      return this.handleError(error);
    }
  }

  static async getModelsSummary(): Promise<any> {
    try {
      const response = await api.get('/api/v1/admin/models/summary');
      return this.handleResponse(response);
    } catch (error) {
      return this.handleError(error);
    }
  }

  static async adminHealthCheck(): Promise<any> {
    try {
      const response = await api.get('/api/v1/admin/health');
      return this.handleResponse(response);
    } catch (error) {
      return this.handleError(error);
    }
  }
}

export { api };
export default api;
