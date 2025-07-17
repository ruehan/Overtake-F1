import { useState, useEffect, useCallback, useRef } from 'react';

interface CacheItem<T> {
  data: T;
  timestamp: number;
  loading: boolean;
}

interface CacheOptions {
  staleTime?: number; // 데이터를 신선하다고 간주하는 시간 (ms)
  cacheTime?: number; // 캐시에 데이터를 보관하는 시간 (ms)
  refetchOnWindowFocus?: boolean;
}

const defaultOptions: CacheOptions = {
  staleTime: 5 * 60 * 1000, // 5분
  cacheTime: 10 * 60 * 1000, // 10분
  refetchOnWindowFocus: false,
};

// 전역 캐시 저장소
const cache = new Map<string, CacheItem<any>>();

// 캐시 정리 함수
const cleanupStaleCache = () => {
  const now = Date.now();
  cache.forEach((item, key) => {
    if (now - item.timestamp > (defaultOptions.cacheTime || 0)) {
      cache.delete(key);
    }
  });
};

// 주기적으로 캐시 정리 (1분마다)
setInterval(cleanupStaleCache, 60 * 1000);

export function useApiCache<T>(
  key: string,
  fetcher: () => Promise<T>,
  options: CacheOptions = {}
) {
  const opts = { ...defaultOptions, ...options };
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const abortControllerRef = useRef<AbortController | null>(null);

  // 캐시에서 데이터 확인
  const getCachedData = useCallback(() => {
    const cached = cache.get(key);
    if (!cached) return null;

    const isStale = Date.now() - cached.timestamp > (opts.staleTime || 0);
    return { ...cached, isStale };
  }, [key, opts.staleTime]);

  // 데이터 페치 함수
  const fetchData = useCallback(async (forceRefresh = false) => {
    const cached = getCachedData();
    
    // 캐시된 데이터가 있고 신선하며 강제 새로고침이 아닌 경우
    if (cached && !cached.isStale && !forceRefresh) {
      setData(cached.data);
      setLoading(false);
      setError(null);
      return cached.data;
    }

    // 이미 로딩 중인 경우 중복 요청 방지
    if (cached?.loading && !forceRefresh) {
      return cached.data;
    }

    // 이전 요청 취소
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }

    abortControllerRef.current = new AbortController();
    
    try {
      setLoading(true);
      setError(null);

      // 캐시에 로딩 상태 저장
      if (cached) {
        cache.set(key, { ...cached, loading: true });
      }

      const result = await fetcher();
      
      // 캐시에 새 데이터 저장
      cache.set(key, {
        data: result,
        timestamp: Date.now(),
        loading: false,
      });

      setData(result);
      setLoading(false);
      return result;
    } catch (err) {
      if (err instanceof Error && err.name === 'AbortError') {
        return cached?.data || null;
      }

      const errorMessage = err instanceof Error ? err.message : 'Unknown error';
      setError(errorMessage);
      setLoading(false);

      // 에러 발생 시 캐시된 데이터라도 표시
      if (cached?.data) {
        setData(cached.data);
        return cached.data;
      }
      
      throw err;
    }
  }, [key, fetcher, getCachedData, opts.staleTime]);

  // 수동 새로고침 함수
  const refetch = useCallback(() => {
    return fetchData(true);
  }, [fetchData]);

  // 캐시 무효화 함수
  const invalidate = useCallback(() => {
    cache.delete(key);
    setData(null);
    setError(null);
  }, [key]);

  // 초기 로드 및 윈도우 포커스시 재페치
  useEffect(() => {
    const cached = getCachedData();
    if (cached && !cached.isStale) {
      setData(cached.data);
      setLoading(false);
    } else {
      fetchData();
    }

    const handleFocus = () => {
      if (opts.refetchOnWindowFocus) {
        const cached = getCachedData();
        if (cached?.isStale) {
          fetchData();
        }
      }
    };

    if (opts.refetchOnWindowFocus) {
      window.addEventListener('focus', handleFocus);
      return () => window.removeEventListener('focus', handleFocus);
    }
  }, [fetchData, getCachedData, opts.refetchOnWindowFocus]);

  // 컴포넌트 언마운트시 요청 취소
  useEffect(() => {
    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    };
  }, []);

  return {
    data,
    loading,
    error,
    refetch,
    invalidate,
    isStale: getCachedData()?.isStale || false,
  };
}

// 캐시 전체 초기화 함수 (필요시 사용)
export const clearAllCache = () => {
  cache.clear();
};

// 특정 패턴의 캐시 무효화 (예: 'standings-*')
export const invalidatePattern = (pattern: string) => {
  const regex = new RegExp(pattern.replace('*', '.*'));
  const keysToDelete: string[] = [];
  cache.forEach((_, key) => {
    if (regex.test(key)) {
      keysToDelete.push(key);
    }
  });
  keysToDelete.forEach(key => cache.delete(key));
}; 