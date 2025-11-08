"use client"

import { useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Progress } from "@/components/ui/progress"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import {
  BarChart3,
  Users,
  Database,
  Play,
  FileText,
  TrendingUp,
  Activity,
  Shield
} from "lucide-react"

// Mock data
const mockKPIs = {
  accuracy: 0.94,
  precision: 0.91,
  recall: 0.89,
  f1Score: 0.90,
  trainingLoss: 0.12,
  validationLoss: 0.15
}

const mockUsers = [
  { id: "1", name: "Dr. Sarah Johnson", email: "sarah@example.com", role: "USER", analyses: 45 },
  { id: "2", name: "Dr. Ahmed Ben Ali", email: "ahmed@example.com", role: "USER", analyses: 32 },
  { id: "3", name: "Admin User", email: "admin@carthaneuro.com", role: "ADMIN", analyses: 0 }
]

const mockDatasets = [
  { id: "1", name: "Alzheimer Dataset v1", samples: 1200, classes: 3, lastTraining: "2024-01-15" },
  { id: "2", name: "Parkinson Dataset v2", samples: 800, classes: 2, lastTraining: "2024-01-10" }
]

const mockPredictions = [
  { id: "1", timestamp: "2024-01-16 14:30", modelVersion: "v2.1", confidence: 0.87 },
  { id: "2", timestamp: "2024-01-16 13:15", modelVersion: "v2.1", confidence: 0.92 },
  { id: "3", timestamp: "2024-01-16 12:45", modelVersion: "v2.1", confidence: 0.78 }
]

export default function AdminDashboard() {
  const [isTraining, setIsTraining] = useState(false)
  const [trainingProgress, setTrainingProgress] = useState(0)

  const handleTrainModel = () => {
    setIsTraining(true)
    setTrainingProgress(0)

    // Simulate training progress
    const interval = setInterval(() => {
      setTrainingProgress(prev => {
        if (prev >= 100) {
          clearInterval(interval)
          setIsTraining(false)
          return 100
        }
        return prev + 10
      })
    }, 1000)
  }

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-900">
      <div className="container mx-auto px-4 py-8">
        <div className="mb-8">
          <h1 className="text-3xl font-bold font-heading mb-2">Admin Dashboard</h1>
          <p className="text-slate-600 dark:text-slate-400">
            Monitor and manage the CarthaNeuro platform
          </p>
        </div>

        {/* Model KPIs */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Accuracy</CardTitle>
              <BarChart3 className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{(mockKPIs.accuracy * 100).toFixed(1)}%</div>
              <p className="text-xs text-muted-foreground">+2.1% from last month</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Precision</CardTitle>
              <TrendingUp className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{(mockKPIs.precision * 100).toFixed(1)}%</div>
              <p className="text-xs text-muted-foreground">+1.5% from last month</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">F1-Score</CardTitle>
              <Activity className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{(mockKPIs.f1Score * 100).toFixed(1)}%</div>
              <p className="text-xs text-muted-foreground">+0.8% from last month</p>
            </CardContent>
          </Card>
        </div>

        <div className="grid lg:grid-cols-2 gap-8 mb-8">
          {/* User Management */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Users className="h-5 w-5" />
                User Management
              </CardTitle>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Name</TableHead>
                    <TableHead>Role</TableHead>
                    <TableHead>Analyses</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {mockUsers.map((user) => (
                    <TableRow key={user.id}>
                      <TableCell>
                        <div>
                          <div className="font-medium">{user.name}</div>
                          <div className="text-sm text-muted-foreground">{user.email}</div>
                        </div>
                      </TableCell>
                      <TableCell>
                        <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
                          user.role === 'ADMIN'
                            ? 'bg-purple-100 text-purple-800 dark:bg-purple-900 dark:text-purple-200'
                            : 'bg-blue-100 text-blue-800 dark:bg-blue-900 dark:text-blue-200'
                        }`}>
                          {user.role === 'ADMIN' && <Shield className="w-3 h-3 mr-1" />}
                          {user.role}
                        </span>
                      </TableCell>
                      <TableCell>{user.analyses}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
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
                {mockDatasets.map((dataset) => (
                  <div key={dataset.id} className="border rounded-lg p-4">
                    <div className="flex justify-between items-start mb-2">
                      <h3 className="font-medium">{dataset.name}</h3>
                      <Button variant="outline" size="sm">Upload New</Button>
                    </div>
                    <div className="text-sm text-muted-foreground space-y-1">
                      <div>Samples: {dataset.samples}</div>
                      <div>Classes: {dataset.classes}</div>
                      <div>Last Training: {dataset.lastTraining}</div>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>

        <div className="grid lg:grid-cols-2 gap-8">
          {/* Model Training */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Play className="h-5 w-5" />
                Model Training
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <Button
                  onClick={handleTrainModel}
                  disabled={isTraining}
                  className="w-full"
                >
                  {isTraining ? "Training..." : "Train Model"}
                </Button>

                {isTraining && (
                  <div className="space-y-2">
                    <div className="flex justify-between text-sm">
                      <span>Progress</span>
                      <span>{trainingProgress}%</span>
                    </div>
                    <Progress value={trainingProgress} />
                    <div className="text-xs text-muted-foreground">
                      Training logs will appear here...
                    </div>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>

          {/* Prediction Logs */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <FileText className="h-5 w-5" />
                Recent Predictions
              </CardTitle>
            </CardHeader>
            <CardContent>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Timestamp</TableHead>
                    <TableHead>Model</TableHead>
                    <TableHead>Confidence</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {mockPredictions.map((prediction) => (
                    <TableRow key={prediction.id}>
                      <TableCell className="text-sm">{prediction.timestamp}</TableCell>
                      <TableCell>{prediction.modelVersion}</TableCell>
                      <TableCell>{(prediction.confidence * 100).toFixed(0)}%</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}