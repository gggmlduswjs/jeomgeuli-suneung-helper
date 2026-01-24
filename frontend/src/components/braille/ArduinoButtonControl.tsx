import { useEffect } from 'react';
import { useArduinoButtons, ButtonEvent } from '../../hooks/useArduinoButtons';

interface ArduinoButtonControlProps {
  onPrev?: () => void;
  onNext?: () => void;
  onPlay?: () => void;
  onPause?: () => void;
  autoConnect?: boolean;
}

/**
 * Arduino 버튼 입력을 받아서 콜백을 호출하는 컴포넌트
 */
export default function ArduinoButtonControl({
  onPrev,
  onNext,
  onPlay,
  onPause,
  autoConnect = false,
}: ArduinoButtonControlProps) {
  const { isConnected, error, connect, disconnect, onButtonPress, offButtonPress } = useArduinoButtons();

  // 버튼 이벤트 처리
  useEffect(() => {
    const handleButtonEvent = (event: ButtonEvent) => {
      if (import.meta.env.DEV) console.log('[ArduinoButtonControl] 버튼 이벤트:', event);
      
      switch (event) {
        case 'prev':
          onPrev?.();
          break;
        case 'next':
          onNext?.();
          break;
        case 'play':
          onPlay?.();
          break;
        case 'pause':
          onPause?.();
          break;
      }
    };

    onButtonPress(handleButtonEvent);

    return () => {
      offButtonPress();
    };
  }, [onPrev, onNext, onPlay, onPause, onButtonPress, offButtonPress]);

  // 자동 연결
  useEffect(() => {
    if (autoConnect && !isConnected && !error) {
      connect().catch((err) => {
        console.error('[ArduinoButtonControl] 자동 연결 실패:', err);
      });
    }
  }, [autoConnect, isConnected, error, connect]);

  // 연결 상태 표시 (개발용)
  if (process.env.NODE_ENV === 'development') {
    return (
      <div className="fixed bottom-4 right-4 bg-card border rounded-lg p-2 text-xs">
        <div>Arduino: {isConnected ? '연결됨' : '연결 안됨'}</div>
        {error && <div className="text-destructive">{error}</div>}
        {!isConnected && (
          <button
            onClick={() => connect()}
            className="mt-1 px-2 py-1 bg-primary text-primary-foreground rounded text-xs"
          >
            연결
          </button>
        )}
        {isConnected && (
          <button
            onClick={disconnect}
            className="mt-1 px-2 py-1 bg-secondary text-secondary-foreground rounded text-xs"
          >
            연결 해제
          </button>
        )}
      </div>
    );
  }

  return null;
}
