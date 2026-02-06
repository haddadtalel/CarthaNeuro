'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Brain, User, AlertCircle, CheckCircle, ArrowRight, Loader2, FileText, Activity } from 'lucide-react';
import { api } from '@/lib/api';
import { isAuthenticated, getUser, logout } from '@/lib/auth';
import { ConsultationFormData, ConsultationResponse } from '@/types';

export default function ConsultationPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<ConsultationResponse | null>(null);
  const [currentStep, setCurrentStep] = useState(1);
  const [patientId, setPatientId] = useState('');

  const [formData, setFormData] = useState<ConsultationFormData>({
    // Patient Identity
    patient_full_name: '',
    patient_reference_id: '',

    // Demographics
    age: 65,
    gender: 'male',
    
    // Medical History
    family_history_ad: false,
    diabetes: false,
    hypertension: false,
    heart_disease: false,
    stroke_history: false,
    smoking: false,
    alcohol_use: false,
    
    // Cognitive Symptoms (0-3 scale)
    memory_complaints: 0,
    difficulty_concentrating: 0,
    problem_solving_difficulty: 0,
    mood_changes: 0,
    confusion: 0,
    personality_changes: 0,
    disorientation: 0,
    difficulty_with_daily_tasks: 0,
    
    // Additional Information
    symptoms_duration_months: 0,
    previous_ad_evaluation: false,
    current_medications: '',
    notes: '',
  });

  useEffect(() => {
    // Check authentication
    if (!isAuthenticated()) {
      router.push('/login');
      return;
    }

    // Generate or get patient ID
    const storedPatientId = localStorage.getItem('patient_id');
    if (storedPatientId) {
      setPatientId(storedPatientId);
    } else {
      const newPatientId = `patient_${Date.now()}`;
      setPatientId(newPatientId);
      localStorage.setItem('patient_id', newPatientId);
    }
  }, [router]);

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>) => {
    const { name, value, type } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? (e.target as HTMLInputElement).checked : type === 'number' ? parseInt(value) || 0 : value
    }));
  };

  const handleSliderChange = (name: string, value: number) => {
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const getStepTitle = (step: number) => {
    switch (step) {
      case 1: return 'Demographics & Medical History';
      case 2: return 'Cognitive Symptoms Assessment';
      case 3: return 'Additional Information';
      default: return '';
    }
  };

  const nextStep = () => {
    // Validate required fields on step 1
    if (currentStep === 1) {
      if (!formData.patient_full_name.trim()) {
        setError('Patient Full Name is required.');
        return;
      }
      if (!(formData.patient_reference_id || '').trim()) {
        setError('Patient Reference ID is required.');
        return;
      }
      if (!patientId.trim()) {
        setError('Patient ID is required.');
        return;
      }
      // Clear error when validation passes
      setError(null);
    }
    if (currentStep < 3) setCurrentStep(currentStep + 1);
  };

  const prevStep = () => {
    if (currentStep > 1) setCurrentStep(currentStep - 1);
  };

  const handleSubmit = async () => {
    setSubmitting(true);
    setError(null);

    // Validation for required fields
    if (!formData.patient_full_name.trim()) {
      setError('Patient Full Name is required.');
      setSubmitting(false);
      return;
    }
    if (!patientId.trim()) {
      setError('Patient ID is required.');
      setSubmitting(false);
      return;
    }

    try {
      const response = await api.createConsultation({
        ...formData,
        patient_id: patientId,
        doctor_id: getUser()?.id,
      });

      const data = response.data as ConsultationResponse;
      setSuccess(data);

      // Store patient name for upload page
      localStorage.setItem('patient_name', formData.patient_full_name);

      // Navigate to upload page after short delay
      setTimeout(() => {
        router.push(`/upload?consultation_id=${data.consultation_id}`);
      }, 2500);

    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to submit consultation. Please try again.');
    } finally {
      setSubmitting(false);
    }
  };

  const handleLogout = () => {
    logout();
    router.push('/login');
  };

  if (success) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
        <div className="card max-w-md w-full text-center">
          <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <CheckCircle className="w-8 h-8 text-green-600" />
          </div>
          <h2 className="text-2xl font-bold text-gray-900 mb-2">Consultation Submitted!</h2>
          <p className="text-gray-600 mb-4">
            Your consultation has been successfully processed.
          </p>
          <div className="bg-gray-50 rounded-lg p-4 mb-4">
            <p className="text-sm text-gray-600">Risk Score</p>
            <p className="text-3xl font-bold text-medical">{(success.risk_score * 100).toFixed(1)}%</p>
          </div>
          <p className="text-sm text-gray-500">Redirecting to MRI upload...</p>
          <div className="mt-4 flex justify-center">
            <Loader2 className="w-6 h-6 animate-spin text-medical" />
          </div>
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
              <div>
                <h1 className="text-xl font-bold text-gray-900">Patient Consultation</h1>
                <p className="text-sm text-gray-500">Step {currentStep} of 3: {getStepTitle(currentStep)}</p>
              </div>
            </div>
            <button onClick={handleLogout} className="btn btn-secondary">
              Logout
            </button>
          </div>
        </div>
      </header>

      {/* Progress Bar */}
      <div className="bg-white border-b border-gray-100">
        <div className="max-w-7xl mx-auto px-4 py-3">
          <div className="flex items-center gap-2">
            {[1, 2, 3].map((step) => (
              <div key={step} className="flex items-center">
                <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium ${
                  step <= currentStep
                    ? 'bg-medical text-white'
                    : 'bg-gray-200 text-gray-500'
                }`}>
                  {step < currentStep ? <CheckCircle className="w-5 h-5" /> : step}
                </div>
                {step < 3 && (
                  <div className={`w-16 h-1 mx-2 ${
                    step < currentStep ? 'bg-medical' : 'bg-gray-200'
                  }`} />
                )}
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Error Message */}
      {error && (
        <div className="max-w-7xl mx-auto px-4 mt-4">
          <div className="p-4 bg-red-50 border border-red-200 rounded-lg flex items-center gap-3 text-red-700">
            <AlertCircle className="w-5 h-5 flex-shrink-0" />
            <span>{error}</span>
          </div>
        </div>
      )}

      {/* Form */}
      <div className="max-w-7xl mx-auto px-4 py-8">
        <div className="card">
          {/* Step 1: Demographics & Medical History */}
          {currentStep === 1 && (
            <div className="space-y-8">
              <div>
                <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
                  <User className="w-5 h-5 text-medical" />
                  Demographics
                </h3>
                <div className="grid md:grid-cols-2 gap-6">
                  <div>
                    <label className="label">Patient Full Name *</label>
                    <input
                      type="text"
                      name="patient_full_name"
                      value={formData.patient_full_name}
                      onChange={handleInputChange}
                      className="input"
                      placeholder="Enter patient's full name"
                      required
                    />
                  </div>
                  <div>
                    <label className="label">Patient Reference ID</label>
                    <input
                      type="text"
                      name="patient_reference_id"
                      value={formData.patient_reference_id}
                      onChange={handleInputChange}
                      className="input"
                      placeholder="e.g., MRN12345"
                    />
                  </div>
                </div>
                <div className="grid md:grid-cols-2 gap-6 mt-6">
                  <div>
                    <label className="label">Age</label>
                    <input
                      type="number"
                      name="age"
                      value={formData.age}
                      onChange={handleInputChange}
                      min="18"
                      max="120"
                      className="input"
                    />
                  </div>
                  <div>
                    <label className="label">Gender</label>
                    <select
                      name="gender"
                      value={formData.gender}
                      onChange={handleInputChange}
                      className="input"
                    >
                      <option value="male">Male</option>
                      <option value="female">Female</option>
                    </select>
                  </div>
                </div>
              </div>

              <div className="border-t pt-8">
                <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
                  <Activity className="w-5 h-5 text-medical" />
                  Medical History
                </h3>
                <div className="grid md:grid-cols-2 gap-4">
                  {[
                    { name: 'family_history_ad', label: 'Family History of Alzheimer\'s' },
                    { name: 'diabetes', label: 'Diabetes' },
                    { name: 'hypertension', label: 'Hypertension' },
                    { name: 'heart_disease', label: 'Heart Disease' },
                    { name: 'stroke_history', label: 'Stroke History' },
                    { name: 'smoking', label: 'Smoking' },
                    { name: 'alcohol_use', label: 'Alcohol Use' },
                  ].map((item) => (
                    <label key={item.name} className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg cursor-pointer hover:bg-gray-100">
                      <input
                        type="checkbox"
                        name={item.name}
                        checked={formData[item.name as keyof ConsultationFormData] as boolean}
                        onChange={handleInputChange}
                        className="w-5 h-5 text-medical rounded focus:ring-medical"
                      />
                      <span className="text-gray-700">{item.label}</span>
                    </label>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* Step 2: Cognitive Symptoms */}
          {currentStep === 2 && (
            <div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">Cognitive Symptoms Assessment</h3>
              <p className="text-gray-600 mb-6">Rate each symptom from 0 (None) to 3 (Severe)</p>
              
              <div className="space-y-6">
                {[
                  { name: 'memory_complaints', label: 'Memory Complaints', desc: 'Forgetting recent events, names, or conversations' },
                  { name: 'difficulty_concentrating', label: 'Difficulty Concentrating', desc: 'Trouble focusing on tasks or following conversations' },
                  { name: 'problem_solving_difficulty', label: 'Problem Solving Difficulty', desc: 'Challenges with planning or solving problems' },
                  { name: 'mood_changes', label: 'Mood Changes', desc: 'Depression, anxiety, or unexplained mood swings' },
                  { name: 'confusion', label: 'Confusion', desc: 'Disorientation about time, place, or people' },
                  { name: 'personality_changes', label: 'Personality Changes', desc: 'Behavioral changes, agitation, or withdrawal' },
                  { name: 'disorientation', label: 'Disorientation', desc: 'Getting lost in familiar places' },
                  { name: 'difficulty_with_daily_tasks', label: 'Difficulty with Daily Tasks', desc: 'Trouble completing familiar daily activities' },
                ].map((symptom) => (
                  <div key={symptom.name} className="p-4 bg-gray-50 rounded-lg">
                    <div className="flex justify-between items-start mb-2">
                      <div>
                        <h4 className="font-medium text-gray-900">{symptom.label}</h4>
                        <p className="text-sm text-gray-500">{symptom.desc}</p>
                      </div>
                      <span className="text-lg font-semibold text-medical bg-white px-3 py-1 rounded-lg">
                        {formData[symptom.name as keyof ConsultationFormData] as number}
                      </span>
                    </div>
                    <input
                      type="range"
                      name={symptom.name}
                      min="0"
                      max="3"
                      value={formData[symptom.name as keyof ConsultationFormData] as number}
                      onChange={(e) => handleSliderChange(symptom.name, parseInt(e.target.value))}
                      className="w-full"
                    />
                    <div className="flex justify-between text-xs text-gray-500 mt-1">
                      <span>None (0)</span>
                      <span>Mild (1)</span>
                      <span>Moderate (2)</span>
                      <span>Severe (3)</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Step 3: Additional Information */}
          {currentStep === 3 && (
            <div className="space-y-6">
              <div>
                <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
                  <FileText className="w-5 h-5 text-medical" />
                  Additional Information
                </h3>
                
                <div className="grid md:grid-cols-2 gap-6">
                  <div>
                    <label className="label">Symptoms Duration (months)</label>
                    <input
                      type="number"
                      name="symptoms_duration_months"
                      value={formData.symptoms_duration_months}
                      onChange={handleInputChange}
                      min="0"
                      className="input"
                      placeholder="0"
                    />
                  </div>
                  
                  <div>
                    <label className="label">Current Medications (optional)</label>
                    <input
                      type="text"
                      name="current_medications"
                      value={formData.current_medications}
                      onChange={handleInputChange}
                      className="input"
                      placeholder="List any current medications"
                    />
                  </div>
                </div>

                <div className="mt-6">
                  <label className="flex items-center gap-3 p-4 bg-gray-50 rounded-lg cursor-pointer">
                    <input
                      type="checkbox"
                      name="previous_ad_evaluation"
                      checked={formData.previous_ad_evaluation}
                      onChange={handleInputChange}
                      className="w-5 h-5 text-medical rounded focus:ring-medical"
                    />
                    <span className="text-gray-700">Previous Alzheimer&apos;s Disease Evaluation</span>
                  </label>
                </div>

                <div className="mt-6">
                  <label className="label">Additional Notes (optional)</label>
                  <textarea
                    name="notes"
                    value={formData.notes}
                    onChange={handleInputChange}
                    className="input"
                    rows={4}
                    placeholder="Any additional information about the patient..."
                  />
                </div>
              </div>

              {/* Summary */}
              <div className="border-t pt-6">
                <h4 className="font-semibold text-gray-900 mb-4">Consultation Summary</h4>
                <div className="bg-medical/5 rounded-lg p-4 space-y-2">
                  <div className="flex justify-between">
                    <span className="text-gray-600">Patient Name:</span>
                    <span className="font-medium">{formData.patient_full_name || 'Not specified'}</span>
                  </div>

                  {formData.patient_reference_id && (
                    <div className="flex justify-between">
                      <span className="text-gray-600">Patient ID:</span>
                      <span className="font-medium">{formData.patient_reference_id}</span>
                    </div>
                  )}
                  <div className="flex justify-between">
                    <span className="text-gray-600">Age:</span>
                    <span className="font-medium">{formData.age} years</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Gender:</span>
                    <span className="font-medium capitalize">{formData.gender}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Risk Factors:</span>
                    <span className="font-medium">
                      {[formData.family_history_ad && 'Family History', formData.diabetes && 'Diabetes', formData.hypertension && 'Hypertension', formData.heart_disease && 'Heart Disease', formData.stroke_history && 'Stroke'].filter(Boolean).join(', ') || 'None'}
                    </span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-gray-600">Total Symptom Score:</span>
                    <span className="font-medium">
                      {[
                        formData.memory_complaints,
                        formData.difficulty_concentrating,
                        formData.problem_solving_difficulty,
                        formData.mood_changes,
                        formData.confusion,
                        formData.personality_changes,
                        formData.disorientation,
                        formData.difficulty_with_daily_tasks,
                      ].reduce((a, b) => a + b, 0)} / 24
                    </span>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Navigation Buttons */}
          <div className="flex justify-between mt-8 pt-6 border-t">
            <button
              onClick={prevStep}
              disabled={currentStep === 1}
              className={`btn ${currentStep === 1 ? 'bg-gray-100 text-gray-400 cursor-not-allowed' : 'btn-secondary'}`}
            >
              Previous
            </button>
            
            {currentStep < 3 ? (
              <button
                onClick={nextStep}
                className="btn btn-primary flex items-center gap-2"
              >
                Next
                <ArrowRight className="w-5 h-5" />
              </button>
            ) : (
              <button
                onClick={handleSubmit}
                disabled={submitting}
                className="btn btn-primary flex items-center gap-2"
              >
                {submitting ? (
                  <>
                    <Loader2 className="w-5 h-5 animate-spin" />
                    Submitting...
                  </>
                ) : (
                  <>
                    Submit Consultation
                    <ArrowRight className="w-5 h-5" />
                  </>
                )}
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

