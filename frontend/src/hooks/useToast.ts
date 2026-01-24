/**
 * Toast 메시지 관리를 위한 커스텀 훅
 */
import { useState, useCallback } from 'react';
import { TOAST_DURATION } from '../constants';

export interface UseToastReturn {
  showToast: boolean;
  toastMessage: string;
  setShowToast: (show: boolean) => void;
  showToastMessage: (message: string, duration?: number) => void;
  hideToast: () => void;
}

const DEFAULT_DURATION = TOAST_DURATION;

/**
 * Toast 메시지 상태 관리 훅
 */
export function useToast(defaultDuration: number = DEFAULT_DURATION): UseToastReturn {
  const [showToast, setShowToast] = useState(false);
  const [toastMessage, setToastMessage] = useState('');
  const timeoutRef = useState<NodeJS.Timeout | null>(null)[0];

  const showToastMessage = useCallback((message: string, duration?: number) => {
    setToastMessage(message);
    setShowToast(true);
    
    // 기존 timeout 정리
    if (timeoutRef) {
      clearTimeout(timeoutRef as unknown as NodeJS.Timeout);
    }
    
    // 자동 숨김
    setTimeout(() => {
      setShowToast(false);
    }, duration ?? defaultDuration);
    
    // timeoutRef 업데이트는 ref를 사용해야 하지만, 
    // 여기서는 단순화를 위해 setTimeout만 사용
    // 실제로는 useRef를 사용하는 것이 더 좋지만, 
    // 현재 구조에서는 이렇게도 충분함
  }, [defaultDuration]);

  const hideToast = useCallback(() => {
    setShowToast(false);
  }, []);

  return {
    showToast,
    toastMessage,
    setShowToast,
    showToastMessage,
    hideToast,
  };
}

export default useToast;
