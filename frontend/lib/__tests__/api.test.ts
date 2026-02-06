/**
 * Frontend API client tests
 */

import { api } from '../lib/api';

// Mock the API client methods for testing
describe('API Client', () => {
  // Mock fetch
  global.fetch = jest.fn();
  
  beforeEach(() => {
    jest.clearAllMocks();
  });
  
  afterEach(() => {
    // Clear auth storage
    localStorage.clear();
  });

  describe('Authentication', () => {
    test('login should return tokens on success', async () => {
      const mockResponse = {
        access_token: 'test_token',
        token_type: 'bearer',
      };
      
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockResponse),
      });

      const result = await api.login('testuser', 'password123');
      
      expect(result.data).toEqual(mockResponse);
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/auth/login'),
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify({ username: 'testuser', password: 'password123' }),
        })
      );
    });

    test('login should throw on failure', async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: false,
        json: () => Promise.resolve({ detail: 'Invalid credentials' }),
      });

      await expect(api.login('testuser', 'wrongpassword')).rejects.toThrow();
    });

    test('register should create new user', async () => {
      const mockUser = {
        email: 'new@example.com',
        username: 'newuser',
        full_name: 'New User',
      };
      
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockUser),
      });

      const result = await api.register({
        email: 'new@example.com',
        username: 'newuser',
        password: 'password123',
        full_name: 'New User',
      });
      
      expect(result.data).toEqual(mockUser);
    });
  });

  describe('Predictions', () => {
    test('createConsultation should send correct data', async () => {
      const consultationData = {
        patient_id: 'patient_001',
        age: 65,
        gender: 'male',
        symptoms: ['memory_loss'],
        duration_months: 12,
        family_history: true,
        lifestyle_factors: { smoking: false, alcohol: false },
        medical_history: { diabetes: false, hypertension: true },
      };

      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ consultation_id: '123' }),
      });

      await api.createConsultation(consultationData);
      
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/predictions/consultation'),
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify(consultationData),
        })
      );
    });

    test('getPrediction should return result', async () => {
      const mockResult = {
        disease_class: "No Alzheimer's Disease",
        probability: 0.85,
        confidence: 'High',
      };

      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockResult),
      });

      const result = await api.getPrediction('result_123');
      
      expect(result.data).toEqual(mockResult);
    });
  });

  describe('Users', () => {
    test('getUsers should return paginated users', async () => {
      const mockResponse = {
        users: [
          { _id: '1', username: 'user1', email: 'user1@test.com' },
          { _id: '2', username: 'user2', email: 'user2@test.com' },
        ],
        total_pages: 5,
      };

      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockResponse),
      });

      const result = await api.getUsers(0, 10);
      
      expect(result.data).toEqual(mockResponse);
    });

    test('updateUser should send update request', async () => {
      const updateData = { full_name: 'Updated Name', role: 'doctor' };

      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ ...updateData, _id: 'user_123' }),
      });

      await api.updateUser('user_123', updateData);
      
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/users/user_123'),
        expect.objectContaining({
          method: 'PUT',
          body: JSON.stringify(updateData),
        })
      );
    });

    test('deleteUser should send delete request', async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ message: 'User deleted' }),
      });

      await api.deleteUser('user_123');
      
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/users/user_123'),
        expect.objectContaining({ method: 'DELETE' })
      );
    });
  });

  describe('Models', () => {
    test('trainModel should start training', async () => {
      const trainingConfig = {
        model_type: 'efficientnet',
        epochs: 10,
        learning_rate: 0.001,
        batch_size: 32,
        model_name: 'test_model',
      };

      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ training_id: 'train_123', status: 'started' }),
      });

      await api.trainModel(trainingConfig);
      
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/models/train'),
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify(trainingConfig),
        })
      );
    });

    test('setProductionModel should update model status', async () => {
      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ message: 'Production model updated' }),
      });

      await api.setProductionModel('model_123');
      
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/models/model_123/set-production'),
        expect.objectContaining({ method: 'POST' })
      );
    });
  });

  describe('Datasets', () => {
    test('uploadDataset should upload file', async () => {
      const formData = new FormData();
      formData.append('name', 'Test Dataset');
      formData.append('file', new Blob(['test'], { type: 'application/zip' }));

      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve({ message: 'Dataset uploaded' }),
      });

      await api.uploadDataset(formData);
      
      expect(global.fetch).toHaveBeenCalledWith(
        expect.stringContaining('/datasets/upload'),
        expect.objectContaining({
          method: 'POST',
          body: formData,
        })
      );
    });
  });

  describe('Admin', () => {
    test('getDashboardStats should return stats', async () => {
      const mockStats = {
        users: { total: 100, admins: 5, doctors: 20 },
        predictions: { total: 500, today: 25, by_class: {} },
        models: { trained: 10, production_model: 'efficientnet_demo' },
        datasets: { total: 5, total_size_mb: 1500 },
      };

      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockStats),
      });

      const result = await api.getDashboardStats();
      
      expect(result.data).toEqual(mockStats);
    });

    test('getRecentActivity should return activity list', async () => {
      const mockActivity = {
        activity: [
          { id: '1', type: 'prediction', result: 'No AD', patient_id: 'patient_001' },
        ],
      };

      (global.fetch as jest.Mock).mockResolvedValueOnce({
        ok: true,
        json: () => Promise.resolve(mockActivity),
      });

      const result = await api.getRecentActivity(10);
      
      expect(result.data).toEqual(mockActivity);
    });
  });
});

