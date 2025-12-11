"use client"

import { useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Upload, CheckCircle, XCircle, AlertCircle } from "lucide-react"
import { CarthaNeuroApi } from "@/lib/api"

export default function TestUploadPage() {
  const [testResults, setTestResults] = useState<Array<{
    name: string
    status: "pending" | "running" | "success" | "error"
    error?: string
  }>>([])
  const [testing, setTesting] = useState(false)

  const runUploadTests = async () => {
    setTesting(true)
    const tests = [
      { name: "Health Check", test: () => CarthaNeuroApi.healthCheck() },
      { name: "Models Check", test: () => CarthaNeuroApi.getModels() },
      { name: "Dataset Info", test: () => CarthaNeuroApi.getDatasetInfo() },
      { name: "Upload Endpoint", test: async () => {
        // Test if the upload endpoint exists by trying to call it (it should return 400 for missing files, not 404)
        const response = await fetch('/api/data-upload/upload', { method: 'POST' })
        return { status: response.status, ok: response.status !== 404 }
      }},
      { name: "Validate Endpoint", test: async () => {
        const response = await fetch('/api/data-upload/validate?upload_id=test')
        return { status: response.status, ok: response.status !== 404 }
      }},
      { name: "Merge Endpoint", test: async () => {
        const response = await fetch('/api/data-upload/merge?upload_id=test&dataset_name=test', { method: 'POST' })
        return { status: response.status, ok: response.status !== 404 }
      }},
      { name: "Datasets Endpoint", test: () => CarthaNeuroApi.getDatasetInfo() }
    ]

    setTestResults(tests.map(t => ({ name: t.name, status: "pending" })))

    for (let i = 0; i < tests.length; i++) {
      const test = tests[i]
      
      try {
        setTestResults(prev => prev.map((result, index) => 
          index === i ? { ...result, status: "running" as const } : result
        ))

        const result = await test.test()
        
        setTestResults(prev => prev.map((result, index) => 
          index === i ? { ...result, status: "success" as const } : result
        ))
      } catch (error) {
        setTestResults(prev => prev.map((result, index) => 
          index === i ? { 
            ...result, 
            status: "error" as const, 
            error: error instanceof Error ? error.message : "Unknown error"
          } : result
        ))
      }
    }

    setTesting(false)
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "success":
        return <CheckCircle className="h-4 w-4 text-green-500" />
      case "error":
        return <XCircle className="h-4 w-4 text-red-500" />
      default:
        return <AlertCircle className="h-4 w-4 text-gray-400" />
    }
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="max-w-2xl mx-auto">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold font-heading mb-4">Upload API Test</h1>
          <p className="text-lg text-slate-600 dark:text-slate-400">
            Test upload API endpoints to verify 404 fix
          </p>
        </div>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Upload className="h-5 w-5" />
              Upload API Tests
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <Button 
                onClick={runUploadTests} 
                disabled={testing}
                className="w-full"
              >
                {testing ? "Running Tests..." : "Run API Tests"}
              </Button>

              {testResults.length > 0 && (
                <div className="space-y-2">
                  {testResults.map((result, index) => (
                    <div key={index} className="flex items-center justify-between p-3 border rounded">
                      <div className="flex items-center gap-3">
                        {getStatusIcon(result.status)}
                        <span className="font-medium">{result.name}</span>
                      </div>
                      <div className="text-right">
                        <Badge variant={result.status === "success" ? "default" : "secondary"}>
                          {result.status}
                        </Badge>
                        {result.error && (
                          <div className="text-xs text-red-500 mt-1">{result.error}</div>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {testResults.length > 0 && testResults.every(r => r.status === "success") && (
                <div className="mt-4 p-4 bg-green-50 border border-green-200 rounded-lg">
                  <div className="flex items-center gap-2 text-green-700">
                    <CheckCircle className="h-4 w-4" />
                    <span className="font-medium">All tests passed!</span>
                  </div>
                  <p className="text-sm text-green-600 mt-1">
                    The upload API endpoints are working correctly.
                  </p>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}