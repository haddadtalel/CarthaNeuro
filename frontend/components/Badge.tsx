'use client';

interface BadgeProps {
  children: React.ReactNode;
  variant?: 'default' | 'success' | 'warning' | 'danger' | 'info';
  size?: 'sm' | 'md';
  className?: string;
}

export function Badge({
  children,
  variant = 'default',
  size = 'md',
  className = '',
}: BadgeProps) {
  const variants = {
    default: 'bg-gray-100 text-gray-800',
    success: 'bg-green-100 text-green-800',
    warning: 'bg-yellow-100 text-yellow-800',
    danger: 'bg-red-100 text-red-800',
    info: 'bg-blue-100 text-blue-800',
  };

  const sizes = {
    sm: 'px-2 py-0.5 text-xs',
    md: 'px-2.5 py-1 text-sm',
  };

  return (
    <span className={`inline-flex items-center font-medium rounded-full ${variants[variant]} ${sizes[size]} ${className}`}>
      {children}
    </span>
  );
}

interface StatusBadgeProps {
  status: string;
  className?: string;
}

export function StatusBadge({ status, className = '' }: StatusBadgeProps) {
  const statusConfig: Record<string, { variant: BadgeProps['variant']; label: string }> = {
    active: { variant: 'success', label: 'Active' },
    inactive: { variant: 'default', label: 'Inactive' },
    pending: { variant: 'warning', label: 'Pending' },
    completed: { variant: 'success', label: 'Completed' },
    failed: { variant: 'danger', label: 'Failed' },
    processing: { variant: 'info', label: 'Processing' },
    training: { variant: 'info', label: 'Training' },
    production: { variant: 'success', label: 'Production' },
    draft: { variant: 'default', label: 'Draft' },
  };

  const config = statusConfig[status.toLowerCase()] || { variant: 'default', label: status };

  return (
    <Badge variant={config.variant} className={className}>
      {config.label}
    </Badge>
  );
}

interface RoleBadgeProps {
  role: string;
  className?: string;
}

export function RoleBadge({ role, className = '' }: RoleBadgeProps) {
  const roleConfig: Record<string, { variant: BadgeProps['variant']; label: string }> = {
    admin: { variant: 'danger', label: 'Admin' },
    doctor: { variant: 'info', label: 'Doctor' },
    user: { variant: 'default', label: 'User' },
  };

  const config = roleConfig[role.toLowerCase()] || { variant: 'default', label: role };

  return (
    <Badge variant={config.variant} className={className}>
      {config.label}
    </Badge>
  );
}

interface ConfidenceBadgeProps {
  confidence: string;
  className?: string;
}

export function ConfidenceBadge({ confidence, className = '' }: ConfidenceBadgeProps) {
  const config: Record<string, { variant: BadgeProps['variant']; label: string }> = {
    'Very High': { variant: 'success', label: 'Very High' },
    'High': { variant: 'success', label: 'High' },
    'Moderate': { variant: 'warning', label: 'Moderate' },
    'Low': { variant: 'warning', label: 'Low' },
    'Very Low': { variant: 'danger', label: 'Very Low' },
  };

  const badgeConfig = config[confidence] || { variant: 'default', label: confidence };

  return (
    <Badge variant={badgeConfig.variant} className={className}>
      {badgeConfig.label}
    </Badge>
  );
}

