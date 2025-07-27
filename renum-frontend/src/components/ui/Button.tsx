import React, { ButtonHTMLAttributes, forwardRef } from 'react';
import { Loader2 } from 'lucide-react';

export interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'outline' | 'danger' | 'destructive';
  size?: 'sm' | 'md' | 'lg' | 'icon';
  fullWidth?: boolean;
  isLoading?: boolean;
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
  children?: React.ReactNode;
}

const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      variant = 'primary',
      size = 'md',
      fullWidth = false,
      isLoading = false,
      leftIcon,
      rightIcon,
      children,
      className = '',
      disabled,
      ...props
    },
    ref
  ) => {
    // Base classes
    const baseClasses = 'inline-flex items-center justify-center font-medium rounded-md focus:outline-none transition-colors';

    // Size classes
    const sizeClasses = {
      sm: 'px-3 py-1.5 text-xs',
      md: 'px-4 py-2 text-sm',
      lg: 'px-6 py-3 text-base',
      icon: 'p-0 h-9 w-9'
    };

    // Variant classes
    const variantClasses = {
      primary: 'bg-indigo-600 text-white hover:bg-indigo-700 focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500',
      secondary: 'bg-gray-100 text-gray-800 hover:bg-gray-200 focus:ring-2 focus:ring-offset-2 focus:ring-gray-500',
      outline: 'bg-white text-gray-700 border border-gray-300 hover:bg-gray-50 focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500',
      danger: 'bg-red-600 text-white hover:bg-red-700 focus:ring-2 focus:ring-offset-2 focus:ring-red-500',
      destructive: 'bg-red-600 text-white hover:bg-red-700 focus:ring-2 focus:ring-offset-2 focus:ring-red-500'
    };

    // Width classes
    const widthClasses = fullWidth ? 'w-full' : '';

    // Disabled classes
    const disabledClasses = disabled || isLoading ? 'opacity-60 cursor-not-allowed' : '';

    // Combine all classes
    const buttonClasses = `${baseClasses} ${sizeClasses[size]} ${variantClasses[variant]} ${widthClasses} ${disabledClasses} ${className}`;

    return (
      <button
        ref={ref}
        className={buttonClasses}
        disabled={disabled || isLoading}
        {...props}
      >
        {isLoading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
        {!isLoading && leftIcon && <span className="mr-2">{leftIcon}</span>}
        {children}
        {!isLoading && rightIcon && <span className="ml-2">{rightIcon}</span>}
      </button>
    );
  }
);

Button.displayName = 'Button';

export default Button;