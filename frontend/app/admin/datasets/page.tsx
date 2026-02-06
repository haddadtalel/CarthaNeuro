'use client';

import { useState, useEffect, useRef } from 'react';
import { useRouter } from 'next/navigation';
import { Upload, File, Trash2, Download, Database, Loader2, Eye } from 'lucide-react';
import { api } from '@/lib/api';
import { isAuthenticated, isAdmin, logout } from '@/lib/auth';
import { Card, Button, Modal, Alert } from '@/components';

interface Dataset {
  _id: string;
  name: string;
  description: string;
  classes: string[];
  class_distribution: Record<string, number>;
  image_count: number;
  size_bytes: number;
  image_extensions: string[];
  uploaded_by: string;
  is_active: boolean;
  status: string;
  created_at: string;
  size_mb?: number;
  total_classes?: number;
  // Train/Test split fields
  has_train_test_split?: boolean;
  train_count?: number;
  test_count?: number;
  train_distribution?: Record<string, number>;
  test_distribution?: Record<string, number>;
}

export default function AdminDatasetsPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(true);
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [selectedDataset, setSelectedDataset] = useState<Dataset | null>(null);
  const [showDetailsModal, setShowDetailsModal] = useState(false);
  const [toast, setToast] = useState<{ message: string; type: 'success' | 'error' } | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [uploadData, setUploadData] = useState({
    name: '',
    description: '',
    file: null as File | null,
  });

  useEffect(() => {
    if (!isAuthenticated() || !isAdmin()) {
      router.push(isAuthenticated() ? '/consultation' : '/login');
      return;
    }
    fetchDatasets();
  }, [router]);

  const fetchDatasets = async () => {
    try {
      const response = await api.getDatasets(0, 50);
      setDatasets((response.data as any).datasets || []);
    } catch (err) {
      console.error('Failed to fetch datasets');
    } finally {
      setLoading(false);
    }
  };

  const showToast = (message: string, type: 'success' | 'error') => {
    setToast({ message, type });
    setTimeout(() => setToast(null), 3000);
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      const fileName = file.name.toLowerCase();
      const isValidExtension = fileName.endsWith('.zip') || 
                               fileName.endsWith('.tar.gz') || 
                               fileName.endsWith('.tgz') ||
                               fileName.endsWith('.gz');

      if (!isValidExtension) {
        showToast('Please upload a ZIP, TAR.GZ, or TGZ file', 'error');
        return;
      }
      if (file.size > 500 * 1024 * 1024) {
        showToast('File size must be less than 500MB', 'error');
        return;
      }
      setUploadData({ ...uploadData, file });
    }
  };

  const handleUpload = async () => {
    if (!uploadData.file || !uploadData.name.trim()) {
      showToast('Please provide a name and select a file', 'error');
      return;
    }

    setUploading(true);
    setUploadProgress(0);

    try {
      const formData = new FormData();
      formData.append('name', uploadData.name);
      formData.append('description', uploadData.description);
      formData.append('file', uploadData.file);

      console.log('Uploading dataset:', uploadData.name);
      console.log('File:', uploadData.file.name, 'Size:', uploadData.file.size);

      // Simulate progress
      const progressInterval = setInterval(() => {
        setUploadProgress(prev => Math.min(prev + 10, 90));
      }, 500);

      const response = await api.uploadDataset(formData);
      console.log('Upload response:', response.data);
      
      clearInterval(progressInterval);
      setUploadProgress(100);
      
      showToast('Dataset uploaded successfully', 'success');
      setShowUploadModal(false);
      setUploadData({ name: '', description: '', file: null });
      fetchDatasets();
    } catch (err: any) {
      console.error('Upload error:', err);
      console.error('Error response:', err.response?.data);
      const errorMessage = err.response?.data?.detail || 
                           err.response?.data?.message || 
                           err.message || 
                           'Upload failed. Please check the console for details.';
      showToast(errorMessage, 'error');
    } finally {
      setUploading(false);
      setUploadProgress(0);
    }
  };

  const deleteDataset = async (datasetId: string) => {
    try {
      await api.deleteDataset(datasetId);
      showToast('Dataset deleted', 'success');
      fetchDatasets();
    } catch (err: any) {
      showToast(err.response?.data?.detail || 'Failed to delete', 'error');
    }
  };

  const handleLogout = () => {
    logout();
    router.push('/login');
  };

  const formatFileSize = (mb: number) => {
    if (mb < 1) return `${(mb * 1024).toFixed(0)} KB`;
    return `${mb.toFixed(1)} MB`;
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
          <button onClick={() => router.push('/admin/models')} className="w-full flex items-center gap-3 px-4 py-3 rounded-lg text-gray-600 hover:bg-gray-100">Models</button>
          <button className="w-full flex items-center gap-3 px-4 py-3 rounded-lg bg-medical text-white">Datasets</button>
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
          <h1 className="text-2xl font-bold text-gray-900">Datasets</h1>
          <Button onClick={() => setShowUploadModal(true)} icon={<Upload className="w-4 h-4" />}>
            Upload Dataset
          </Button>
        </div>

        {loading ? (
          <div className="flex items-center justify-center py-12">
            <Loader2 className="w-8 h-8 animate-spin text-medical" />
          </div>
        ) : (
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
            {datasets.map((dataset) => (
              <Card key={dataset._id} hover>
                <div className="flex items-start gap-3">
                  <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center flex-shrink-0">
                    <Database className="w-5 h-5 text-blue-600" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <h3 className="font-semibold text-gray-900 truncate">{dataset.name}</h3>
                    <p className="text-sm text-gray-500 line-clamp-2">{dataset.description || 'No description'}</p>
                  </div>
                </div>

                <div className="mt-4 grid grid-cols-2 gap-2 text-sm">
                  <div>
                    <span className="text-gray-500">Images</span>
                    <p className="font-medium">{dataset.image_count}</p>
                  </div>
                  <div>
                    <span className="text-gray-500">Size</span>
                    <p className="font-medium">{formatFileSize((dataset.size_bytes || 0) / (1024 * 1024))}</p>
                  </div>
                  <div>
                    <span className="text-gray-500">Classes</span>
                    <p className="font-medium">{dataset.total_classes || dataset.classes?.length || Object.keys(dataset.class_distribution || {}).length}</p>
                  </div>
                  <div>
                    <span className="text-gray-500">Status</span>
                    <p className={`font-medium capitalize ${
                      dataset.status === 'ready' ? 'text-green-600' : 'text-gray-600'
                    }`}>
                      {dataset.status}
                    </p>
                  </div>
                </div>

                <div className="mt-4 pt-4 border-t border-gray-100 flex gap-2">
                  <Button size="sm" variant="secondary" onClick={() => {
                    setSelectedDataset(dataset);
                    setShowDetailsModal(true);
                  }}>
                    <Eye className="w-4 h-4" />
                  </Button>
                  <Button size="sm" variant="secondary"><Download className="w-4 h-4" /></Button>
                  <Button size="sm" variant="danger" onClick={() => deleteDataset(dataset._id)}>
                    <Trash2 className="w-4 h-4" />
                  </Button>
                </div>
              </Card>
            ))}

            {datasets.length === 0 && (
              <div className="col-span-full text-center py-12">
                <Database className="w-12 h-12 text-gray-300 mx-auto mb-4" />
                <p className="text-gray-500">No datasets uploaded yet</p>
                <Button onClick={() => setShowUploadModal(true)} className="mt-4" icon={<Upload className="w-4 h-4" />}>
                  Upload First Dataset
                </Button>
              </div>
            )}
          </div>
        )}
      </main>

      {/* Upload Modal */}
      <Modal isOpen={showUploadModal} onClose={() => !uploading && setShowUploadModal(false)} title="Upload Dataset" size="md">
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Dataset Name</label>
            <input
              type="text"
              value={uploadData.name}
              onChange={(e) => setUploadData({ ...uploadData, name: e.target.value })}
              placeholder="e.g., Alzheimer MRI Dataset v2"
              className="w-full rounded-lg border border-gray-300 px-4 py-2 focus:outline-none focus:ring-2 focus:ring-medical"
              disabled={uploading}
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
            <textarea
              value={uploadData.description}
              onChange={(e) => setUploadData({ ...uploadData, description: e.target.value })}
              placeholder="Describe the dataset..."
              rows={3}
              className="w-full rounded-lg border border-gray-300 px-4 py-2 focus:outline-none focus:ring-2 focus:ring-medical"
              disabled={uploading}
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Dataset File (ZIP)</label>
            <div
              onClick={() => fileInputRef.current?.click()}
              className={`border-2 border-dashed rounded-lg p-6 text-center cursor-pointer transition-colors ${
                uploadData.file ? 'border-medical bg-blue-50' : 'border-gray-300 hover:border-gray-400'
              }`}
            >
              {uploadData.file ? (
                <div className="flex items-center justify-center gap-2">
                  <File className="w-5 h-5 text-medical" />
                  <span>{uploadData.file.name}</span>
                  <span className="text-sm text-gray-500">({formatFileSize(uploadData.file.size / (1024 * 1024))})</span>
                </div>
              ) : (
                <div>
                  <Upload className="w-8 h-8 text-gray-400 mx-auto mb-2" />
                  <p className="text-gray-600">Click to select or drag and drop</p>
                  <p className="text-sm text-gray-500 mt-1">ZIP file containing image folders (max 500MB)</p>
                </div>
              )}
            </div>
            <input
              ref={fileInputRef}
              type="file"
              accept=".zip,.tar.gz,.tgz,.gz"
              onChange={handleFileSelect}
              className="hidden"
              disabled={uploading}
            />
          </div>

          {uploading && (
            <div>
              <div className="flex justify-between text-sm mb-1">
                <span>Uploading...</span>
                <span>{uploadProgress}%</span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div
                  className="bg-medical h-2 rounded-full transition-all duration-300"
                  style={{ width: `${uploadProgress}%` }}
                />
              </div>
            </div>
          )}

          <Alert type="info">
            <p className="font-medium mb-1">Supported Formats:</p>
            <ul className="list-disc list-inside text-xs space-y-1">
              <li><strong>Train/Test Structure:</strong> ZIP with train/ and test/ folders, each containing class subfolders (recommended for best validation accuracy)</li>
              <li><strong>Single Folder:</strong> ZIP with class subfolders only (auto 80/20 split)</li>
            </ul>
          </Alert>
        </div>

        <div className="mt-6 flex justify-end gap-3">
          <Button
            variant="secondary"
            onClick={() => setShowUploadModal(false)}
            disabled={uploading}
          >
            Cancel
          </Button>
          <Button onClick={handleUpload} loading={uploading} icon={<Upload className="w-4 h-4" />}>
            Upload
          </Button>
        </div>
      </Modal>

      {/* Details Modal */}
      <Modal isOpen={showDetailsModal} onClose={() => setShowDetailsModal(false)} title="Dataset Details" size="md">
        {selectedDataset && (
          <div className="space-y-4">
            <div>
              <h3 className="text-lg font-semibold">{selectedDataset.name}</h3>
              <p className="text-gray-600">{selectedDataset.description}</p>
            </div>

            {/* Train/Test Split Info */}
            {selectedDataset.has_train_test_split ? (
              <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                <div className="flex items-center gap-2 mb-3">
                  <span className="text-lg">📊</span>
                  <h4 className="font-medium text-green-800">Train/Test Split Detected</h4>
                </div>
                <div className="grid grid-cols-2 gap-4">
                  <div className="bg-white rounded-lg p-3">
                    <p className="text-sm text-gray-500">Training Images</p>
                    <p className="text-xl font-bold text-green-600">{selectedDataset.train_count || 0}</p>
                  </div>
                  <div className="bg-white rounded-lg p-3">
                    <p className="text-sm text-gray-500">Test Images</p>
                    <p className="text-xl font-bold text-blue-600">{selectedDataset.test_count || 0}</p>
                  </div>
                </div>
                <p className="text-xs text-green-700 mt-2">
                  ✓ Dataset uses train/test folder structure. Training will use the exact train/test split.
                </p>
              </div>
            ) : (
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <div className="flex items-center gap-2 mb-2">
                  <span className="text-lg">📊</span>
                  <h4 className="font-medium text-blue-800">Automatic 80/20 Split</h4>
                </div>
                <p className="text-xs text-blue-700">
                  Dataset will be split 80% training / 20% validation automatically during training.
                </p>
              </div>
            )}

            <div className="grid grid-cols-3 gap-4">
              <div className="bg-gray-50 p-3 rounded-lg text-center">
                <p className="text-2xl font-bold text-medical">{selectedDataset.image_count}</p>
                <p className="text-sm text-gray-500">Total Images</p>
              </div>
              <div className="bg-gray-50 p-3 rounded-lg text-center">
                <p className="text-2xl font-bold text-medical">{formatFileSize((selectedDataset.size_bytes || 0) / (1024 * 1024))}</p>
                <p className="text-sm text-gray-500">File Size</p>
              </div>
              <div className="bg-gray-50 p-3 rounded-lg text-center">
                <p className="text-2xl font-bold text-medical">{selectedDataset.total_classes || selectedDataset.classes?.length || Object.keys(selectedDataset.class_distribution || {}).length}</p>
                <p className="text-sm text-gray-500">Classes</p>
              </div>
            </div>

            <div>
              <h4 className="font-medium mb-2">Class Distribution</h4>
              <div className="space-y-2">
                {Object.entries(selectedDataset.class_distribution).map(([className, count]) => (
                  <div key={className} className="flex items-center gap-3">
                    <div className="flex-1">
                      <div className="flex justify-between text-sm mb-1">
                        <span className="capitalize">{className.replace(/_/g, ' ')}</span>
                        <span>{count} images</span>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-2">
                        <div
                          className="bg-medical h-2 rounded-full"
                          style={{ width: `${(count / selectedDataset.image_count) * 100}%` }}
                        />
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div className="text-sm text-gray-500 pt-4 border-t">
              <p>Created: {new Date(selectedDataset.created_at).toLocaleString()}</p>
              <p>Uploaded by: {selectedDataset.uploaded_by}</p>
            </div>
          </div>
        )}
      </Modal>
    </div>
  );
}

