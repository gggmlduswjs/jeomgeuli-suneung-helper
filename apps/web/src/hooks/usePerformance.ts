import { useEffect, useRef } from 'react';
import performanceMonitor from '../lib/performance';

/**
 * 성능 측정 훅
 * 컴포넌트 렌더링 시간 및 사용자 액션 시간 측정
 */
export function usePerformance(componentName: string) {
  const renderStartRef = useRef<number>(Date.now());
  const actionStartRef = useRef<Map<string, number>>(new Map());

  // 컴포넌트 렌더링 시간 측정
  useEffect(() => {
    const renderTime = Date.now() - renderStartRef.current;
    if (renderTime > 0) {
      performanceMonitor.measureRender(componentName, renderTime);
    }
  });

  /**
   * 액션 시작
   */
  const startAction = (actionName: string) => {
    actionStartRef.current.set(actionName, Date.now());
  };

  /**
   * 액션 종료 및 측정
   */
  const endAction = (actionName: string) => {
    const startTime = actionStartRef.current.get(actionName);
    if (startTime) {
      const duration = Date.now() - startTime;
      performanceMonitor.measureUserAction(`${componentName}:${actionName}`, duration);
      actionStartRef.current.delete(actionName);
    }
  };

  /**
   * 액션 측정 (자동 시작/종료)
   */
  const measureAction = async <T,>(actionName: string, fn: () => Promise<T>): Promise<T> => {
    startAction(actionName);
    try {
      const result = await fn();
      return result;
    } finally {
      endAction(actionName);
    }
  };

  return {
    startAction,
    endAction,
    measureAction,
  };
}

/**
 * 성능 리포트 훅
 */
export function usePerformanceReport(filter?: { name?: string; since?: number }) {
  const report = performanceMonitor.generateReport(filter);
  const warnings = performanceMonitor.checkPerformanceWarnings();

  return {
    report,
    warnings,
    getMetrics: (name?: string) => performanceMonitor.getMetrics({ name }),
  };
}

