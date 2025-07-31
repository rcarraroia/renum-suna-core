import React, { ReactNode } from 'react';
import { useLazyLoad } from '../../hooks/useIntersectionObserver';

interface LazySectionProps {
  children: ReactNode;
  fallback?: ReactNode;
  className?: string;
  rootMargin?: string;
  threshold?: number;
  minHeight?: string | number;
}

const LazySection: React.FC<LazySectionProps> = ({
  children,
  fallback,
  className = '',
  rootMargin = '100px',
  threshold = 0.1,
  minHeight = 'auto',
}) => {
  const { ref, shouldLoad } = useLazyLoad({
    rootMargin,
    threshold,
  });

  return (
    <div
      ref={ref as React.RefObject<HTMLDivElement>}
      className={className}
      style={{ minHeight }}
    >
      {shouldLoad ? children : fallback}
    </div>
  );
};

export default LazySection;