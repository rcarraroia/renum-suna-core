import React, { lazy, Suspense } from 'react';

// Loading fallback component
const LoadingFallback = ({ height = 'h-64', message = 'Carregando...' }: { height?: string; message?: string }) => (
  <div className={`animate-pulse bg-gray-200 ${height} rounded-lg flex items-center justify-center`}>
    <div className="text-gray-500 text-sm">{message}</div>
  </div>
);

// Utility function to create lazy components with proper error handling
const createLazyComponent = (importFn: () => Promise<any>, fallback: React.ReactNode, displayName?: string) => {
  const LazyComponent = lazy(importFn);
  
  const WrappedComponent = (props: any) => (
    <Suspense fallback={fallback}>
      <LazyComponent {...props} />
    </Suspense>
  );
  
  WrappedComponent.displayName = displayName || 'LazyComponent';
  
  return WrappedComponent;
};

// Lazy load admin components (não críticos para usuários normais)
export const LazyWebSocketStatsChart = createLazyComponent(
  () => import('../admin/WebSocketStatsChart').then(module => ({ default: module.WebSocketStatsChart })),
  <LoadingFallback height="h-64" message="Carregando estatísticas..." />,
  'LazyWebSocketStatsChart'
);

export const LazyWebSocketBroadcastPanel = createLazyComponent(
  () => import('../admin/WebSocketBroadcastPanel').then(module => ({ default: module.WebSocketBroadcastPanel })),
  <LoadingFallback height="h-32" message="Carregando painel..." />,
  'LazyWebSocketBroadcastPanel'
);

// Lazy load chat interface (componente pesado) - usa default export
export const LazyChatInterface = createLazyComponent(
  () => import('../ChatInterface'),
  <div className="animate-pulse bg-gray-200 h-96 rounded-lg flex items-center justify-center">
    <div className="text-gray-500">Carregando chat...</div>
  </div>,
  'LazyChatInterface'
);

// Lazy load notifications center - usa default export
export const LazyNotificationsCenter = createLazyComponent(
  () => import('../notifications/NotificationsCenter'),
  <LoadingFallback height="h-48" message="Carregando notificações..." />,
  'LazyNotificationsCenter'
);

// Lazy load team execution monitor - usa default export
export const LazyTeamExecutionMonitor = createLazyComponent(
  () => import('../teams/TeamExecutionMonitor'),
  <LoadingFallback height="h-64" message="Carregando monitor..." />,
  'LazyTeamExecutionMonitor'
);