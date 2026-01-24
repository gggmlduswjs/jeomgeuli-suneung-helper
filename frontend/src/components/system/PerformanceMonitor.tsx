import { useEffect, useState } from 'react';
import performanceMonitor from '../../lib/performance';
import { usePerformanceReport } from '../../hooks/usePerformance';

/**
 * 성능 모니터링 컴포넌트 (개발 모드 전용)
 */
export default function PerformanceMonitor() {
  const { report, warnings } = usePerformanceReport();
  const [isVisible, setIsVisible] = useState(false);

  useEffect(() => {
    // 개발 모드에서만 표시
    if (!import.meta.env.DEV) return;

    // 경고가 있으면 자동 표시
    if (warnings.length > 0) {
      setIsVisible(true);
    }
  }, [warnings]);

  if (!import.meta.env.DEV || !isVisible) {
    return null;
  }

  return (
    <div className="fixed bottom-4 right-4 bg-card border border-border rounded-lg shadow-lg p-4 max-w-md z-50">
      <div className="flex items-center justify-between mb-2">
        <h3 className="text-sm font-semibold">성능 모니터</h3>
        <button
          onClick={() => setIsVisible(false)}
          className="text-muted hover:text-fg"
          aria-label="닫기"
        >
          ×
        </button>
      </div>

      {warnings.length > 0 && (
        <div className="mb-3">
          <h4 className="text-xs font-semibold text-danger mb-1">경고</h4>
          <ul className="text-xs space-y-1">
            {warnings.map((warning, idx) => (
              <li key={idx} className="text-danger">• {warning}</li>
            ))}
          </ul>
        </div>
      )}

      <div className="text-xs space-y-1">
        <div>
          <span className="text-muted">메트릭 수:</span>{' '}
          <span className="font-mono">{report.totalMetrics}</span>
        </div>
        {report.totalMetrics > 0 && (
          <>
            <div>
              <span className="text-muted">평균 렌더 시간:</span>{' '}
              <span className="font-mono">
                {report.averageRenderTime.toFixed(2)}ms
              </span>
            </div>
            <div>
              <span className="text-muted">느린 액션:</span>{' '}
              <span className="font-mono">
                {report.slowActions.length}개
              </span>
            </div>
          </>
        )}
      </div>

      <button
        onClick={() => {
          performanceMonitor.clear();
          setIsVisible(false);
        }}
        className="mt-2 text-xs text-muted hover:text-fg"
      >
        메트릭 초기화
      </button>
    </div>
  );
}

