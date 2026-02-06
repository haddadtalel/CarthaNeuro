'use client';

export function Checkbox({ label, checked, onChange, disabled, className }: any) {
  return (
    <label className={`flex items-center gap-2 cursor-pointer ${disabled ? 'opacity-50 cursor-not-allowed' : ''} ${className}`}>
      <input
        type="checkbox"
        checked={checked}
        onChange={(e: any) => onChange?.(e.target.checked)}
        disabled={disabled}
        className="w-4 h-4 text-medical border-gray-300 rounded focus:ring-medical"
      />
      <span className="text-gray-700">{label}</span>
    </label>
  );
}

