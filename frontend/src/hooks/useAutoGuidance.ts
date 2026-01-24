import { useEffect, useRef } from 'react';
import { useTTS } from './useTTS';

/**
 * Auto-play TTS guidance on screen enter or content change
 *
 * @param message - The message to speak
 * @param deps - Dependencies to trigger re-announcement
 * @param options - Configuration options
 * @returns void
 *
 * @example
 * // Auto-announce question on load
 * useAutoGuidance(
 *   '국어 문학 3강 5번 문제입니다. 문제를 읽고 답하세요.',
 *   [currentQuestion]
 * );
 *
 * @example
 * // Disable auto-announce
 * useAutoGuidance(
 *   '결과가 저장되었습니다.',
 *   [result],
 *   { enabled: false }
 * );
 */
export function useAutoGuidance(
  message: string | string[],
  deps: React.DependencyList = [],
  options: {
    enabled?: boolean;
    delay?: number;
    allowDuringMic?: boolean;
    onEnd?: () => void;
  } = {}
) {
  const { speak } = useTTS();
  const {
    enabled = true,
    delay = 500,
    allowDuringMic = false,
    onEnd
  } = options;

  // Track previous message to avoid duplicate announcements
  const prevMessageRef = useRef<string | string[] | null>(null);
  const isFirstMount = useRef(true);

  useEffect(() => {
    if (!enabled || !message) return;

    // Convert message to string for comparison
    const messageStr = Array.isArray(message) ? message.join(' ') : message;
    const prevMessageStr = prevMessageRef.current 
      ? (Array.isArray(prevMessageRef.current) ? prevMessageRef.current.join(' ') : prevMessageRef.current)
      : null;

    // Skip if message hasn't actually changed (except on first mount)
    if (!isFirstMount.current && messageStr === prevMessageStr) {
      return;
    }

    isFirstMount.current = false;
    prevMessageRef.current = message;

    const timer = setTimeout(() => {
      speak(message, {
        onEnd
      });
    }, delay);

    return () => {
      clearTimeout(timer);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [enabled, delay, allowDuringMic, message, ...deps]);
}

/**
 * Conditional auto-guidance that only triggers when a condition is met
 *
 * @example
 * // Only announce when answer is submitted
 * useConditionalGuidance(
 *   answerResult ? '정답입니다!' : '',
 *   !!answerResult,
 *   [answerResult]
 * );
 */
export function useConditionalGuidance(
  message: string | string[],
  condition: boolean,
  deps: React.DependencyList = [],
  options: {
    delay?: number;
    allowDuringMic?: boolean;
    onEnd?: () => void;
  } = {}
) {
  useAutoGuidance(message, deps, {
    ...options,
    enabled: condition && !!message,
  });
}

/**
 * Queue multiple guidance messages with delays between them
 *
 * @example
 * // Announce multiple parts in sequence
 * useQueuedGuidance([
 *   '3강 5번 문제입니다.',
 *   '다음 지문을 읽고 물음에 답하세요.',
 * ], [currentQuestion]);
 */
export function useQueuedGuidance(
  messages: string[],
  deps: React.DependencyList = [],
  options: {
    enabled?: boolean;
    delay?: number;
    betweenDelay?: number;
    allowDuringMic?: boolean;
    onEnd?: () => void;
  } = {}
) {
  const { speak } = useTTS();
  const {
    enabled = true,
    delay = 500,
    betweenDelay = 1000,
    allowDuringMic = false,
    onEnd
  } = options;

  useEffect(() => {
    if (!enabled || !messages.length) return;

    const timers: NodeJS.Timeout[] = [];

    // Initial delay before starting
    const initialTimer = setTimeout(() => {
      let currentDelay = 0;

      messages.forEach((message, index) => {
        const isLast = index === messages.length - 1;
        const timer = setTimeout(() => {
          speak(message, {
            onEnd: isLast ? onEnd : undefined,
          });
        }, currentDelay);

        timers.push(timer);
        currentDelay += betweenDelay;
      });
    }, delay);

    timers.push(initialTimer);

    return () => {
      timers.forEach(timer => clearTimeout(timer));
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [enabled, delay, betweenDelay, allowDuringMic, ...deps]);
}
