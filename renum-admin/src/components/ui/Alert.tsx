import React from 'react';
import { cn } from '../../lib/utils';
import { AlertCircle, CheckCircle, Info, XCircle, X } from 'lucide-react';

type AlertVariant = 'success' | 'error' | 'warning' | 'info';

interface AlertProps extends React.HTMLAttributes<HTMLDivElement> {
  variant: AlertVariant;
  title?: string;
  children: React.ReactNode;
  onClose?: () => void;
}

const Alert = React.forwardRef<HTMLDivElement, AlertProps>(
  ({ variant, title, children, onClose, className, ...props }, ref) => {
    const variantClasses = {
      success: 'bg-green-50 border-green-200 text-green-800',
      error: 'bg-red-50 border-red-200 text-red-800',
      warning: 'bg-yellow-50 border-yellow-200 text-yellow-800',
      info: 'bg-blue-50 border-blue-200 text-blue-800',
    };

    const iconClasses = {
      success: 'text-green-500',
      error: 'text-red-500',
      warning: 'text-yellow-500',
      info: 'text-blue-500',
    };

    const Icon = {
      success: CheckCircle,
      error: XCircle,
      warning: AlertCircle,
      info: Info,
    }[variant];

    return (
      <div
        ref={ref}
        className={cn(
          'border rounded-md p-4',
          variantClasses[variant],
          className
        )}
        {...props}
      >
        <div className="flex">
          <div className="flex-shrink-0">
            <Icon className={cn('h-5 w-5', iconClasses[variant])} />
          </div>
          <div className="ml-3 flex-1">
            {title && (
              <h3 className="text-sm font-medium">{title}</h3>
            )}
            <div className={cn('text-sm', title && 'mt-2')}>
              {children}
            </div>
          </div>
          {onClose && (
            <div className="ml-auto pl-3">
              <div className="-mx-1.5 -my-1.5">
                <button
                  type="button"
                  className={cn(
                    'inline-flex rounded-md p-1.5 focus:outline-none focus:ring-2 focus:ring-offset-2',
                    {
                      'bg-green-50 text-green-500 hover:bg-green-100 focus:ring-green-600 focus:ring-offset-green-50': variant === 'success',
                      'bg-red-50 text-red-500 hover:bg-red-100 focus:ring-red-600 focus:ring-offset-red-50': variant === 'error',
                      'bg-yellow-50 text-yellow-500 hover:bg-yellow-100 focus:ring-yellow-600 focus:ring-offset-yellow-50': variant === 'warning',
                      'bg-blue-50 text-blue-500 hover:bg-blue-100 focus:ring-blue-600 focus:ring-offset-blue-50': variant === 'info',
                    }
                  )}
                  onClick={onClose}
                >
                  <span className="sr-only">Fechar</span>
                  <X className="h-4 w-4" />
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    );
  }
);

Alert.displayName = 'Alert';

export default Alert;