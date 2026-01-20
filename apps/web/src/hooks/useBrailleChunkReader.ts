/**
 * 점자 청크 리더 훅
 * 텍스트를 청크로 분할하고 순차적으로 점자 디스플레이에 출력
 */
import { useState, useEffect, useMemo, useCallback, useRef } from 'react';
import { splitToBrailleChunks, estimateBrailleCells } from '../lib/braille';
import { brailleDisplayConfig } from '../config/brailleDisplay';
import useBrailleBLE from './useBrailleBLE';
import { useArduinoButtons } from './useArduinoButtons';

export interface UseBrailleChunkReaderOptions {
  maxCells?: number;
  strategy?: 'word' | 'sentence' | 'smart';
  autoPlay?: boolean; // 자동 재생 여부
  delayMs?: number; // 청크 간 지연 시간 (ms)
  subject?: 'math' | 'korean' | 'english' | 'science' | 'social'; // 과목별 전략 적용
}

export interface UseBrailleChunkReaderReturn {
  chunks: string[];
  currentIndex: number;
  currentChunk: string | null;
  totalChunks: number;
  next: () => void;
  prev: () => void;
  goTo: (index: number) => void;
  play: () => void;
  pause: () => void;
  reset: () => void;
  isPlaying: boolean;
}

export function useBrailleChunkReader(
  text: string,
  options: UseBrailleChunkReaderOptions = {}
): UseBrailleChunkReaderReturn {
  const config = brailleDisplayConfig.get();
  const { isConnected, writeText } = useBrailleBLE();
  
  // Arduino 버튼 제어 (선택적)
  const { isConnected: isArduinoConnected, connect: connectArduino, onButtonPress, offButtonPress } = useArduinoButtons();
  
  // 과목별 전략 적용
  const getSubjectStrategy = (subject?: string): 'word' | 'sentence' | 'smart' => {
    if (!subject) return config.chunkStrategy;
    
    switch (subject) {
      case 'math':
        return 'smart'; // 수식 단위
      case 'korean':
        return 'sentence'; // 문장 단위
      case 'english':
        return 'word'; // 단어 단위
      case 'science':
      case 'social':
        return 'smart'; // 용어 중심
      default:
        return config.chunkStrategy;
    }
  };
  
  const {
    maxCells = config.maxCells,
    strategy = options.subject ? getSubjectStrategy(options.subject) : config.chunkStrategy,
    autoPlay = false,
    delayMs = 2000,
  } = options;

  // 청크 분할
  const chunks = useMemo(() => {
    if (!text || text.trim().length === 0) {
      return [];
    }
    return splitToBrailleChunks(text, {
      maxCells,
      strategy,
      preserveMeaning: true,
    });
  }, [text, maxCells, strategy]);

  const [currentIndex, setCurrentIndex] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const intervalRef = useRef<NodeJS.Timeout | null>(null);
  const lastTextRef = useRef<string>(''); // 이전 텍스트 추적
  
  // 다음 청크로 이동
  const next = useCallback(() => {
    setCurrentIndex((prev) => Math.min(prev + 1, chunks.length - 1));
  }, [chunks.length]);

  // 이전 청크로 이동
  const prev = useCallback(() => {
    setCurrentIndex((prev) => Math.max(prev - 1, 0));
  }, []);

  // 특정 인덱스로 이동
  const goTo = useCallback((index: number) => {
    setCurrentIndex(Math.max(0, Math.min(index, chunks.length - 1)));
  }, [chunks.length]);

  // 재생 시작
  const play = useCallback(() => {
    setIsPlaying(true);
  }, []);

  // 일시정지
  const pause = useCallback(() => {
    setIsPlaying(false);
  }, []);

  // Arduino 버튼 이벤트 처리
  useEffect(() => {
    if (!isArduinoConnected) return;
    
    const handleButtonEvent = (event: 'prev' | 'next' | 'play' | 'pause') => {
      switch (event) {
        case 'prev':
          prev();
          break;
        case 'next':
          next();
          break;
        case 'play':
          play();
          break;
        case 'pause':
          pause();
          break;
      }
    };
    
    onButtonPress(handleButtonEvent);
    
    return () => {
      offButtonPress();
    };
  }, [isArduinoConnected, prev, next, play, pause, onButtonPress, offButtonPress]);

  // 텍스트가 변경되면 인덱스와 재생 상태 초기화
  useEffect(() => {
    if (text !== lastTextRef.current) {
      setCurrentIndex(0);
      setIsPlaying(false);
      // 기존 인터벌 정리
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
      lastTextRef.current = text;
    }
  }, [text]);

  // 현재 청크
  const currentChunk = chunks[currentIndex] || null;

  // 현재 청크를 점자로 출력
  useEffect(() => {
    if (currentChunk && isConnected) {
      // 텍스트 변경 시 즉시 출력
      writeText(currentChunk).catch((error) => {
        console.error('[useBrailleChunkReader] Failed to write to braille:', error);
      });
    }
  }, [currentIndex, currentChunk, isConnected, writeText]);

  // 자동 재생
  useEffect(() => {
    if (autoPlay && isPlaying && chunks.length > 0) {
      intervalRef.current = setInterval(() => {
        setCurrentIndex((prev) => {
          if (prev < chunks.length - 1) {
            return prev + 1;
          } else {
            setIsPlaying(false);
            return prev;
          }
        });
      }, delayMs);

      return () => {
        if (intervalRef.current) {
          clearInterval(intervalRef.current);
          intervalRef.current = null;
        }
      };
    }
  }, [autoPlay, isPlaying, chunks.length, delayMs]);

  // 초기화
  const reset = useCallback(() => {
    setCurrentIndex(0);
    setIsPlaying(false);
  }, []);

  return {
    chunks,
    currentIndex,
    currentChunk,
    totalChunks: chunks.length,
    next,
    prev,
    goTo,
    play,
    pause,
    reset,
    isPlaying,
  };
}

