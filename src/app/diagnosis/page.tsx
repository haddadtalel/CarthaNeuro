"use client"

import { useState, useRef } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Progress } from "@/components/ui/progress"
import { Upload, Image as ImageIcon, Download, History } from "lucide-react"
import Image from "next/image"

interface PredictionResult {
  disease: string
  confidence: number
  heatmapUrl?: string
  llmAnalysis?: {
    clinical_summary: string
    risk_score: string
    suspected_region: string
    key_observations: string[]
    recommendations: string[]
  }
}

interface DiagnosisHistory {
  id: string
  date: string
  disease: string
  confidence: number
}

export default function DiagnosisPage() {
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [previewUrl, setPreviewUrl] = useState<string | null>(null)
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [result, setResult] = useState<PredictionResult | null>(null)
  const [history, setHistory] = useState<DiagnosisHistory[]>([
    {
      id: "1",
      date: "2024-01-15",
      disease: "Alzheimer's",
      confidence: 0.87
    },
    {
      id: "2",
      date: "2024-01-10",
      disease: "Healthy",
      confidence: 0.92
    }
  ])
  const fileInputRef = useRef<HTMLInputElement>(null)

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (file) {
      setSelectedFile(file)
      const url = URL.createObjectURL(file)
      setPreviewUrl(url)
      setResult(null)
    }
  }

  const handleUploadClick = () => {
    fileInputRef.current?.click()
  }

  const handleAnalysis = async () => {
    if (!selectedFile) return

    setIsAnalyzing(true)

    try {
      // Import the API client
      const { CarthaNeuroApi } = await import('@/lib/api')

      // Call the backend API with the file
      const response = await CarthaNeuroApi.predict({
        image: selectedFile,
        patientContext: 'Brain MRI analysis for tumor detection and classification',
        modelName: 'lili',
        useLlm: true
      })

      if (!response.success) {
        throw new Error(response.error || 'Analysis failed')
      }

      const backendResult = response.result
      const prediction = backendResult?.prediction

      // Transform the response to match our UI format
      const transformedResult: PredictionResult = {
        disease: prediction?.class === 'glioma' ? "Glioma" :
                prediction?.class === 'meningioma' ? "Meningioma" :
                prediction?.class === 'pituitary' ? "Pituitary Tumor" :
                prediction?.class === 'notumor' ? "No Tumor Detected" :
                prediction?.class || "Unknown",
        confidence: prediction?.confidence || 0,
        heatmapUrl: undefined, // Will implement Grad-CAM later
        llmAnalysis: backendResult?.llm_analysis?.structured_data
      }

      setResult(transformedResult)

      // Add to history
      const newHistory: DiagnosisHistory = {
        id: Date.now().toString(),
        date: new Date().toISOString().split('T')[0],
        disease: transformedResult.disease,
        confidence: transformedResult.confidence
      }
      setHistory(prev => [newHistory, ...prev])

    } catch (error) {
      console.error('Analysis error:', error)
      
      let errorMessage = 'Analysis failed. Please try again.'
      
      if (error instanceof Error) {
        if (error.message.includes('Unable to connect to backend')) {
          errorMessage = 'Cannot connect to the analysis server. Please check if the backend is running.'
        } else {
          errorMessage = error.message
        }
      }
      
      alert(errorMessage)
    } finally {
      setIsAnalyzing(false)
    }
  }

  const downloadReport = () => {
    // Mock PDF download
    const element = document.createElement('a')
    element.href = '#'
    element.download = 'diagnosis-report.pdf'
    element.click()
  }

  const getDiseaseColor = (disease: string) => {
    switch (disease) {
      case "Glioma": return "text-red-600"
      case "Meningioma": return "text-orange-600" 
      case "Pituitary Tumor": return "text-purple-600"
      case "No Tumor Detected": return "text-green-600"
      case "Alzheimer's": return "text-red-600"
      case "Parkinson's": return "text-orange-600"
      case "Healthy": return "text-green-600"
      default: return "text-gray-600"
    }
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="max-w-6xl mx-auto">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold font-heading mb-4">Brain MRI Diagnosis</h1>
          <p className="text-lg text-slate-600 dark:text-slate-400">
            Upload your brain MRI image for AI-powered analysis
          </p>
        </div>

        <div className="grid lg:grid-cols-3 gap-8">
          {/* Main Analysis Area */}
          <div className="lg:col-span-2 space-y-6">
            {/* Upload Section */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Upload className="h-5 w-5" />
                  Upload MRI Image
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <Input
                    ref={fileInputRef}
                    type="file"
                    accept="image/*,.dcm"
                    onChange={handleFileSelect}
                    className="hidden"
                  />
                  <Button
                    onClick={handleUploadClick}
                    variant="outline"
                    className="w-full h-32 border-2 border-dashed"
                  >
                    <div className="text-center">
                      <Upload className="h-8 w-8 mx-auto mb-2 text-slate-400" />
                      <p className="text-sm text-slate-600 dark:text-slate-400">
                        Click to upload MRI image (PNG, JPG, DICOM)
                      </p>
                    </div>
                  </Button>

                  {previewUrl && (
                    <div className="mt-4">
                      <h3 className="text-sm font-medium mb-2">Preview:</h3>
                      <div className="relative w-full max-w-md mx-auto">
                        <Image
                          src={previewUrl}
                          alt="MRI Preview"
                          width={400}
                          height={400}
                          className="rounded-lg border"
                        />
                      </div>
                    </div>
                  )}

                  {selectedFile && !isAnalyzing && !result && (
                    <Button onClick={handleAnalysis} className="w-full">
                      <ImageIcon className="h-4 w-4 mr-2" />
                      Run Analysis
                    </Button>
                  )}
                </div>
              </CardContent>
            </Card>

            {/* Analysis Progress */}
            {isAnalyzing && (
              <Card>
                <CardContent className="pt-6">
                  <div className="space-y-4">
                    <div className="flex items-center justify-between">
                      <h3 className="text-lg font-semibold">Analyzing Image...</h3>
                      <span className="text-sm text-slate-500">Processing</span>
                    </div>
                    <Progress value={75} className="w-full" />
                    <p className="text-sm text-slate-600 dark:text-slate-400">
                      Our AI is analyzing the brain structures and patterns...
                    </p>
                  </div>
                </CardContent>
              </Card>
            )}

            {/* Results Section */}
            {result && (
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <ImageIcon className="h-5 w-5" />
                    Analysis Results
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="space-y-6">
                    <div className="text-center">
                      <div className={`text-3xl font-bold ${getDiseaseColor(result.disease)}`}>
                        {result.disease}
                      </div>
                      <div className="text-lg text-slate-600 dark:text-slate-400 mt-2">
                        Confidence: {(result.confidence * 100).toFixed(1)}%
                      </div>
                    </div>

                    {/* LLM Analysis Section */}
                    {result.llmAnalysis && (
                      <div className="space-y-4">
                        <h3 className="text-lg font-semibold">AI Analysis Summary</h3>
                        
                        <div className="grid md:grid-cols-2 gap-4">
                          <Card>
                            <CardHeader className="pb-3">
                              <CardTitle className="text-sm">Clinical Summary</CardTitle>
                            </CardHeader>
                            <CardContent>
                              <p className="text-sm text-slate-600 dark:text-slate-400">
                                {result.llmAnalysis.clinical_summary}
                              </p>
                            </CardContent>
                          </Card>

                          <Card>
                            <CardHeader className="pb-3">
                              <CardTitle className="text-sm">Risk Assessment</CardTitle>
                            </CardHeader>
                            <CardContent>
                              <p className="text-sm text-slate-600 dark:text-slate-400">
                                {result.llmAnalysis.risk_score}
                              </p>
                            </CardContent>
                          </Card>

                          <Card>
                            <CardHeader className="pb-3">
                              <CardTitle className="text-sm">Suspected Region</CardTitle>
                            </CardHeader>
                            <CardContent>
                              <p className="text-sm text-slate-600 dark:text-slate-400">
                                {result.llmAnalysis.suspected_region}
                              </p>
                            </CardContent>
                          </Card>

                          <Card>
                            <CardHeader className="pb-3">
                              <CardTitle className="text-sm">Key Observations</CardTitle>
                            </CardHeader>
                            <CardContent>
                              <ul className="text-sm text-slate-600 dark:text-slate-400 space-y-1">
                                {result.llmAnalysis.key_observations?.map((obs, index) => (
                                  <li key={index} className="flex items-start">
                                    <span className="text-primary mr-2">•</span>
                                    {obs}
                                  </li>
                                ))}
                              </ul>
                            </CardContent>
                          </Card>
                        </div>

                        <Card>
                          <CardHeader className="pb-3">
                            <CardTitle className="text-sm">Recommendations</CardTitle>
                          </CardHeader>
                          <CardContent>
                            <ul className="text-sm text-slate-600 dark:text-slate-400 space-y-1">
                              {result.llmAnalysis.recommendations?.map((rec, index) => (
                                <li key={index} className="flex items-start">
                                  <span className="text-primary mr-2">✓</span>
                                  {rec}
                                </li>
                              ))}
                            </ul>
                          </CardContent>
                        </Card>
                      </div>
                    )}

                    {result.heatmapUrl && (
                      <div>
                        <h3 className="text-sm font-medium mb-2">Explainability Heatmap:</h3>
                        <div className="relative w-full max-w-md mx-auto">
                          <Image
                            src={result.heatmapUrl}
                            alt="Grad-CAM Heatmap"
                            width={400}
                            height={400}
                            className="rounded-lg border"
                          />
                        </div>
                        <p className="text-xs text-slate-500 mt-2 text-center">
                          Red areas show regions the AI focused on for diagnosis
                        </p>
                      </div>
                    )}

                    <Button onClick={downloadReport} variant="outline" className="w-full">
                      <Download className="h-4 w-4 mr-2" />
                      Download Report (PDF)
                    </Button>
                  </div>
                </CardContent>
              </Card>
            )}
          </div>

          {/* History Sidebar */}
          <div className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <History className="h-5 w-5" />
                  Previous Analyses
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {history.map((item) => (
                    <div key={item.id} className="border-b pb-4 last:border-b-0">
                      <div className="flex justify-between items-start">
                        <div>
                          <div className={`font-medium ${getDiseaseColor(item.disease)}`}>
                            {item.disease}
                          </div>
                          <div className="text-sm text-slate-500">{item.date}</div>
                        </div>
                        <div className="text-right">
                          <div className="text-sm font-medium">
                            {(item.confidence * 100).toFixed(0)}%
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  )
}