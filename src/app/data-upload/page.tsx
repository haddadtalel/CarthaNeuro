"use client"

import { useState, useRef, useCallback, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Progress } from "@/components/ui/progress"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { Badge } from "@/components/ui/badge"
import { Upload, FileImage, CheckCircle, XCircle, FolderOpen, Database } from "lucide-react"
import { toast } from "react-hot-toast"

interface UploadedFile {
  name: string
  size: number
  status: 'pending' | 'uploading' | 'success' | 'error'
  class?: string
}

interface DatasetInfo {
  name: string
  total_samples: number
  class_distribution: Record<string, number>
  status: string
  last_updated: string
}

const CLASS_LABELS = [
  { value: 'glioma', label: 'Glioma', color: 'bg-red-500' },
  { value: 'meningioma', label: 'Meningioma', color: 'bg-orange-500' },
  { value: 'notumor', label: 'No Tumor', color: 'bg-green-500' },
  { value: 'pituitary', label: 'Pituitary', color: 'bg-purple-500' }
]

export default function DataUploadPage() {
  const [selectedFiles, setSelectedFiles] = useState<UploadedFile[]>([])
  const [selectedClass, setSelectedClass] = useState<string>('')
  const [datasetName, setDatasetName] = useState<string>('custom_dataset')
  const [isUploading, setIsUploading] = useState(false)
  const [uploadProgress, setUploadProgress] = useState(0)
  const [uploadId, setUploadId] = useState<string | null>(null)
  const [validationResult, setValidationResult] = useState<any>(null)
  const [datasets, setDatasets] = useState<DatasetInfo[]>([])
  const [activeTab, setActiveTab] = useState<'upload' | 'datasets'>('upload')
  
  const fileInputRef = useRef<HTMLInputElement>(null)
  const zipInputRef = useRef<HTMLInputElement>(null)

  const loadDatasets = async () => {
    try {
      const response = await fetch('/api/data-upload/datasets')
      if (response.ok) {
        const data = await response.json()
        setDatasets(data)
      }
    } catch (error) {
      console.error('Failed to load datasets:', error)
    }
  }

  // Load datasets on component mount
  useEffect(() => {
    loadDatasets()
  }, [])

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = event.target.files
    if (files) {
      const newFiles: UploadedFile[] = Array.from(files).map(file => ({
        name: file.name,
        size: file.size,
        status: 'pending'
      }))
      setSelectedFiles(prev => [...prev, ...newFiles])
    }
  }

  const handleDrop = useCallback((event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault()
    const files = event.dataTransfer.files
    if (files) {
      const newFiles: UploadedFile[] = Array.from(files).map(file => ({
        name: file.name,
        size: file.size,
        status: 'pending'
      }))
      setSelectedFiles(prev => [...prev, ...newFiles])
    }
  }, [])

  const handleDragOver = useCallback((event: React.DragEvent<HTMLDivElement>) => {
    event.preventDefault()
  }, [])

  const removeFile = (index: number) => {
    setSelectedFiles(prev => prev.filter((_, i) => i !== index))
  }

  const clearAllFiles = () => {
    setSelectedFiles([])
    setValidationResult(null)
    setUploadId(null)
  }

  const validateFiles = async () => {
    if (!uploadId) {
      toast.error('Please upload files first')
      return
    }

    try {
      const response = await fetch(`/api/data-upload/validate?upload_id=${uploadId}`)
      if (response.ok) {
        const result = await response.json()
        setValidationResult(result)
        toast.success('Files validated successfully')
      } else {
        throw new Error('Validation failed')
      }
    } catch (error) {
      toast.error('Failed to validate files')
    }
  }

  const mergeDataset = async () => {
    if (!uploadId) {
      toast.error('No upload ID found')
      return
    }

    try {
      const response = await fetch(`/api/data-upload/merge?upload_id=${uploadId}&dataset_name=${datasetName}`, {
        method: 'POST'
      })
      
      if (response.ok) {
        const result = await response.json()
        toast.success(result.message)
        clearAllFiles()
        loadDatasets() // Refresh datasets list
      } else {
        throw new Error('Merge failed')
      }
    } catch (error) {
      toast.error('Failed to merge dataset')
    }
  }

  const handleUpload = async () => {
    if (!selectedFiles.length) {
      toast.error('Please select files to upload')
      return
    }

    if (!selectedClass) {
      toast.error('Please select a class label')
      return
    }

    setIsUploading(true)
    setUploadProgress(0)

    try {
      const formData = new FormData()
      
      // Add class label and dataset name
      formData.append('class_label', selectedClass)
      formData.append('dataset_name', datasetName)

      // Add files
      const fileInput = fileInputRef.current
      if (fileInput?.files) {
        Array.from(fileInput.files).forEach(file => {
          formData.append('files', file)
        })
      }

      // Simulate progress for better UX
      const progressInterval = setInterval(() => {
        setUploadProgress(prev => {
          if (prev >= 90) {
            clearInterval(progressInterval)
            return 90
          }
          return prev + 10
        })
      }, 200)

      // Get the access token from localStorage
      const accessToken = localStorage.getItem('access_token')
      
      const response = await fetch('/api/data-upload/upload', {
        method: 'POST',
        headers: accessToken ? {
          'Authorization': `Bearer ${accessToken}`
        } : {},
        body: formData
      })

      clearInterval(progressInterval)
      setUploadProgress(100)

      if (response.ok) {
        const result = await response.json()
        setUploadId(result.upload_id)
        toast.success(result.message)
        
        // Update file statuses - if upload succeeded, mark all files as success
        // The backend returns unique filenames (UUIDs), not original names
        const uploadSuccessful = result.success && result.uploaded_files.length > 0
        setSelectedFiles(prev => prev.map(file => ({
          ...file,
          status: uploadSuccessful ? 'success' : 'error'
        })))
      } else {
        const error = await response.json()
        throw new Error(error.detail || 'Upload failed')
      }
    } catch (error) {
      toast.error(error instanceof Error ? error.message : 'Upload failed')
      setSelectedFiles(prev => prev.map(file => ({ ...file, status: 'error' })))
    } finally {
      setIsUploading(false)
    }
  }

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes'
    const k = 1024
    const sizes = ['Bytes', 'KB', 'MB', 'GB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
  }

  const getClassInfo = (classValue: string) => {
    return CLASS_LABELS.find(c => c.value === classValue) || CLASS_LABELS[0]
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="max-w-6xl mx-auto">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold font-heading mb-4">Training Data Upload</h1>
          <p className="text-lg text-slate-600 dark:text-slate-400">
            Upload brain MRI images to expand your training dataset
          </p>
        </div>

        {/* Tabs */}
        <div className="flex mb-8">
          <Button
            variant={activeTab === 'upload' ? 'default' : 'outline'}
            onClick={() => setActiveTab('upload')}
            className="mr-4"
          >
            <Upload className="h-4 w-4 mr-2" />
            Upload Data
          </Button>
          <Button
            variant={activeTab === 'datasets' ? 'default' : 'outline'}
            onClick={() => setActiveTab('datasets')}
          >
            <Database className="h-4 w-4 mr-2" />
            Manage Datasets
          </Button>
        </div>

        {activeTab === 'upload' ? (
          <div className="grid lg:grid-cols-3 gap-8">
            {/* Upload Section */}
            <div className="lg:col-span-2 space-y-6">
              {/* Configuration */}
              <Card>
                <CardHeader>
                  <CardTitle>Upload Configuration</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium mb-2">Class Label</label>
                    <Select value={selectedClass} onValueChange={setSelectedClass}>
                      <SelectTrigger>
                        <SelectValue placeholder="Select class for uploaded images" />
                      </SelectTrigger>
                      <SelectContent>
                        {CLASS_LABELS.map((classInfo) => (
                          <SelectItem key={classInfo.value} value={classInfo.value}>
                            <div className="flex items-center gap-2">
                              <div className={`w-3 h-3 rounded-full ${classInfo.color}`} />
                              {classInfo.label}
                            </div>
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>

                  <div>
                    <label className="block text-sm font-medium mb-2">Dataset Name</label>
                    <Input
                      value={datasetName}
                      onChange={(e) => setDatasetName(e.target.value)}
                      placeholder="Enter dataset name"
                    />
                  </div>
                </CardContent>
              </Card>

              {/* File Upload */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <FileImage className="h-5 w-5" />
                    Select Images
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4">
                    {/* Hidden file inputs */}
                    <input
                      ref={fileInputRef}
                      type="file"
                      multiple
                      accept="image/*,.dcm,.nii"
                      onChange={handleFileSelect}
                      className="hidden"
                    />
                    <input
                      ref={zipInputRef}
                      type="file"
                      accept=".zip"
                      onChange={handleFileSelect}
                      className="hidden"
                    />

                    {/* Drop zone */}
                    <div
                      onDrop={handleDrop}
                      onDragOver={handleDragOver}
                      className="border-2 border-dashed border-slate-300 dark:border-slate-600 rounded-lg p-8 text-center hover:border-slate-400 dark:hover:border-slate-500 transition-colors"
                    >
                      <Upload className="h-12 w-12 mx-auto mb-4 text-slate-400" />
                      <p className="text-lg font-medium mb-2">
                        Drag and drop images here
                      </p>
                      <p className="text-sm text-slate-500 mb-4">
                        Support for JPG, PNG, DICOM (.dcm), and NIfTI (.nii) files
                      </p>
                      <div className="flex gap-2 justify-center">
                        <Button onClick={() => fileInputRef.current?.click()} variant="outline">
                          Select Images
                        </Button>
                        <Button onClick={() => zipInputRef.current?.click()} variant="outline">
                          Upload ZIP
                        </Button>
                      </div>
                    </div>

                    {/* Selected files */}
                    {selectedFiles.length > 0 && (
                      <div>
                        <div className="flex justify-between items-center mb-3">
                          <h3 className="font-medium">Selected Files ({selectedFiles.length})</h3>
                          <Button onClick={clearAllFiles} variant="outline" size="sm">
                            Clear All
                          </Button>
                        </div>
                        
                        <div className="max-h-60 overflow-y-auto space-y-2">
                          {selectedFiles.map((file, index) => (
                            <div key={index} className="flex items-center justify-between p-3 border rounded-lg">
                              <div className="flex items-center gap-3">
                                {file.status === 'pending' && <FileImage className="h-4 w-4 text-slate-400" />}
                                {file.status === 'uploading' && <div className="h-4 w-4 border-2 border-blue-500 border-t-transparent rounded-full animate-spin" />}
                                {file.status === 'success' && <CheckCircle className="h-4 w-4 text-green-500" />}
                                {file.status === 'error' && <XCircle className="h-4 w-4 text-red-500" />}
                                
                                <div>
                                  <p className="font-medium text-sm">{file.name}</p>
                                  <p className="text-xs text-slate-500">{formatFileSize(file.size)}</p>
                                </div>
                              </div>
                              
                              <Button
                                onClick={() => removeFile(index)}
                                variant="ghost"
                                size="sm"
                                disabled={isUploading}
                              >
                                Remove
                              </Button>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Upload button */}
                    {selectedFiles.length > 0 && !isUploading && (
                      <Button onClick={handleUpload} className="w-full" disabled={!selectedClass}>
                        <Upload className="h-4 w-4 mr-2" />
                        Upload {selectedFiles.length} Files
                      </Button>
                    )}

                    {/* Upload progress */}
                    {isUploading && (
                      <div className="space-y-2">
                        <div className="flex justify-between text-sm">
                          <span>Uploading files...</span>
                          <span>{uploadProgress}%</span>
                        </div>
                        <Progress value={uploadProgress} className="w-full" />
                      </div>
                    )}
                  </div>
                </CardContent>
              </Card>

              {/* Validation and Merge */}
              {uploadId && validationResult && (
                <Card>
                  <CardHeader>
                    <CardTitle>Validation Results</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <p className="text-sm font-medium">Valid Files</p>
                        <p className="text-2xl font-bold text-green-600">{validationResult.valid_files.length}</p>
                      </div>
                      <div>
                        <p className="text-sm font-medium">Invalid Files</p>
                        <p className="text-2xl font-bold text-red-600">{validationResult.invalid_files.length}</p>
                      </div>
                    </div>

                    {validationResult.file_counts && Object.keys(validationResult.file_counts).length > 0 && (
                      <div>
                        <p className="text-sm font-medium mb-2">Class Distribution</p>
                        <div className="flex flex-wrap gap-2">
                          {Object.entries(validationResult.file_counts).map(([className, count]: [string, unknown]) => {
                              const classInfo = getClassInfo(className)
                              return (
                                <Badge key={className} className={`${classInfo.color} text-white`}>
                                  {classInfo.label}: {count as number}
                                </Badge>
                              )
                            })}
                        </div>
                      </div>
                    )}

                    <div className="flex gap-2">
                      <Button onClick={mergeDataset} className="flex-1">
                        Merge into Dataset
                      </Button>
                      <Button onClick={validateFiles} variant="outline">
                        Re-validate
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              )}
            </div>

            {/* Sidebar */}
            <div className="space-y-6">
              {/* Quick Actions */}
              <Card>
                <CardHeader>
                  <CardTitle>Quick Actions</CardTitle>
                </CardHeader>
                <CardContent className="space-y-3">
                  {uploadId && !validationResult && (
                    <Button onClick={validateFiles} variant="outline" className="w-full">
                      <CheckCircle className="h-4 w-4 mr-2" />
                      Validate Uploaded Files
                    </Button>
                  )}
                  
                  <Button variant="outline" className="w-full" onClick={loadDatasets}>
                    <Database className="h-4 w-4 mr-2" />
                    Refresh Datasets
                  </Button>
                </CardContent>
              </Card>

              {/* Guidelines */}
              <Card>
                <CardHeader>
                  <CardTitle>Upload Guidelines</CardTitle>
                </CardHeader>
                <CardContent className="text-sm text-slate-600 dark:text-slate-400">
                  <ul className="space-y-2">
                    <li>• Images should be clear brain MRI scans</li>
                    <li>• Supported formats: JPG, PNG, DICOM, NIfTI</li>
                    <li>• Each upload batch must belong to one class</li>
                    <li>• Files are automatically validated after upload</li>
                    <li>• ZIP archives are automatically extracted</li>
                  </ul>
                </CardContent>
              </Card>
            </div>
          </div>
        ) : (
          /* Datasets Tab */
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Database className="h-5 w-5" />
                Available Datasets
              </CardTitle>
            </CardHeader>
            <CardContent>
              {datasets.length > 0 ? (
                <div className="space-y-4">
                  {datasets.map((dataset, index) => (
                    <div key={index} className="border rounded-lg p-4">
                      <div className="flex justify-between items-start mb-3">
                        <div>
                          <h3 className="font-semibold text-lg">{dataset.name}</h3>
                          <p className="text-sm text-slate-500">
                            {dataset.total_samples} samples • Updated {dataset.last_updated}
                          </p>
                        </div>
                        <Badge variant={dataset.status === 'ready' ? 'default' : 'secondary'}>
                          {dataset.status}
                        </Badge>
                      </div>
                      
                      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                        {Object.entries(dataset.class_distribution).map(([className, count]) => {
                          const classInfo = getClassInfo(className)
                          return (
                            <div key={className} className="text-center p-2 bg-slate-50 dark:bg-slate-800 rounded">
                              <div className={`w-3 h-3 rounded-full ${classInfo.color} mx-auto mb-1`} />
                              <p className="text-xs font-medium">{classInfo.label}</p>
                              <p className="text-sm font-bold">{count}</p>
                            </div>
                          )
                        })}
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-8 text-slate-500">
                  <Database className="h-12 w-12 mx-auto mb-4" />
                  <p>No datasets found</p>
                  <p className="text-sm">Upload training data to create your first dataset</p>
                </div>
              )}
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  )
}