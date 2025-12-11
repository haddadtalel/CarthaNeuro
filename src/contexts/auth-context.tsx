/**
 * Authentication Context for CarthaNeuro
 * Provides authentication state and methods to the entire application
 */
'use client';

import React, { createContext, useContext, useEffect, useState, useCallback, ReactNode } from 'react';
import { useRouter } from 'next/navigation';
import {
  LoginRequest,
  RegisterRequest,
  UserProfileUpdate,
  AuthContextType,
  AuthState,
} from '@/types/auth';
import { authService } from '@/lib/auth-service';

const AuthContext = createContext<AuthContextType | null>(null);

interface AuthProviderProps {
  children: ReactNode;
}

export function AuthProvider({ children }: AuthProviderProps) {
  const router = useRouter();
  
  const [state, setState] = useState<AuthState>({
    user: null,
    tokens: null,
    isAuthenticated: false,
    isLoading: true,
    error: null,
  });

  /**
   * Logout user
   */
  const logout = useCallback((): void => {
    authService.logout();
    setState({
      user: null,
      tokens: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,
    });
    
    // Redirect to login page
    router.push('/login');
  }, [router]);

  /**
   * Initialize authentication state from localStorage
   */
  const initializeAuth = useCallback(async () => {
    try {
      setState(prev => ({ ...prev, isLoading: true, error: null }));
      
      // Check if user has stored authentication data
      if (authService.isAuthenticated()) {
        const user = authService.getStoredUser();
        const tokens = authService.getStoredTokens();
        
        if (user && tokens) {
          setState({
            user,
            tokens,
            isAuthenticated: true,
            isLoading: false,
            error: null,
          });
          
          // Verify token is still valid by fetching current user
          try {
            const currentUser = await authService.getCurrentUser();
            setState(prev => ({
              ...prev,
              user: currentUser,
              isLoading: false,
            }));
          } catch (error) {
            // Token might be expired, logout user
            console.error('Token verification failed:', error);
            logout();
          }
        } else {
          // Invalid stored data, clear it
          authService.logout();
          setState({
            user: null,
            tokens: null,
            isAuthenticated: false,
            isLoading: false,
            error: null,
          });
        }
      } else {
        setState({
          user: null,
          tokens: null,
          isAuthenticated: false,
          isLoading: false,
          error: null,
        });
      }
    } catch (error: unknown) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error';
      console.error('Auth initialization failed:', error);
      setState({
        user: null,
        tokens: null,
        isAuthenticated: false,
        isLoading: false,
        error: errorMessage,
      });
    }
  }, [logout]);

  useEffect(() => {
    // Using void to handle the promise without awaiting
    void initializeAuth();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  /**
   * Login user
   */
  const login = async (email: string, password: string): Promise<void> => {
    try {
      setState(prev => ({ ...prev, isLoading: true, error: null }));
      
      const loginData: LoginRequest = { email, password };
      const { user, tokens } = await authService.login(loginData);
      
      setState({
        user,
        tokens,
        isAuthenticated: true,
        isLoading: false,
        error: null,
      });
      
      // Use window.location for reliable redirect after login
      // router.push doesn't always work reliably in context providers
      window.location.href = '/diagnosis';
    } catch (error: unknown) {
      const errorMessage = error instanceof Error ? error.message : 'Login failed';
      setState(prev => ({
        ...prev,
        isLoading: false,
        error: errorMessage,
      }));
      throw new Error(errorMessage);
    }
  };

  /**
   * Register new user
   */
  const register = async (userData: RegisterRequest): Promise<void> => {
    try {
      setState(prev => ({ ...prev, isLoading: true, error: null }));
      
      const { user, tokens } = await authService.register(userData);
      
      setState({
        user,
        tokens,
        isAuthenticated: true,
        isLoading: false,
        error: null,
      });
      
      // Use window.location for reliable redirect after registration
      window.location.href = '/diagnosis';
    } catch (error: unknown) {
      const errorMessage = error instanceof Error ? error.message : 'Registration failed';
      setState(prev => ({
        ...prev,
        isLoading: false,
        error: errorMessage,
      }));
      throw new Error(errorMessage);
    }
  };

  /**
   * Refresh access token
   */
  const refreshToken = async (): Promise<void> => {
    try {
      const tokens = await authService.refreshToken();
      setState(prev => ({
        ...prev,
        tokens,
      }));
    } catch (error: unknown) {
      console.error('Token refresh failed:', error);
      // If refresh fails, logout user
      logout();
      const errorMessage = error instanceof Error ? error.message : 'Token refresh failed';
      throw new Error(errorMessage);
    }
  };

  /**
   * Update user profile
   */
  const updateProfile = async (data: UserProfileUpdate): Promise<void> => {
    try {
      setState(prev => ({ ...prev, error: null }));
      
      const updatedUser = await authService.updateProfile(data);
      
      setState(prev => ({
        ...prev,
        user: updatedUser,
      }));
    } catch (error: unknown) {
      const errorMessage = error instanceof Error ? error.message : 'Profile update failed';
      setState(prev => ({
        ...prev,
        error: errorMessage,
      }));
      throw new Error(errorMessage);
    }
  };

  /**
   * Change user password
   */
  const changePassword = async (oldPassword: string, newPassword: string): Promise<void> => {
    try {
      setState(prev => ({ ...prev, error: null }));
      
      await authService.changePassword({ old_password: oldPassword, new_password: newPassword });
    } catch (error: unknown) {
      const errorMessage = error instanceof Error ? error.message : 'Password change failed';
      setState(prev => ({
        ...prev,
        error: errorMessage,
      }));
      throw new Error(errorMessage);
    }
  };

  /**
   * Clear authentication error
   */
  const clearError = (): void => {
    setState(prev => ({ ...prev, error: null }));
  };

  const contextValue: AuthContextType = {
    ...state,
    login,
    register,
    logout,
    refreshToken,
    updateProfile,
    changePassword,
    clearError,
  };

  return (
    <AuthContext.Provider value={contextValue}>
      {children}
    </AuthContext.Provider>
  );
}

/**
 * Hook to use authentication context
 */
export function useAuth(): AuthContextType {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}

/**
 * Hook to check if user is authenticated
 */
export function useRequireAuth(): AuthContextType {
  const auth = useAuth();
  const router = useRouter();
  
  useEffect(() => {
    if (!auth.isLoading && !auth.isAuthenticated) {
      router.push('/login');
    }
  }, [auth.isLoading, auth.isAuthenticated, router]);
  
  return auth;
}

/**
 * Hook for optional authentication (returns null if not authenticated)
 */
export function useOptionalAuth(): AuthContextType | null {
  const auth = useAuth();
  
  if (auth.isLoading) {
    return auth; // Still loading
  }
  
  if (!auth.isAuthenticated) {
    return null; // Not authenticated
  }
  
  return auth; // Authenticated
}