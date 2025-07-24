/**
 * Componente de toast para notificações em tempo real
 */

import React, { useState, useEffect } from 'react';
import { useWebSocketNotifications } from '../../hooks/useWebSocketNotifications';
import { WebSocketNotification } from '../../types/websocket';

interface NotificationToastProps {
  maxToasts?: number;
  autoHideDelay?: number;
  position?: 'top-right' | 'top-left' | 'bottom-right' | 'bottom-left';
  className?: string;
}

interface ToastNotification extends WebSocketNotification {
  toastId: string;
  showTime: number;
}

/**
 * Componente de toast para notificações em tempo real
 */
const NotificationToast: React.FC<NotificationToastProps> = ({
  maxToasts = 3,
  autoHideDelay = 5000,
  position = 'top-right',
  className = '',
}) => {
  const { notifications, markAsRead, removeNotification } = useWebSocketNotifications();
  const [toasts, setToasts] = useState<ToastNotification[]>([]);

  // Monitora novas notificações e cria toasts
  useEffect(() => {
    const latestNotification = notifications[0];
    
    if (latestNotification && !latestNotification.read) {
      const existingToast = toasts.find(t => t.id === latestNotification.id);
      
      if (!existingToast) {
        const newToast: ToastNotification = {
          ...latestNotification,
          toastId: `toast-${latestNotification.id}-${Date.now()}`,
          showTime: Date.now(),
        };
        
        setToasts(prev => {
          const updated = [newToast, ...prev].slice(0, maxToasts);
          return updated;
        });
      }
    }
  }, [notifications, toasts, maxToasts]);

  // Auto-hide toasts
  useEffect(() => {
    const timers: NodeJS.Timeout[] = [];
    
    toasts.forEach((toast) => {
      const timeElapsed = Date.now() - toast.showTime;
      const remainingTime = autoHideDelay - timeElapsed;
      
      if (remainingTime > 0) {
        const timer = setTimeout(() => {
          setToasts(prev => prev.filter(t => t.toastId !== toast.toastId));
        }, remainingTime);
        
        timers.push(timer);
      }
    });
    
    return () => {
      timers.forEach(timer => clearTimeout(timer));
    };
  }, [toasts, autoHideDelay]);

  // Remove um toast
  const removeToast = (toastId: string) => {
    setToasts(prev => prev.filter(t => t.toastId !== toastId));
  };

  // Manipula o clique em um toast
  const handleToastClick = (toast: ToastNotification) => {
    // Marca como lida
    if (!toast.read) {
      markAsRead(toast.id);
    }
    
    // Executa ação se houver
    if (toast.action?.type === 'url' && toast.action?.payload) {
      window.open(toast.action.payload, '_blank');
    }
    
    // Remove o toast
    removeToast(toast.toastId);
  };

  // Manipula o clique no botão de fechar
  const handleClose = (e: React.MouseEvent, toastId: string) => {
    e.stopPropagation();
    removeToast(toastId);
  };

  // Define as classes de posição
  const getPositionClasses = () => {
    switch (position) {
      case 'top-left':
        return 'top-4 left-4';
      case 'bottom-right':
        return 'bottom-4 right-4';
      case 'bottom-left':
        return 'bottom-4 left-4';
      case 'top-right':
      default:
        return 'top-4 right-4';
    }
  };

  // Define a cor com base no tipo de notificação
  const getTypeColor = (type: string) => {
    switch (type) {
      case 'success':
        return 'bg-green-500 border-green-600';
      case 'warning':
        return 'bg-yellow-500 border-yellow-600';
      case 'error':
        return 'bg-red-500 border-red-600';
      case 'info':
      default:
        return 'bg-blue-500 border-blue-600';
    }
  };

  // Define o ícone com base no tipo de notificação
  const getTypeIcon = (type: string) => {
    const iconClass = 'h-5 w-5 text-white';
    
    switch (type) {
      case 'success':
        return (
          <svg className={iconClass} xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
          </svg>
        );
      case 'warning':
        return (
          <svg className={iconClass} xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
            <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
          </svg>
        );
      case 'error':
        return (
          <svg className={iconClass} xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
          </svg>
        );
      case 'info':
      default:
        return (
          <svg className={iconClass} xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
            <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
          </svg>
        );
    }
  };

  if (toasts.length === 0) {
    return null;
  }

  return (
    <div className={`fixed ${getPositionClasses()} z-50 space-y-2 ${className}`}>
      {toasts.map((toast, index) => (
        <div
          key={toast.toastId}
          className={`
            ${getTypeColor(toast.type)} 
            text-white rounded-lg shadow-lg border-l-4 p-4 max-w-sm cursor-pointer
            transform transition-all duration-300 ease-in-out
            ${index === 0 ? 'translate-x-0 opacity-100' : 'translate-x-2 opacity-90'}
            hover:scale-105 hover:shadow-xl
          `}
          onClick={() => handleToastClick(toast)}
          style={{
            animationDelay: `${index * 100}ms`,
          }}
        >
          <div className="flex items-start">
            {/* Ícone */}
            <div className="flex-shrink-0 mr-3">
              {getTypeIcon(toast.type)}
            </div>

            {/* Conteúdo */}
            <div className="flex-1 min-w-0">
              <h4 className="font-medium text-white text-sm mb-1">
                {toast.title}
              </h4>
              <p className="text-white text-xs opacity-90 line-clamp-2">
                {toast.message}
              </p>
              
              {toast.action && (
                <div className="mt-2">
                  <span className="text-xs text-white opacity-75 underline">
                    Clique para ver detalhes
                  </span>
                </div>
              )}
            </div>

            {/* Botão de fechar */}
            <button
              onClick={(e) => handleClose(e, toast.toastId)}
              className="flex-shrink-0 ml-2 text-white opacity-70 hover:opacity-100 transition-opacity"
            >
              <svg className="h-4 w-4" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
              </svg>
            </button>
          </div>

          {/* Barra de progresso */}
          <div className="mt-2 h-1 bg-white bg-opacity-20 rounded-full overflow-hidden">
            <div
              className="h-full bg-white bg-opacity-40 rounded-full transition-all duration-100 ease-linear"
              style={{
                width: `${Math.max(0, 100 - ((Date.now() - toast.showTime) / autoHideDelay) * 100)}%`,
              }}
            />
          </div>
        </div>
      ))}
    </div>
  );
};

export default NotificationToast;