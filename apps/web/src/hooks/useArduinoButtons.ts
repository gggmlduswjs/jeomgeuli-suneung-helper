import { useState, useCallback, useEffect, useRef } from 'react';

export type ButtonEvent = 'prev' | 'next' | 'play' | 'pause';

export interface UseArduinoButtonsReturn {
  isConnected: boolean;
  error: string | null;
  connect: () => Promise<void>;
  disconnect: () => void;
  onButtonPress: (callback: (event: ButtonEvent) => void) => void;
  offButtonPress: () => void;
}

/**
 * Arduino 버튼 입력을 받는 Hook
 * Web Serial API를 사용하여 Arduino와 통신
 */
export function useArduinoButtons(): UseArduinoButtonsReturn {
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const portRef = useRef<SerialPort | null>(null);
  const readerRef = useRef<ReadableStreamDefaultReader<Uint8Array> | null>(null);
  const buttonCallbackRef = useRef<((event: ButtonEvent) => void) | null>(null);
  const textDecoderRef = useRef<TextDecoder | null>(null);
  const bufferRef = useRef<string>('');

  // Web Serial API 지원 확인
  const isSerialSupported = typeof navigator !== 'undefined' && 'serial' in navigator;

  // 연결 해제
  const disconnect = useCallback(() => {
    if (readerRef.current) {
      readerRef.current.cancel().catch(() => {});
      readerRef.current = null;
    }
    if (portRef.current) {
      portRef.current.close().catch(() => {});
      portRef.current = null;
    }
    setIsConnected(false);
    bufferRef.current = '';
  }, []);

  // 연결
  const connect = useCallback(async () => {
    try {
      setError(null);

      if (!isSerialSupported) {
        throw new Error('Web Serial API를 지원하지 않는 브라우저입니다. Chrome 또는 Edge를 사용해주세요.');
      }

      // 이미 연결되어 있으면 재연결 시도
      if (portRef.current && portRef.current.readable) {
        console.log('[Arduino] 이미 연결된 포트가 있습니다.');
        return;
      }

      // 포트 선택
      const port = await (navigator as any).serial.requestPort();
      await port.open({ baudRate: 9600 });
      
      portRef.current = port;
      textDecoderRef.current = new TextDecoder();

      // 읽기 스트림 시작
      const reader = port.readable?.getReader();
      if (!reader) {
        throw new Error('읽기 스트림을 가져올 수 없습니다.');
      }

      readerRef.current = reader;
      setIsConnected(true);

      // 데이터 읽기 루프
      (async () => {
        try {
          while (true) {
            const { value, done } = await reader.read();
            if (done) break;

            if (textDecoderRef.current) {
              const chunk = textDecoderRef.current.decode(value, { stream: true });
              bufferRef.current += chunk;

              // 줄 단위로 파싱
              const lines = bufferRef.current.split('\n');
              bufferRef.current = lines.pop() || ''; // 마지막 불완전한 줄은 버퍼에 유지

              for (const line of lines) {
                const trimmed = line.trim();
                if (!trimmed) continue;

                // 버튼 이벤트 파싱
                if (trimmed.startsWith('BTN:')) {
                  const parts = trimmed.split(':');
                  if (parts.length >= 2) {
                    const buttonNum = parts[1];
                    let event: ButtonEvent | null = null;

                    if (buttonNum === '1') {
                      event = 'prev';
                    } else if (buttonNum === '2') {
                      event = 'next';
                    } else if (buttonNum === '3') {
                      const action = parts[2] || 'PLAY';
                      event = action === 'PAUSE' ? 'pause' : 'play';
                    }

                    if (event && buttonCallbackRef.current) {
                      buttonCallbackRef.current(event);
                    }
                  }
                }
              }
            }
          }
        } catch (err: any) {
          if (err.name !== 'AbortError') {
            console.error('[Arduino] 읽기 오류:', err);
            setError(`읽기 오류: ${err.message}`);
            disconnect();
          }
        }
      })();

      console.log('[Arduino] 연결 성공');
    } catch (err: any) {
      console.error('[Arduino] 연결 실패:', err);
      setError(err.message || '연결에 실패했습니다.');
      disconnect();
      throw err;
    }
  }, [isSerialSupported, disconnect]);

  // 버튼 이벤트 콜백 등록
  const onButtonPress = useCallback((callback: (event: ButtonEvent) => void) => {
    buttonCallbackRef.current = callback;
  }, []);

  // 버튼 이벤트 콜백 제거
  const offButtonPress = useCallback(() => {
    buttonCallbackRef.current = null;
  }, []);

  // 컴포넌트 언마운트 시 연결 해제
  useEffect(() => {
    return () => {
      disconnect();
    };
  }, [disconnect]);

  return {
    isConnected,
    error,
    connect,
    disconnect,
    onButtonPress,
    offButtonPress,
  };
}
