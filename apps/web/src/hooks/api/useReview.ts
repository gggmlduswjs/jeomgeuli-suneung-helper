/**
 * 복습 관련 훅
 */
import { useState, useCallback } from 'react';
import { reviewAPI } from '../../services/review';
import type { ReviewQueueItem, ReviewComplete } from '../../types/review';

export function useReview() {
  const [queue, setQueue] = useState<ReviewQueueItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadQueue = useCallback(async (userId: string, bookId?: string) => {
    setLoading(true);
    setError(null);
    try {
      const data = await reviewAPI.getQueue(userId, bookId);
      setQueue(data);
      return data;
    } catch (err: any) {
      setError(err.message || '복습 큐를 불러오는 중 오류가 발생했습니다.');
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const complete = useCallback(async (data: ReviewComplete) => {
    setLoading(true);
    setError(null);
    try {
      await reviewAPI.complete(data);
      // 큐에서 제거
      setQueue(prev => prev.filter(item => item.unit_id !== data.unit_id));
    } catch (err: any) {
      setError(err.message || '복습 완료 처리 중 오류가 발생했습니다.');
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  return {
    queue,
    loading,
    error,
    loadQueue,
    complete,
  };
}
