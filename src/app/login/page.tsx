"use client"

import { useState } from "react"
import Link from "next/link"
import { useRouter } from "next/navigation"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Brain, Eye, EyeOff, AlertCircle } from "lucide-react"
import { motion } from "framer-motion"

export default function LoginPage() {
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [showPassword, setShowPassword] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState("")
  const router = useRouter()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsLoading(true)
    setError("")

    try {
      // Mock authentication - replace with real auth logic
      if (email === "admin@carthaneuro.com" && password === "admin123") {
        // Admin login
        localStorage.setItem("user", JSON.stringify({
          id: "1",
          email: "admin@carthaneuro.com",
          name: "Admin User",
          role: "ADMIN"
        }))
        router.push("/admin")
      } else if (email === "user@example.com" && password === "user123") {
        // Regular user login
        localStorage.setItem("user", JSON.stringify({
          id: "2",
          email: "user@example.com",
          name: "Dr. Sarah Johnson",
          role: "USER"
        }))
        router.push("/diagnosis")
      } else {
        setError("Invalid email or password")
      }
    } catch (err) {
      setError("An error occurred. Please try again.")
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-blue-50 dark:from-slate-900 dark:via-slate-800 dark:to-slate-900 flex items-center justify-center p-4">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="w-full max-w-md"
      >
        <div className="text-center mb-8">
          <Link href="/" className="inline-flex items-center space-x-2 mb-6">
            <div className="p-3 bg-primary/10 rounded-full">
              <Brain className="h-8 w-8 text-primary" />
            </div>
            <span className="text-2xl font-bold font-heading">CarthaNeuro</span>
          </Link>
          <h1 className="text-2xl font-bold font-heading mb-2">Welcome Back</h1>
          <p className="text-slate-600 dark:text-slate-400">
            Sign in to access your medical AI dashboard
          </p>
        </div>

        <Card>
          <CardHeader>
            <CardTitle>Sign In</CardTitle>
            <CardDescription>
              Enter your credentials to access the platform
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="space-y-2">
                <label htmlFor="email" className="text-sm font-medium">
                  Email
                </label>
                <Input
                  id="email"
                  type="email"
                  placeholder="doctor@hospital.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                  className="w-full"
                />
              </div>

              <div className="space-y-2">
                <label htmlFor="password" className="text-sm font-medium">
                  Password
                </label>
                <div className="relative">
                  <Input
                    id="password"
                    type={showPassword ? "text" : "password"}
                    placeholder="Enter your password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    required
                    className="w-full pr-10"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-500 hover:text-slate-700 dark:text-slate-400 dark:hover:text-slate-200"
                  >
                    {showPassword ? (
                      <EyeOff className="h-4 w-4" />
                    ) : (
                      <Eye className="h-4 w-4" />
                    )}
                  </button>
                </div>
              </div>

              {error && (
                <div className="flex items-center space-x-2 text-red-600 dark:text-red-400 text-sm">
                  <AlertCircle className="h-4 w-4" />
                  <span>{error}</span>
                </div>
              )}

              <Button
                type="submit"
                className="w-full"
                disabled={isLoading}
              >
                {isLoading ? "Signing in..." : "Sign In"}
              </Button>
            </form>

            <div className="mt-6 text-center">
              <p className="text-sm text-slate-600 dark:text-slate-400">
                Don't have an account?{" "}
                <Link href="/about" className="text-primary hover:underline">
                  Contact us
                </Link>
              </p>
            </div>

            <div className="mt-6 p-4 bg-blue-50 dark:bg-blue-950/20 rounded-lg">
              <h3 className="text-sm font-medium text-blue-900 dark:text-blue-100 mb-2">
                Demo Credentials
              </h3>
              <div className="text-xs text-blue-700 dark:text-blue-300 space-y-1">
                <div><strong>Admin:</strong> admin@carthaneuro.com / admin123</div>
                <div><strong>User:</strong> user@example.com / user123</div>
              </div>
            </div>
          </CardContent>
        </Card>
      </motion.div>
    </div>
  )
}