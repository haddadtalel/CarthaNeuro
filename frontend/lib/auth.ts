import { User } from '@/types';

const TOKEN_KEY = 'access_token';
const REFRESH_TOKEN_KEY = 'refresh_token';
const USER_KEY = 'user';

export function getToken(): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem(TOKEN_KEY);
}

export function setToken(token: string): void {
  if (typeof window !== 'undefined') {
    localStorage.setItem(TOKEN_KEY, token);
  }
}

export function removeToken(): void {
  if (typeof window !== 'undefined') {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(REFRESH_TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
  }
}

export function getRefreshToken(): string | null {
  if (typeof window === 'undefined') return null;
  return localStorage.getItem(REFRESH_TOKEN_KEY);
}

export function setRefreshToken(token: string): void {
  if (typeof window !== 'undefined') {
    localStorage.setItem(REFRESH_TOKEN_KEY, token);
  }
}

export function getUser(): User | null {
  if (typeof window === 'undefined') return null;
  const userStr = localStorage.getItem(USER_KEY);
  if (userStr) {
    try {
      return JSON.parse(userStr);
    } catch {
      return null;
    }
  }
  return null;
}

export function setUser(user: User): void {
  if (typeof window !== 'undefined') {
    localStorage.setItem(USER_KEY, JSON.stringify(user));
  }
}

export function isAuthenticated(): boolean {
  return !!getToken();
}

export function getUserRole(): string | null {
  const user = getUser();
  return user?.role || null;
}

export function isAdmin(): boolean {
  return getUserRole() === 'admin';
}

export function isDoctor(): boolean {
  const role = getUserRole();
  return role === 'doctor' || role === 'admin';
}

export function saveAuthData(accessToken: string, refreshToken: string, user: User): void {
  setToken(accessToken);
  setRefreshToken(refreshToken);
  setUser(user);
}

export function clearAuthData(): void {
  removeToken();
}

export function logout(): void {
  clearAuthData();
  if (typeof window !== 'undefined') {
    localStorage.removeItem('patient_id');
  }
}

