'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import {
  Brain, Users, Activity, Database, Cpu, LogOut,
  BarChart3, TrendingUp, AlertCircle, CheckCircle, Loader2,
  PieChart, Clock, Shield, FileText, Upload, Eye, Play, Plus
} from 'lucide-react';
import { api } from '@/lib/api';
import { isAuthenticated, isAdmin, getUser, logout } from '@/lib/auth';
import { DashboardStats, TrainedModel, ActivityItem, User } from '@/types';
import { Modal, Input, Select, Button } from '@/components';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  PieChart as RechartsPie, Pie, Cell, LineChart, Line, Legend
} from 'recharts';

const COLORS = ['#0284c7', '#9333ea', '#10b981', '#f59e0b', '#ef4444'];

export default function AdminDashboard() {
  const router = useRouter();
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [recentActivity, setRecentActivity] = useState<ActivityItem[]>([]);
  const [activeTab, setActiveTab] = useState('overview');
  const [trainingModels, setTrainingModels] = useState<TrainedModel[]>([]);
  const [datasets, setDatasets] = useState<any[]>([]);
  const [predictions, setPredictions] = useState<any[]>([]);
  const [predictionsError, setPredictionsError] = useState<string | null>(null);
  const [exportLoading, setExportLoading] = useState(false);

  // Modal states
  const [showAddUserModal, setShowAddUserModal] = useState(false);
  const [showTrainModelModal, setShowTrainModelModal] = useState(false);
  const [showUploadDatasetModal, setShowUploadDatasetModal] = useState(false);

  // User management state
  const [users, setUsers] = useState<User[]>([]);
  const [editingUser, setEditingUser] = useState<User | null>(null);

  // Form states
  const [userForm, setUserForm] = useState({
    username: '',
    email: '',
    full_name: '',
    role: 'doctor',
    password: '',
  });
  const [trainForm, setTrainForm] = useState({
    model_type: 'efficientnet',
    epochs: 10,
    learning_rate: 0.001,
    batch_size: 32,
    model_name: '',
    dataset_id: '',
  });
  const [uploadForm, setUploadForm] = useState({
    file: null as File | null,
    name: '',
    description: '',
  });

  // Loading states for modals
  const [userLoading, setUserLoading] = useState(false);
  const [trainLoading, setTrainLoading] = useState(false);
  const [uploadLoading, setUploadLoading] = useState(false);

  // Notification state
  const [notification, setNotification] = useState<{
    type: 'success' | 'error' | 'info';
    message: string;
  } | null>(null);

  // Dataset details modal
  const [showDatasetDetails, setShowDatasetDetails] = useState(false);
  const [selectedDataset, setSelectedDataset] = useState<any>(null);
  const [datasetDetails, setDatasetDetails] = useState<any>(null);
  const [loadingDatasetDetails, setLoadingDatasetDetails] = useState(false);

  // Model details modal
  const [showModelDetails, setShowModelDetails] = useState(false);
  const [selectedModel, setSelectedModel] = useState<any>(null);
  const [modelMetrics, setModelMetrics] = useState<any>(null);
  const [loadingModelMetrics, setLoadingModelMetrics] = useState(false);

  useEffect(() => {
    if (!isAuthenticated()) {
      router.push('/login');
      return;
    }

    if (!isAdmin()) {
      router.push('/consultation');
      return;
    }

    fetchDashboardData();
  }, [router]);

  useEffect(() => {
    if (activeTab === 'predictions') {
      // Always fetch fresh predictions when predictions tab becomes active
      fetchPredictions();
    }
  }, [activeTab]);

  const fetchDashboardData = async () => {
    try {
      const [statsRes, activityRes, modelsRes, datasetsRes, usersRes, predictionsRes] = await Promise.all([
        api.getDashboardStats(),
        api.getRecentActivity(10),
        api.getModels(0, 10),
        api.getDatasets(0, 10),
        api.getUsers({ skip: 0, limit: 50, role: 'doctor' }),
        api.getPredictionsAdmin(0, 50),
      ]);

      setStats(statsRes.data as DashboardStats);
      setRecentActivity(activityRes.data as ActivityItem[]);
      setTrainingModels(modelsRes.data as TrainedModel[]);
      setDatasets(datasetsRes.data || []);
      setUsers(usersRes.data || []);
      setPredictions(predictionsRes.data || []);
    } catch (err) {
      console.error('Failed to fetch dashboard data:', err);
    } finally {
      setLoading(false);
    }
  };

  const fetchPredictions = async () => {
    try {
      setPredictionsError(null);
      const response = await api.getPredictionsAdmin(0, 50);
      const predictionsData = Array.isArray(response.data) ? response.data : [];
      // Sort by created_at descending (most recent first)
      predictionsData.sort((a: any, b: any) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime());
      setPredictions(predictionsData);
    } catch (err) {
      console.error('Failed to fetch predictions:', err);
      setPredictionsError('Failed to load predictions');
    }
  };

  const handleLogout = () => {
    logout();
    router.push('/login');
  };

  const handleExportPredictions = async () => {
    try {
      setExportLoading(true);
      // Use the predictions data from state
      const csvHeaders = ['Patient ID', 'Disease Class', 'Probability', 'Confidence', 'Doctor', 'Date'];
      const csvData = predictions.map((pred: any) => [
        pred.patient_id,
        pred.disease_class,
        pred.probability,
        pred.confidence,
        pred.doctor?.username || 'Unknown',
        pred.created_at
      ]);

      const csvContent = [csvHeaders, ...csvData]
        .map((row: any[]) => row.map((field: any) => `"${field}"`).join(','))
        .join('\n');

      // Download CSV
      const blob = new Blob([csvContent], { type: 'text/csv' });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `predictions_${new Date().toISOString().split('T')[0]}.csv`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);
    } catch (err) {
      console.error('Failed to export predictions:', err);
    } finally {
      setExportLoading(false);
    }
  };

  // User management handlers
  const handleEditUser = (user: User) => {
    setEditingUser(user);
    setUserForm({
      username: user.username,
      email: user.email,
      full_name: user.full_name || '',
      role: user.role,
      password: '', // Don't populate password for editing
    });
    setShowAddUserModal(true);
  };

  const handleDeleteUser = async (userId: string) => {
    if (!confirm('Are you sure you want to delete this user?')) return;

    try {
      await api.deleteUser(userId);
      setNotification({ type: 'success', message: 'User deleted successfully!' });
      fetchDashboardData(); // Refresh data
    } catch (err: any) {
      setNotification({ type: 'error', message: err.response?.data?.detail || 'Failed to delete user' });
    }
  };

  // Modal handlers
  const handleAddUser = async () => {
    try {
      setUserLoading(true);

      if (editingUser && editingUser.id) {
        // Update existing user
        const updateData = {
          username: userForm.username,
          email: userForm.email,
          full_name: userForm.full_name,
          role: userForm.role,
          is_active: true, // Keep active when editing
        };
        await api.updateUser(editingUser.id, updateData);
        setNotification({ type: 'success', message: 'User updated successfully!' });
      } else {
        // Create new user
        if (!userForm.password || userForm.password.length < 8) {
          setNotification({ type: 'error', message: 'Password must be at least 8 characters' });
          setUserLoading(false);
          return;
        }

        await api.createUser({
          username: userForm.username,
          email: userForm.email,
          full_name: userForm.full_name,
          password: userForm.password,
          is_active: true,
        });
        setNotification({ type: 'success', message: 'User created successfully!' });
      }

      setShowAddUserModal(false);
      setEditingUser(null);
      setUserForm({ username: '', email: '', full_name: '', role: 'doctor', password: '' });
      fetchDashboardData(); // Refresh data
    } catch (err: any) {
      setNotification({ type: 'error', message: err.response?.data?.detail || 'Operation failed' });
    } finally {
      setUserLoading(false);
    }
  };

  const handleTrainModel = async () => {
    try {
      setTrainLoading(true);
      await api.trainModel({
        model_type: trainForm.model_type,
        epochs: trainForm.epochs,
        learning_rate: trainForm.learning_rate,
        batch_size: trainForm.batch_size,
        model_name: trainForm.model_name,
        dataset_id: trainForm.dataset_id || undefined,
      });
      setNotification({ type: 'success', message: 'Model training started successfully!' });
      setShowTrainModelModal(false);
      setTrainForm({ model_type: 'efficientnet', epochs: 10, learning_rate: 0.001, batch_size: 32, model_name: '', dataset_id: '' });
      fetchDashboardData(); // Refresh data
    } catch (err: any) {
      setNotification({ type: 'error', message: err.response?.data?.detail || 'Failed to start training' });
    } finally {
      setTrainLoading(false);
    }
  };

  const handleUploadDataset = async () => {
    if (!uploadForm.file) return;

    try {
      setUploadLoading(true);
      const formData = new FormData();
      formData.append('file', uploadForm.file);
      formData.append('name', uploadForm.name);
      formData.append('description', uploadForm.description);

      await api.uploadDataset(formData);
      setNotification({ type: 'success', message: 'Dataset uploaded successfully!' });
      setShowUploadDatasetModal(false);
      setUploadForm({ file: null, name: '', description: '' });
      fetchDashboardData(); // Refresh data
    } catch (err: any) {
      setNotification({ type: 'error', message: err.response?.data?.detail || 'Failed to upload dataset' });
    } finally {
      setUploadLoading(false);
    }
  };

  // Dataset details handler
  const handleViewDatasetDetails = async (dataset: any) => {
    setSelectedDataset(dataset);
    setLoadingDatasetDetails(true);
    setShowDatasetDetails(true);

    try {
      const response = await api.getDatasetDetails(dataset._id || dataset.id);
      setDatasetDetails(response.data);
    } catch (err: any) {
      setNotification({ type: 'error', message: 'Failed to load dataset details' });
      setShowDatasetDetails(false);
    } finally {
      setLoadingDatasetDetails(false);
    }
  };

  // Model details handler
  const handleViewModelDetails = async (model: any) => {
    setSelectedModel(model);
    setShowModelDetails(true);
    setLoadingModelMetrics(true);

    try {
      const response = await api.getModelMetrics(model._id);
      setModelMetrics(response.data);
    } catch (err: any) {
      console.error('Failed to fetch model metrics:', err);
      setModelMetrics(null);
    } finally {
      setLoadingModelMetrics(false);
    }
  };

  // Set production model handler
  const handleSetProductionModel = async (modelId: string) => {
    try {
      console.log('handleSetProductionModel called with:', modelId);
      if (!modelId || modelId === 'undefined') {
        console.error('Model ID is undefined');
        setNotification({ type: 'error', message: 'Model ID is undefined' });
        return;
      }
      await api.setProductionModel(modelId);
      setNotification({ type: 'success', message: 'Production model updated successfully!' });
      fetchDashboardData(); // Refresh data
    } catch (err: any) {
      console.error('Failed to set production model:', err);
      setNotification({ type: 'error', message: err.response?.data?.detail || 'Failed to set production model' });
    }
  };

  // Clear notification after 5 seconds
  useEffect(() => {
    if (notification) {
      const timer = setTimeout(() => setNotification(null), 5000);
      return () => clearTimeout(timer);
    }
  }, [notification]);

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="w-10 h-10 text-medical animate-spin mx-auto mb-4" />
          <p className="text-gray-600">Loading dashboard...</p>
        </div>
      </div>
    );
  }

  // Prepare chart data
  const predictionChartData = stats?.predictions.by_class ? Object.entries(stats.predictions.by_class).map(([name, count]) => ({
    name: name.length > 15 ? name.substring(0, 15) + '...' : name,
    count,
  })) : [];

  const userChartData = [
    { name: 'Admins', value: stats?.users.admins || 0 },
    { name: 'Doctors', value: stats?.users.doctors || 0 },
    { name: 'Users', value: (stats?.users.total || 0) - (stats?.users.admins || 0) - (stats?.users.doctors || 0) },
  ].filter(d => d.value > 0);

  const sidebarLinks = [
    { id: 'overview', label: 'Overview', icon: BarChart3 },
    { id: 'users', label: 'Doctors', icon: Users },
    { id: 'predictions', label: 'Predictions', icon: Activity },
    { id: 'models', label: 'AI Models', icon: Cpu },
    { id: 'datasets', label: 'Datasets', icon: Database },
  ];

  return (
    <div className="min-h-screen bg-gray-50 flex">
      {/* Sidebar */}
      <aside className="w-64 bg-white border-r border-gray-200 min-h-screen">
        <div className="p-4 border-b border-gray-100">
          <div className="flex items-center gap-2">
            <Brain className="w-8 h-8 text-medical" />
            <span className="text-xl font-bold text-gray-900">Cartha Neuro</span>
          </div>
          <p className="text-xs text-gray-500 mt-1">Admin Dashboard</p>
        </div>

        <nav className="p-4 space-y-1">
          {sidebarLinks.map((link) => (
            <button
              key={link.id}
              onClick={() => setActiveTab(link.id)}
              className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-colors ${
                activeTab === link.id
                  ? 'bg-medical text-white'
                  : 'text-gray-600 hover:bg-gray-100'
              }`}
            >
              <link.icon className="w-5 h-5" />
              <span>{link.label}</span>
            </button>
          ))}
        </nav>

        <div className="p-4 border-t border-gray-100">
          <button
            onClick={handleLogout}
            className="w-full flex items-center gap-3 px-4 py-3 text-red-600 hover:bg-red-50 rounded-lg transition-colors"
          >
            <LogOut className="w-5 h-5" />
            <span>Logout</span>
          </button>
        </div>
      </aside>

      {/* Main Content */}
      <main className="flex-1 p-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-2xl font-bold text-gray-900">Dashboard Overview</h1>
          <p className="text-gray-600">Welcome back, {getUser()?.full_name || getUser()?.username}</p>
        </div>

        {/* Notification */}
        {notification && (
          <div className={`mb-6 p-4 rounded-lg ${
            notification.type === 'success' ? 'bg-green-50 border border-green-200' :
            notification.type === 'error' ? 'bg-red-50 border border-red-200' :
            'bg-blue-50 border border-blue-200'
          }`}>
            <div className="flex items-center">
              {notification.type === 'success' ? (
                <CheckCircle className="w-5 h-5 text-green-600 mr-2" />
              ) : notification.type === 'error' ? (
                <AlertCircle className="w-5 h-5 text-red-600 mr-2" />
              ) : (
                <AlertCircle className="w-5 h-5 text-blue-600 mr-2" />
              )}
              <p className={
                notification.type === 'success' ? 'text-green-800' :
                notification.type === 'error' ? 'text-red-800' :
                'text-blue-800'
              }>
                {notification.message}
              </p>
            </div>
          </div>
        )}

        {/* Overview Tab */}
        {activeTab === 'overview' && (
          <div className="space-y-6">
            {/* Stats Cards */}
            <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
              <div className="card">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-600">Total Users</p>
                    <p className="text-3xl font-bold text-gray-900">{stats?.users.total || 0}</p>
                  </div>
                  <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center">
                    <Users className="w-6 h-6 text-blue-600" />
                  </div>
                </div>
                <div className="mt-4 flex items-center text-sm">
                  <TrendingUp className="w-4 h-4 text-green-500 mr-1" />
                  <span className="text-green-600">{stats?.users.recent_registrations || 0} new this week</span>
                </div>
              </div>

              <div className="card">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-600">Total Predictions</p>
                    <p className="text-3xl font-bold text-gray-900">{stats?.predictions.total || 0}</p>
                  </div>
                  <div className="w-12 h-12 bg-purple-100 rounded-lg flex items-center justify-center">
                    <Activity className="w-6 h-6 text-purple-600" />
                  </div>
                </div>
                <div className="mt-4 flex items-center text-sm">
                  <span className="text-gray-600">{stats?.predictions.today || 0} predictions today</span>
                </div>
              </div>

              <div className="card">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-600">Datasets</p>
                    <p className="text-3xl font-bold text-gray-900">{stats?.datasets.total || 0}</p>
                  </div>
                  <div className="w-12 h-12 bg-green-100 rounded-lg flex items-center justify-center">
                    <Database className="w-6 h-6 text-green-600" />
                  </div>
                </div>
                <div className="mt-4 flex items-center text-sm">
                  <span className="text-gray-600">{stats?.datasets.total_size_mb || 0} MB total</span>
                </div>
              </div>

              <div className="card">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-600">Trained Models</p>
                    <p className="text-3xl font-bold text-gray-900">{stats?.models.trained || 0}</p>
                  </div>
                  <div className="w-12 h-12 bg-orange-100 rounded-lg flex items-center justify-center">
                    <Cpu className="w-6 h-6 text-orange-600" />
                  </div>
                </div>
                <div className="mt-4 flex items-center text-sm">
                  {stats?.models.production_model ? (
                    <span className="text-green-600">● {stats.models.production_model}</span>
                  ) : (
                    <span className="text-gray-400">No production model</span>
                  )}
                </div>
              </div>
            </div>

          {/* Charts */}
          <div className="grid lg:grid-cols-2 gap-6">
            <div className="card">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Predictions by Disease Class</h3>
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={predictionChartData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="name" fontSize={12} />
                    <YAxis />
                    <Tooltip />
                    <Bar dataKey="count" fill="#0284c7" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>

            <div className="card">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">User Distribution</h3>
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <RechartsPie>
                    <Pie
                      data={userChartData}
                      cx="50%"
                      cy="50%"
                      labelLine={false}
                      label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                      outerRadius={80}
                      fill="#8884d8"
                      dataKey="value"
                    >
                      {userChartData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip />
                  </RechartsPie>
                </ResponsiveContainer>
              </div>
            </div>
          </div>

          {/* Recent Activity */}
          <div className="card">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Recent Activity</h3>
            <div className="space-y-3">
              {recentActivity.length > 0 ? (
                recentActivity.map((activity) => (
                  <div key={activity.id} className="flex items-center gap-4 p-3 bg-gray-50 rounded-lg">
                    <div className="w-10 h-10 bg-medical/10 rounded-full flex items-center justify-center">
                      <Activity className="w-5 h-5 text-medical" />
                    </div>
                    <div className="flex-1">
                      <p className="font-medium text-gray-900">{activity.result || activity.type}</p>
                      <p className="text-sm text-gray-500">
                        Patient: {activity.patient_id}
                      </p>
                    </div>
                    <div className="text-sm text-gray-500">
                      {activity.timestamp ? new Date(activity.timestamp).toLocaleString() : 'Recently'}
                    </div>
                  </div>
                ))
              ) : (
                <p className="text-gray-500 text-center py-8">No recent activity</p>
              )}
            </div>
          </div>
        </div>
      )}

        {/* Users Tab */}
        {activeTab === 'users' && (
          <div className="space-y-6">
            <div className="card">
              <div className="flex justify-between items-center mb-6">
                <h3 className="text-lg font-semibold text-gray-900">Doctor Management</h3>
                <button onClick={() => setShowAddUserModal(true)} className="btn btn-primary flex items-center gap-2">
                  <Plus className="w-5 h-5" />
                  Add Doctor
                </button>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="bg-gray-50">
                      <th className="table-header">User</th>
                      <th className="table-header">Role</th>
                      <th className="table-header">Status</th>
                      <th className="table-header">Joined</th>
                      <th className="table-header">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-100">
                    {users.map((user) => (
                      <tr key={user.id} className="hover:bg-gray-50">
                        <td className="table-cell">
                          <div>
                            <p className="font-medium text-gray-900">{user.username}</p>
                            <p className="text-sm text-gray-500">{user.email}</p>
                          </div>
                        </td>
                        <td className="table-cell">
                          <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                            user.role === 'admin' ? 'bg-purple-100 text-purple-800' :
                            user.role === 'doctor' ? 'bg-blue-100 text-blue-800' :
                            'bg-gray-100 text-gray-800'
                          }`}>
                            {user.role}
                          </span>
                        </td>
                        <td className="table-cell">
                          <span className={`flex items-center gap-1 ${user.is_active ? 'text-green-600' : 'text-red-600'}`}>
                            {user.is_active ? <CheckCircle className="w-4 h-4" /> : <AlertCircle className="w-4 h-4" />}
                            {user.is_active ? 'Active' : 'Inactive'}
                          </span>
                        </td>
                        <td className="table-cell text-gray-500">
                          {new Date(user.created_at).toLocaleDateString()}
                        </td>
                        <td className="table-cell">
                          <div className="flex gap-2">
                            <button
                              onClick={() => handleEditUser(user)}
                              className="text-blue-600 hover:underline"
                            >
                              Edit
                            </button>
                            {user.username !== 'admin' && (
                              <button
                                  onClick={() => handleDeleteUser(user.id!)}
                                  className="text-red-600 hover:underline"
                                >
                                  Delete
                                </button>
                            )}
                          </div>
                        </td>
                      </tr>
                    ))}
                    {users.length === 0 && (
                      <tr>
                        <td colSpan={5} className="table-cell text-center text-gray-500 py-8">
                          No doctors found. Add your first doctor user.
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

        {/* Predictions Tab */}
        {activeTab === 'predictions' && (
          <div className="card">
            <div className="flex justify-between items-center mb-6">
              <h3 className="text-lg font-semibold text-gray-900">Prediction History</h3>
              <div className="flex gap-4">
                <button onClick={handleExportPredictions} disabled={exportLoading} className="btn btn-secondary flex items-center gap-2">
                  <FileText className="w-5 h-5" />
                  {exportLoading ? 'Exporting...' : 'Export'}
                </button>
              </div>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="bg-gray-50">
                    <th className="table-header">Patient ID</th>
                    <th className="table-header">Prediction</th>
                    <th className="table-header">Probability</th>
                    <th className="table-header">Confidence</th>
                    <th className="table-header">Doctor</th>
                    <th className="table-header">Date</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {predictions.length > 0 ? (
                    predictions.map((pred: any) => (
                      <tr key={pred.prediction_id} className="hover:bg-gray-50">
                        <td className="table-cell font-medium">{pred.patient_id}</td>
                        <td className="table-cell">
                          <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                            pred.disease_class.includes('No Alzheimer') ? 'bg-green-100 text-green-800' :
                            pred.disease_class.includes('Mild Cognitive') ? 'bg-yellow-100 text-yellow-800' :
                            pred.disease_class.includes('Early') ? 'bg-orange-100 text-orange-800' :
                            'bg-red-100 text-red-800'
                          }`}>
                            {pred.disease_class}
                          </span>
                        </td>
                        <td className="table-cell">{(pred.probability * 100).toFixed(1)}%</td>
                        <td className="table-cell">{pred.confidence}</td>
                        <td className="table-cell text-gray-500">{pred.doctor?.username || 'Unknown'}</td>
                        <td className="table-cell text-gray-500">{new Date(pred.created_at).toLocaleDateString()}</td>
                      </tr>
                    ))
                  ) : (
                    <tr>
                      <td colSpan={6} className="table-cell text-center text-gray-500 py-8">
                        {predictionsError ? (
                          <div>
                            <div>{predictionsError}</div>
                            <div className="text-xs mt-2">Check console for more details</div>
                          </div>
                        ) : (
                          'No predictions yet. Predictions will appear here after doctors use the system.'
                        )}
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Models Tab */}
        {activeTab === 'models' && (
          <div className="space-y-6">
            <div className="card">
              <div className="flex justify-between items-center mb-6">
                <h3 className="text-lg font-semibold text-gray-900">AI Models</h3>
                <button onClick={() => setShowTrainModelModal(true)} className="btn btn-primary flex items-center gap-2">
                  <Cpu className="w-5 h-5" />
                  Train New Model
                </button>
              </div>
              <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
                {trainingModels.length > 0 ? (
                  trainingModels.map((model) => (
                    <div key={model._id} className="border rounded-lg p-4 hover:shadow-md transition-shadow">
                      <div className="flex justify-between items-start mb-3">
                        <div className="flex items-center gap-2">
                          <Cpu className="w-5 h-5 text-medical" />
                          <h4 className="font-semibold text-gray-900">{model.name}</h4>
                        </div>
                        {model.is_production && (
                          <span className="px-2 py-1 bg-green-100 text-green-800 text-xs rounded-full">Production</span>
                        )}
                      </div>

                      <div className="space-y-2 text-sm mb-4">
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

                      <div className="flex gap-2">
                        <button
                          onClick={() => handleViewModelDetails(model)}
                          className="flex-1 flex items-center justify-center gap-1 px-3 py-2 text-sm bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors"
                        >
                          <Eye className="w-4 h-4" />
                          Details
                        </button>
                        {!model.is_production && model.status === 'completed' && (
                          <button
                            onClick={() => handleSetProductionModel(model._id)}
                            className="flex-1 flex items-center justify-center gap-1 px-3 py-2 text-sm bg-medical text-white rounded-lg hover:bg-medical/90 transition-colors"
                          >
                            <Play className="w-4 h-4" />
                            Set Prod
                          </button>
                        )}
                      </div>
                    </div>
                  ))
                ) : (
                  <>
                    <div className="border rounded-lg p-4 hover:shadow-md transition-shadow">
                      <div className="flex justify-between items-start mb-3">
                        <div className="flex items-center gap-2">
                          <Cpu className="w-5 h-5 text-medical" />
                          <h4 className="font-semibold text-gray-900">efficientnet_demo</h4>
                        </div>
                        <span className="px-2 py-1 bg-green-100 text-green-800 text-xs rounded-full">Production</span>
                      </div>

                      <div className="space-y-2 text-sm mb-4">
                        <div className="flex justify-between">
                          <span className="text-gray-500">Type</span>
                          <span className="capitalize">efficientnet</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-500">Status</span>
                          <span className="px-2 py-0.5 rounded-full text-xs bg-green-100 text-green-800">completed</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-500">Accuracy</span>
                          <span className="text-medical font-medium">85.5%</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-500">Created</span>
                          <span>2024-01-01</span>
                        </div>
                      </div>

                      <div className="flex gap-2">
                        <button
                          onClick={() => setNotification({ type: 'info', message: 'Demo model - no detailed metrics available' })}
                          className="flex-1 flex items-center justify-center gap-1 px-3 py-2 text-sm bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors"
                        >
                          <Eye className="w-4 h-4" />
                          Details
                        </button>
                      </div>
                    </div>
                    <div className="border rounded-lg p-4 hover:shadow-md transition-shadow">
                      <div className="flex justify-between items-start mb-3">
                        <div className="flex items-center gap-2">
                          <Cpu className="w-5 h-5 text-medical" />
                          <h4 className="font-semibold text-gray-900">resnet_demo</h4>
                        </div>
                      </div>

                      <div className="space-y-2 text-sm mb-4">
                        <div className="flex justify-between">
                          <span className="text-gray-500">Type</span>
                          <span className="capitalize">resnet</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-500">Status</span>
                          <span className="px-2 py-0.5 rounded-full text-xs bg-green-100 text-green-800">completed</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-500">Accuracy</span>
                          <span className="text-medical font-medium">83.2%</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-500">Created</span>
                          <span>2024-01-01</span>
                        </div>
                      </div>

                      <div className="flex gap-2">
                        <button
                          onClick={() => setNotification({ type: 'info', message: 'Demo model - no detailed metrics available' })}
                          className="flex-1 flex items-center justify-center gap-1 px-3 py-2 text-sm bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors"
                        >
                          <Eye className="w-4 h-4" />
                          Details
                        </button>
                        <button
                          onClick={() => setNotification({ type: 'info', message: 'Demo model - cannot set as production' })}
                          className="flex-1 flex items-center justify-center gap-1 px-3 py-2 text-sm bg-medical text-white rounded-lg hover:bg-medical/90 transition-colors"
                        >
                          <Play className="w-4 h-4" />
                          Set Prod
                        </button>
                      </div>
                    </div>
                  </>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Datasets Tab */}
        {activeTab === 'datasets' && (
          <div className="card">
            <div className="flex justify-between items-center mb-6">
              <h3 className="text-lg font-semibold text-gray-900">Datasets</h3>
              <button onClick={() => setShowUploadDatasetModal(true)} className="btn btn-primary flex items-center gap-2">
                <Upload className="w-5 h-5" />
                Upload Dataset
              </button>
            </div>
            <div className="space-y-4">
              {datasets.length > 0 ? (
                datasets.map((dataset) => (
                  <div key={dataset.id || dataset._id} className="border rounded-lg p-4 flex justify-between items-center">
                    <div>
                      <h4 className="font-semibold">{dataset.name}</h4>
                      <p className="text-sm text-gray-600">
                        {dataset.description || 'No description'}
                        {dataset.num_images && ` • ${dataset.num_images} images`}
                        {dataset.num_classes && ` • ${dataset.num_classes} classes`}
                      </p>
                    </div>
                    <div className="text-right">
                      <p className="text-sm text-gray-600">
                        {dataset.size_mb ? `${dataset.size_mb} MB` : 'Size unknown'}
                      </p>
                      <button
                        onClick={() => handleViewDatasetDetails(dataset)}
                        className="text-medical hover:underline text-sm"
                      >
                        View Details
                      </button>
                    </div>
                  </div>
                ))
              ) : (
                <p className="text-gray-500 text-center py-8">No datasets uploaded yet</p>
              )}
            </div>
          </div>
        )}


        {/* Modals */}
        {/* Add/Edit User Modal */}
        <Modal
          isOpen={showAddUserModal}
          onClose={() => {
            setShowAddUserModal(false);
            setEditingUser(null);
            setUserForm({ username: '', email: '', full_name: '', role: 'doctor', password: '' });
          }}
          title={editingUser ? 'Edit Doctor' : 'Add New Doctor'}
        >
          <div className="space-y-4">
            <Input
              label="Username"
              value={userForm.username}
              onChange={(e) => setUserForm({...userForm, username: e.target.value})}
              placeholder="Enter username"
              required
            />
            <Input
              label="Email"
              type="email"
              value={userForm.email}
              onChange={(e) => setUserForm({...userForm, email: e.target.value})}
              placeholder="Enter email"
              required
            />
            <Input
              label="Full Name"
              value={userForm.full_name}
              onChange={(e) => setUserForm({...userForm, full_name: e.target.value})}
              placeholder="Enter full name"
            />
            {!editingUser && (
              <Input
                label="Password"
                type="password"
                value={userForm.password}
                onChange={(e) => setUserForm({...userForm, password: e.target.value})}
                placeholder="Enter password"
                required
                helperText="Must be at least 8 characters"
              />
            )}
            <Select
              label="Role"
              value={userForm.role}
              onChange={(value) => setUserForm({...userForm, role: value})}
              options={[
                { value: 'doctor', label: 'Doctor' },
                { value: 'admin', label: 'Admin' },
              ]}
            />
            <div className="flex justify-end gap-3 pt-4">
              <Button
                variant="secondary"
                onClick={() => {
                  setShowAddUserModal(false);
                  setEditingUser(null);
                  setUserForm({ username: '', email: '', full_name: '', role: 'doctor', password: '' });
                }}
              >
                Cancel
              </Button>
              <Button
                onClick={handleAddUser}
                loading={userLoading}
                disabled={!userForm.username || !userForm.email || (!editingUser && !userForm.password)}
              >
                {editingUser ? 'Update' : 'Add'} Doctor
              </Button>
            </div>
          </div>
        </Modal>

        {/* Train Model Modal */}
        <Modal
          isOpen={showTrainModelModal}
          onClose={() => setShowTrainModelModal(false)}
          title="Train New Model"
        >
          <div className="space-y-4">
            <Input
              label="Model Name"
              value={trainForm.model_name}
              onChange={(e) => setTrainForm({...trainForm, model_name: e.target.value})}
              placeholder="Enter model name"
            />
            <Select
              label="Model Type"
              value={trainForm.model_type}
              onChange={(value) => setTrainForm({...trainForm, model_type: value})}
              options={[
                { value: 'efficientnet', label: 'EfficientNet' },
                { value: 'resnet', label: 'ResNet50' },
              ]}
            />
            <Select
              label="Dataset (Optional)"
              value={trainForm.dataset_id}
              onChange={(value) => setTrainForm({...trainForm, dataset_id: value})}
              options={[
                { value: '', label: 'Use synthetic data' },
                ...datasets.map((dataset) => ({
                  value: dataset._id || dataset.id,
                  label: dataset.name
                }))
              ]}
            />
            <Input
              label="Epochs"
              type="number"
              value={trainForm.epochs}
              onChange={(e) => setTrainForm({...trainForm, epochs: parseInt(e.target.value)})}
              min="1"
              max="100"
            />
            <Input
              label="Learning Rate"
              type="number"
              step="0.0001"
              value={trainForm.learning_rate}
              onChange={(e) => setTrainForm({...trainForm, learning_rate: parseFloat(e.target.value)})}
              min="0.0001"
              max="0.1"
            />
            <Input
              label="Batch Size"
              type="number"
              value={trainForm.batch_size}
              onChange={(e) => setTrainForm({...trainForm, batch_size: parseInt(e.target.value)})}
              min="1"
              max="128"
            />
            <div className="flex justify-end gap-3 pt-4">
              <Button
                variant="secondary"
                onClick={() => setShowTrainModelModal(false)}
              >
                Cancel
              </Button>
              <Button
                onClick={handleTrainModel}
                loading={trainLoading}
                disabled={!trainForm.model_name.trim()}
              >
                Start Training
              </Button>
            </div>
          </div>
        </Modal>

        {/* Upload Dataset Modal */}
        <Modal
          isOpen={showUploadDatasetModal}
          onClose={() => setShowUploadDatasetModal(false)}
          title="Upload Dataset"
        >
          <div className="space-y-4">
            <Input
              label="Dataset Name"
              value={uploadForm.name}
              onChange={(e) => setUploadForm({...uploadForm, name: e.target.value})}
              placeholder="Enter dataset name"
            />
            <Input
              label="Description"
              value={uploadForm.description}
              onChange={(e) => setUploadForm({...uploadForm, description: e.target.value})}
              placeholder="Enter description"
            />
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Dataset File
              </label>
              <input
                type="file"
                accept=".zip,.tar.gz,.tar,.rar"
                onChange={(e) => setUploadForm({...uploadForm, file: e.target.files?.[0] || null})}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-medical focus:border-transparent"
              />
              <p className="text-sm text-gray-500 mt-1">
                Supported formats: ZIP, TAR.GZ, TAR, RAR
              </p>
            </div>
            <div className="flex justify-end gap-3 pt-4">
              <Button
                variant="secondary"
                onClick={() => setShowUploadDatasetModal(false)}
              >
                Cancel
              </Button>
              <Button
                onClick={handleUploadDataset}
                loading={uploadLoading}
                disabled={!uploadForm.file || !uploadForm.name}
              >
                Upload Dataset
              </Button>
            </div>
          </div>
        </Modal>

        {/* Dataset Details Modal */}
        <Modal
          isOpen={showDatasetDetails}
          onClose={() => setShowDatasetDetails(false)}
          title={selectedDataset ? `Dataset: ${selectedDataset.name}` : 'Dataset Details'}
          size="lg"
        >
          {loadingDatasetDetails ? (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="w-6 h-6 text-medical animate-spin mr-2" />
              <span>Loading dataset details...</span>
            </div>
          ) : datasetDetails ? (
            <div className="space-y-6">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <h4 className="font-semibold text-gray-900">Basic Information</h4>
                  <div className="mt-2 space-y-1 text-sm">
                    <p><span className="font-medium">Name:</span> {datasetDetails.name}</p>
                    <p><span className="font-medium">Description:</span> {datasetDetails.description || 'No description'}</p>
                    <p><span className="font-medium">Total Images:</span> {datasetDetails.image_count || 0}</p>
                    <p><span className="font-medium">Size:</span> {datasetDetails.size_mb || 0} MB</p>
                    <p><span className="font-medium">Classes:</span> {datasetDetails.classes?.length || 0}</p>
                  </div>
                </div>
                <div>
                  <h4 className="font-semibold text-gray-900">Class Distribution</h4>
                  <div className="mt-2 space-y-2">
                    {datasetDetails.class_distribution ? (
                      Object.entries(datasetDetails.class_distribution).map(([className, count]: [string, any]) => (
                        <div key={className} className="flex justify-between text-sm">
                          <span>{className}:</span>
                          <span className="font-medium">{count} images</span>
                        </div>
                      ))
                    ) : (
                      <p className="text-sm text-gray-500">No class distribution available</p>
                    )}
                  </div>
                </div>
              </div>

              {datasetDetails.classes && (
                <div>
                  <h4 className="font-semibold text-gray-900 mb-2">Classes</h4>
                  <div className="flex flex-wrap gap-2">
                    {datasetDetails.classes.map((className: string) => (
                      <span key={className} className="px-3 py-1 bg-medical/10 text-medical rounded-full text-sm">
                        {className}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="text-center py-8">
              <p className="text-gray-500">Failed to load dataset details</p>
            </div>
          )}
        </Modal>

        {/* Model Details Modal */}
        <Modal
          isOpen={showModelDetails}
          onClose={() => setShowModelDetails(false)}
          title="Model Details"
          size="lg"
        >
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
              {loadingModelMetrics ? (
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
      </main>
    </div>
  );
}
