"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Brain, Eye, EyeOff, AlertCircle, CheckCircle, User, Mail, Lock } from "lucide-react";
import { motion } from "framer-motion";
import { useAuth } from "@/contexts/auth-context";
import { RegisterRequest } from "@/types/auth";
import { authService } from "@/lib/auth-service";

export default function RegisterPage() {
  const router = useRouter();
  const { register, isLoading } = useAuth();
  
  const [formData, setFormData] = useState<RegisterRequest>({
    username: "",
    email: "",
    password: "",
    first_name: "",
    last_name: "",
  });
  
  const [confirmPassword, setConfirmPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [emailExists, setEmailExists] = useState(false);
  const [usernameExists, setUsernameExists] = useState(false);
  const [checkingAvailability, setCheckingAvailability] = useState<Record<string, boolean>>({});

  // Form validation
  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {};

    if (!formData.username) {
      newErrors.username = "Username is required";
    } else if (formData.username.length < 3) {
      newErrors.username = "Username must be at least 3 characters";
    }

    if (!formData.email) {
      newErrors.email = "Email is required";
    } else if (!/\S+@\S+\.\S+/.test(formData.email)) {
      newErrors.email = "Please enter a valid email";
    }

    if (!formData.password) {
      newErrors.password = "Password is required";
    } else if (formData.password.length < 6) {
      newErrors.password = "Password must be at least 6 characters";
    }

    if (!confirmPassword) {
      newErrors.confirmPassword = "Please confirm your password";
    } else if (formData.password !== confirmPassword) {
      newErrors.confirmPassword = "Passwords do not match";
    }

    if (emailExists) {
      newErrors.email = "This email is already registered";
    }

    if (usernameExists) {
      newErrors.username = "This username is already taken";
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  // Check email availability
  const checkEmailAvailability = async (email: string) => {
    if (!email || !/\S+@\S+\.\S+/.test(email)) return;
    
    setCheckingAvailability(prev => ({ ...prev, email: true }));
    try {
      const exists = await authService.checkEmail(email);
      setEmailExists(exists);
    } catch (error) {
      console.error("Failed to check email availability:", error);
    } finally {
      setCheckingAvailability(prev => ({ ...prev, email: false }));
    }
  };

  // Check username availability
  const checkUsernameAvailability = async (username: string) => {
    if (!username || username.length < 3) return;
    
    setCheckingAvailability(prev => ({ ...prev, username: true }));
    try {
      const exists = await authService.checkUsername(username);
      setUsernameExists(exists);
    } catch (error) {
      console.error("Failed to check username availability:", error);
    } finally {
      setCheckingAvailability(prev => ({ ...prev, username: false }));
    }
  };

  // Handle form submission
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!validateForm()) {
      return;
    }

    try {
      await register(formData);
    } catch (error: any) {
      setErrors({ submit: error.message });
    }
  };

  // Handle input changes
  const handleInputChange = (field: keyof RegisterRequest, value: string) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    
    // Clear field errors when user starts typing
    if (errors[field]) {
      setErrors(prev => ({ ...prev, [field]: "" }));
    }

    // Check availability for email and username
    if (field === "email" && value !== formData.email) {
      const timeoutId = setTimeout(() => checkEmailAvailability(value), 500);
      return () => clearTimeout(timeoutId);
    }
    
    if (field === "username" && value !== formData.username) {
      const timeoutId = setTimeout(() => checkUsernameAvailability(value), 500);
      return () => clearTimeout(timeoutId);
    }
  };

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
          <h1 className="text-2xl font-bold font-heading mb-2">Create Account</h1>
          <p className="text-slate-600 dark:text-slate-400">
            Join our medical AI platform to get started
          </p>
        </div>

        <Card>
          <CardHeader>
            <CardTitle>Sign Up</CardTitle>
            <CardDescription>
              Create your account to access the platform
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-4">
              {/* Username */}
              <div className="space-y-2">
                <label htmlFor="username" className="text-sm font-medium flex items-center gap-2">
                  <User className="h-4 w-4" />
                  Username
                </label>
                <div className="relative">
                  <Input
                    id="username"
                    type="text"
                    placeholder="Choose a username"
                    value={formData.username}
                    onChange={(e) => handleInputChange("username", e.target.value)}
                    className={`${errors.username ? "border-red-500" : ""} ${usernameExists ? "border-red-500" : ""}`}
                  />
                  {checkingAvailability.username && (
                    <div className="absolute right-3 top-1/2 -translate-y-1/2">
                      <div className="animate-spin h-4 w-4 border-2 border-primary border-t-transparent rounded-full" />
                    </div>
                  )}
                  {!checkingAvailability.username && formData.username && !errors.username && (
                    <div className="absolute right-3 top-1/2 -translate-y-1/2">
                      {usernameExists ? (
                        <AlertCircle className="h-4 w-4 text-red-500" />
                      ) : (
                        <CheckCircle className="h-4 w-4 text-green-500" />
                      )}
                    </div>
                  )}
                </div>
                {errors.username && (
                  <p className="text-red-500 text-sm">{errors.username}</p>
                )}
              </div>

              {/* Email */}
              <div className="space-y-2">
                <label htmlFor="email" className="text-sm font-medium flex items-center gap-2">
                  <Mail className="h-4 w-4" />
                  Email
                </label>
                <div className="relative">
                  <Input
                    id="email"
                    type="email"
                    placeholder="your.email@hospital.com"
                    value={formData.email}
                    onChange={(e) => handleInputChange("email", e.target.value)}
                    className={`${errors.email ? "border-red-500" : ""} ${emailExists ? "border-red-500" : ""}`}
                  />
                  {checkingAvailability.email && (
                    <div className="absolute right-3 top-1/2 -translate-y-1/2">
                      <div className="animate-spin h-4 w-4 border-2 border-primary border-t-transparent rounded-full" />
                    </div>
                  )}
                  {!checkingAvailability.email && formData.email && !errors.email && (
                    <div className="absolute right-3 top-1/2 -translate-y-1/2">
                      {emailExists ? (
                        <AlertCircle className="h-4 w-4 text-red-500" />
                      ) : (
                        <CheckCircle className="h-4 w-4 text-green-500" />
                      )}
                    </div>
                  )}
                </div>
                {errors.email && (
                  <p className="text-red-500 text-sm">{errors.email}</p>
                )}
              </div>

              {/* Name fields */}
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <label htmlFor="first_name" className="text-sm font-medium">
                    First Name
                  </label>
                  <Input
                    id="first_name"
                    type="text"
                    placeholder="First name"
                    value={formData.first_name}
                    onChange={(e) => handleInputChange("first_name", e.target.value)}
                  />
                </div>
                <div className="space-y-2">
                  <label htmlFor="last_name" className="text-sm font-medium">
                    Last Name
                  </label>
                  <Input
                    id="last_name"
                    type="text"
                    placeholder="Last name"
                    value={formData.last_name}
                    onChange={(e) => handleInputChange("last_name", e.target.value)}
                  />
                </div>
              </div>

              {/* Password */}
              <div className="space-y-2">
                <label htmlFor="password" className="text-sm font-medium flex items-center gap-2">
                  <Lock className="h-4 w-4" />
                  Password
                </label>
                <div className="relative">
                  <Input
                    id="password"
                    type={showPassword ? "text" : "password"}
                    placeholder="Create a password"
                    value={formData.password}
                    onChange={(e) => handleInputChange("password", e.target.value)}
                    className={`${errors.password ? "border-red-500" : ""} pr-10`}
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
                {errors.password && (
                  <p className="text-red-500 text-sm">{errors.password}</p>
                )}
              </div>

              {/* Confirm Password */}
              <div className="space-y-2">
                <label htmlFor="confirmPassword" className="text-sm font-medium flex items-center gap-2">
                  <Lock className="h-4 w-4" />
                  Confirm Password
                </label>
                <div className="relative">
                  <Input
                    id="confirmPassword"
                    type={showConfirmPassword ? "text" : "password"}
                    placeholder="Confirm your password"
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    className={`${errors.confirmPassword ? "border-red-500" : ""} pr-10`}
                  />
                  <button
                    type="button"
                    onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-500 hover:text-slate-700 dark:text-slate-400 dark:hover:text-slate-200"
                  >
                    {showConfirmPassword ? (
                      <EyeOff className="h-4 w-4" />
                    ) : (
                      <Eye className="h-4 w-4" />
                    )}
                  </button>
                </div>
                {errors.confirmPassword && (
                  <p className="text-red-500 text-sm">{errors.confirmPassword}</p>
                )}
              </div>

              {/* Submit error */}
              {errors.submit && (
                <div className="flex items-center space-x-2 text-red-600 dark:text-red-400 text-sm">
                  <AlertCircle className="h-4 w-4" />
                  <span>{errors.submit}</span>
                </div>
              )}

              <Button
                type="submit"
                className="w-full"
                disabled={isLoading || emailExists || usernameExists}
              >
                {isLoading ? "Creating account..." : "Create Account"}
              </Button>
            </form>

            <div className="mt-6 text-center">
              <p className="text-sm text-slate-600 dark:text-slate-400">
                Already have an account?{" "}
                <Link href="/login" className="text-primary hover:underline">
                  Sign in
                </Link>
              </p>
            </div>
          </CardContent>
        </Card>
      </motion.div>
    </div>
  );
}