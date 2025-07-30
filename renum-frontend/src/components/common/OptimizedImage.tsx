import React, { useState } from 'react';
import Image, { ImageProps } from 'next/image';
import { cn } from '../../lib/utils';

interface OptimizedImageProps extends Omit<ImageProps, 'onLoad' | 'onError'> {
  fallbackSrc?: string;
  showPlaceholder?: boolean;
  placeholderClassName?: string;
  containerClassName?: string;
}

const OptimizedImage: React.FC<OptimizedImageProps> = ({
  src,
  alt,
  fallbackSrc = '/images/placeholder.png',
  showPlaceholder = true,
  placeholderClassName,
  containerClassName,
  className,
  ...props
}) => {
  const [isLoading, setIsLoading] = useState(true);
  const [hasError, setHasError] = useState(false);
  const [currentSrc, setCurrentSrc] = useState(src);

  const handleLoad = () => {
    setIsLoading(false);
  };

  const handleError = () => {
    setHasError(true);
    setIsLoading(false);
    if (fallbackSrc && currentSrc !== fallbackSrc) {
      setCurrentSrc(fallbackSrc);
      setHasError(false);
    }
  };

  return (
    <div className={cn('relative overflow-hidden', containerClassName)}>
      {/* Loading placeholder */}
      {isLoading && showPlaceholder && (
        <div
          className={cn(
            'absolute inset-0 bg-gray-200 animate-pulse flex items-center justify-center',
            placeholderClassName
          )}
        >
          <div className="text-gray-400 text-sm">Carregando...</div>
        </div>
      )}

      {/* Error state */}
      {hasError && !fallbackSrc && (
        <div
          className={cn(
            'absolute inset-0 bg-gray-100 flex items-center justify-center',
            className
          )}
        >
          <div className="text-gray-400 text-sm text-center">
            <div>Imagem não disponível</div>
            <div className="text-xs mt-1">{alt}</div>
          </div>
        </div>
      )}

      {/* Actual image */}
      {!hasError && (
        <Image
          src={currentSrc}
          alt={alt}
          className={cn(
            'transition-opacity duration-300',
            isLoading ? 'opacity-0' : 'opacity-100',
            className
          )}
          onLoad={handleLoad}
          onError={handleError}
          // Performance optimizations
          priority={props.priority}
          quality={props.quality || 85}
          placeholder={props.placeholder || 'blur'}
          blurDataURL={
            props.blurDataURL ||
            'data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAYEBQYFBAYGBQYHBwYIChAKCgkJChQODwwQFxQYGBcUFhYaHSUfGhsjHBYWICwgIyYnKSopGR8tMC0oMCUoKSj/2wBDAQcHBwoIChMKChMoGhYaKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCj/wAARCAAIAAoDASIAAhEBAxEB/8QAFQABAQAAAAAAAAAAAAAAAAAAAAv/xAAhEAACAQMDBQAAAAAAAAAAAAABAgMABAUGIWGRkqGx0f/EABUBAQEAAAAAAAAAAAAAAAAAAAMF/8QAGhEAAgIDAAAAAAAAAAAAAAAAAAECEgMRkf/aAAwDAQACEQMRAD8AltJagyeH0AthI5xdrLcNM91BF5pX2HaH9bcfaSXWGaRmknyJckliyjqTzSlT54b6bk+h0R//2Q=='
          }
          {...props}
        />
      )}
    </div>
  );
};

export default OptimizedImage;