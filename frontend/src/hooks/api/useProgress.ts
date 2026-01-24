/**
 * 진도 관련 훅
 */
import { useState, useCallback } from 'react';
import { progressAPI } from '../../services/progress';
import type { Progress, ProgressCreate } from '../../types/progress';

export function useProgress() {
  const [progress, setProgress] = useState<Progress | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const saveProgress = useCallback(async (data: ProgressCreate) => {
    setLoading(true);
    setError(null);
    try {
      await progressAPI.save(data);
      // 저장 후 현재 진도 조회
      const current = await progressAPI.getContinue(data.user_id);
      setProgress(current);
    } catch (err: any) {
      setError(err.message || '진도 저장 중 오류가 발생했습니다.');
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const getContinue = useCallback(async (userId: string) => {
    setLoading(true);
    setError(null);
    try {
      const data = await progressAPI.getContinue(userId);
      setProgress(data);
      return data;
    } catch (err: any) {
      setError(err.message || '진도를 불러오는 중 오류가 발생했습니다.');
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  return {
    progress,
    loading,
    error,
    saveProgress,
    getContinue,
  };
}
