'use client';

interface SelectProps {
  label?: string;
  error?: string;
  options: { value: string; label: string }[];
  value?: string;
  onChange?: (value: string) => void;
  placeholder?: string;
  className?: string;
  disabled?: boolean;
  required?: boolean;
}

export function Select({
  label,
  error,
  options,
  value,
  onChange,
  placeholder = 'Select an option',
  className = '',
  disabled = false,
  required = false,
}: SelectProps) {
  return (
    <div className="w-full">
      {label && (
        <label className="block text-sm font-medium text-gray-700 mb-1">
          {label}
          {required && <span className="text-red-500 ml-1">*</span>}
        </label>
      )}
      <select
        value={value}
        onChange={(e) => onChange?.(e.target.value)}
        disabled={disabled}
        className={`
          block w-full rounded-lg border px-4 py-2.5 transition-colors duration-200 appearance-none
          bg-white
          ${error 
            ? 'border-red-300 focus:border-red-500 focus:ring-red-200' 
            : 'border-gray-300 focus:border-medical focus:ring-medical/20'
          }
          focus:outline-none focus:ring-2
          disabled:bg-gray-50 disabled:text-gray-500 disabled:cursor-not-allowed
          bg-[url('data:image/svg+xml;charset=utf-8,%3Csvg%20xmlns%3D%22http%3A%2F%2Fwww.w3.org%2F2000%2Fsvg%22%20fill%3D%22none%22%20viewBox%3D%220%200%2020%2020%22%3E%3Cpath%20stroke%3D%22%236b7280%22%20stroke-linecap%3D%22round%22%20stroke-linejoin%3D%22round%22%20stroke-width%3D%221.5%22%20d%3D%22m6%208%204%204%204-4%22%2F%3E%3C%2Fsvg%3E')]
          bg-[length:1.5rem_1.5rem] bg-[right_0.5rem_center] bg-no-repeat pr-10
          ${className}
        `}
      >
        <option value="" disabled>{placeholder}</option>
        {options.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
      {error && <p className="mt-1 text-sm text-red-600">{error}</p>}
    </div>
  );
}

interface CheckboxProps {
  label: string;
  checked?: boolean;
  onChange?: (checked: boolean) => void;
  disabled?: boolean;
  className?: string;
}

export function Checkbox({
  label,
  checked = false,
  onChange,
  disabled = false,
  className = '',
}: CheckboxProps) {
  return (
    <label className={`flex items-center gap-2 cursor-pointer ${disabled ? 'opacity-50 cursor-not-allowed' : ''} ${className}`}>
      <input
        type="checkbox"
        checked={checked}
        onChange={(e) => onChange?.(e.target.checked)}
        disabled={disabled}
        className="w-4 h-4 text-medical border-gray-300 rounded focus:ring-medical"
      />
      <span className="text-gray-700">{label}</span>
    </label>
  );
}

interface RadioGroupProps {
  label: string;
  name: string;
  options: { value: string; label: string }[];
  value?: string;
  onChange?: (value: string) => void;
  disabled?: boolean;
  className?: string;
}

export function RadioGroup({
  label,
  name,
  options,
  value,
  onChange,
  disabled = false,
  className = '',
}: RadioGroupProps) {
  return (
    <fieldset className={className}>
      <legend className="text-sm font-medium text-gray-700 mb-2">{label}</legend>
      <div className="space-y-2">
        {options.map((option) => (
          <label key={option.value} className="flex items-center gap-2 cursor-pointer">
            <input
              type="radio"
              name={name}
              value={option.value}
              checked={value === option.value}
              onChange={(e) => onChange?.(e.target.value)}
              disabled={disabled}
              className="w-4 h-4 text-medical border-gray-300 focus:ring-medical"
            />
            <span className="text-gray-700">{option.label}</span>
          </label>
        ))}
      </div>
    </fieldset>
  );
}

