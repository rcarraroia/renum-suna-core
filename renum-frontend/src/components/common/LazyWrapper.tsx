import React, { Suspense, ComponentType } from 'react';
import { Loader2 } from 'lucide-react';

interface LazyWrapperProps {
  fallback?: React.ReactNode;
  children: React.ReactNode;
}

// Loading spinner component
const DefaultFallback = () => (
  <div className="flex items-center justify-center p-8">
    <Loader2 className="h-8 w-8 animate-spin text-blue-500" />
    <span className="ml-2 text-gray-600">Carregando...</span>
  </div>
);

// Lazy wrapper component
export const LazyWrapper: React.FC<LazyWrapperProps> = ({ 
  fallback = <DefaultFallback />, 
  children 
}) => {
  return (
    <Suspense fallback={fallback}>
      {children}
    </Suspense>
  );
};

// HOC for lazy loading components
export function withLazyLoading<P extends object>(
  Component: ComponentType<P>,
  fallback?: React.ReactNode
) {
  const LazyComponent = React.lazy(() => Promise.resolve({ default: Component }));
  
  const WrappedComponent = (props: P) => (
    <LazyWrapper fallback={fallback}>
      <LazyComponent {...(props as any)} />
    </LazyWrapper>
  );
  
  WrappedComponent.displayName = `withLazyLoading(${Component.displayName || Component.name || 'Component'})`;
  
  return WrappedComponent;
}

// Utility for creating lazy components with custom loading
export function createLazyComponent<P extends Record<string, any>>(
  importFn: () => Promise<{ default: ComponentType<P> }>,
  fallback?: React.ReactNode
) {
  const LazyComponent = React.lazy(importFn);
  
  const LazyComponentWrapper = (props: P) => (
    <LazyWrapper fallback={fallback}>
      <LazyComponent {...(props as any)} />
    </LazyWrapper>
  );
  
  LazyComponentWrapper.displayName = 'LazyComponent';
  
  return LazyComponentWrapper;
}

export default LazyWrapper;