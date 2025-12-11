/**
 * Authentication types and interfaces for CarthaNeuro frontend
 */

export interface User {
  user_id: string;
  username: string;
  email: string;
  first_name?: string;
  last_name?: string;
  role: string;
  is_active: boolean;
  is_email_verified: boolean;
  created_at: string;
  last_login?: string;
}

export interface AuthTokens {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface RegisterRequest {
  username: string;
  email: string;
  password: string;
  first_name?: string;
  last_name?: string;
}

export interface AuthResponse {
  success: boolean;
  message: string;
  user?: User;
  tokens?: AuthTokens;
}

export interface ChangePasswordRequest {
  old_password: string;
  new_password: string;
}

export interface RefreshTokenRequest {
  refresh_token: string;
}

export interface UserProfileUpdate {
  first_name?: string;
  last_name?: string;
}

export interface AuthState {
  user: User | null;
  tokens: AuthTokens | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
}

export interface AuthContextType extends AuthState {
  login: (email: string, password: string) => Promise<void>;
  register: (userData: RegisterRequest) => Promise<void>;
  logout: () => void;
  refreshToken: () => Promise<void>;
  updateProfile: (data: UserProfileUpdate) => Promise<void>;
  changePassword: (oldPassword: string, newPassword: string) => Promise<void>;
  clearError: () => void;
}

export interface ApiError {
  message: string;
  status?: number;
  field?: string;
}