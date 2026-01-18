/**
 * 알림 포인트 관련 훅
 */
import { useState, useCallback } from 'react';
import { syncpointsAPI } from '../../services/syncpoints';
import type { Syncpoint, SyncLogCreate } from '../../types/syncpoint';

export function useSyncpoints() {
  const [syncpoints, setSyncpoints] = useState<Syncpoint[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadSyncpoints = useCallback(async (lessonId: string) => {
    setLoading(true);
    setError(null);
    try {
      const data = await syncpointsAPI.list(lessonId);
      setSyncpoints(data);
      return data;
    } catch (err: any) {
      setError(err.message || '알림 포인트를 불러오는 중 오류가 발생했습니다.');
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const logEvent = useCallback(async (data: SyncLogCreate) => {
    try {
      await syncpointsAPI.log(data);
    } catch (err: any) {
      console.error('[useSyncpoints] 로그 전송 실패:', err);
      throw err;
    }
  }, []);

  return {
    syncpoints,
    loading,
    error,
    loadSyncpoints,
    logEvent,
  };
}
