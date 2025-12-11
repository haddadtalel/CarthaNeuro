"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Cpu, Zap, Settings, Loader2 } from "lucide-react"
import { CarthaNeuroApi } from "@/lib/api"

interface TrainingConfigProps {
  modelType: string
  modelName: string
  onTrainingStart?: (jobId: string) => void
}

interface TrainingJobResponse {
  success: boolean
  job_id: string
  message: string
  parameters: any
  timestamp: number
}

export function TrainingConfig({ modelType, modelName, onTrainingStart }: TrainingConfigProps) {
  const [isExpanded, setIsExpanded] = useState(false)
  const [loading, setLoading] = useState(false)
  const [gpuAvailable, setGpuAvailable] = useState(true) // Will be determined from backend
  const [device, setDevice] = useState("cpu")
  const [trainingParams, setTrainingParams] = useState({
    architecture: "resnet",
    numEpochs: 10,
    batchSize: 32,
    learningRate: 0.001,
    validationSplit: 0.2,
    modelName: modelName,
    saveAfterTraining: true,
    enableAutoSave: true
  })
  const [jobId, setJobId] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [autoSaveEnabled, setAutoSaveEnabled] = useState(true)

  const handleStartTraining = async () => {
    setLoading(true)
    setError(null)

    try {
      const data: any = {
        modelType: modelType,
        architecture: trainingParams.architecture,
        numEpochs: trainingParams.numEpochs,
        batchSize: trainingParams.batchSize,
        learningRate: trainingParams.learningRate,
        validationSplit: trainingParams.validationSplit,
        device: device,
        modelName: trainingParams.modelName,
        saveAfterTraining: trainingParams.saveAfterTraining
      }

      const response: TrainingJobResponse = await CarthaNeuroApi.trainModel({
        ...data,
        model_name: trainingParams.modelName || `model_${Date.now()}`,
        save_after_training: trainingParams.saveAfterTraining,
        auto_save_after_training: trainingParams.enableAutoSave
      })
      
      if (response.success) {
        setJobId(response.job_id)
        onTrainingStart?.(response.job_id)
        setIsExpanded(false)
      } else {
        setError(response.message || 'Training failed to start')
      }
    } catch (error) {
      console.error('Training failed:', error)
      setError(error instanceof Error ? error.message : 'Training failed')
    } finally {
      setLoading(false)
    }
  }

  const handleGpuToggle = () => {
    const newDevice = device === "cuda" ? "cpu" : "cuda"
    if (newDevice === "cuda" && !gpuAvailable) {
      return // Don't allow GPU if not available
    }
    setDevice(newDevice)
  }

  const getDeviceIcon = (deviceType: string) => {
    if (deviceType === "cuda") {
      return <Zap className="h-4 w-4 text-yellow-500" />
    }
    return <Cpu className="h-4 w-4 text-blue-500" />
  }

  return (
    <Card>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg flex items-center gap-2">
            {getDeviceIcon(device)}
            Training Configuration
          </CardTitle>
          <div className="flex items-center gap-2">
            <Badge variant={device === "cuda" ? "default" : "secondary"}>
              {device.toUpperCase()}
            </Badge>
            <Button 
              onClick={() => setIsExpanded(!isExpanded)} 
              variant="outline" 
              size="sm"
            >
              <Settings className="h-4 w-4 mr-1" />
              {isExpanded ? 'Hide' : 'Configure'}
            </Button>
          </div>
        </div>
      </CardHeader>
      
      {isExpanded && (
        <CardContent className="space-y-6">
          {/* Device Selection */}
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <div>
                <p className="font-medium">Training Device</p>
                <p className="text-sm text-slate-500">
                  Choose where to run the training computation
                </p>
              </div>
              <Button
                onClick={handleGpuToggle}
                disabled={!gpuAvailable}
                variant={device === "cuda" ? "default" : "outline"}
                className="flex items-center gap-2"
              >
                {getDeviceIcon(device)}
                {device === "cuda" ? 'GPU Mode' : 'CPU Mode'}
              </Button>
            </div>
            
            {!gpuAvailable && (
              <div className="bg-orange-50 border border-orange-200 rounded-lg p-3">
                <p className="text-sm text-orange-700">
                  <Zap className="h-4 w-4 inline mr-1" />
                  GPU training is not available on this system. Training will use CPU.
                </p>
              </div>
            )}
            
            <div className="grid grid-cols-2 gap-4">
              <div className={`p-3 rounded-lg border-2 ${device === "cpu" ? "border-blue-500 bg-blue-50" : "border-slate-200"}`}>
                <div className="flex items-center gap-2 mb-2">
                  <Cpu className="h-5 w-5 text-blue-500" />
                  <span className="font-medium">CPU Training</span>
                </div>
                <ul className="text-sm text-slate-600 space-y-1">
                  <li>• Slower but reliable</li>
                  <li>• Lower memory usage</li>
                  <li>• Works on all systems</li>
                </ul>
              </div>
              
              <div className={`p-3 rounded-lg border-2 ${device === "cuda" ? "border-yellow-500 bg-yellow-50" : "border-slate-200"}`}>
                <div className="flex items-center gap-2 mb-2">
                  <Zap className="h-5 w-5 text-yellow-500" />
                  <span className="font-medium">GPU Training</span>
                </div>
                <ul className="text-sm text-slate-600 space-y-1">
                  <li>• Much faster training</li>
                  <li>• Higher memory usage</li>
                  <li>• Requires CUDA GPU</li>
                </ul>
              </div>
            </div>
          </div>

          {/* Training Parameters */}
          <div className="space-y-4">
            <h3 className="font-medium">Training Parameters</h3>
            
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium mb-1">Architecture</label>
                <Select value={trainingParams.architecture} onValueChange={(value) => 
                  setTrainingParams(prev => ({ ...prev, architecture: value }))
                }>
                  <SelectTrigger>
                    <SelectValue placeholder="Select architecture" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="resnet">ResNet</SelectItem>
                    <SelectItem value="densenet">DenseNet</SelectItem>
                    <SelectItem value="efficientnet">EfficientNet</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              
              <div>
                <label className="block text-sm font-medium mb-1">Epochs</label>
                <Input
                  type="number"
                  min="1"
                  max="100"
                  value={trainingParams.numEpochs}
                  onChange={(e) => setTrainingParams(prev => ({ 
                    ...prev, 
                    numEpochs: parseInt(e.target.value) || 10 
                  }))}
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium mb-1">Batch Size</label>
                <Input
                  type="number"
                  min="1"
                  max="128"
                  value={trainingParams.batchSize}
                  onChange={(e) => setTrainingParams(prev => ({ 
                    ...prev, 
                    batchSize: parseInt(e.target.value) || 32 
                  }))}
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium mb-1">Learning Rate</label>
                <Input
                  type="number"
                  min="0.0001"
                  max="1"
                  step="0.0001"
                  value={trainingParams.learningRate}
                  onChange={(e) => setTrainingParams(prev => ({ 
                    ...prev, 
                    learningRate: parseFloat(e.target.value) || 0.001 
                  }))}
                />
              </div>
            </div>
            
            <div>
              <label className="block text-sm font-medium mb-1">Validation Split</label>
              <Input
                type="number"
                min="0.1"
                max="0.5"
                step="0.1"
                value={trainingParams.validationSplit}
                onChange={(e) => setTrainingParams(prev => ({ 
                  ...prev, 
                  validationSplit: parseFloat(e.target.value) || 0.2 
                }))}
              />
            </div>
            
            <div className="space-y-3">
              <div className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  id="saveModel"
                  checked={trainingParams.saveAfterTraining}
                  onChange={(e) => setTrainingParams(prev => ({ 
                    ...prev, 
                    saveAfterTraining: e.target.checked 
                  }))}
                  className="rounded"
                />
                <label htmlFor="saveModel" className="text-sm font-medium">
                  Save model after training
                </label>
              </div>
              
              <div className="flex items-center space-x-2">
                <input
                  type="checkbox"
                  id="autoSave"
                  checked={trainingParams.enableAutoSave}
                  onChange={(e) => setTrainingParams(prev => ({ 
                    ...prev, 
                    enableAutoSave: e.target.checked 
                  }))}
                  className="rounded"
                />
                <label htmlFor="autoSave" className="text-sm font-medium">
                  Enable auto-save (automatically saves model when training completes)
                </label>
              </div>
            </div>
          </div>

          {error && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-3">
              <p className="text-sm text-red-600">{error}</p>
            </div>
          )}

          <div className="flex justify-end space-x-2">
            <Button variant="outline" onClick={() => setIsExpanded(false)}>
              Cancel
            </Button>
            <Button 
              onClick={handleStartTraining} 
              disabled={loading}
              className="flex items-center gap-2"
            >
              {loading ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  Starting Training...
                </>
              ) : (
                <>
                  {getDeviceIcon(device)}
                  Start Training on {device.toUpperCase()}
                </>
              )}
            </Button>
          </div>
        </CardContent>
      )}
    </Card>
  )
}