import { useState, useEffect, useCallback, useRef } from 'react';

interface UseLazyDataOptions<T> {
  fetchFn: () => Promise<T>;
  dependencies?: any[];
  enabled?: boolean;
  delay?: number;
  retryCount?: number;
  retryDelay?: number;
}

interface UseLazyDataReturn<T> {
  data: T | null;
  isLoading: boolean;
  error: Error | null;
  refetch: () => Promise<void>;
  reset: () => void;
}

export function useLazyData<T>({
  fetchFn,
  dependencies = [],
  enabled = true,
  delay = 0,
  retryCount = 0,
  retryDelay = 1000,
}: UseLazyDataOptions<T>): UseLazyDataReturn<T> {
  const [data, setData] = useState<T | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  const [retryAttempts, setRetryAttempts] = useState(0);
  
  const timeoutRef = useRef<NodeJS.Timeout>();
  const abortControllerRef = useRef<AbortController>();

  const fetchData = useCallback(async () => {
    if (!enabled) return;

    // Cancel previous request
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }

    abortControllerRef.current = new AbortController();
    setIsLoading(true);
    setError(null);

    try {
      const result = await fetchFn();
      
      // Check if request was aborted
      if (abortControllerRef.current.signal.aborted) {
        return;
      }

      setData(result);
      setRetryAttempts(0);
    } catch (err) {
      // Check if request was aborted
      if (abortControllerRef.current.signal.aborted) {
        return;
      }

      const error = err instanceof Error ? err : new Error('Unknown error');
      setError(error);

      // Retry logic
      if (retryAttempts < retryCount) {
        setRetryAttempts(prev => prev + 1);
        setTimeout(() => {
          fetchData();
        }, retryDelay);
      }
    } finally {
      setIsLoading(false);
    }
  }, [fetchFn, enabled, retryAttempts, retryCount, retryDelay]);

  const refetch = useCallback(async () => {
    setRetryAttempts(0);
    await fetchData();
  }, [fetchData]);

  const reset = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
    }
    setData(null);
    setIsLoading(false);
    setError(null);
    setRetryAttempts(0);
  }, []);

  useEffect(() => {
    if (!enabled) return;

    if (delay > 0) {
      timeoutRef.current = setTimeout(fetchData, delay);
    } else {
      fetchData();
    }

    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    };
  }, [fetchData, delay, enabled, ...dependencies]);

  useEffect(() => {
    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
    };
  }, []);

  return {
    data,
    isLoading,
    error,
    refetch,
    reset,
  };
}

export default useLazyData;