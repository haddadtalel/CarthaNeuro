'use client';

import { useState, useEffect, useCallback } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { Brain, Upload, FileImage, AlertCircle, CheckCircle, Loader2, ArrowRight, Activity } from 'lucide-react';
import { api } from '@/lib/api';
import { isAuthenticated, getUser, logout } from '@/lib/auth';
import { MRIUploadResponse, PredictionResponse, PredictionRequest } from '@/types';

export default function UploadPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const consultationId = searchParams.get('consultation_id');

  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [predicting, setPredicting] = useState(false);
  const [downloading, setDownloading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<PredictionResponse | null>(null);
  const [patientId, setPatientId] = useState('');
  const [patientName, setPatientName] = useState('');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [uploadResult, setUploadResult] = useState<MRIUploadResponse | null>(null);

  useEffect(() => {
    if (!isAuthenticated()) {
      router.push('/login');
      return;
    }

    const storedPatientId = localStorage.getItem('patient_id');
    const storedPatientName = localStorage.getItem('patient_name');
    if (storedPatientId) {
      setPatientId(storedPatientId);
    } else {
      router.push('/consultation');
    }
    if (storedPatientName) {
      setPatientName(storedPatientName);
    }

    // Fetch consultation data if consultation_id is provided
    if (consultationId) {
      fetchConsultationData();
    }
  }, [router, consultationId]);

  const fetchConsultationData = async () => {
    if (!consultationId) return;

    try {
      const response = await api.getConsultation(consultationId);
      const consultation = response.data;
      if (consultation.patient_full_name) {
        setPatientName(consultation.patient_full_name);
      }
    } catch (err) {
      console.error('Failed to fetch consultation data:', err);
    }
  };

  const handleFileSelect = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      // Validate file type
      const validTypes = ['image/jpeg', 'image/png', 'image/jpg'];
      if (!validTypes.includes(file.type)) {
        setError('Invalid file type. Please upload a JPEG or PNG image.');
        return;
      }

      // Validate file size (max 10MB)
      if (file.size > 10 * 1024 * 1024) {
        setError('File too large. Maximum size is 10MB.');
        return;
      }

      setSelectedFile(file);
      setError(null);

      // Create preview
      const reader = new FileReader();
      reader.onloadend = () => {
        setPreview(reader.result as string);
      };
      reader.readAsDataURL(file);
    }
  }, []);

  const handleUpload = async () => {
    if (!selectedFile) {
      setError('Please select an MRI image to upload.');
      return;
    }

    setUploading(true);
    setError(null);

    try {
      const response = await api.uploadMRI(selectedFile, patientId, consultationId || undefined);
      const data = response.data as MRIUploadResponse;
      setUploadResult(data);

      if (!data.validation.valid) {
        setError(`Image validation failed: ${data.validation.message}`);
        setUploading(false);
        return;
      }

      // Auto-predict after successful upload
      await handlePredict(data.mri_id);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to upload MRI. Please try again.');
    } finally {
      setUploading(false);
    }
  };

  const handlePredict = async (mriId: string) => {
    setPredicting(true);
    setError(null);

    try {
      const request: PredictionRequest = {
        patient_id: patientId,
        patient_full_name: patientName || 'Unknown Patient',
        mri_image_id: mriId,
        consultation_id: consultationId || undefined,
        model_type: 'efficientnet',
      };

      const response = await api.createPrediction(request);
      const data = response.data;

      // Debug: Check if data contains validation errors
      console.log('Raw prediction response:', data);

      // Check if any field contains validation error structure
      const hasValidationError = (obj: any): boolean => {
        if (obj && typeof obj === 'object') {
          if ('type' in obj && 'loc' in obj && 'msg' in obj && 'input' in obj && 'url' in obj) {
            return true;
          }
          for (const key in obj) {
            if (hasValidationError(obj[key])) {
              return true;
            }
          }
        }
        return false;
      };

      if (hasValidationError(data)) {
        console.error('Prediction response contains validation error objects:', data);
        setError('Prediction failed due to data validation errors. Please check the console for details.');
        setSuccess(null); // Clear any previous success state
        return;
      }

      // Additional check for FastAPI validation error format
      if (data && typeof data === 'object' && 'detail' in data) {
        console.error('Prediction API returned error details:', data.detail);
        setError('Prediction failed. Please check the console for details.');
        setSuccess(null); // Clear any previous success state
        return;
      }

      setSuccess(data as PredictionResponse);

      // Save to local history
      const history = JSON.parse(localStorage.getItem('prediction_history') || '[]');
      history.unshift(data);
      localStorage.setItem('prediction_history', JSON.stringify(history.slice(0, 10)));

    } catch (err: any) {
      // Safely extract error message
      let errorMessage = 'Failed to generate prediction. Please try again.';

      if (err.response?.data?.detail) {
        const detail = err.response.data.detail;
        if (typeof detail === 'string') {
          errorMessage = detail;
        } else if (Array.isArray(detail)) {
          // Handle validation error arrays
          errorMessage = detail.map((item: any) =>
            typeof item === 'string' ? item : item.msg || 'Validation error'
          ).join(', ');
        } else if (typeof detail === 'object' && detail.msg) {
          errorMessage = detail.msg;
        }
      }

      setError(errorMessage);
    } finally {
      setPredicting(false);
    }
  };

  const handleLogout = () => {
    logout();
    router.push('/login');
  };

  const resetForm = () => {
    setSelectedFile(null);
    setPreview(null);
    setUploadResult(null);
    setSuccess(null);
    setError(null);
  };

  const getConfidenceColor = (confidence: string) => {
    if (typeof confidence !== 'string') return 'text-gray-600';
    switch (confidence) {
      case 'Very High': return 'text-green-600';
      case 'High': return 'text-green-500';
      case 'Moderate': return 'text-yellow-600';
      case 'Low': return 'text-orange-500';
      case 'Very Low': return 'text-red-500';
      default: return 'text-gray-600';
    }
  };

  const getResultColor = (diseaseClass: string) => {
    if (typeof diseaseClass !== 'string') return 'bg-gray-100 text-gray-800';
    if (diseaseClass.includes('No Alzheimer')) return 'bg-green-100 text-green-800';
    if (diseaseClass.includes('Mild Cognitive')) return 'bg-yellow-100 text-yellow-800';
    if (diseaseClass.includes('Early')) return 'bg-orange-100 text-orange-800';
    if (diseaseClass.includes('Moderate')) return 'bg-red-100 text-red-800';
    return 'bg-purple-100 text-purple-800';
  };

  // Safety check for success data
  const isValidSuccessData = (data: any) => {
    if (!data || typeof data !== 'object') return false;

    // Check for validation error signatures
    if ('type' in data && 'loc' in data && 'msg' in data && 'input' in data && 'url' in data) return false;

    // Check required fields are correct types
    if (typeof data.disease_class !== 'string') return false;
    if (typeof data.probability !== 'number') return false;
    if (typeof data.confidence !== 'string') return false;
    if (typeof data.recommendations !== 'string') return false;
    if (typeof data.model_used !== 'string') return false;

    // Check factors object if present
    if (data.factors && typeof data.factors === 'object') {
      const factors = data.factors;
      if (typeof factors.contribution_image !== 'number' || typeof factors.contribution_consultation !== 'number') return false;
    }

    return true;
  };

  const handleDownloadReport = async (predictionId: string) => {
    setDownloading(true);
    try {
      const blob = await api.downloadReport(predictionId);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `medical_report_${predictionId}.pdf`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (err) {
      console.error('Failed to download report:', err);
      setError('Failed to download report. Please try again.');
    } finally {
      setDownloading(false);
    }
  };

  if (success && isValidSuccessData(success)) {
    return (
      <div className="min-h-screen bg-gray-50">
        {/* Header */}
        <header className="bg-white border-b border-gray-100">
          <div className="max-w-7xl mx-auto px-4 py-4">
            <div className="flex justify-between items-center">
              <div className="flex items-center gap-3">
                <Brain className="w-8 h-8 text-medical" />
                <h1 className="text-xl font-bold text-gray-900">Prediction Results</h1>
              </div>
              <button onClick={handleLogout} className="btn btn-secondary">
                Logout
              </button>
            </div>
          </div>
        </header>

        <div className="max-w-4xl mx-auto px-4 py-8">
          <div className="card text-center">
            <div className="w-20 h-20 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-6">
              <CheckCircle className="w-10 h-10 text-green-600" />
            </div>
            <h2 className="text-2xl font-bold text-gray-900 mb-2">Analysis Complete!</h2>
            <p className="text-gray-600 mb-4">Based on MRI analysis and consultation data</p>
            <p className="text-sm text-gray-500 mb-8">Patient: {success.patient_full_name || 'Unknown Patient'}</p>

            {/* Main Result */}
            <div className={`inline-block px-6 py-3 rounded-xl text-lg font-semibold mb-6 ${getResultColor(success.disease_class || 'Unknown')}`}>
              {success.disease_class || 'Unknown'}
            </div>

            {/* Probability */}
            <div className="grid md:grid-cols-3 gap-6 mb-8">
              <div className="bg-gray-50 rounded-lg p-4">
                <p className="text-sm text-gray-600 mb-1">Probability</p>
                <p className="text-3xl font-bold text-medical">
                  {typeof success.probability === 'number' ? (success.probability * 100).toFixed(1) : 'N/A'}%
                </p>
              </div>
              <div className="bg-gray-50 rounded-lg p-4">
                <p className="text-sm text-gray-600 mb-1">Confidence</p>
                <p className={`text-3xl font-bold ${getConfidenceColor(success.confidence || 'Unknown')}`}>
                  {success.confidence || 'Unknown'}
                </p>
              </div>
              <div className="bg-gray-50 rounded-lg p-4">
                <p className="text-sm text-gray-600 mb-1">Model Used</p>
                <p className="text-lg font-semibold text-gray-900 capitalize">
                  {typeof success.model_used === 'string' ? success.model_used : 'Unknown'}
                </p>
              </div>
            </div>

            {/* Factors Breakdown */}
            {success.factors && typeof success.factors === 'object' && 'contribution_image' in success.factors && 'contribution_consultation' in success.factors && (
              <div className="bg-gray-50 rounded-lg p-6 mb-6 text-left">
                <h3 className="font-semibold text-gray-900 mb-4">Analysis Breakdown</h3>
                <div className="space-y-3">
                  <div className="flex justify-between items-center">
                    <span className="text-gray-600">MRI Image Analysis</span>
                    <div className="flex items-center gap-2">
                      <div className="w-32 h-2 bg-gray-200 rounded-full overflow-hidden">
                        <div className="h-full bg-medical rounded-full" style={{ width: `${(success.factors.contribution_image || 0) * 100}%` }} />
                      </div>
                      <span className="text-sm font-medium">{((success.factors.contribution_image || 0) * 100).toFixed(0)}%</span>
                    </div>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-gray-600">Consultation Data</span>
                    <div className="flex items-center gap-2">
                      <div className="w-32 h-2 bg-gray-200 rounded-full overflow-hidden">
                        <div className="h-full bg-purple-500 rounded-full" style={{ width: `${(success.factors.contribution_consultation || 0) * 100}%` }} />
                      </div>
                      <span className="text-sm font-medium">{((success.factors.contribution_consultation || 0) * 100).toFixed(0)}%</span>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Recommendations */}
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-6 mb-6 text-left">
              <h3 className="font-semibold text-blue-900 mb-3 flex items-center gap-2">
                <Activity className="w-5 h-5" />
                Recommendations
              </h3>
              <div className="text-blue-800 whitespace-pre-line">
                {typeof success.recommendations === 'string' ? success.recommendations : 'No recommendations available'}
              </div>
            </div>

            {/* Actions */}
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <button onClick={resetForm} className="btn btn-secondary">
                New Analysis
              </button>
              <button
                onClick={() => handleDownloadReport(success.prediction_id)}
                disabled={downloading}
                className="btn btn-outline flex items-center justify-center gap-2"
              >
                {downloading ? (
                  <>
                    <Loader2 className="w-5 h-5 animate-spin" />
                    Downloading...
                  </>
                ) : (
                  'Download PDF Report'
                )}
              </button>
              <button onClick={() => router.push('/consultation')} className="btn btn-primary">
                Complete Consultation
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  } else if (success) {
    // Invalid success data - show error
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
        <div className="card max-w-md w-full text-center">
          <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <AlertCircle className="w-8 h-8 text-red-600" />
          </div>
          <h2 className="text-2xl font-bold text-gray-900 mb-2">Data Error</h2>
          <p className="text-gray-600 mb-4">
            The prediction response contains invalid data. Please try again.
          </p>
          <button onClick={resetForm} className="btn btn-primary">
            Try Again
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-100">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <div className="flex justify-between items-center">
            <div className="flex items-center gap-3">
              <Brain className="w-8 h-8 text-medical" />
              <h1 className="text-xl font-bold text-gray-900">MRI Upload</h1>
            </div>
            <button onClick={handleLogout} className="btn btn-secondary">
              Logout
            </button>
          </div>
        </div>
      </header>

      {/* Error Message */}
      {error && typeof error === 'string' && (
        <div className="max-w-7xl mx-auto px-4 mt-4">
          <div className="p-4 bg-red-50 border border-red-200 rounded-lg flex items-center gap-3 text-red-700">
            <AlertCircle className="w-5 h-5 flex-shrink-0" />
            <span>{error}</span>
          </div>
        </div>
      )}

      {/* Main Content */}
      <div className="max-w-4xl mx-auto px-4 py-8">
        <div className="card">
          <h2 className="text-lg font-semibold text-gray-900 mb-6">Upload Brain MRI Image</h2>

          {/* Upload Area */}
          {!preview ? (
            <div className="mb-6">
              <label className={`dropzone ${loading ? 'opacity-50 cursor-not-allowed' : ''}`}>
                <input
                  type="file"
                  accept="image/jpeg,image/png,image/jpg"
                  onChange={handleFileSelect}
                  disabled={loading}
                  className="hidden"
                />
                <Upload className="w-12 h-12 text-gray-400 mx-auto mb-4" />
                <p className="text-lg font-medium text-gray-700 mb-2">
                  {selectedFile ? selectedFile.name : 'Click or drag to upload MRI image'}
                </p>
                <p className="text-sm text-gray-500">
                  Supported formats: JPEG, PNG (max 10MB)
                </p>
              </label>
            </div>
          ) : (
            /* Preview */
            <div className="mb-6">
              <div className="relative bg-gray-100 rounded-xl p-4">
                <img
                  src={preview}
                  alt="MRI Preview"
                  className="max-h-96 mx-auto rounded-lg"
                />
                <button
                  onClick={resetForm}
                  className="absolute top-2 right-2 bg-gray-800 text-white rounded-full w-8 h-8 flex items-center justify-center hover:bg-gray-700"
                >
                  ×
                </button>
              </div>
              <div className="mt-2 text-sm text-gray-500 text-center">
                {selectedFile?.name} ({(selectedFile?.size || 0 / 1024).toFixed(1)} KB)
              </div>
            </div>
          )}

          {/* Upload Result */}
          {uploadResult && uploadResult.validation.valid && (
            <div className="mb-6 p-4 bg-green-50 border border-green-200 rounded-lg flex items-center gap-3">
              <CheckCircle className="w-5 h-5 text-green-600" />
              <span className="text-green-700">Image validated successfully</span>
            </div>
          )}

          {/* Upload Button */}
          {selectedFile && !uploadResult && (
            <button
              onClick={handleUpload}
              disabled={uploading || predicting}
              className="btn btn-primary w-full py-3 flex items-center justify-center gap-2"
            >
              {uploading ? (
                <>
                  <Loader2 className="w-5 h-5 animate-spin" />
                  Uploading...
                </>
              ) : (
                <>
                  <Upload className="w-5 h-5" />
                  Upload and Analyze
                </>
              )}
            </button>
          )}

          {/* Predicting State */}
          {predicting && (
            <div className="text-center py-8">
              <div className="w-16 h-16 bg-medical/10 rounded-full flex items-center justify-center mx-auto mb-4">
                <Activity className="w-8 h-8 text-medical animate-pulse" />
              </div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">Analyzing MRI...</h3>
              <p className="text-gray-600 mb-4">
                Our AI model is processing the image and combining it with consultation data
              </p>
              <div className="flex justify-center">
                <Loader2 className="w-8 h-8 animate-spin text-medical" />
              </div>
            </div>
          )}

          {/* Instructions */}
          <div className="mt-8 p-4 bg-blue-50 border border-blue-200 rounded-lg">
            <h4 className="font-semibold text-blue-900 mb-2">MRI Image Guidelines</h4>
            <ul className="text-sm text-blue-800 space-y-1">
              <li>• Use T1 or T2 weighted brain MRI images</li>
              <li>• Ensure the image shows clear brain anatomy</li>
              <li>• Minimum resolution: 64x64 pixels</li>
              <li>• Maximum resolution: 4096x4096 pixels</li>
              <li>• File size: up to 10MB</li>
              <li>• Accepted formats: JPEG, PNG</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}

