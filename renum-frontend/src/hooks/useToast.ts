import { useState } from 'react';

export interface Toast {
  id: string;
  message: string;
  type: 'success' | 'error' | 'info';
  duration?: number;
}

export const useToast = () => {
  const [toasts, setToasts] = useState<Toast[]>([]);

  const addToast = (message: string, type: 'success' | 'error' | 'info' = 'info', duration = 5000) => {
    const id = Math.random().toString(36).substring(2, 9);
    const toast = { id, message, type, duration };
    
    setToasts((prevToasts) => [...prevToasts, toast]);
    
    return id;
  };

  const removeToast = (id: string) => {
    setToasts((prevToasts) => prevToasts.filter((toast) => toast.id !== id));
  };

  const success = (message: string, duration?: number) => {
    return addToast(message, 'success', duration);
  };

  const error = (message: string, duration?: number) => {
    return addToast(message, 'error', duration);
  };

  const info = (message: string, duration?: number) => {
    return addToast(message, 'info', duration);
  };

  return {
    toasts,
    addToast,
    removeToast,
    success,
    error,
    info
  };
};

export default useToast;