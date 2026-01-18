/**
 * Accessibility - Keyboard Navigation Hook
 * 키보드 네비게이션을 위한 커스텀 훅
 */
import { useEffect, useCallback, useRef } from 'react';

export interface KeyboardNavigationOptions {
  /**
   * 네비게이션 가능한 요소 선택자
   */
  selector?: string;
  
  /**
   * 방향키로 네비게이션할지 여부
   */
  enableArrowKeys?: boolean;
  
  /**
   * Tab 키로 네비게이션할지 여부
   */
  enableTab?: boolean;
  
  /**
   * Enter/Space 키로 활성화할지 여부
   */
  enableActivation?: boolean;
  
  /**
   * 네비게이션 변경 시 콜백
   */
  onNavigate?: (index: number) => void;
  
  /**
   * 활성화 시 콜백
   */
  onActivate?: (index: number) => void;
}

/**
 * 키보드 네비게이션 훅
 */
export function useKeyboardNavigation(options: KeyboardNavigationOptions = {}) {
  const {
    selector = 'button, a, [role="button"], [tabindex="0"]',
    enableArrowKeys = true,
    enableTab = true,
    enableActivation = true,
    onNavigate,
    onActivate,
  } = options;

  const containerRef = useRef<HTMLElement | null>(null);
  const currentIndexRef = useRef<number>(-1);

  const getFocusableElements = useCallback(() => {
    if (!containerRef.current) return [];
    return Array.from(
      containerRef.current.querySelectorAll<HTMLElement>(selector)
    ).filter(
      (el) => !el.hasAttribute('disabled') && el.offsetParent !== null
    );
  }, [selector]);

  const focusElement = useCallback(
    (index: number) => {
      const elements = getFocusableElements();
      if (index >= 0 && index < elements.length) {
        elements[index].focus();
        currentIndexRef.current = index;
        onNavigate?.(index);
      }
    },
    [getFocusableElements, onNavigate]
  );

  const handleKeyDown = useCallback(
    (e: KeyboardEvent) => {
      if (!containerRef.current?.contains(e.target as Node)) return;

      const elements = getFocusableElements();
      if (elements.length === 0) return;

      let newIndex = currentIndexRef.current;

      // 방향키 네비게이션
      if (enableArrowKeys) {
        if (e.key === 'ArrowDown' || e.key === 'ArrowRight') {
          e.preventDefault();
          newIndex = (currentIndexRef.current + 1) % elements.length;
          focusElement(newIndex);
          return;
        }
        if (e.key === 'ArrowUp' || e.key === 'ArrowLeft') {
          e.preventDefault();
          newIndex =
            currentIndexRef.current <= 0
              ? elements.length - 1
              : currentIndexRef.current - 1;
          focusElement(newIndex);
          return;
        }
      }

      // Home/End 키
      if (e.key === 'Home') {
        e.preventDefault();
        focusElement(0);
        return;
      }
      if (e.key === 'End') {
        e.preventDefault();
        focusElement(elements.length - 1);
        return;
      }

      // Enter/Space 활성화
      if (enableActivation && (e.key === 'Enter' || e.key === ' ')) {
        const target = e.target as HTMLElement;
        if (target.matches(selector)) {
          e.preventDefault();
          const index = elements.indexOf(target);
          if (index >= 0) {
            onActivate?.(index);
            target.click();
          }
        }
      }
    },
    [
      selector,
      enableArrowKeys,
      enableActivation,
      getFocusableElements,
      focusElement,
      onActivate,
    ]
  );

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    // 초기 포커스 설정
    const elements = getFocusableElements();
    if (elements.length > 0 && currentIndexRef.current < 0) {
      currentIndexRef.current = 0;
    }

    container.addEventListener('keydown', handleKeyDown);

    return () => {
      container.removeEventListener('keydown', handleKeyDown);
    };
  }, [handleKeyDown, getFocusableElements]);

  return {
    containerRef,
    focusElement,
    getFocusableElements,
  };
}


