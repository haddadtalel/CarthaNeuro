'use client';

import React, { useState, useEffect } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import Link from 'next/link';
import { Brain, Mail, Lock, User, ArrowRight, AlertCircle, Loader2 } from 'lucide-react';
import { api } from '@/lib/api';
import { saveAuthData, isAuthenticated } from '@/lib/auth';
import { AuthResponse, RegisterData, ValidationError } from '@/types';

// Helper function to format backend errors
function formatError(error: any): string[] {
  const errors: string[] = [];

  // Handle axios error response
  const errorData = error?.response?.data;
  
  if (!errorData) {
    // Network error or unknown error
    return ['An unexpected error occurred. Please try again.'];
  }

  // Handle string detail (custom backend errors)
  if (typeof errorData.detail === 'string') {
    return [errorData.detail];
  }

  // Handle array of Pydantic validation errors
  if (Array.isArray(errorData.detail)) {
    errorData.detail.forEach((err: ValidationError) => {
      if (err.msg) {
        // Format field location for better readability
        const loc = Array.isArray(err.loc) 
          ? err.loc.slice(1).join(' > ') 
          : err.loc;
        
        // Create human-readable message
        const fieldName = loc.charAt(0).toUpperCase() + loc.slice(1);
        
        // Customize common validation messages
        let message = err.msg;
        
        if (err.type === 'value_error.email') {
          message = 'Please enter a valid email address';
        } else if (err.type === 'value_error.string.pattern_mismatch') {
          if (loc === 'password') {
            message = 'Password must be at least 8 characters';
          } else {
            message = err.msg;
          }
        } else if (err.type === 'value_error.any_str.min_length') {
          message = `${fieldName} must be at least ${err.ctx?.min_length || 3} characters`;
        } else if (err.type === 'value_error.any_str.max_length') {
          message = `${fieldName} must be at most ${err.ctx?.max_length || 50} characters`;
        } else if (loc && err.msg) {
          message = `${fieldName}: ${err.msg}`;
        }
        
        errors.push(message);
      }
    });

    if (errors.length === 0) {
      // Fallback if no messages were extracted
      return ['Validation failed. Please check your input.'];
    }
    
    return errors;
  }

  // Handle other error formats
  if (typeof errorData === 'string') {
    return [errorData];
  }

  // Final fallback
  return ['An error occurred. Please try again.'];
}

