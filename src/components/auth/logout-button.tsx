/**
 * Logout Button Component
 * Provides a consistent logout interface across the application
 */
'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { LogOut, Loader2 } from 'lucide-react';
import { useAuth } from '@/contexts/auth-context';

interface LogoutButtonProps {
  variant?: 'default' | 'outline' | 'ghost' | 'destructive';
  size?: 'default' | 'sm' | 'lg' | 'icon';
  className?: string;
  showText?: boolean;
  redirectTo?: string;
}

export function LogoutButton({ 
  variant = 'outline', 
  size = 'default',
  className = '',
  showText = true,
  redirectTo
}: LogoutButtonProps) {
  const { logout, isLoading } = useAuth();
  const [isLoggingOut, setIsLoggingOut] = useState(false);

  const handleLogout = async () => {
    if (isLoading || isLoggingOut) return;

    try {
      setIsLoggingOut(true);
      // Add any cleanup logic here before logout
      await logout();
    } catch (error) {
      console.error('Logout failed:', error);
      // Force logout even if there's an error
      logout();
    } finally {
      setIsLoggingOut(false);
    }
  };

  const isDisabled = isLoading || isLoggingOut;

  return (
    <Button
      variant={variant}
      size={size}
      onClick={handleLogout}
      disabled={isDisabled}
      className={className}
    >
      {isLoggingOut ? (
        <Loader2 className="h-4 w-4 animate-spin" />
      ) : (
        <LogOut className="h-4 w-4" />
      )}
      {showText && (
        <span className="ml-2">
          {isLoggingOut ? 'Logging out...' : 'Logout'}
        </span>
      )}
    </Button>
  );
}

/**
 * Simple logout button for navigation bars
 */
export function SimpleLogoutButton() {
  const { logout, user } = useAuth();

  const handleLogout = () => {
    logout();
  };

  return (
    <button
      onClick={handleLogout}
      className="flex items-center space-x-2 text-slate-600 hover:text-slate-900 dark:text-slate-400 dark:hover:text-slate-100 transition-colors"
    >
      <LogOut className="h-4 w-4" />
      <span className="text-sm">Logout</span>
    </button>
  );
}

/**
 * Logout menu item for dropdown menus
 */
export function LogoutMenuItem() {
  const { logout } = useAuth();

  const handleLogout = () => {
    logout();
  };

  return (
    <button
      onClick={handleLogout}
      className="w-full text-left px-4 py-2 text-sm text-slate-700 hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-slate-800 flex items-center space-x-2"
    >
      <LogOut className="h-4 w-4" />
      <span>Logout</span>
    </button>
  );
}

/**
 * Full logout modal component
 */
interface LogoutModalProps {
  isOpen: boolean;
  onClose: () => void;
  onLogout: () => void;
}

export function LogoutModal({ isOpen, onClose, onLogout }: LogoutModalProps) {
  if (!isOpen) return null;

  const handleLogout = () => {
    onLogout();
    onClose();
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white dark:bg-slate-800 rounded-lg p-6 max-w-sm w-full mx-4">
        <h3 className="text-lg font-semibold text-slate-900 dark:text-slate-100 mb-4">
          Confirm Logout
        </h3>
        <p className="text-slate-600 dark:text-slate-400 mb-6">
          Are you sure you want to logout? You&apos;ll need to login again to access your account.
        </p>
        <div className="flex space-x-3">
          <button
            onClick={onClose}
            className="flex-1 px-4 py-2 text-slate-700 bg-slate-100 hover:bg-slate-200 dark:text-slate-300 dark:bg-slate-700 dark:hover:bg-slate-600 rounded-lg transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={handleLogout}
            className="flex-1 px-4 py-2 text-white bg-red-600 hover:bg-red-700 rounded-lg transition-colors"
          >
            Logout
          </button>
        </div>
      </div>
    </div>
  );
}