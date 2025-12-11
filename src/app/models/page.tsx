"use client"

import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Brain, Cpu, Database, Activity, RefreshCw, Download, Trash2, Settings, Zap } from "lucide-react"
import { CarthaNeuroApi, ModelInfo, KerasModelInfo ,DatasetInfo} from "@/lib/api"
import { TrainingConfig } from "@/components/training-config"
import { AdminModelManager } from "@/components/admin-model-manager"

interface HealthStatus {
  status: string
  models_loaded: string[]
  uptime: string
  memory_usage?: Record<string, any>
}

export default function ModelsPage() {
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [healthStatus, setHealthStatus] = useState<HealthStatus | null>(null)
  const [pytorchModels, setPytorchModels] = useState<ModelInfo[]>([])
  const [kerasModels, setKerasModels] = useState<KerasModelInfo[]>([])
  const [datasetInfo, setDatasetInfo] = useState<DatasetInfo | null>(null)
  const [trainingJobs, setTrainingJobs] = useState<string[]>([])
  const [isAdmin, setIsAdmin] = useState(false)

  useEffect(() => {
    loadData()
    checkAdminStatus()
  }, [])

  const loadData = async () => {
    setLoading(true)
    setError(null)

    try {
      const [health, models, keras, dataset] = await Promise.all([
        CarthaNeuroApi.healthCheck(),
        CarthaNeuroApi.getModels(),
        CarthaNeuroApi.getKerasModels(),
        CarthaNeuroApi.getDatasetInfo()
      ])

      setHealthStatus(health)
      setPytorchModels(models)
      setKerasModels(keras?.models || [])
      setDatasetInfo(dataset)
    } catch (error) {
      console.error('Failed to load models data:', error)
      setError(error instanceof Error ? error.message : 'Failed to load models data')
    } finally {
      setLoading(false)
    }
  }

  const checkAdminStatus = () => {
    // Simple admin check - in a real app, this would come from authentication state
    const user = localStorage.getItem('user')
    if (user) {
      try {
        const userData = JSON.parse(user)
        setIsAdmin(userData.role === 'admin' || userData.is_admin === true)
      } catch {
        setIsAdmin(false)
      }
    } else {
      setIsAdmin(false)
    }
  }

  const reloadModels = async (modelTypes?: string[]) => {
    try {
      await CarthaNeuroApi.reloadModels(modelTypes)
      await loadData() // Refresh data
    } catch (error) {
      console.error('Failed to reload models:', error)
      setError(error instanceof Error ? error.message : 'Failed to reload models')
    }
  }

  const handleTrainingStart = (jobId: string) => {
    setTrainingJobs(prev => [...prev, jobId])
    // In a real app, you might want to start polling for job status here
    console.log('Training started with job ID:', jobId)
  }

  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'healthy':
      case 'loaded':
        return 'bg-green-500'
      case 'unavailable':
      case 'error':
        return 'bg-red-500'
      case 'loading':
        return 'bg-yellow-500'
      default:
        return 'bg-gray-500'
    }
  }

  const getDeviceIcon = (device: string) => {
    if (!device) return <Database className="h-4 w-4" />
    if (device.includes('cuda') || device.includes('gpu')) {
      return <Zap className="h-4 w-4 text-yellow-500" />
    }
    return <Cpu className="h-4 w-4 text-blue-500" />
  }

  if (loading) {
    return (
      <div className="container mx-auto px-4 py-8">
        <div className="flex items-center justify-center min-h-96">
          <div className="text-center">
            <RefreshCw className="h-8 w-8 animate-spin mx-auto mb-4 text-primary" />
            <p className="text-lg text-slate-600 dark:text-slate-400">Loading models...</p>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="max-w-6xl mx-auto">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold font-heading mb-4">Models Management</h1>
          <p className="text-lg text-slate-600 dark:text-slate-400">
            Monitor and manage AI models for brain tumor classification
          </p>
        </div>

        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-6">
            <p className="text-red-600">{error}</p>
            <Button 
              onClick={loadData} 
              variant="outline" 
              size="sm" 
              className="mt-2"
            >
              Retry
            </Button>
          </div>
        )}

        {/* System Status */}
        {healthStatus && (
          <Card className="mb-8">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Activity className="h-5 w-5" />
                System Status
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid md:grid-cols-4 gap-4">
                <div className="text-center">
                  <div className="flex items-center justify-center mb-2">
                    <div className={`w-3 h-3 rounded-full ${getStatusColor(healthStatus.status)}`} />
                  </div>
                  <p className="text-sm font-medium">{healthStatus.status}</p>
                  <p className="text-xs text-slate-500">System Status</p>
                </div>
                <div className="text-center">
                  <p className="text-2xl font-bold">{healthStatus.models_loaded.length}</p>
                  <p className="text-xs text-slate-500">Models Loaded</p>
                </div>
                <div className="text-center">
                  <p className="text-sm font-medium">{healthStatus.uptime}</p>
                  <p className="text-xs text-slate-500">Uptime</p>
                </div>
                <div className="text-center">
                  {healthStatus.memory_usage?.system_memory_percent !== undefined ? (
                    <>
                      <p className="text-sm font-medium">
                        {healthStatus.memory_usage.system_memory_percent?.toFixed(1)}%
                      </p>
                      <p className="text-xs text-slate-500">Memory Usage</p>
                    </>
                  ) : (
                    <p className="text-sm text-slate-500">N/A</p>
                  )}
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        <Tabs defaultValue="pytorch" className="space-y-6">
          <TabsList className={`grid w-full ${isAdmin ? 'grid-cols-4' : 'grid-cols-3'}`}>
            <TabsTrigger value="pytorch">PyTorch Models</TabsTrigger>
            <TabsTrigger value="keras">Keras Models</TabsTrigger>
            <TabsTrigger value="dataset">Dataset Info</TabsTrigger>
            {isAdmin && <TabsTrigger value="admin">Admin Panel</TabsTrigger>}
          </TabsList>

          {/* PyTorch Models */}
          <TabsContent value="pytorch">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Brain className="h-5 w-5" />
                    PyTorch Models
                  </div>
                  <Button onClick={() => reloadModels()} size="sm">
                    <RefreshCw className="h-4 w-4 mr-2" />
                    Reload All
                  </Button>
                </CardTitle>
              </CardHeader>
              <CardContent>
                {pytorchModels.length === 0 ? (
                  <div className="text-center py-8">
                    <Brain className="h-12 w-12 mx-auto mb-4 text-slate-300" />
                    <p className="text-slate-500">No PyTorch models available</p>
                  </div>
                ) : (
                  <div className="grid gap-4">
                    {pytorchModels.map((model) => (
                      <div key={model.name} className="border rounded-lg p-4">
                        <div className="flex items-center justify-between mb-3">
                          <div className="flex items-center gap-3">
                            <div className={`w-3 h-3 rounded-full ${getStatusColor(model.status)}`} />
                            <h3 className="font-semibold">{model.name}</h3>
                            <Badge variant="outline">{model.type}</Badge>
                            <Badge variant={model.device?.includes('cuda') ? "default" : "secondary"}>
                              {model.device?.includes('cuda') ? (
                                <>
                                  <Zap className="h-3 w-3 mr-1" />
                                  GPU
                                </>
                              ) : (
                                <>
                                  <Cpu className="h-3 w-3 mr-1" />
                                  CPU
                                </>
                              )}
                            </Badge>
                          </div>
                          <div className="flex items-center gap-2">
                            {getDeviceIcon(model.device)}
                            <span className="text-sm text-slate-500">{model.device || 'Unknown'}</span>
                          </div>
                        </div>
                        
                        <div className="grid md:grid-cols-3 gap-4 text-sm">
                          <div>
                            <p className="text-slate-500">Classes: {model.num_classes}</p>
                            <div className="flex flex-wrap gap-1 mt-1">
                              {model.classes?.slice(0, 3).map((cls) => (
                                <Badge key={cls} variant="secondary" className="text-xs">
                                  {cls}
                                </Badge>
                              )) || []}
                              {(model.classes?.length || 0) > 3 && (
                                <Badge variant="secondary" className="text-xs">
                                  +{(model.classes?.length || 0) - 3} more
                                </Badge>
                              )}
                            </div>
                          </div>
                          <div>
                            {model.loaded_at && (
                              <p className="text-slate-500">
                                Loaded: {new Date(model.loaded_at * 1000).toLocaleString()}
                              </p>
                            )}
                            {model.load_time && (
                              <p className="text-slate-500">
                                Load time: {model.load_time.toFixed(2)}s
                              </p>
                            )}
                          </div>
                          <div className="flex gap-2">
                            <Button size="sm" variant="outline">
                              <Settings className="h-4 w-4 mr-1" />
                              Configure
                            </Button>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* Keras Models */}
          <TabsContent value="keras">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Cpu className="h-5 w-5" />
                    Keras Models
                  </div>
                  <Button onClick={() => reloadModels(['keras'])} size="sm">
                    <RefreshCw className="h-4 w-4 mr-2" />
                    Refresh
                  </Button>
                </CardTitle>
              </CardHeader>
              <CardContent>
                {kerasModels.length === 0 ? (
                  <div className="text-center py-8">
                    <Cpu className="h-12 w-12 mx-auto mb-4 text-slate-300" />
                    <p className="text-slate-500">No Keras models available</p>
                    <p className="text-sm text-slate-400 mt-2">
                      Train models using the Training section
                    </p>
                  </div>
                ) : (
                  <div className="grid gap-4">
                    {kerasModels.map((model) => (
                      <div key={model.model_name} className="border rounded-lg p-4">
                        <div className="flex items-center justify-between mb-3">
                          <div className="flex items-center gap-3">
                            <div className="w-3 h-3 rounded-full bg-blue-500" />
                            <h3 className="font-semibold">{model.model_name}</h3>
                            <Badge variant="outline">{model.model_type}</Badge>
                          </div>
                          <div className="flex items-center gap-2">
                            <span className="text-sm text-slate-500">
                              {model.size_mb.toFixed(1)} MB
                            </span>
                          </div>
                        </div>
                        
                        <div className="grid md:grid-cols-3 gap-4 text-sm">
                          <div>
                            <p className="text-slate-500">
                              Created: {new Date(model.created_at * 1000).toLocaleDateString()}
                            </p>
                            {model.classes && (
                              <div className="flex flex-wrap gap-1 mt-1">
                                {model.classes.slice(0, 3).map((cls) => (
                                  <Badge key={cls} variant="secondary" className="text-xs">
                                    {cls}
                                  </Badge>
                                ))}
                              </div>
                            )}
                          </div>
                          <div>
                            <p className="text-slate-500">Framework: {model.framework}</p>
                            {model.num_classes && (
                              <p className="text-slate-500">Classes: {model.num_classes}</p>
                            )}
                          </div>
                          <div className="flex gap-2">
                            <Button size="sm" variant="outline">
                              <Download className="h-4 w-4 mr-1" />
                              Download
                            </Button>
                            <Button size="sm" variant="outline">
                              <Trash2 className="h-4 w-4" />
                            </Button>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* Dataset Info */}
          <TabsContent value="dataset">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Database className="h-5 w-5" />
                  Dataset Information
                </CardTitle>
              </CardHeader>
              <CardContent>
                {datasetInfo ? (
                  <div className="space-y-6">
                    <div className="grid md:grid-cols-3 gap-6">
                      <div className="text-center">
                        <p className="text-3xl font-bold">{datasetInfo.total_samples}</p>
                        <p className="text-sm text-slate-500">Total Samples</p>
                      </div>
                      <div className="text-center">
                        <p className="text-3xl font-bold">{datasetInfo.classes?.length || 0}</p>
                        <p className="text-sm text-slate-500">Classes</p>
                      </div>
                      <div className="text-center">
                        <p className="text-3xl font-bold">
                          {datasetInfo.available_formats?.length || 0}
                        </p>
                        <p className="text-sm text-slate-500">Formats</p>
                      </div>
                    </div>

                    <div>
                      <h3 className="font-semibold mb-3">Class Distribution</h3>
                      <div className="space-y-2">
                        {Object.entries(datasetInfo.class_distribution || {}).map(([className, count]) => {
                          const countNum = Number(count) || 0
                          return (
                          <div key={className} className="flex items-center justify-between">
                            <span className="capitalize">{className}</span>
                            <div className="flex items-center gap-2">
                              <div className="w-32 bg-slate-200 rounded-full h-2">
                                <div 
                                  className="bg-primary h-2 rounded-full"
                                  style={{ 
                                    width: `${datasetInfo.total_samples > 0 ? (countNum / datasetInfo.total_samples) * 100 : 0}%` 
                                  }}
                                />
                              </div>
                              <span className="text-sm text-slate-500">{countNum}</span>
                            </div>
                          </div>
                          )
                        })}
                      </div>
                    </div>

                    <div>
                      <h3 className="font-semibold mb-3">Available Formats</h3>
                      <div className="flex gap-2">
                        {(datasetInfo.available_formats || []).map((format: string) => (
                          <Badge key={format} variant="outline">
                            {format.toUpperCase()}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  </div>
                ) : (
                  <div className="text-center py-8">
                    <Database className="h-12 w-12 mx-auto mb-4 text-slate-300" />
                    <p className="text-slate-500">No dataset information available</p>
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* Admin Panel */}
          {isAdmin && (
            <TabsContent value="admin">
              <AdminModelManager isAdmin={true} />
            </TabsContent>
          )}
        </Tabs>
      </div>
    </div>
  )
}