export default function LoginPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const isRegister = searchParams.get('register') === 'true';

  const [isLogin, setIsLogin] = useState(!isRegister);
  const [loading, setLoading] = useState(false);
  const [errors, setErrors] = useState<string[] | null>(null);

  // Login form state
  const [loginData, setLoginData] = useState({
    username: '',
    password: '',
  });

  // Register form state
  const [registerData, setRegisterData] = useState<RegisterData>({
    email: '',
    username: '',
    password: '',
    full_name: '',
    role: 'user',
  });

  useEffect(() => {
    // Redirect if already authenticated
    if (isAuthenticated()) {
      const userStr = localStorage.getItem('user');
      if (userStr) {
        try {
          const user = JSON.parse(userStr);
          if (user.role === 'admin') {
            router.push('/admin/dashboard');
          } else {
            router.push('/consultation');
          }
        } catch (e) {
          console.error('Failed to parse user data:', e);
        }
      }
    }
  }, [router]);

  // Auto-dismiss timer ref
  const errorTimerRef = React.useRef<ReturnType<typeof setTimeout> | null>(null);
  
  // Track if we just set an error to prevent double-display
  const justSetErrorRef = React.useRef<boolean>(false);

  const clearErrorTimer = () => {
    if (errorTimerRef.current) {
      clearTimeout(errorTimerRef.current);
      errorTimerRef.current = null;
    }
  };

  // Effect to manage error timer
  useEffect(() => {
    if (errors) {
      // If we just set the error in this render cycle, skip storage
      if (!justSetErrorRef.current) {
        // Store error in sessionStorage to persist across re-renders
        sessionStorage.setItem('loginError', JSON.stringify({
          message: errors,
          timestamp: Date.now()
        }));
      }
      justSetErrorRef.current = false;
      
      // Start timer to clear error
      clearErrorTimer();
      errorTimerRef.current = setTimeout(() => {
        setErrors(null);
        sessionStorage.removeItem('loginError');
      }, 5000);
    } else {
      // Only restore from sessionStorage if we didn't just set an error
      if (!justSetErrorRef.current) {
        // Check if there's a persisted error to restore
        const persisted = sessionStorage.getItem('loginError');
        if (persisted) {
          const parsed = JSON.parse(persisted);
          const elapsed = Date.now() - parsed.timestamp;
          if (elapsed < 5000) {
            setErrors(parsed.message);
          } else {
            sessionStorage.removeItem('loginError');
          }
        }
      }
    }
    
    return () => {
      clearErrorTimer();
    };
  }, [errors]);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setErrors(null);
    sessionStorage.removeItem('loginError');
    clearErrorTimer();

    try {
      console.log('Attempting login...');
      const response = await api.login(loginData.username, loginData.password);
      console.log('Login response received:', response);
      console.log('Response status:', response.status);
      console.log('Response data:', response.data);
      
      const data = response.data as AuthResponse;
  
      
      console.log('Saving auth data...');
      saveAuthData(data.access_token, data.refresh_token, data.user);
      console.log('Auth data saved successfully');
      
      // Check localStorage
      const savedToken = localStorage.getItem('access_token');
      const savedUser = localStorage.getItem('user');
      console.log('Token in localStorage:', savedToken ? 'present' : 'missing');
      console.log('User in localStorage:', savedUser ? 'present' : 'missing');
      
      // Redirect based on role
      console.log('User role:', data.user.role);
      if (data.user.role === 'admin') {
        router.push('/admin/dashboard');
      } else {
        router.push('/consultation');
      }
    } catch (err: any) {
      console.error('Login error:', err);
      console.error('Error response:', err.response);
      console.error('Error data:', err.response?.data);
      justSetErrorRef.current = true;
      setErrors(['Incorrect username or password']);
    } finally {
      setLoading(false);
    }
  };

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setErrors(null);
    sessionStorage.removeItem('loginError');
    clearErrorTimer();

    try {
      const response = await api.register(registerData);
      const data = response.data;
      
      // Auto login after registration
      const loginResponse = await api.login(registerData.username, registerData.password);
      const authData = loginResponse.data as AuthResponse;
      
      saveAuthData(authData.access_token, authData.refresh_token, authData.user);
      
      router.push('/consultation');
    } catch (err: any) {
      justSetErrorRef.current = true;
      setErrors(['An error occurred. Please try again.']);
    } finally {
      setLoading(false);
    }
  };

  const handleInputChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>,
    setter: React.Dispatch<React.SetStateAction<any>>
  ) => {
    const { name, value, type } = e.target;
    setter((prev: any) => ({
      ...prev,
      [name]: type === 'checkbox' ? (e.target as HTMLInputElement).checked : value,
    }));
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        {/* Logo */}
        <div className="text-center mb-8">
          <Link href="/" className="inline-flex items-center gap-2">
            <Brain className="w-10 h-10 text-medical" />
            <span className="text-2xl font-bold text-gray-900">Cartha Neuro</span>
          </Link>
        </div>

        {/* Form Card */}
        <div className="card">
          {/* Tab Switch */}
          <div className="flex mb-6">
            <button
              onClick={() => {
                setIsLogin(true);
                setErrors(null);
              }}
              className={`flex-1 py-2 text-center font-medium transition-colors ${
                isLogin
                  ? 'text-medical border-b-2 border-medical'
                  : 'text-gray-500 hover:text-gray-700'
              }`}
            >
              Sign In
            </button>
            <button
              onClick={() => {
                setIsLogin(false);
                setErrors(null);
              }}
              className={`flex-1 py-2 text-center font-medium transition-colors ${
                !isLogin
                  ? 'text-medical border-b-2 border-medical'
                  : 'text-gray-500 hover:text-gray-700'
              }`}
            >
              Register
            </button>
          </div>

          {/* Error Messages */}
          {errors && errors.length > 0 && (
            <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg animate-fade-in animate-error-persist">
              {errors.map((err, index) => (
                <div key={index} className="flex items-start gap-2 text-red-700 text-sm mb-1 last:mb-0">
                  <AlertCircle className="w-5 h-5 flex-shrink-0 mt-0.5" />
                  <span>{err}</span>
                </div>
              ))}
            </div>
          )}

          {isLogin ? (
            /* Login Form */
            <form onSubmit={handleLogin} className="space-y-4">
              <div>
                <label className="label">Username</label>
                <div className="relative">
                  <User className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
                  <input
                    type="text"
                    name="username"
                    value={loginData.username}
                    onChange={(e) => handleInputChange(e, setLoginData)}
                    className="input pl-10"
                    placeholder="Enter your username"
                    required
                  />
                </div>
              </div>

              <div>
                <label className="label">Password</label>
                <div className="relative">
                  <Lock className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
                  <input
                    type="password"
                    name="password"
                    value={loginData.password}
                    onChange={(e) => handleInputChange(e, setLoginData)}
                    className="input pl-10"
                    placeholder="Enter your password"
                    required
                  />
                </div>
              </div>

              <button
                type="submit"
                disabled={loading}
                className="btn btn-primary w-full py-3 flex items-center justify-center gap-2"
              >
                {loading ? (
                  <Loader2 className="w-5 h-5 animate-spin" />
                ) : (
                  <>
                    Sign In
                    <ArrowRight className="w-5 h-5" />
                  </>
                )}
              </button>
            </form>
          ) : (
            /* Registration Form */
            <form onSubmit={handleRegister} className="space-y-4">
              <div>
                <label className="label">Full Name</label>
                <div className="relative">
                  <User className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
                  <input
                    type="text"
                    name="full_name"
                    value={registerData.full_name}
                    onChange={(e) => handleInputChange(e, setRegisterData)}
                    className="input pl-10"
                    placeholder="Enter your full name"
                  />
                </div>
              </div>

              <div>
                <label className="label">Email</label>
                <div className="relative">
                  <Mail className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
                  <input
                    type="email"
                    name="email"
                    value={registerData.email}
                    onChange={(e) => handleInputChange(e, setRegisterData)}
                    className="input pl-10"
                    placeholder="Enter your email"
                    required
                  />
                </div>
              </div>

              <div>
                <label className="label">Username</label>
                <div className="relative">
                  <User className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
                  <input
                    type="text"
                    name="username"
                    value={registerData.username}
                    onChange={(e) => handleInputChange(e, setRegisterData)}
                    className="input pl-10"
                    placeholder="Choose a username"
                    required
                  />
                </div>
              </div>

              <div>
                <label className="label">Password</label>
                <div className="relative">
                  <Lock className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
                  <input
                    type="password"
                    name="password"
                    value={registerData.password}
                    onChange={(e) => handleInputChange(e, setRegisterData)}
                    className="input pl-10"
                    placeholder="Create a password (min 8 characters)"
                    minLength={8}
                    required
                  />
                </div>
              </div>


              <button
                type="submit"
                disabled={loading}
                className="btn btn-primary w-full py-3 flex items-center justify-center gap-2"
              >
                {loading ? (
                  <Loader2 className="w-5 h-5 animate-spin" />
                ) : (
                  <>
                    Create Account
                    <ArrowRight className="w-5 h-5" />
                  </>
                )}
              </button>
            </form>
          )}
        </div>

        {/* Back to Home */}
        <div className="text-center mt-6">
          <Link href="/" className="text-gray-600 hover:text-medical transition-colors">
            ← Back to Home
          </Link>
        </div>
      </div>
    </div>
  );
}
