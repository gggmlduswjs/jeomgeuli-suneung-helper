import { useEffect, useRef } from 'react';
import { useBrailleChunkReader, UseBrailleChunkReaderOptions } from './useBrailleChunkReader';

/**
 * Auto-send content to braille device when content changes
 *
 * @param content - The text content to display on braille device
 * @param options - Configuration options
 * @returns Chunk reader controls for manual navigation
 *
 * @example
 * // Auto-send question to braille device
 * const braille = useAutoBraille(questionText, {
 *   strategy: 'sentence',
 *   subject: 'korean',
 * });
 *
 * // Manual navigation
 * <button onClick={braille.next}>다음</button>
 * <button onClick={braille.prev}>이전</button>
 */
export function useAutoBraille(
  content: string,
  options: UseBrailleChunkReaderOptions & {
    enabled?: boolean;
    delay?: number;
  } = {}
) {
  const {
    enabled = true,
    delay = 300,
    maxCells,
    strategy = 'sentence',
    autoPlay = false,
    delayMs = 2000,
    subject,
  } = options;

  const chunkReader = useBrailleChunkReader(content, {
    maxCells,
    strategy,
    autoPlay,
    delayMs,
    subject,
  });

  // Track if content has been sent to avoid duplicate sends
  const lastSentContent = useRef<string>('');
  const timerRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    if (!enabled || !content) return;

    // Skip if content hasn't changed
    if (content === lastSentContent.current) return;

    // Clear any pending timer
    if (timerRef.current) {
      clearTimeout(timerRef.current);
    }

    // Send content after delay
    timerRef.current = setTimeout(() => {
      lastSentContent.current = content;

      // Content is automatically sent by useBrailleChunkReader
      // when currentChunk changes, so we just need to reset
      // to the first chunk when content changes
      if (chunkReader.currentIndex !== 0) {
        chunkReader.reset();
      }
    }, delay);

    return () => {
      if (timerRef.current) {
        clearTimeout(timerRef.current);
      }
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [content, enabled, delay]);

  return chunkReader;
}

/**
 * Auto-send content with conditional enable
 *
 * @example
 * // Only send when question is loaded
 * const braille = useConditionalBraille(
 *   questionText,
 *   !!questionText && !isLoading
 * );
 */
export function useConditionalBraille(
  content: string,
  condition: boolean,
  options: Omit<UseBrailleChunkReaderOptions, 'autoPlay'> & {
    delay?: number;
  } = {}
) {
  return useAutoBraille(content, {
    ...options,
    enabled: condition && !!content,
  });
}

/**
 * Auto-send with auto-scroll through chunks
 *
 * @example
 * // Auto-scroll through question text
 * const braille = useAutoScrollBraille(questionText, {
 *   delayMs: 3000, // 3 seconds per chunk
 *   subject: 'korean',
 * });
 */
export function useAutoScrollBraille(
  content: string,
  options: UseBrailleChunkReaderOptions & {
    enabled?: boolean;
    delay?: number;
  } = {}
) {
  return useAutoBraille(content, {
    ...options,
    autoPlay: true,
  });
}
