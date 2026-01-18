import { useCallback, useRef, useState } from 'react';

export interface UsePointerGestureOptions {
  onLongPress?: () => void;
  onTap?: () => void;
  longPressDuration?: number;
  tapThreshold?: number;
  moveThreshold?: number;
  enabled?: boolean;
}

export interface UsePointerGestureReturn {
  isLongPressing: boolean;
  handlePointerDown: (e: React.PointerEvent) => void;
  handlePointerUp: (e: React.PointerEvent) => void;
  handlePointerMove: (e: React.PointerEvent) => void;
  handlePointerCancel: (e: React.PointerEvent) => void;
}

/**
 * usePointerGesture - 포인터 제스처 감지 훅
 * 롱프레스와 탭을 감지합니다.
 */
export function usePointerGesture(options: UsePointerGestureOptions = {}): UsePointerGestureReturn {
  const {
    onLongPress,
    onTap,
    longPressDuration = 500,
    tapThreshold = 300,
    moveThreshold = 10,
    enabled = true,
  } = options;

  const [isLongPressing, setIsLongPressing] = useState(false);
  const longPressTimerRef = useRef<NodeJS.Timeout | null>(null);
  const pressStartRef = useRef<{ x: number; y: number; time: number } | null>(null);
  const hasStartedRef = useRef(false);
  const lastPointerRef = useRef<number>(0);

  const throttlePointer = useCallback((ms: number = 300) => {
    const now = Date.now();
    if (now - lastPointerRef.current < ms) return false;
    lastPointerRef.current = now;
    return true;
  }, []);

  const handlePointerDown = useCallback((e: React.PointerEvent) => {
    if (!enabled) return;

    // 버튼이나 입력 필드에서는 작동하지 않도록
    const target = e.target as HTMLElement;
    if (
      target.tagName === 'BUTTON' ||
      target.tagName === 'INPUT' ||
      target.tagName === 'TEXTAREA' ||
      target.closest('button') ||
      target.closest('input') ||
      target.closest('textarea') ||
      target.closest('a')
    ) {
      return;
    }

    pressStartRef.current = {
      x: e.clientX,
      y: e.clientY,
      time: Date.now(),
    };
    hasStartedRef.current = false;

    longPressTimerRef.current = setTimeout(() => {
      setIsLongPressing(true);
      hasStartedRef.current = true;
      onLongPress?.();
    }, longPressDuration);
  }, [enabled, longPressDuration, onLongPress]);

  const handlePointerUp = useCallback((e: React.PointerEvent) => {
    if (!enabled) return;

    if (longPressTimerRef.current) {
      clearTimeout(longPressTimerRef.current);
      longPressTimerRef.current = null;
    }

    // 롱프레스가 시작되었으면 롱프레스 종료 처리
    if (hasStartedRef.current && isLongPressing) {
      setIsLongPressing(false);
      hasStartedRef.current = false;
      return;
    }

    // 짧은 탭 처리
    if (pressStartRef.current) {
      const startTime = pressStartRef.current.time;
      const dt = Date.now() - startTime;
      if (dt < tapThreshold && throttlePointer(300)) {
        onTap?.();
      }
    }

    // 애니메이션 숨기기
    setTimeout(() => {
      setIsLongPressing(false);
    }, 200);

    pressStartRef.current = null;
  }, [enabled, isLongPressing, tapThreshold, onTap, throttlePointer]);

  const handlePointerMove = useCallback((e: React.PointerEvent) => {
    if (!enabled || !pressStartRef.current) return;

    const dx = Math.abs(e.clientX - pressStartRef.current.x);
    const dy = Math.abs(e.clientY - pressStartRef.current.y);

    if (dx > moveThreshold || dy > moveThreshold) {
      // 포인터 이동 시 롱프레스 취소
      if (longPressTimerRef.current) {
        clearTimeout(longPressTimerRef.current);
        longPressTimerRef.current = null;
      }
      pressStartRef.current = null;
    }
  }, [enabled, moveThreshold]);

  const handlePointerCancel = useCallback((e: React.PointerEvent) => {
    handlePointerUp(e);
  }, [handlePointerUp]);

  return {
    isLongPressing,
    handlePointerDown,
    handlePointerUp,
    handlePointerMove,
    handlePointerCancel,
  };
}



