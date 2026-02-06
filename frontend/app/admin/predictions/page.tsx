'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Search, Filter, Download, Loader2 } from 'lucide-react';
import { api } from '@/lib/api';
import { isAuthenticated, isAdmin, logout } from '@/lib/auth';
import { Card, Button, Input, Badge } from '@/components';
import { Prediction, Doctor } from '@/types';

export default function AdminPredictionsPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(true);
  const [predictions, setPredictions] = useState<Prediction[]>([]);
  const [search, setSearch] = useState('');
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [filter, setFilter] = useState('all');
  const [dateFrom, setDateFrom] = useState('');
  const [dateTo, setDateTo] = useState('');

  useEffect(() => {
    if (!isAuthenticated()) {
      router.push('/login');
      return;
    }
    if (!isAdmin()) {
      router.push('/consultation');
      return;
    }
    fetchPredictions();
  }, [router, page, filter]);

  const fetchPredictions = async () => {
    try {
      setLoading(true);
      const response = await api.getPredictionsAdmin(0, 50); // Fetch first 50 predictions like users
      setPredictions(response.data || []);
      setTotalPages(1); // No pagination for now
    } catch (err) {
      console.error('Failed to fetch predictions');
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = () => {
    logout();
    router.push('/login');
  };

  const filteredPredictions = predictions.filter(pred => {
    const matchesSearch = !search ||
      pred.patient_full_name?.toLowerCase().includes(search.toLowerCase()) ||
      pred.patient_id.toLowerCase().includes(search.toLowerCase());

    const matchesFilter = filter === 'all' ||
      (filter === 'no_ad' && pred.disease_class.includes('No Alzheimer')) ||
      (filter === 'mci' && pred.disease_class.includes('Mild Cognitive')) ||
      (filter === 'early' && pred.disease_class.includes('Early')) ||
      (filter === 'moderate' && pred.disease_class.includes('Moderate')) ||
      (filter === 'advanced' && pred.disease_class.includes('Advanced'));

    const predDate = new Date(pred.created_at);
    const matchesDateFrom = !dateFrom || predDate >= new Date(dateFrom);
    const matchesDateTo = !dateTo || predDate <= new Date(dateTo + 'T23:59:59');

    return matchesSearch && matchesFilter && matchesDateFrom && matchesDateTo;
  });

  const exportData = () => {
    const csv = filteredPredictions.map(p =>
      `${p.patient_full_name || 'Unknown'},${p.patient_id},${p.disease_class},${(p.probability * 100).toFixed(1)}%,${p.confidence},${new Date(p.created_at).toISOString()}`
    ).join('\n');

    const header = 'Patient Name,Patient ID,Prediction,Probability,Confidence,Date\n';
    const blob = new Blob([header + csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'predictions_export.csv';
    a.click();
  };

  const getPredictionBadge = (prediction: string | undefined) => {
    if (!prediction) return 'gray';
    if (prediction.includes('No Alzheimer')) return 'success';
    if (prediction.includes('Mild Cognitive')) return 'warning';
    if (prediction.includes('Early')) return 'orange';
    if (prediction.includes('Moderate')) return 'red';
    return 'purple';
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
          <button className="w-full flex items-center gap-3 px-4 py-3 rounded-lg bg-medical text-white">Predictions</button>
          <button onClick={() => router.push('/admin/models')} className="w-full flex items-center gap-3 px-4 py-3 rounded-lg text-gray-600 hover:bg-gray-100">Models</button>
          <button onClick={() => router.push('/admin/datasets')} className="w-full flex items-center gap-3 px-4 py-3 rounded-lg text-gray-600 hover:bg-gray-100">Datasets</button>
        </nav>

        <div className="p-4 border-t border-gray-100 mt-auto">
          <button onClick={handleLogout} className="w-full flex items-center gap-3 px-4 py-3 text-red-600 hover:bg-red-50 rounded-lg">Logout</button>
        </div>
      </aside>

      <main className="flex-1 p-8">
        <div className="flex justify-between items-center mb-6">
          <h1 className="text-2xl font-bold text-gray-900">Prediction History</h1>
          <Button onClick={exportData} icon={<Download className="w-4 h-4" />}>Export CSV</Button>
        </div>

        <Card className="mb-4">
          <div className="flex flex-wrap gap-4">
            <div className="flex-1 min-w-[200px]">
              <Input
                placeholder="Search by patient name or ID..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                leftIcon={<Search className="w-4 h-4" />}
              />
            </div>
            <select
              value={filter}
              onChange={(e) => setFilter(e.target.value)}
              className="rounded-lg border border-gray-300 px-4 py-2 focus:outline-none focus:ring-2 focus:ring-medical"
            >
              <option value="all">All Predictions</option>
              <option value="no_ad">No AD</option>
              <option value="mci">MCI</option>
              <option value="early">Early AD</option>
              <option value="moderate">Moderate AD</option>
              <option value="advanced">Advanced AD</option>
            </select>
            <Input
              type="date"
              placeholder="From"
              value={dateFrom}
              onChange={(e) => setDateFrom(e.target.value)}
              className="w-40"
            />
            <Input
              type="date"
              placeholder="To"
              value={dateTo}
              onChange={(e) => setDateTo(e.target.value)}
              className="w-40"
            />
          </div>
        </Card>

        <Card>
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="w-8 h-8 animate-spin text-medical" />
            </div>
          ) : (
            <>
              <table className="w-full">
              <thead>
                  <tr className="bg-gray-50 text-left">
                    <th className="px-4 py-3 text-sm font-medium text-gray-500">Patient</th>
                    <th className="px-4 py-3 text-sm font-medium text-gray-500">Prediction</th>
                    <th className="px-4 py-3 text-sm font-medium text-gray-500">Probability</th>
                    <th className="px-4 py-3 text-sm font-medium text-gray-500">Confidence</th>
                    <th className="px-4 py-3 text-sm font-medium text-gray-500">Doctor</th>
                    <th className="px-4 py-3 text-sm font-medium text-gray-500">Date</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {filteredPredictions.map((pred) => (
                    <tr key={pred._id} className="hover:bg-gray-50">
                      <td className="px-4 py-3">
                        <div>
                          <p className="font-medium">{pred.patient_full_name || 'Unknown'}</p>
                          <p className="text-sm text-gray-500">{pred.patient_id}</p>
                        </div>
                      </td>
                      <td className="px-4 py-3">
                        <Badge variant={getPredictionBadge(pred.disease_class) as any}>{pred.disease_class}</Badge>
                      </td>
                      <td className="px-4 py-3">{(pred.probability * 100).toFixed(1)}%</td>
                      <td className="px-4 py-3">{pred.confidence}</td>
                      <td className="px-4 py-3">
                        <div>
                          <p className="text-sm font-medium text-gray-900">
                            {(pred.doctor as Doctor)?.full_name || (pred.doctor as Doctor)?.username || 'Unknown'}
                          </p>
                          <p className="text-xs text-gray-500">
                            {(pred.doctor as Doctor)?.email || ''}
                          </p>
                        </div>
                      </td>
                      <td className="px-4 py-3 text-sm text-gray-500">
                        {new Date(pred.created_at).toLocaleString()}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>

              {/* Pagination removed for simplicity - shows first 50 predictions */}
            </>
          )}
        </Card>
      </main>
    </div>
  );
}

