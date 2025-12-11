/**
 * Authentication Utilities and Helper Functions
 * Provides common authentication-related utilities
 */
import { User } from '@/types/auth';
import { jwtDecode } from 'jwt-decode';

interface JWTPayload {
  sub: string;
  exp: number;
  iat: number;
  type: string;
}

/**
 * Check if user is authenticated
 */
export function isAuthenticated(): boolean {
  if (typeof window === 'undefined') return false;
  
  const token = localStorage.getItem('access_token');
  const user = localStorage.getItem('user');
  
  return !!(token && user);
}

/**
 * Get stored user data
 */
export function getStoredUser(): User | null {
  if (typeof window === 'undefined') return null;
  
  try {
    const userStr = localStorage.getItem('user');
    return userStr ? JSON.parse(userStr) : null;
  } catch {
    return null;
  }
}

/**
 * Get stored access token
 */
export function getStoredToken(): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem('access_token');
}

/**
 * Check if token is expired
 */
export function isTokenExpired(token: string): boolean {
  try {
    const decoded = jwtDecode<JWTPayload>(token);
    const currentTime = Date.now() / 1000;
    return decoded.exp < currentTime;
  } catch {
    return true; // Consider invalid tokens as expired
  }
}

/**
 * Get token expiration time
 */
export function getTokenExpirationTime(token: string): Date | null {
  try {
    const decoded = jwtDecode<JWTPayload>(token);
    return new Date(decoded.exp * 1000);
  } catch {
    return null;
  }
}

/**
 * Check if user has required role
 */
export function hasRole(user: User | null, allowedRoles: string[]): boolean {
  if (!user) return false;
  return allowedRoles.includes(user.role);
}

/**
 * Check if user is admin
 */
export function isAdmin(user: User | null): boolean {
  return hasRole(user, ['admin', 'system_admin']);
}

/**
 * Check if user is doctor
 */
export function isDoctor(user: User | null): boolean {
  return hasRole(user, ['doctor', 'admin', 'system_admin']);
}

/**
 * Format user display name
 */
export function formatUserName(user: User): string {
  if (user.first_name && user.last_name) {
    return `${user.first_name} ${user.last_name}`;
  }
  return user.username;
}

/**
 * Format user initials for avatar
 */
export function getUserInitials(user: User): string {
  if (user.first_name && user.last_name) {
    return `${user.first_name[0]}${user.last_name[0]}`.toUpperCase();
  }
  return user.username[0].toUpperCase();
}

/**
 * Validate email format
 */
export function isValidEmail(email: string): boolean {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  return emailRegex.test(email);
}

/**
 * Validate password strength
 */
export function validatePasswordStrength(password: string): {
  isValid: boolean;
  errors: string[];
  score: number;
} {
  const errors: string[] = [];
  let score = 0;

  if (password.length < 6) {
    errors.push('Password must be at least 6 characters long');
  } else {
    score += 1;
  }

  if (password.length >= 8) {
    score += 1;
  }

  if (/[a-z]/.test(password)) {
    score += 1;
  } else {
    errors.push('Password must contain at least one lowercase letter');
  }

  if (/[A-Z]/.test(password)) {
    score += 1;
  } else {
    errors.push('Password must contain at least one uppercase letter');
  }

  if (/\d/.test(password)) {
    score += 1;
  } else {
    errors.push('Password must contain at least one number');
  }

  if (/[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?]/.test(password)) {
    score += 1;
  } else {
    errors.push('Password must contain at least one special character');
  }

  return {
    isValid: errors.length === 0,
    errors,
    score: Math.min(score, 5), // Cap score at 5
  };
}

/**
 * Generate random password
 */
export function generateRandomPassword(length: number = 12): string {
  const lowercase = 'abcdefghijklmnopqrstuvwxyz';
  const uppercase = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ';
  const numbers = '0123456789';
  const symbols = '!@#$%^&*()_+-=[]{}|;:,.<>?';
  
  const allChars = lowercase + uppercase + numbers + symbols;
  
  let password = '';
  
  // Ensure at least one character from each category
  password += lowercase[Math.floor(Math.random() * lowercase.length)];
  password += uppercase[Math.floor(Math.random() * uppercase.length)];
  password += numbers[Math.floor(Math.random() * numbers.length)];
  password += symbols[Math.floor(Math.random() * symbols.length)];
  
  // Fill the rest randomly
  for (let i = 4; i < length; i++) {
    password += allChars[Math.floor(Math.random() * allChars.length)];
  }
  
  // Shuffle the password
  return password.split('').sort(() => Math.random() - 0.5).join('');
}

/**
 * Debounce function for input validation
 */
export function debounce<T extends (...args: any[]) => any>(
  func: T,
  delay: number
): (...args: Parameters<T>) => void {
  let timeoutId: NodeJS.Timeout;
  
  return (...args: Parameters<T>) => {
    clearTimeout(timeoutId);
    timeoutId = setTimeout(() => func(...args), delay);
  };
}

/**
 * Get user role display name
 */
export function getRoleDisplayName(role: string): string {
  const roleMap: Record<string, string> = {
    'admin': 'Administrator',
    'system_admin': 'System Administrator',
    'doctor': 'Doctor',
    'user': 'User',
  };
  
  return roleMap[role] || role;
}

/**
 * Get user role color for UI
 */
export function getRoleColor(role: string): string {
  const colorMap: Record<string, string> = {
    'admin': 'bg-red-100 text-red-800 dark:bg-red-900/20 dark:text-red-400',
    'system_admin': 'bg-purple-100 text-purple-800 dark:bg-purple-900/20 dark:text-purple-400',
    'doctor': 'bg-blue-100 text-blue-800 dark:bg-blue-900/20 dark:text-blue-400',
    'user': 'bg-gray-100 text-gray-800 dark:bg-gray-900/20 dark:text-gray-400',
  };
  
  return colorMap[role] || 'bg-gray-100 text-gray-800 dark:bg-gray-900/20 dark:text-gray-400';
}

/**
 * Clean up expired tokens and user data
 */
export function cleanupAuthData(): void {
  if (typeof window === 'undefined') return;
  
  const token = localStorage.getItem('access_token');
  
  // If token exists and is expired, clean up all auth data
  if (token && isTokenExpired(token)) {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user');
  }
}

/**
 * Initialize auth data cleanup on app start
 */
export function initializeAuthCleanup(): void {
  if (typeof window !== 'undefined') {
    cleanupAuthData();
    
    // Set up periodic cleanup (every 5 minutes)
    setInterval(cleanupAuthData, 5 * 60 * 1000);
  }
}