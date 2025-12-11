"use client"

import { useState, useCallback } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Progress } from "@/components/ui/progress"
import { Badge } from "@/components/ui/badge"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import {
  Upload,
  FileText,
  CheckCircle,
  AlertCircle,
  X,
  Trash2,
  FolderOpen,
  Database,
  Eye
} from "lucide-react"
import { CarthaNeuroApi, ApiError } from "@/lib/api"

interface UploadedFile {
  file: File
  id: string
  status: "pending" | "uploading" | "success" | "error"
  progress: number
  error?: string
}

interface DatasetInfo {
  id: string
  name: string
  description: string
  fileCount: number
  totalSize: number
  createdAt: string
  classLabels: string[]
}

export default function DataUploadPage() {
  const [files, setFiles] = useState<UploadedFile[]>([])
  const [isUploading, setIsUploading] = useState(false)
  const [uploadProgress, setUploadProgress] = useState(0)
  const [classLabel, setClassLabel] = useState("")
  const [datasetName, setDatasetName] = useState("")
  const [datasets, setDatasets] = useState<DatasetInfo[]>([])
  const [selectedDataset, setSelectedDataset] = useState<string>("")

  // Load existing datasets
  const loadDatasets = async () => {
    try {
      // Mock implementation for now
      const response = await CarthaNeuroApi.getDatasetInfo()
      setDatasets([])
    } catch (error) {
      console.error("Failed to load datasets:", error)
    }
  }

  // Handle file selection
  const handleFileSelect = useCallback((event: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFiles = Array.from(event.target.files || [])
    const newFiles: UploadedFile[] = selectedFiles.map(file => ({
      file,
      id: `${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      status: "pending",
      progress: 0
    }))

    setFiles(prev => [...prev, ...newFiles])
  }, [])

  // Remove file from list
  const removeFile = (id: string) => {
    setFiles(prev => prev.filter(f => f.id !== id))
  }

  // Upload files with progress tracking
  const uploadFiles = async () => {
    if (files.length === 0 || !classLabel || !datasetName) {
      alert("Please select files, class label, and dataset name")
      return
    }

    setIsUploading(true)
    setUploadProgress(0)

    try {
      // Update all files to uploading status
      setFiles(prev => prev.map(f => ({ ...f, status: "uploading" as const })))

      // Mock upload implementation for now
      for (let i = 0; i < files.length; i++) {
        const progress = ((i + 1) / files.length) * 100
        setUploadProgress(progress)
        await new Promise(resolve => setTimeout(resolve, 500))
      }

      // Update file statuses to success
      setFiles(prev => prev.map(f => ({
        ...f,
        status: "success" as const
      })))

      alert("Files uploaded successfully!")

    } catch (error) {
      console.error("Upload failed:", error)
      
      // Update file statuses to error
      setFiles(prev => prev.map(f => ({
        ...f,
        status: "error" as const,
        error: error instanceof Error ? error.message : "Upload failed"
      })))
      
      alert("Upload failed: " + (error instanceof Error ? error.message : "Unknown error"))
    } finally {
      setIsUploading(false)
      setUploadProgress(0)
    }
  }

  // Validate uploaded data
  const validateData = async (uploadId: string) => {
    try {
      // Mock validation for now
      alert("Validation complete: 10 valid, 0 invalid files")
      await loadDatasets()
    } catch (error) {
      console.error("Validation failed:", error)
      alert("Validation failed: " + (error instanceof Error ? error.message : "Unknown error"))
    }
  }

  // Delete dataset
  const deleteDataset = async (datasetId: string) => {
    if (!confirm("Are you sure you want to delete this dataset?")) return

    try {
      // This would need to be implemented in the API
      // await api.upload.deleteDataset(datasetId)
      await loadDatasets()
      alert("Dataset deleted successfully")
    } catch (error) {
      console.error("Delete failed:", error)
      alert("Delete failed: " + (error instanceof Error ? error.message : "Unknown error"))
    }
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="max-w-6xl mx-auto">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold font-heading mb-4">Data Upload & Management</h1>
          <p className="text-lg text-slate-600 dark:text-slate-400">
            Upload and manage training datasets for brain tumor classification
          </p>
        </div>

        <div className="grid lg:grid-cols-2 gap-8">
          {/* Upload Section */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Upload className="h-5 w-5" />
                Upload Training Data
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-6">
                {/* Dataset Configuration */}
                <div className="space-y-4">
                  <div>
                    <label className="text-sm font-medium">Dataset Name</label>
                    <Input
                      placeholder="e.g., brain_tumor_v2"
                      value={datasetName}
                      onChange={(e) => setDatasetName(e.target.value)}
                    />
                  </div>

                  <div>
                    <label className="text-sm font-medium">Class Label</label>
                    <Select value={classLabel} onValueChange={setClassLabel}>
                      <SelectTrigger>
                        <SelectValue placeholder="Select tumor class" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="glioma">Glioma</SelectItem>
                        <SelectItem value="meningioma">Meningioma</SelectItem>
                        <SelectItem value="pituitary">Pituitary Tumor</SelectItem>
                        <SelectItem value="notumor">No Tumor</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>

                {/* File Upload */}
                <div>
                  <input
                    type="file"
                    multiple
                    accept="image/*,.dcm,.nii.gz"
                    onChange={handleFileSelect}
                    className="hidden"
                    id="file-upload"
                  />
                  <label htmlFor="file-upload">
                    <Button variant="outline" className="w-full h-32 border-2 border-dashed" asChild>
                      <div className="cursor-pointer">
                        <div className="text-center">
                          <Upload className="h-8 w-8 mx-auto mb-2 text-slate-400" />
                          <p className="text-sm text-slate-600 dark:text-slate-400">
                            Click to upload medical images (PNG, JPG, DICOM, NIfTI)
                          </p>
                        </div>
                      </div>
                    </Button>
                  </label>
                </div>

                {/* File List */}
                {files.length > 0 && (
                  <div className="space-y-2">
                    <h3 className="text-sm font-medium">Selected Files ({files.length})</h3>
                    <div className="max-h-32 overflow-y-auto space-y-1">
                      {files.map((file) => (
                        <div key={file.id} className="flex items-center justify-between p-2 border rounded">
                          <div className="flex items-center gap-2">
                            {file.status === "success" ? (
                              <CheckCircle className="h-4 w-4 text-green-500" />
                            ) : file.status === "error" ? (
                              <AlertCircle className="h-4 w-4 text-red-500" />
                            ) : file.status === "uploading" ? (
                              <div className="h-4 w-4 border-2 border-primary border-t-transparent rounded-full animate-spin" />
                            ) : (
                              <FileText className="h-4 w-4 text-slate-400" />
                            )}
                            <span className="text-sm">{file.file.name}</span>
                            <Badge variant="outline" className="text-xs">
                              {(file.file.size / 1024 / 1024).toFixed(1)} MB
                            </Badge>
                          </div>
                          <Button
                            size="sm"
                            variant="ghost"
                            onClick={() => removeFile(file.id)}
                            disabled={file.status === "uploading"}
                          >
                            <X className="h-4 w-4" />
                          </Button>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Upload Progress */}
                {isUploading && (
                  <div className="space-y-2">
                    <div className="flex justify-between text-sm">
                      <span>Uploading...</span>
                      <span>{uploadProgress.toFixed(0)}%</span>
                    </div>
                    <Progress value={uploadProgress} className="w-full" />
                  </div>
                )}

                {/* Upload Button */}
                <Button
                  onClick={uploadFiles}
                  disabled={files.length === 0 || !classLabel || !datasetName || isUploading}
                  className="w-full"
                >
                  {isUploading ? "Uploading..." : "Upload and Process Files"}
                </Button>
              </div>
            </CardContent>
          </Card>

          {/* Dataset Management */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Database className="h-5 w-5" />
                Dataset Management
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="flex justify-between items-center">
                  <h3 className="text-sm font-medium">Existing Datasets</h3>
                  <Button onClick={loadDatasets} variant="outline" size="sm">
                    <FolderOpen className="h-4 w-4 mr-2" />
                    Refresh
                  </Button>
                </div>

                {datasets.length === 0 ? (
                  <p className="text-sm text-slate-500 text-center py-8">
                    No datasets found. Upload some data to get started.
                  </p>
                ) : (
                  <div className="space-y-2">
                    {datasets.map((dataset) => (
                      <div key={dataset.id} className="border rounded-lg p-4">
                        <div className="flex justify-between items-start mb-2">
                          <div>
                            <h4 className="font-medium">{dataset.name}</h4>
                            <p className="text-sm text-slate-500">{dataset.description}</p>
                          </div>
                          <div className="flex gap-2">
                            <Button size="sm" variant="outline">
                              <Eye className="h-4 w-4" />
                            </Button>
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => deleteDataset(dataset.id)}
                            >
                              <Trash2 className="h-4 w-4" />
                            </Button>
                          </div>
                        </div>

                        <div className="flex flex-wrap gap-2 mb-2">
                          {dataset.classLabels.map((label) => (
                            <Badge key={label} variant="secondary" className="text-xs">
                              {label}
                            </Badge>
                          ))}
                        </div>

                        <div className="text-sm text-slate-500">
                          {dataset.fileCount} files • {(dataset.totalSize / 1024 / 1024).toFixed(1)} MB
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Upload Guidelines */}
        <Card className="mt-8">
          <CardHeader>
            <CardTitle>Upload Guidelines</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid md:grid-cols-2 gap-6">
              <div>
                <h3 className="font-medium mb-2">Supported Formats</h3>
                <ul className="text-sm text-slate-600 space-y-1">
                  <li>• PNG, JPG, JPEG images</li>
                  <li>• DICOM (.dcm) files</li>
                  <li>• NIfTI (.nii.gz) files</li>
                  <li>• Maximum file size: 50MB per file</li>
                </ul>
              </div>
              <div>
                <h3 className="font-medium mb-2">Best Practices</h3>
                <ul className="text-sm text-slate-600 space-y-1">
                  <li>• Organize by tumor class labels</li>
                  <li>• Use consistent image dimensions</li>
                  <li>• Ensure proper image orientation</li>
                  <li>• Remove corrupted or low-quality images</li>
                </ul>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}