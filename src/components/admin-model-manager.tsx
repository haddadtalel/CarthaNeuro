"use client"

import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import { 
  Database, 
  Cloud, 
  Trash2, 
  RefreshCw, 
  Shield, 
  Loader2, 
  CheckCircle, 
  AlertCircle,
  Upload,
  HardDrive,
  Clock,
  User
} from "lucide-react"
import { CarthaNeuroApi } from "@/lib/api"

interface AutoSavedModel {
  model_name: string
  path: string
  saved_at: string
  model_type: string
  framework: string
  save_id: string
  size_mb?: number
}

interface AdminModelManagerProps {
  isAdmin?: boolean
}

export function AdminModelManager({ isAdmin = false }: AdminModelManagerProps) {
  const [autoSavedModels, setAutoSavedModels] = useState<AutoSavedModel[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [showPushForm, setShowPushForm] = useState(false)
  const [selectedModel, setSelectedModel] = useState<AutoSavedModel | null>(null)
  const [pushMetadata, setPushMetadata] = useState({
    description: "",
    version: "1.0"
  })
  const [userId, setUserId] = useState("")
  const [pushing, setPushing] = useState(false)
  const [cleanupLoading, setCleanupLoading] = useState(false)
  const [summary, setSummary] = useState<any>(null)

  useEffect(() => {
    if (isAdmin) {
      loadData()
    }
  }, [isAdmin])

  const loadData = async () => {
    setLoading(true)
    setError(null)

    try {
      const [autoSavedResponse, summaryResponse] = await Promise.all([
        CarthaNeuroApi.getAutoSavedModels(),
        CarthaNeuroApi.getModelsSummary()
      ])

      if (autoSavedResponse.success) {
        setAutoSavedModels(autoSavedResponse.models)
      }

      if (summaryResponse.success) {
        setSummary(summaryResponse.summary)
      }
    } catch (error) {
      console.error('Failed to load admin model data:', error)
      setError(error instanceof Error ? error.message : 'Failed to load admin model data')
    } finally {
      setLoading(false)
    }
  }

  const handlePushToCloud = async () => {
    if (!selectedModel || !userId.trim()) {
      setError("Model and user ID are required")
      return
    }

    setPushing(true)
    setError(null)

    try {
      const response = await CarthaNeuroApi.pushModelToCloud({
        model_name: selectedModel.model_name,
        user_id: userId.trim(),
        push_metadata: {
          description: pushMetadata.description,
          version: pushMetadata.version
        },
        confirm: true
      })

      if (response.success) {
        setShowPushForm(false)
        setSelectedModel(null)
        setPushMetadata({ description: "", version: "1.0" })
        setUserId("")
        // Refresh the data
        await loadData()
      } else {
        setError(response.error || 'Failed to push model to cloud')
      }
    } catch (error) {
      console.error('Failed to push model to cloud:', error)
      setError(error instanceof Error ? error.message : 'Failed to push model to cloud')
    } finally {
      setPushing(false)
    }
  }

  const handleCleanup = async () => {
    setCleanupLoading(true)
    setError(null)

    try {
      const response = await CarthaNeuroApi.cleanupAutoSavedModels()
      
      if (response.success) {
        await loadData() // Refresh the data
      } else {
        setError('Failed to cleanup auto-saved models')
      }
    } catch (error) {
      console.error('Failed to cleanup models:', error)
      setError(error instanceof Error ? error.message : 'Failed to cleanup models')
    } finally {
      setCleanupLoading(false)
    }
  }

  const openPushForm = (model: AutoSavedModel) => {
    setSelectedModel(model)
    setShowPushForm(true)
    setError(null)
  }

  if (!isAdmin) {
    return (
      <Card>
        <CardContent className="flex items-center justify-center py-8">
          <div className="text-center">
            <Shield className="h-12 w-12 mx-auto mb-4 text-slate-300" />
            <p className="text-slate-500">Admin access required</p>
            <p className="text-sm text-slate-400">Contact an administrator to manage auto-saved models</p>
          </div>
        </CardContent>
      </Card>
    )
  }

  if (loading) {
    return (
      <Card>
        <CardContent className="flex items-center justify-center py-8">
          <div className="text-center">
            <Loader2 className="h-8 w-8 animate-spin mx-auto mb-4 text-primary" />
            <p className="text-lg text-slate-600 dark:text-slate-400">Loading admin data...</p>
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <div className="space-y-6">
      {/* Summary Cards */}
      {summary && (
        <div className="grid md:grid-cols-3 gap-4">
          <Card>
            <CardContent className="flex items-center justify-between p-4">
              <div>
                <p className="text-sm text-slate-500">Auto-Saved Models</p>
                <p className="text-2xl font-bold">{summary.auto_saved_models.count}</p>
              </div>
              <Clock className="h-8 w-8 text-blue-500" />
            </CardContent>
          </Card>
          <Card>
            <CardContent className="flex items-center justify-between p-4">
              <div>
                <p className="text-sm text-slate-500">Regular Saved Models</p>
                <p className="text-2xl font-bold">{summary.regular_saved_models.count}</p>
              </div>
              <HardDrive className="h-8 w-8 text-green-500" />
            </CardContent>
          </Card>
          <Card>
            <CardContent className="flex items-center justify-between p-4">
              <div>
                <p className="text-sm text-slate-500">Total Models</p>
                <p className="text-2xl font-bold">{summary.total_models}</p>
              </div>
              <Database className="h-8 w-8 text-purple-500" />
            </CardContent>
          </Card>
        </div>
      )}

      {/* Auto-Saved Models Management */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Clock className="h-5 w-5" />
              Auto-Saved Models Management
            </div>
            <div className="flex gap-2">
              <Button onClick={loadData} variant="outline" size="sm">
                <RefreshCw className="h-4 w-4 mr-2" />
                Refresh
              </Button>
              <Button 
                onClick={handleCleanup} 
                variant="destructive" 
                size="sm"
                disabled={cleanupLoading || autoSavedModels.length === 0}
              >
                {cleanupLoading ? (
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                ) : (
                  <Trash2 className="h-4 w-4 mr-2" />
                )}
                Cleanup All
              </Button>
            </div>
          </CardTitle>
        </CardHeader>
        <CardContent>
          {error && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-3 mb-4">
              <div className="flex items-center gap-2">
                <AlertCircle className="h-4 w-4 text-red-600" />
                <p className="text-sm text-red-600">{error}</p>
              </div>
            </div>
          )}

          {autoSavedModels.length === 0 ? (
            <div className="text-center py-8">
              <Clock className="h-12 w-12 mx-auto mb-4 text-slate-300" />
              <p className="text-slate-500">No auto-saved models available</p>
              <p className="text-sm text-slate-400 mt-2">
                Auto-saved models appear here when training completes
              </p>
            </div>
          ) : (
            <div className="space-y-4">
              {autoSavedModels.map((model) => (
                <div key={model.save_id} className="border rounded-lg p-4">
                  <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center gap-3">
                      <div className="w-3 h-3 rounded-full bg-blue-500" />
                      <h3 className="font-semibold">{model.model_name}</h3>
                      <Badge variant="outline">{model.framework}</Badge>
                      <Badge variant="secondary">{model.model_type}</Badge>
                    </div>
                    <div className="flex items-center gap-2">
                      {model.size_mb && (
                        <span className="text-sm text-slate-500">
                          {model.size_mb.toFixed(1)} MB
                        </span>
                      )}
                      <Button 
                        onClick={() => openPushForm(model)}
                        size="sm"
                        className="flex items-center gap-2"
                      >
                        <Cloud className="h-4 w-4" />
                        Push to Cloud
                      </Button>
                    </div>
                  </div>
                  
                  <div className="grid md:grid-cols-2 gap-4 text-sm text-slate-600">
                    <div>
                      <p><strong>Saved:</strong> {new Date(model.saved_at).toLocaleString()}</p>
                      <p><strong>Path:</strong> {model.path}</p>
                    </div>
                    <div>
                      <p><strong>Save ID:</strong> {model.save_id}</p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Push to Cloud Form */}
      {showPushForm && selectedModel && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Cloud className="h-5 w-5" />
              Push Model to MongoDB Cloud
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="bg-slate-50 p-4 rounded-lg">
              <h4 className="font-semibold mb-2">Model Information</h4>
              <p><strong>Name:</strong> {selectedModel.model_name}</p>
              <p><strong>Type:</strong> {selectedModel.model_type}</p>
              <p><strong>Framework:</strong> {selectedModel.framework}</p>
              <p><strong>Saved:</strong> {new Date(selectedModel.saved_at).toLocaleString()}</p>
            </div>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-1">User ID *</label>
                <Input
                  value={userId}
                  onChange={(e) => setUserId(e.target.value)}
                  placeholder="Enter the original model owner user ID"
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-1">Description</label>
                <Input
                  value={pushMetadata.description}
                  onChange={(e) => setPushMetadata(prev => ({ ...prev, description: e.target.value }))}
                  placeholder="Describe this model for cloud storage"
                />
              </div>

              <div>
                <label className="block text-sm font-medium mb-1">Version</label>
                <Input
                  value={pushMetadata.version}
                  onChange={(e) => setPushMetadata(prev => ({ ...prev, version: e.target.value }))}
                  placeholder="1.0"
                />
              </div>
            </div>

            <div className="flex justify-end space-x-2">
              <Button 
                variant="outline" 
                onClick={() => setShowPushForm(false)}
                disabled={pushing}
              >
                Cancel
              </Button>
              <Button 
                onClick={handlePushToCloud}
                disabled={pushing || !userId.trim()}
                className="flex items-center gap-2"
              >
                {pushing ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <Upload className="h-4 w-4" />
                )}
                {pushing ? 'Pushing...' : 'Push to Cloud'}
              </Button>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}