'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Play, Settings, Check, X, Loader2, Cpu, Eye } from 'lucide-react';
import { api } from '@/lib/api';
import { isAuthenticated, isAdmin, logout } from '@/lib/auth';
import { Card, Button, Input, Modal, Alert } from '@/components';

interface Dataset {
  _id: string;
  name: string;
  classes: string[];
  class_distribution: Record<string, number>;
  image_count: number;
  status: string;
}

interface TrainedModel {
  id: string;
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
  metrics: {
    test_accuracy?: number;
    final_val_accuracy?: number;
    class_mapping?: Record<string, number>;
  };
  is_production: boolean;
  created_at: string;
}

export default function AdminModelsPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(true);
  const [models, setModels] = useState<TrainedModel[]>([]);
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [showTrainModal, setShowTrainModal] = useState(false);
  const [training, setTraining] = useState(false);
  const [trainingProgress, setTrainingProgress] = useState(0);
  const [trainingLogs, setTrainingLogs] = useState<string[]>([]);
  const [toast, setToast] = useState<{ message: string; type: 'success' | 'error' } | null>(null);
  const [config, setConfig] = useState({
    model_type: 'efficientnet',
    epochs: 10,
    learning_rate: 0.001,
    batch_size: 32,
    model_name: '',
    dataset_id: '',
  });
  const [error, setError] = useState<string | null>(null);
  const [selectedModel, setSelectedModel] = useState<TrainedModel | null>(null);
  const [showDetailsModal, setShowDetailsModal] = useState(false);
  const [modelMetrics, setModelMetrics] = useState<any>(null);
  const [loadingMetrics, setLoadingMetrics] = useState(false);

  useEffect(() => {
    if (!isAuthenticated() || !isAdmin()) {
      router.push(isAuthenticated() ? '/consultation' : '/login');
      return;
    }
    fetchModels();
    fetchDatasets();
  }, [router]);

  const fetchModels = async () => {
    try {
      const response = await api.getModels(0, 20);
      const data = response.data as any;
      console.log('=== RAW API RESPONSE ===');
      console.log('response.data:', JSON.stringify(data, null, 2));
      
      let modelsData = Array.isArray(data) ? data : (data.models || []);
      console.log('modelsData after extraction:', JSON.stringify(modelsData, null, 2));
      
      // Normalize model data to ensure id and _id are both present
      modelsData = modelsData.map((model: any) => {
        console.log('Processing model:', JSON.stringify(model, null, 2));
        // If model has _id but no id, copy _id to id
        if (model._id && !model.id) {
          model.id = model._id;
        }
        // If model has id but no _id, copy id to _id
        if (model.id && !model._id) {
          model._id = model.id;
        }
        return model;
      });
      
      console.log('Final modelsData:', JSON.stringify(modelsData, null, 2));
      setModels(modelsData);
    } catch (err) {
      console.error('Failed to fetch models:', err);
    } finally {
      setLoading(false);
    }
  };

  const fetchDatasets = async () => {
    try {
      const response = await api.getDatasets(0, 50);
      const datasetsData = (response.data as any).datasets || [];
      // Only show ready datasets
      const readyDatasets = datasetsData.filter((d: Dataset) => d.status === 'ready');
      setDatasets(readyDatasets);
    } catch (err) {
      console.error('Failed to fetch datasets');
    }
  };

  const showToast = (message: string, type: 'success' | 'error') => {
    setToast({ message, type });
    setTimeout(() => setToast(null), 3000);
  };

  const handleTrain = async () => {
    if (!config.model_name.trim()) {
      setError('Model name is required');
      return;
    }

    setTraining(true);
    setTrainingProgress(0);
    setTrainingLogs(['Starting training...']);

    try {
      console.log('Starting training with config:', config);
      const response = await api.trainModel(config);
      const data = response.data as any;
      console.log('Training response:', data);
      
      if (data.training_id) {
        // Poll for training status
        pollTrainingStatus(data.training_id);
      } else {
        showToast('Training started successfully', 'success');
        setShowTrainModal(false);
        fetchModels();
        setTraining(false);
      }
    } catch (err: any) {
      console.error('Training error:', err);
      console.error('Error response:', err.response?.data);
      showToast(err.response?.data?.detail || err.response?.data?.message || 'Training failed. Check console for details.', 'error');
      setTraining(false);
    }
  };

  const pollTrainingStatus = async (trainingId: string) => {
    const maxAttempts = 60;
    let attempts = 0;

    const poll = async () => {
      try {
        const response = await api.getTrainingStatus(trainingId);
        const data = response.data as any;

        if (data.status === 'completed') {
          setTrainingProgress(100);
          setTrainingLogs(prev => [...prev, 'Training completed!']);
          showToast('Model trained successfully', 'success');
          setShowTrainModal(false);
          setTraining(false);
          fetchModels();
        } else if (data.status === 'failed') {
          setTrainingLogs(prev => [...prev, `Training failed: ${data.error || 'Unknown error'}`]);
          showToast('Training failed', 'error');
          setTraining(false);
        } else {
          setTrainingProgress(data.progress || 0);
          if (data.logs) {
            setTrainingLogs(prev => [...prev, ...data.logs]);
          }
          attempts++;
          if (attempts < maxAttempts) {
            setTimeout(poll, 5000);
          } else {
            showToast('Training timed out', 'error');
            setTraining(false);
          }
        }
      } catch (err) {
        attempts++;
        if (attempts < maxAttempts) {
          setTimeout(poll, 5000);
        } else {
          showToast('Failed to get training status', 'error');
          setTraining(false);
        }
      }
    };

    poll();
  };

  const handleSetProductionModel = (model: TrainedModel) => {
    // Directly use _id which is always present from MongoDB
    const modelId = String(model._id);
    console.log('handleSetProductionModel called with:', modelId);
    if (modelId && modelId !== 'undefined') {
      setProductionModelById(modelId);
    } else {
      console.error('Model ID is undefined for model:', model);
      alert('Error: Model ID is undefined');
    }
  };

  const setProductionModelById = async (modelId: string) => {
    try {
      await api.setProductionModel(modelId);
      showToast('Production model updated', 'success');
      fetchModels();
    } catch (err: any) {
      showToast(err.response?.data?.detail || 'Failed to set production model', 'error');
    }
  };

  const deleteModel = async (modelId: string) => {
    try {
      await api.deleteModel(modelId);
      showToast('Model deleted', 'success');
      fetchModels();
    } catch (err: any) {
      showToast(err.response?.data?.detail || 'Failed to delete model', 'error');
    }
  };

  const viewModelDetails = async (model: TrainedModel) => {
    setSelectedModel(model);
    setShowDetailsModal(true);
    setLoadingMetrics(true);

    try {
      // Safely get model ID - use 'id' or '_id' or the model's _id property
      const modelId = model.id || model._id || (model as any)._id;
      console.log('Fetching metrics for model:', modelId);
      
      if (!modelId || modelId === 'undefined') {
        throw new Error('Model ID is undefined');
      }
      
      const response = await api.getModelMetrics(modelId);
      setModelMetrics(response.data);
    } catch (err: any) {
      console.error('Failed to fetch model metrics:', err);
      setModelMetrics(null);
    } finally {
      setLoadingMetrics(false);
    }
  };

  const handleLogout = () => {
    logout();
    router.push('/login');
  };

  return (
    <div className="min-h-screen bg-gray-50 flex">
      <aside className="w-64 bg-white border-r border-gray-200 min-h-screen">
        <div className="p-4 border-b border-gray-100">
          <div className="flex items-center gap-2">
            <span className="text-xl font-bold text-medical">Cartha</span>
            <span className="text-xl font-bold text-gray-900">Neuro</span>
          </div>
          <p className="text-xs text-gray-500 mt-1">Admin Panel</p>
        </div>

        <nav className="p-4 space-y-1">
          <button onClick={() => router.push('/admin/dashboard')} className="w-full flex items-center gap-3 px-4 py-3 rounded-lg text-gray-600 hover:bg-gray-100">Dashboard</button>
          <button onClick={() => router.push('/admin/users')} className="w-full flex items-center gap-3 px-4 py-3 rounded-lg text-gray-600 hover:bg-gray-100">Users</button>
          <button onClick={() => router.push('/admin/predictions')} className="w-full flex items-center gap-3 px-4 py-3 rounded-lg text-gray-600 hover:bg-gray-100">Predictions</button>
          <button className="w-full flex items-center gap-3 px-4 py-3 rounded-lg bg-medical text-white">Models</button>
          <button onClick={() => router.push('/admin/datasets')} className="w-full flex items-center gap-3 px-4 py-3 rounded-lg text-gray-600 hover:bg-gray-100">Datasets</button>
        </nav>

        <div className="p-4 border-t border-gray-100 mt-auto">
          <button onClick={handleLogout} className="w-full flex items-center gap-3 px-4 py-3 text-red-600 hover:bg-red-50 rounded-lg">Logout</button>
        </div>
      </aside>

      <main className="flex-1 p-8">
        {toast && (
          <div className={`fixed top-4 right-4 px-4 py-2 rounded-lg text-white z-50 ${toast.type === 'success' ? 'bg-green-600' : 'bg-red-600'}`}>
            {toast.message}
          </div>
        )}

        <div className="flex justify-between items-center mb-6">
          <h1 className="text-2xl font-bold text-gray-900">AI Models</h1>
          <Button onClick={() => setShowTrainModal(true)} icon={<Play className="w-4 h-4" />}>
            Train New Model
          </Button>
        </div>

        {loading ? (
          <div className="flex items-center justify-center py-12">
            <Loader2 className="w-8 h-8 animate-spin text-medical" />
          </div>
        ) : (
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
            {models.map((model) => (
              <Card key={model._id} hover>
                <div className="flex justify-between items-start mb-3">
                  <div className="flex items-center gap-2">
                    <Cpu className="w-5 h-5 text-medical" />
                    <h3 className="font-semibold text-gray-900">{model.name}</h3>
                  </div>
                  {model.is_production && (
                    <span className="px-2 py-1 bg-green-100 text-green-800 text-xs rounded-full">Production</span>
                  )}
                </div>
                
                <div className="space-y-2 text-sm">
                  <div className="flex justify-between">
                    <span className="text-gray-500">Type</span>
                    <span className="capitalize">{model.model_type}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-500">Status</span>
                    <span className={`px-2 py-0.5 rounded-full text-xs ${
                      model.status === 'completed' ? 'bg-green-100 text-green-800' :
                      model.status === 'training' ? 'bg-blue-100 text-blue-800' :
                      model.status === 'failed' ? 'bg-red-100 text-red-800' :
                      'bg-gray-100 text-gray-800'
                    }`}>
                      {model.status}
                    </span>
                  </div>
                  {model.metrics && (
                    <div className="flex justify-between">
                      <span className="text-gray-500">Accuracy</span>
                      <span className="text-medical font-medium">
                        {((model.metrics.test_accuracy ?? model.metrics.final_val_accuracy ?? 0) * 100).toFixed(1)}%
                      </span>
                    </div>
                  )}
                  <div className="flex justify-between">
                    <span className="text-gray-500">Created</span>
                    <span>{new Date(model.created_at).toLocaleDateString()}</span>
                  </div>
                </div>

                <div className="mt-4 pt-4 border-t border-gray-100 flex gap-2">
                  <Button size="sm" variant="secondary" onClick={() => viewModelDetails(model)}>
                    <Eye className="w-4 h-4" />
                  </Button>
                  {!model.is_production && model.status === 'completed' && (
                    <Button size="sm" variant="secondary" onClick={() => handleSetProductionModel(model)}>
                      Set Production
                    </Button>
                  )}
                  <Button size="sm" variant="danger" onClick={() => {
                      const actualModelId = model.id || model._id || (model as any)['_id'];
                      if (actualModelId && actualModelId !== 'undefined') {
                        deleteModel(actualModelId);
                      }
                    }}>Delete</Button>
                </div>
              </Card>
            ))}
          </div>
        )}
      </main>

      {/* Train Model Modal */}
      <Modal isOpen={showTrainModal} onClose={() => !training && setShowTrainModal(false)} title="Train New Model" size="lg">
        {training ? (
          <div className="space-y-4">
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div 
                className="bg-medical h-2 rounded-full transition-all duration-300" 
                style={{ width: `${trainingProgress}%` }}
              />
            </div>
            <p className="text-center text-gray-600">Training Progress: {trainingProgress}%</p>
            <div className="bg-gray-900 text-green-400 p-4 rounded-lg font-mono text-sm max-h-48 overflow-y-auto">
              {trainingLogs.map((log, i) => (
                <div key={i}>{log}</div>
              ))}
            </div>
          </div>
        ) : (
          <form onSubmit={(e) => { e.preventDefault(); handleTrain(); }}>
            {error && <Alert type="error">{error}</Alert>}
            
            <div className="space-y-4">
              <Input
                label="Model Name"
                value={config.model_name}
                onChange={(e: React.ChangeEvent<HTMLInputElement>) => setConfig({ ...config, model_name: e.target.value })}
                placeholder="e.g., efficientnet_v2"
                required
              />

              {datasets.length > 0 && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Training Dataset (Optional)</label>
                  <select
                    value={config.dataset_id}
                    onChange={(e: React.ChangeEvent<HTMLSelectElement>) => setConfig({ ...config, dataset_id: e.target.value })}
                    className="w-full rounded-lg border border-gray-300 px-4 py-2 focus:outline-none focus:ring-2 focus:ring-medical"
                  >
                    <option value="">Use synthetic data (demo mode)</option>
                    {datasets.map((dataset) => (
                      <option key={dataset._id} value={dataset._id}>
                        {dataset.name} ({dataset.image_count} images, {dataset.classes?.length || 0} classes)
                      </option>
                    ))}
                  </select>
                  <p className="text-xs text-gray-500 mt-1">Select a dataset to train on real data, or leave empty for demo mode</p>
                </div>
              )}

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Model Architecture</label>
                <select
                  value={config.model_type}
                  onChange={(e: React.ChangeEvent<HTMLSelectElement>) => setConfig({ ...config, model_type: e.target.value })}
                  className="w-full rounded-lg border border-gray-300 px-4 py-2 focus:outline-none focus:ring-2 focus:ring-medical"
                >
                  <option value="efficientnet">EfficientNet-B0</option>
                  <option value="resnet">ResNet50</option>
                </select>
              </div>

              <div className="grid grid-cols-3 gap-4">
                <Input
                  label="Epochs"
                  type="number"
                  value={config.epochs}
                  onChange={(e: React.ChangeEvent<HTMLInputElement>) => setConfig({ ...config, epochs: parseInt(e.target.value) || 1 })}
                  min="1"
                  max="100"
                />
                <Input
                  label="Learning Rate"
                  type="number"
                  step="0.0001"
                  value={config.learning_rate}
                  onChange={(e: React.ChangeEvent<HTMLInputElement>) => setConfig({ ...config, learning_rate: parseFloat(e.target.value) || 0.001 })}
                />
                <Input
                  label="Batch Size"
                  type="number"
                  value={config.batch_size}
                  onChange={(e: React.ChangeEvent<HTMLInputElement>) => setConfig({ ...config, batch_size: parseInt(e.target.value) || 32 })}
                  min="8"
                  max="128"
                />
              </div>

              <Alert type="info">
                {config.dataset_id
                  ? `Training on ${datasets.find(d => d._id === config.dataset_id)?.name || 'selected dataset'}. This may take several hours.`
                  : 'Training in demo mode with synthetic data. For real MRI classification, select a dataset above.'}
              </Alert>
            </div>

            <div className="mt-6 flex justify-end gap-3">
              <Button type="button" variant="secondary" onClick={() => setShowTrainModal(false)}>Cancel</Button>
              <Button type="submit" icon={<Play className="w-4 h-4" />}>Start Training</Button>
            </div>
          </form>
        )}
      </Modal>

      {/* Model Details Modal */}
      <Modal isOpen={showDetailsModal} onClose={() => setShowDetailsModal(false)} title="Model Details" size="lg">
        {selectedModel && (
          <div className="space-y-6">
            {/* Model Header */}
            <div className="flex items-center gap-3">
              <div className="w-12 h-12 bg-medical/10 rounded-lg flex items-center justify-center">
                <Cpu className="w-6 h-6 text-medical" />
              </div>
              <div>
                <h3 className="text-lg font-semibold">{selectedModel.name}</h3>
                <p className="text-gray-600 capitalize">{selectedModel.model_type} Model</p>
              </div>
            </div>

            {/* Training Configuration */}
            {selectedModel.config && (
              <div>
                <h4 className="font-medium mb-3">Training Configuration</h4>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div className="bg-gray-50 p-3 rounded-lg text-center">
                    <p className="text-2xl font-bold text-medical">{(selectedModel.config as any).epochs || 'N/A'}</p>
                    <p className="text-sm text-gray-500">Epochs</p>
                  </div>
                  <div className="bg-gray-50 p-3 rounded-lg text-center">
                    <p className="text-2xl font-bold text-medical">{(selectedModel.config as any).learning_rate || 'N/A'}</p>
                    <p className="text-sm text-gray-500">Learning Rate</p>
                  </div>
                  <div className="bg-gray-50 p-3 rounded-lg text-center">
                    <p className="text-2xl font-bold text-medical">{(selectedModel.config as any).batch_size || 'N/A'}</p>
                    <p className="text-sm text-gray-500">Batch Size</p>
                  </div>
                  <div className="bg-gray-50 p-3 rounded-lg text-center">
                    <p className="text-2xl font-bold text-medical">{(selectedModel.config as any).dataset_id ? 'Real' : 'Synthetic'}</p>
                    <p className="text-sm text-gray-500">Dataset Type</p>
                  </div>
                </div>
              </div>
            )}

            {/* Metrics */}
            {loadingMetrics ? (
              <div className="flex items-center justify-center py-8">
                <Loader2 className="w-6 h-6 animate-spin text-medical" />
                <span className="ml-2">Loading metrics...</span>
              </div>
            ) : modelMetrics ? (
              <div>
                <h4 className="font-medium mb-3">Performance Metrics</h4>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {/* Test Metrics */}
                  {modelMetrics.test_metrics && (
                    <div className="bg-gray-50 p-4 rounded-lg">
                      <h5 className="font-medium mb-2">Test Performance</h5>
                      <div className="space-y-2">
                        <div className="flex justify-between">
                          <span className="text-gray-600">Accuracy:</span>
                          <span className="font-medium text-medical">
                            {((modelMetrics.test_metrics.accuracy || 0) * 100).toFixed(2)}%
                          </span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-600">Loss:</span>
                          <span className="font-medium">{(modelMetrics.test_metrics.loss || 0).toFixed(4)}</span>
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Training History */}
                  {modelMetrics.training_history && (
                    <div className="bg-gray-50 p-4 rounded-lg">
                      <h5 className="font-medium mb-2">Training Summary</h5>
                      <div className="space-y-2">
                        <div className="flex justify-between">
                          <span className="text-gray-600">Final Train Accuracy:</span>
                          <span className="font-medium text-medical">
                            {((modelMetrics.training_history.accuracy?.[modelMetrics.training_history.accuracy.length - 1] || 0) * 100).toFixed(2)}%
                          </span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-600">Final Val Accuracy:</span>
                          <span className="font-medium text-medical">
                            {((modelMetrics.training_history.val_accuracy?.[modelMetrics.training_history.val_accuracy.length - 1] || 0) * 100).toFixed(2)}%
                          </span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-600">Epochs Completed:</span>
                          <span className="font-medium">{modelMetrics.training_history.accuracy?.length || 0}</span>
                        </div>
                      </div>
                    </div>
                  )}
                </div>

                {/* Classification Report */}
                {modelMetrics.classification_report && (
                  <div className="mt-4">
                    <h5 className="font-medium mb-2">Class-wise Performance</h5>
                    <div className="overflow-x-auto">
                      <table className="min-w-full bg-gray-50 rounded-lg">
                        <thead>
                          <tr className="border-b border-gray-200">
                            <th className="px-4 py-2 text-left text-sm font-medium text-gray-700">Class</th>
                            <th className="px-4 py-2 text-left text-sm font-medium text-gray-700">Precision</th>
                            <th className="px-4 py-2 text-left text-sm font-medium text-gray-700">Recall</th>
                            <th className="px-4 py-2 text-left text-sm font-medium text-gray-700">F1-Score</th>
                            <th className="px-4 py-2 text-left text-sm font-medium text-gray-700">Support</th>
                          </tr>
                        </thead>
                        <tbody>
                          {Object.entries(modelMetrics.classification_report).map(([className, metrics]: [string, any]) => {
                            if (typeof metrics === 'object' && 'precision' in metrics) {
                              return (
                                <tr key={className} className="border-b border-gray-200">
                                  <td className="px-4 py-2 text-sm text-gray-900">{className}</td>
                                  <td className="px-4 py-2 text-sm text-gray-900">{(metrics.precision * 100).toFixed(1)}%</td>
                                  <td className="px-4 py-2 text-sm text-gray-900">{(metrics.recall * 100).toFixed(1)}%</td>
                                  <td className="px-4 py-2 text-sm text-gray-900">{(metrics['f1-score'] * 100).toFixed(1)}%</td>
                                  <td className="px-4 py-2 text-sm text-gray-900">{metrics.support}</td>
                                </tr>
                              );
                            }
                            return null;
                          })}
                        </tbody>
                      </table>
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <div className="text-center py-8 text-gray-500">
                No detailed metrics available for this model
              </div>
            )}

            {/* Model Info */}
            <div className="pt-4 border-t border-gray-100">
              <div className="flex justify-between text-sm text-gray-500">
                <span>Status: <span className={`capitalize ${
                  selectedModel.status === 'completed' ? 'text-green-600' :
                  selectedModel.status === 'training' ? 'text-blue-600' :
                  selectedModel.status === 'failed' ? 'text-red-600' :
                  'text-gray-600'
                }`}>{selectedModel.status}</span></span>
                <span>Created: {new Date(selectedModel.created_at).toLocaleString()}</span>
              </div>
              {selectedModel.is_production && (
                <div className="mt-2 px-3 py-1 bg-green-100 text-green-800 text-sm rounded-full inline-block">
                  Production Model
                </div>
              )}
            </div>
          </div>
        )}
      </Modal>
    </div>
  );
}

