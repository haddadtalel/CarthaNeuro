/**
 * Authentication service for CarthaNeuro frontend
 * Handles all API calls to the backend authentication endpoints
 */
import api from './api';
import {
  User,
  AuthTokens,
  LoginRequest,
  RegisterRequest,
  AuthResponse,
  ChangePasswordRequest,
  UserProfileUpdate,
} from '@/types/auth';

interface ApiError {
  response?: {
    data?: {
      detail?: string;
    };
  };
  message?: string;
}

class AuthService {
  /**
   * Login user with email and password
   */
  async login(credentials: LoginRequest): Promise<{ user: User; tokens: AuthTokens }> {
    try {
      const response = await api.post<AuthResponse>('/api/v1/auth/login', credentials);
      
      if (response.data.success && response.data.user && response.data.tokens) {
        // Store tokens in localStorage
        localStorage.setItem('access_token', response.data.tokens.access_token);
        localStorage.setItem('refresh_token', response.data.tokens.refresh_token);
        localStorage.setItem('user', JSON.stringify(response.data.user));
        
        // Also set token as cookie for middleware authentication
        document.cookie = `access_token=${response.data.tokens.access_token}; path=/; max-age=${response.data.tokens.expires_in || 3600}`;
        
        return {
          user: response.data.user,
          tokens: response.data.tokens,
        };
      }
      
      throw new Error(response.data.message || 'Login failed');
    } catch (error: unknown) {
      const apiError = error as ApiError;
      const message = apiError.response?.data?.detail || apiError.message || 'Login failed';
      throw new Error(message);
    }
  }

  /**
   * Register new user
   */
  async register(userData: RegisterRequest): Promise<{ user: User; tokens: AuthTokens }> {
    try {
      const response = await api.post<AuthResponse>('/api/v1/auth/register', userData);
      
      if (response.data.success && response.data.user && response.data.tokens) {
        // Store tokens in localStorage
        localStorage.setItem('access_token', response.data.tokens.access_token);
        localStorage.setItem('refresh_token', response.data.tokens.refresh_token);
        localStorage.setItem('user', JSON.stringify(response.data.user));
        
        // Also set token as cookie for middleware authentication
        document.cookie = `access_token=${response.data.tokens.access_token}; path=/; max-age=${response.data.tokens.expires_in || 3600}`;
        
        return {
          user: response.data.user,
          tokens: response.data.tokens,
        };
      }
      
      throw new Error(response.data.message || 'Registration failed');
    } catch (error: unknown) {
      const apiError = error as ApiError;
      const message = apiError.response?.data?.detail || apiError.message || 'Registration failed';
      throw new Error(message);
    }
  }

  /**
   * Logout user (clear local storage and cookies)
   */
  logout(): void {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user');
    
    // Also clear the cookie
    document.cookie = 'access_token=; path=/; max-age=0';
  }

  /**
   * Refresh access token
   */
  async refreshToken(): Promise<AuthTokens> {
    try {
      const refreshToken = localStorage.getItem('refresh_token');
      if (!refreshToken) {
        throw new Error('No refresh token available');
      }

      const response = await api.post<AuthResponse>('/api/v1/auth/refresh', {
        refresh_token: refreshToken,
      });

      if (response.data.success && response.data.tokens) {
        localStorage.setItem('access_token', response.data.tokens.access_token);
        return response.data.tokens;
      }

      throw new Error('Token refresh failed');
    } catch (error: unknown) {
      // If refresh fails, logout user
      this.logout();
      const apiError = error as ApiError;
      const message = apiError.response?.data?.detail || apiError.message || 'Token refresh failed';
      throw new Error(message);
    }
  }

  /**
   * Get current user profile
   */
  async getCurrentUser(): Promise<User> {
    try {
      const response = await api.get<AuthResponse>('/api/v1/auth/me');
      
      if (response.data.success && response.data.user) {
        // Update stored user data
        localStorage.setItem('user', JSON.stringify(response.data.user));
        return response.data.user;
      }
      
      throw new Error('Failed to get user profile');
    } catch (error: unknown) {
      const apiError = error as ApiError;
      const message = apiError.response?.data?.detail || apiError.message || 'Failed to get user profile';
      throw new Error(message);
    }
  }

  /**
   * Update user profile
   */
  async updateProfile(profileData: UserProfileUpdate): Promise<User> {
    try {
      const response = await api.put<AuthResponse>('/api/v1/auth/me', profileData);
      
      if (response.data.success && response.data.user) {
        // Update stored user data
        localStorage.setItem('user', JSON.stringify(response.data.user));
        return response.data.user;
      }
      
      throw new Error(response.data.message || 'Profile update failed');
    } catch (error: unknown) {
      const apiError = error as ApiError;
      const message = apiError.response?.data?.detail || apiError.message || 'Profile update failed';
      throw new Error(message);
    }
  }

  /**
   * Change user password
   */
  async changePassword(passwordData: ChangePasswordRequest): Promise<void> {
    try {
      const response = await api.post<AuthResponse>('/api/v1/auth/change-password', passwordData);
      
      if (!response.data.success) {
        throw new Error(response.data.message || 'Password change failed');
      }
    } catch (error: unknown) {
      const apiError = error as ApiError;
      const message = apiError.response?.data?.detail || apiError.message || 'Password change failed';
      throw new Error(message);
    }
  }

  /**
   * Check if user is authenticated (has valid tokens)
   */
  isAuthenticated(): boolean {
    const token = localStorage.getItem('access_token');
    const user = localStorage.getItem('user');
    return !!(token && user);
  }

  /**
   * Get stored user data
   */
  getStoredUser(): User | null {
    try {
      const userStr = localStorage.getItem('user');
      return userStr ? JSON.parse(userStr) : null;
    } catch {
      return null;
    }
  }

  /**
   * Get stored tokens
   */
  getStoredTokens(): AuthTokens | null {
    try {
      const accessToken = localStorage.getItem('access_token');
      const refreshToken = localStorage.getItem('refresh_token');
      
      if (accessToken && refreshToken) {
        return {
          access_token: accessToken,
          refresh_token: refreshToken,
          token_type: 'bearer',
          expires_in: 3600, // Default 1 hour
        };
      }
      
      return null;
    } catch {
      return null;
    }
  }

  /**
   * Check email availability
   */
  async checkEmail(email: string): Promise<boolean> {
    try {
      const response = await api.get('/api/v1/auth/check-email', {
        params: { email },
      });
      
      return response.data.email_exists || false;
    } catch (error: unknown) {
      console.error('Failed to check email:', error);
      return false;
    }
  }

  /**
   * Check username availability
   */
  async checkUsername(username: string): Promise<boolean> {
    try {
      const response = await api.get('/api/v1/auth/check-username', {
        params: { username },
      });
      
      return response.data.username_exists || false;
    } catch (error: unknown) {
      console.error('Failed to check username:', error);
      return false;
    }
  }
}

// Export singleton instance
export const authService = new AuthService();
export default authService;
