"use client"

import { useState, useRef } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Progress } from "@/components/ui/progress"
import { Upload, Image as ImageIcon, Download, History, AlertCircle } from "lucide-react"
import Image from "next/image"

// Update this with your actual deployed backend
const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

interface PredictionResult {
  predicted_class: string
  confidence: number
  all_probabilities: Record<string, number>
}

interface DiagnosisHistory {
  id: string
  date: string
  disease: string
  confidence: number
}

interface DiseaseState {
  selectedFile: File | null
  previewUrl: string | null
  isAnalyzing: boolean
  result: PredictionResult | null
  error: string | null
}

const diseaseTypes = ["Alzheimer's", "Tumor", "Parkinson's", "Cancer"]

// Map model class names → Human readable - UPDATED based on your backend output
const CLASS_MAPPING: Record<string, string> = {
  "Mild Impairment": "Mild Alzheimer's",
  "Moderate Impairment": "Moderate Alzheimer's", 
  "No Impairment": "No Alzheimer's (Healthy)",
  "Very Mild Impairment": "Very Mild Alzheimer's",
}

export default function DiagnosisPage() {
  const [selectedDisease, setSelectedDisease] = useState<string | null>(null)

  const fileInputRefs = {
    "Alzheimer's": useRef<HTMLInputElement>(null),
    "Tumor": useRef<HTMLInputElement>(null),
    "Parkinson's": useRef<HTMLInputElement>(null),
    "Cancer": useRef<HTMLInputElement>(null),
  }

  const [diseasesState, setDiseasesState] = useState<Record<string, DiseaseState>>(() => {
    const initial: Record<string, DiseaseState> = {}
    diseaseTypes.forEach(d => {
      initial[d] = {
        selectedFile: null,
        previewUrl: null,
        isAnalyzing: false,
        result: null,
        error: null
      }
    })
    return initial
  })

  const [history, setHistory] = useState<DiagnosisHistory[]>([])

  const currentDisease = selectedDisease
  const state = currentDisease ? diseasesState[currentDisease] : null

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>, disease: string) => {
    const file = e.target.files?.[0]
    if (!file) return

    // Validate file type
    if (!file.type.startsWith('image/')) {
      setDiseasesState(prev => ({
        ...prev,
        [disease]: {
          ...prev[disease],
          error: "Please select a valid image file (JPEG, PNG, etc.)"
        }
      }))
      return
    }

    const url = URL.createObjectURL(file)
    setDiseasesState(prev => ({
      ...prev,
      [disease]: {
        selectedFile: file,
        previewUrl: url,
        result: null,
        error: null,
        isAnalyzing: false
      }
    }))
  }

  const handleAnalysis = async (disease: string) => {
    if (!state?.selectedFile || !disease) return

    setDiseasesState(prev => ({
      ...prev,
      [disease]: { ...prev[disease], isAnalyzing: true, error: null }
    }))

    if (disease === "Alzheimer's") {
      try {
        const formData = new FormData()
        formData.append("file", state.selectedFile)

        console.log("Sending request to backend...")
        const response = await fetch(`${API_URL}/predict`, {
          method: "POST",
          body: formData,
        })

        if (!response.ok) {
          const errorText = await response.text()
          console.error("Backend error:", response.status, errorText)
          throw new Error(`Server error: ${response.status} - ${errorText}`)
        }

        const data = await response.json()
        console.log("Backend response:", data)

        // FIXED: Use confidence directly (it's already 0-1 from backend)
        const confidence = data.confidence
        
        // FIXED: Map the class names properly
        const mappedClass = CLASS_MAPPING[data.predicted_class] || data.predicted_class
        
        // FIXED: Process probabilities correctly
        const allProbabilities: Record<string, number> = {}
        Object.entries(data.all_probabilities || {}).forEach(([key, value]) => {
          const mappedKey = CLASS_MAPPING[key] || key
          allProbabilities[mappedKey] = typeof value === 'number' ? value : parseFloat(value as string)
        })

        const result: PredictionResult = {
          predicted_class: mappedClass,
          confidence: confidence,
          all_probabilities: allProbabilities
        }

        console.log("Processed result:", result)

        setDiseasesState(prev => ({
          ...prev,
          [disease]: { ...prev[disease], result, isAnalyzing: false }
        }))

        // Add to history
        setHistory(prev => [{
          id: Date.now().toString(),
          date: new Date().toLocaleDateString(),
          disease: mappedClass,
          confidence
        }, ...prev.slice(0, 9)]) // Keep last 10

      } catch (err: any) {
        console.error("Analysis failed:", err)
        setDiseasesState(prev => ({
          ...prev,
          [disease]: {
            ...prev[disease],
            isAnalyzing: false,
            error: err.message || "Failed to analyze image. Please make sure the backend server is running on http://localhost:8000"
          }
        }))
      }
    } else {
      // Mock for other diseases (unchanged)
      setTimeout(() => {
        const mockResult: PredictionResult = {
          predicted_class: "Coming Soon",
          confidence: 0.95,
          all_probabilities: { "Detected": 0.95, "Not Detected": 0.05 }
        }
        setDiseasesState(prev => ({
          ...prev,
          [disease]: { ...prev[disease], result: mockResult, isAnalyzing: false }
        }))
      }, 2500)
    }
  }

  const downloadReport = () => {
    if (!state?.result || !currentDisease) return

    const probs = state.result.all_probabilities
    const lines = [
      "BRAIN MRI DIAGNOSIS REPORT",
      "=".repeat(50),
      `Disease Analyzed: ${currentDisease}`,
      `Date: ${new Date().toLocaleDateString()}`,
      `Time: ${new Date().toLocaleTimeString()}`,
      "",
      "RESULT:",
      `- Predicted: ${state.result.predicted_class}`,
      `- Confidence: ${(state.result.confidence * 100).toFixed(2)}%`,
      "",
      "DETAILED PROBABILITIES:",
      ...Object.entries(probs)
        .sort((a, b) => b[1] - a[1])
        .map(([cls, prob]) => `  • ${cls}: ${(prob * 100).toFixed(2)}%`),
      "",
      "DISCLAIMER:",
      "This is an AI-powered screening tool and NOT a medical diagnosis.",
      "Please consult a neurologist or radiologist for official interpretation.",
      "",
      "Generated by AI Brain MRI Analyzer"
    ]

    const blob = new Blob([lines.join("\n")], { type: "text/plain" })
    const url = URL.createObjectURL(blob)
    const a = document.createElement("a")
    a.href = url
    a.download = `MRI_Report_${currentDisease.replace(/\s+/g, '_')}_${Date.now()}.txt`
    a.click()
    URL.revokeObjectURL(url)
  }

  const getSeverityColor = (cls: string) => {
    if (cls.includes("Healthy") || cls.includes("No Alzheimer")) return "text-green-600"
    if (cls.includes("Very Mild")) return "text-yellow-600"
    if (cls.includes("Mild")) return "text-orange-600"
    if (cls.includes("Moderate")) return "text-red-600"
    return "text-gray-600"
  }

  const getBadgeClass = (cls: string) => {
    if (cls.includes("Healthy") || cls.includes("No Alzheimer")) return "bg-green-100 text-green-800 border-green-300"
    if (cls.includes("Very Mild")) return "bg-yellow-100 text-yellow-800 border-yellow-300"
    if (cls.includes("Mild")) return "bg-orange-100 text-orange-800 border-orange-300"
    if (cls.includes("Moderate")) return "bg-red-100 text-red-800 border-red-300"
    return "bg-gray-100 text-gray-800 border-gray-300"
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="max-w-7xl mx-auto">
        <div className="text-center mb-10">
          <h1 className="text-4xl font-bold mb-4">Brain MRI AI Diagnosis</h1>
          <p className="text-lg text-muted-foreground">
            Upload your MRI scan for instant AI-powered analysis
          </p>
        </div>

        <div className="grid lg:grid-cols-3 gap-8">
          {/* Main Panel */}
          <div className="lg:col-span-2">
            <Card>
              <CardHeader>
                <div className="flex flex-wrap gap-3 justify-center">
                  {diseaseTypes.map((d) => (
                    <Button
                      key={d}
                      variant={selectedDisease === d ? "default" : "outline"}
                      onClick={() => setSelectedDisease(d)}
                    >
                      {d}
                    </Button>
                  ))}
                </div>
              </CardHeader>

              <CardContent>
                {state ? (
                  <>
                    <Input
                      ref={fileInputRefs[currentDisease]}
                      type="file"
                      accept="image/*"
                      onChange={(e) => handleFileSelect(e, currentDisease)}
                      className="hidden"
                    />

                    <Button
                      variant="outline"
                      className="w-full h-40 border-dashed border-2"
                      onClick={() => fileInputRefs[currentDisease].current?.click()}
                    >
                      <div className="text-center">
                        <Upload className="w-12 h-12 mx-auto mb-3 text-muted-foreground" />
                        <p>Click to upload MRI</p>
                        <p className="text-xs text-muted-foreground">JPG, PNG</p>
                      </div>
                    </Button>

                    {state.previewUrl && (
                      <div className="my-6 text-center">
                        <Image
                          src={state.previewUrl}
                          alt="MRI Preview"
                          width={380}
                          height={380}
                          className="rounded-lg shadow-md mx-auto"
                        />
                      </div>
                    )}

                    {state.error && (
                      <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-4">
                        <div className="flex gap-3">
                          <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0" />
                          <div>
                            <p className="text-sm text-red-700 font-semibold">Analysis Error</p>
                            <p className="text-sm text-red-700 mt-1">{state.error}</p>
                            {state.error.includes("localhost") && (
                              <p className="text-xs text-red-600 mt-2">
                                Make sure the backend server is running with: 
                                <code className="ml-1 bg-red-100 px-1 rounded">python main.py</code>
                              </p>
                            )}
                          </div>
                        </div>
                      </div>
                    )}

                    {state.selectedFile && !state.result && !state.isAnalyzing && (
                      <Button
                        size="lg"
                        className="w-full"
                        onClick={() => handleAnalysis(currentDisease)}
                      >
                        <ImageIcon className="w-5 h-5 mr-2" />
                        Analyze with AI
                      </Button>
                    )}

                    {state.isAnalyzing && (
                      <div className="text-center py-8">
                        <div className="animate-spin w-12 h-12 border-4 border-blue-600 border-t-transparent rounded-full mx-auto mb-4" />
                        <p>AI is analyzing your brain MRI...</p>
                        <p className="text-sm text-muted-foreground mt-2">
                          This may take a few seconds
                        </p>
                        <Progress value={80} className="mt-4 max-w-sm mx-auto" />
                      </div>
                    )}

                    {state.result && (
                      <div className="mt-8 p-6 bg-gradient-to-br from-blue-50 to-indigo-50 rounded-xl border">
                        <div className="text-center mb-6">
                          <span className={`inline-block px-6 py-3 rounded-full text-lg font-bold border-2 ${getBadgeClass(state.result.predicted_class)}`}>
                            {state.result.predicted_class}
                          </span>
                          <div className="mt-6">
                            <p className="text-sm font-semibold text-center text-black">Confidence :</p>
                            <p className="text-5xl font-bold mt-2 text-black">
                              {(state.result.confidence * 100).toFixed(1)}%
                            </p>
                          </div>
                        </div>

                        <div className="space-y-4 mt-8">
                          <h3 className="font-semibold text-center text-black">Probability Breakdown</h3>
                          {Object.entries(state.result.all_probabilities)
                            .sort((a, b) => b[1] - a[1])
                            .map(([label, prob]) => (
                              <div key={label} className="flex justify-between items-center">
                                <span className={`text-sm font-medium ${getSeverityColor(label)}`}>
                                  {label}
                                </span>
                                <div className="flex items-center gap-3 w-48">
                                  <Progress value={prob * 100} className="flex-1" />
                                  <span className="text-sm font-medium w-16 text-right">
                                    {(prob * 100).toFixed(1)}%
                                  </span>
                                </div>
                              </div>
                            ))}
                        </div>

                        <Button onClick={downloadReport} variant="secondary" className="w-full mt-8">
                          <Download className="w-4 h-4 mr-2" />
                          Download Medical Report
                        </Button>
                      </div>
                    )}
                  </>
                ) : (
                  <div className="text-center py-20 text-muted-foreground">
                    <ImageIcon className="w-20 h-20 mx-auto mb-4 opacity-50" />
                    <p>Select a condition above to start</p>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <History className="w-5 h-5" />
                  Recent Scans
                </CardTitle>
              </CardHeader>
              <CardContent>
                {history.length === 0 ? (
                  <p className="text-sm text-muted-foreground text-center py-8">
                    No scans yet
                  </p>
                ) : (
                  <div className="space-y-4">
                    {history.map((h) => (
                      <div key={h.id} className="flex justify-between items-center border-b pb-3 last:border-0">
                        <div>
                          <p className={`font-medium ${getSeverityColor(h.disease)}`}>
                            {h.disease}
                          </p>
                          <p className="text-xs text-muted-foreground">{h.date}</p>
                        </div>
                        <span className="text-lg font-bold">
                          {(h.confidence * 100).toFixed(0)}%
                        </span>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>

            <Card className="bg-amber-50 border-amber-200">
              <CardHeader>
                <CardTitle className="text-amber-900 flex items-center gap-2">
                  <AlertCircle className="w-5 h-5" />
                  Important
                </CardTitle>
              </CardHeader>
              <CardContent className="text-sm text-amber-800">
                <p>
                  This tool uses AI to assist in screening. 
                  <strong> It is not a substitute for professional medical diagnosis.</strong>
                </p>
                <p className="mt-2">
                  Always consult a qualified neurologist with your MRI results.
                </p>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  )
}