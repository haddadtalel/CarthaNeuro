/**
 * Authentication Guard Components
 * Provides client-side route protection and role-based access control
 */
'use client';

import { ReactNode } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import { useAuth } from '@/contexts/auth-context';

interface AuthGuardProps {
  children: ReactNode;
  redirectTo?: string;
  requireAuth?: boolean;
}

interface RoleGuardProps {
  children: ReactNode;
  allowedRoles?: string[];
  fallbackComponent?: ReactNode;
  redirectTo?: string;
}

/**
 * Main authentication guard component
 */
export function AuthGuard({ 
  children, 
  redirectTo = '/login', 
  requireAuth = true 
}: AuthGuardProps) {
  const { isAuthenticated, isLoading } = useAuth();
  const router = useRouter();
  const pathname = usePathname();

  // Show loading spinner while checking authentication
  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-primary" />
      </div>
    );
  }

  // Redirect to login if authentication is required but user is not authenticated
  if (requireAuth && !isAuthenticated) {
    if (pathname !== redirectTo) {
      router.push(redirectTo);
    }
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <p className="text-lg text-slate-600 dark:text-slate-400 mb-4">
            Authentication required
          </p>
          <p className="text-sm text-slate-500 dark:text-slate-500">
            Redirecting to login...
          </p>
        </div>
      </div>
    );
  }

  // If auth is not required and user is authenticated, don't show content
  if (!requireAuth && isAuthenticated) {
    return null;
  }

  // User is authenticated and content should be shown
  return <>{children}</>;
}

/**
 * Role-based access control guard
 */
export function RoleGuard({ 
  children, 
  allowedRoles = [], 
  fallbackComponent,
  redirectTo = '/unauthorized'
}: RoleGuardProps) {
  const { user, isAuthenticated } = useAuth();

  // If user is not authenticated, don't render anything
  if (!isAuthenticated || !user) {
    return null;
  }

  // Check if user has required role
  const hasRequiredRole = allowedRoles.includes(user.role);

  // If user doesn't have required role
  if (!hasRequiredRole) {
    // If custom fallback is provided, render it
    if (fallbackComponent) {
      return <>{fallbackComponent}</>;
    }

    // Default fallback: redirect to unauthorized page
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-slate-900 dark:text-slate-100 mb-4">
            Access Denied
          </h1>
          <p className="text-slate-600 dark:text-slate-400 mb-4">
            You don&apos;t have permission to access this page.
          </p>
          <p className="text-sm text-slate-500 dark:text-slate-500">
            Required roles: {allowedRoles.join(', ')}<br />
            Your role: {user.role}
          </p>
        </div>
      </div>
    );
  }

  // User has required role, render children
  return <>{children}</>;
}

/**
 * Admin-only guard component
 */
export function AdminGuard({ children }: { children: ReactNode }) {
  return (
    <RoleGuard 
      allowedRoles={['admin', 'system_admin']}
      redirectTo="/unauthorized"
    >
      {children}
    </RoleGuard>
  );
}

/**
 * Doctor/Admin guard component
 */
export function DoctorGuard({ children }: { children: ReactNode }) {
  return (
    <RoleGuard 
      allowedRoles={['admin', 'system_admin', 'doctor']}
      redirectTo="/unauthorized"
    >
      {children}
    </RoleGuard>
  );
}

/**
 * Guest-only guard (for login/register pages)
 */
export function GuestGuard({ children }: { children: ReactNode }) {
  const { isAuthenticated, isLoading } = useAuth();

  // Show loading spinner while checking authentication
  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-primary" />
      </div>
    );
  }

  // If user is authenticated, don't render anything (will redirect via middleware)
  if (isAuthenticated) {
    return null;
  }

  // User is not authenticated, show content
  return <>{children}</>;
}

/**
 * Conditional rendering based on authentication status
 */
interface AuthConditionalProps {
  children: ReactNode;
  authenticatedComponent: ReactNode;
  unauthenticatedComponent?: ReactNode;
  loadingComponent?: ReactNode;
}

export function AuthConditional({
  children,
  authenticatedComponent,
  unauthenticatedComponent,
  loadingComponent
}: AuthConditionalProps) {
  const { isAuthenticated, isLoading } = useAuth();

  if (isLoading) {
    return loadingComponent || (
      <div className="flex items-center justify-center p-4">
        <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-primary" />
      </div>
    );
  }

  if (isAuthenticated) {
    return <>{authenticatedComponent}</>;
  }

  return unauthenticatedComponent || <>{children}</>;
}

/**
 * User info display component
 */
export function UserInfo() {
  const { user } = useAuth();

  if (!user) return null;

  return (
    <div className="flex items-center space-x-2">
      <div className="w-8 h-8 bg-primary/10 rounded-full flex items-center justify-center">
        <span className="text-sm font-medium text-primary">
          {user.first_name?.[0]?.toUpperCase() || user.username[0].toUpperCase()}
        </span>
      </div>
      <div className="text-sm">
        <p className="font-medium text-slate-900 dark:text-slate-100">
          {user.first_name && user.last_name 
            ? `${user.first_name} ${user.last_name}` 
            : user.username
          }
        </p>
        <p className="text-slate-500 dark:text-slate-400">
          {user.role}
        </p>
      </div>
    </div>
  );
}