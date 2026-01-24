/**
 * 교재 파싱 상태 모니터링 커스텀 hook
 */
import { useEffect, useState } from 'react';
import { booksAPI } from '../services/api/client';

interface ParseMonitoringOptions {
  bookId: string;
  onComplete?: () => void;
  onFailed?: () => void;
  interval?: number;
}

export function useParseMonitoring({
  bookId,
  onComplete,
  onFailed,
  interval = 5000
}: ParseMonitoringOptions) {
  const [progress, setProgress] = useState(0);
  const [status, setStatus] = useState<string | null>(null);

  useEffect(() => {
    let lastStatus: string | null = null;
    let isActive = true;

    const checkStatus = async () => {
      if (!isActive) return;

      try {
        const statusData = await booksAPI.getParseStatus(bookId);

        if (!isActive) return;

        setProgress(statusData.progress);
        setStatus(statusData.status);

        // 상태가 변경되었을 때만 로그 출력
        if (lastStatus !== statusData.status && import.meta.env.DEV) {
          if (import.meta.env.DEV) console.log('[ParseMonitoring] Status:', statusData);
          lastStatus = statusData.status;
        }

        // 완료 또는 실패 시 콜백 호출
        if (statusData.status === 'DONE') {
          onComplete?.();
        } else if (statusData.status === 'FAILED') {
          onFailed?.();
        }
      } catch (error) {
        console.error('[ParseMonitoring] Error:', error);
      }
    };

    // 초기 체크
    checkStatus();

    // 주기적 체크 (DONE이나 FAILED가 아닐 때만)
    const intervalId = setInterval(() => {
      if (status !== 'DONE' && status !== 'FAILED') {
        checkStatus();
      } else {
        clearInterval(intervalId);
      }
    }, interval);

    return () => {
      isActive = false;
      clearInterval(intervalId);
    };
  }, [bookId, onComplete, onFailed, interval, status]);

  return { progress, status };
}
