import { useEffect, useState, useRef } from 'react';
import { useVoiceStore } from '../../store/voice';
import VoiceEventBus, { VoiceEventType, onMicMode, onMicIntent, onTranscript, onCommand, onError } from '../../lib/voice/VoiceEventBus';
import VoiceService from '../../services/voice';
import micMode from '../../lib/voice/MicMode';

interface EventLog {
  type: string;
  detail: any;
  timestamp: number;
}

/**
 * 음성 인식 디버그 패널
 * 개발 모드에서 음성 인식 상태를 실시간으로 확인할 수 있습니다.
 */
export default function VoiceRecognitionDebug() {
  const [isVisible, setIsVisible] = useState(false);
  const [eventLogs, setEventLogs] = useState<EventLog[]>([]);
  const logsRef = useRef<EventLog[]>([]);
  const maxLogs = 50;

  // Store 상태
  const isListening = useVoiceStore(state => state.isListening);
  const transcript = useVoiceStore(state => state.transcript);
  const alternatives = useVoiceStore(state => state.alternatives);
  const sttError = useVoiceStore(state => state.sttError);
  const micMode = useVoiceStore(state => state.micMode);
  const isSpeaking = useVoiceStore(state => state.isSpeaking);
  const lastTranscriptTime = useVoiceStore(state => state.lastTranscriptTime);
  const lastTranscriptText = useVoiceStore(state => state.lastTranscriptText);

  // 이벤트 로깅
  useEffect(() => {
    const addLog = (type: string, detail: any) => {
      const log: EventLog = {
        type,
        detail,
        timestamp: Date.now(),
      };
      logsRef.current = [log, ...logsRef.current].slice(0, maxLogs);
      setEventLogs([...logsRef.current]);
    };

    // VoiceEventBus 이벤트 리스너 등록
    const unsubMicMode = onMicMode((detail) => {
      addLog('MIC_MODE', detail);
    });

    const unsubMicIntent = onMicIntent((detail) => {
      addLog('MIC_INTENT', detail);
    });

    const unsubTranscript = onTranscript((detail) => {
      addLog('TRANSCRIPT', detail);
    });

    const unsubCommand = onCommand((detail) => {
      addLog('COMMAND', detail);
    });

    const unsubError = onError((detail) => {
      addLog('ERROR', detail);
    });

    // Window 이벤트도 캡처
    const handleWindowEvent = (e: Event) => {
      const customEvent = e as CustomEvent;
      if (customEvent.type.startsWith('voice:')) {
        addLog(`WINDOW:${customEvent.type}`, customEvent.detail);
      }
    };

    window.addEventListener('voice:mic-mode', handleWindowEvent);
    window.addEventListener('voice:mic-intent', handleWindowEvent);
    window.addEventListener('voice:transcript', handleWindowEvent);
    window.addEventListener('voice:command', handleWindowEvent);
    window.addEventListener('voice:error', handleWindowEvent);

    return () => {
      unsubMicMode();
      unsubMicIntent();
      unsubTranscript();
      unsubCommand();
      unsubError();
      window.removeEventListener('voice:mic-mode', handleWindowEvent);
      window.removeEventListener('voice:mic-intent', handleWindowEvent);
      window.removeEventListener('voice:transcript', handleWindowEvent);
      window.removeEventListener('voice:command', handleWindowEvent);
      window.removeEventListener('voice:error', handleWindowEvent);
    };
  }, []);

  // 브라우저 지원 확인
  const [browserSupport, setBrowserSupport] = useState<{
    speechRecognition: boolean;
    speechSynthesis: boolean;
    mediaDevices: boolean;
  } | null>(null);

  useEffect(() => {
    const checkSupport = () => {
      const Recognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
      const support = {
        speechRecognition: !!Recognition,
        speechSynthesis: 'speechSynthesis' in window,
        mediaDevices: 'mediaDevices' in navigator && 'getUserMedia' in navigator.mediaDevices,
      };
      setBrowserSupport(support);
      console.log('[VoiceDebug] 브라우저 지원 확인:', support);
      if (!support.speechRecognition) {
        console.warn('[VoiceDebug] ⚠️ Speech Recognition이 지원되지 않습니다. Chrome/Edge 브라우저를 사용해주세요.');
      }
    };
    checkSupport();
    console.log('[VoiceDebug] 디버그 패널 초기화 완료');
  }, []);

  // 테스트 함수
  const testVoiceRecognition = async () => {
    try {
      console.log('[VoiceDebug] 음성 인식 테스트 시작');
      console.log('[VoiceDebug] VoiceService 상태:', {
        isInitialized: (VoiceService as any).isInitialized,
        sttProvider: !!(VoiceService as any).sttProvider,
      });
      
      // 브라우저 권한 확인
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        console.log('[VoiceDebug] 마이크 권한 확인됨');
        stream.getTracks().forEach(track => track.stop());
      } catch (permError) {
        console.error('[VoiceDebug] 마이크 권한 오류:', permError);
        alert('마이크 권한이 필요합니다. 브라우저 설정에서 마이크 권한을 허용해주세요.');
        return;
      }

      await VoiceService.startSTT({
        onResult: (text) => {
          console.log('[VoiceDebug] 인식 결과:', text);
          alert(`인식된 텍스트: ${text}`);
        },
        onError: (error) => {
          console.error('[VoiceDebug] 에러:', error);
          alert(`에러: ${error}`);
        },
        autoStop: true,
      });
    } catch (error: any) {
      console.error('[VoiceDebug] 테스트 실패:', error);
      alert(`테스트 실패: ${error?.message || error}`);
    }
  };

  const testMicMode = () => {
    console.log('[VoiceDebug] MicMode 테스트');
    micMode.requestStart();
    setTimeout(() => {
      micMode.requestStop();
    }, 3000);
  };

  // 개발 모드에서만 표시
  if (!import.meta.env.DEV) {
    return null;
  }

  const formatTime = (timestamp: number) => {
    if (!timestamp) return '-';
    const date = new Date(timestamp);
    return date.toLocaleTimeString('ko-KR', { 
      hour12: false,
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit',
      fractionalSecondDigits: 3,
    });
  };

  const getTimeAgo = (timestamp: number) => {
    if (!timestamp) return '-';
    const diff = Date.now() - timestamp;
    if (diff < 1000) return '방금';
    return `${(diff / 1000).toFixed(1)}초 전`;
  };

  return (
    <>
      {/* 토글 버튼 */}
      <button
        onClick={() => setIsVisible(!isVisible)}
        className="fixed bottom-4 left-4 z-[9999] bg-primary text-white px-4 py-3 rounded-lg shadow-2xl text-sm font-bold hover:bg-primary/90 transition-colors border-2 border-white animate-pulse"
        aria-label="음성 인식 디버그 패널 토글"
        style={{ 
          boxShadow: '0 4px 20px rgba(0,0,0,0.3)',
        }}
      >
        🎤 음성 인식 디버그
      </button>

      {/* 디버그 패널 */}
      {isVisible && (
        <div className="fixed bottom-20 left-4 z-[9998] bg-card border-2 border-primary rounded-lg shadow-2xl p-4 max-w-2xl max-h-[80vh] overflow-y-auto" style={{ minWidth: '400px' }}>
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-bold">🎤 음성 인식 디버그</h2>
            <button
              onClick={() => setIsVisible(false)}
              className="text-muted hover:text-fg text-xl"
              aria-label="닫기"
            >
              ×
            </button>
          </div>

          {/* 현재 상태 */}
          <div className="mb-4 space-y-2">
            <h3 className="text-sm font-semibold text-muted">현재 상태</h3>
            <div className="grid grid-cols-2 gap-2 text-xs">
              <div className="flex items-center gap-2">
                <span className={`w-3 h-3 rounded-full ${isListening ? 'bg-red-500 animate-pulse' : 'bg-gray-400'}`} />
                <span className="text-muted">인식 중:</span>
                <span className="font-mono">{isListening ? '예' : '아니오'}</span>
              </div>
              <div className="flex items-center gap-2">
                <span className={`w-3 h-3 rounded-full ${micMode ? 'bg-blue-500' : 'bg-gray-400'}`} />
                <span className="text-muted">마이크 모드:</span>
                <span className="font-mono">{micMode ? '활성' : '비활성'}</span>
              </div>
              <div className="flex items-center gap-2">
                <span className={`w-3 h-3 rounded-full ${isSpeaking ? 'bg-green-500 animate-pulse' : 'bg-gray-400'}`} />
                <span className="text-muted">TTS 재생 중:</span>
                <span className="font-mono">{isSpeaking ? '예' : '아니오'}</span>
              </div>
              {sttError && (
                <div className="col-span-2 text-red-500 text-xs">
                  <span className="font-semibold">에러:</span> {sttError}
                </div>
              )}
            </div>
          </div>

          {/* 현재 인식 텍스트 */}
          <div className="mb-4">
            <h3 className="text-sm font-semibold text-muted mb-2">인식된 텍스트</h3>
            <div className="bg-muted/50 rounded p-2 text-sm">
              {transcript || <span className="text-muted italic">인식된 텍스트가 없습니다</span>}
            </div>
            {transcript && (
              <div className="mt-1 text-xs text-muted">
                인식 시간: {formatTime(lastTranscriptTime)} ({getTimeAgo(lastTranscriptTime)})
              </div>
            )}
          </div>

          {/* 대안 텍스트 */}
          {alternatives && alternatives.length > 0 && (
            <div className="mb-4">
              <h3 className="text-sm font-semibold text-muted mb-2">대안 텍스트</h3>
              <div className="space-y-1">
                {alternatives.map((alt, idx) => (
                  <div key={idx} className="bg-muted/30 rounded p-2 text-xs flex justify-between">
                    <span>{alt.transcript}</span>
                    {alt.confidence !== undefined && (
                      <span className="text-muted">{(alt.confidence * 100).toFixed(1)}%</span>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* 이벤트 로그 */}
          <div className="mb-4">
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-sm font-semibold text-muted">이벤트 로그</h3>
              <button
                onClick={() => {
                  logsRef.current = [];
                  setEventLogs([]);
                }}
                className="text-xs text-primary hover:underline"
              >
                초기화
              </button>
            </div>
            <div className="space-y-1 max-h-60 overflow-y-auto">
              {eventLogs.length === 0 ? (
                <div className="text-xs text-muted italic">이벤트가 없습니다</div>
              ) : (
                eventLogs.map((log, idx) => (
                  <div
                    key={idx}
                    className="bg-muted/20 rounded p-2 text-xs font-mono border-l-2 border-primary"
                  >
                    <div className="flex justify-between items-start mb-1">
                      <span className="font-semibold text-primary">{log.type}</span>
                      <span className="text-muted text-[10px]">{formatTime(log.timestamp)}</span>
                    </div>
                    <pre className="text-[10px] overflow-x-auto whitespace-pre-wrap break-words">
                      {JSON.stringify(log.detail, null, 2)}
                    </pre>
                  </div>
                ))
              )}
            </div>
          </div>

          {/* Store 상태 요약 */}
          <div className="mb-4">
            <h3 className="text-sm font-semibold text-muted mb-2">Store 상태</h3>
            <div className="bg-muted/20 rounded p-2 text-xs font-mono space-y-1">
              <div>lastTranscriptText: {lastTranscriptText || '(없음)'}</div>
              <div>lastTranscriptTime: {lastTranscriptTime ? formatTime(lastTranscriptTime) : '(없음)'}</div>
            </div>
          </div>

          {/* 브라우저 지원 확인 */}
          {browserSupport && (
            <div className="mb-4">
              <h3 className="text-sm font-semibold text-muted mb-2">브라우저 지원</h3>
              <div className="space-y-1 text-xs">
                <div className="flex items-center gap-2">
                  <span className={`w-3 h-3 rounded-full ${browserSupport.speechRecognition ? 'bg-green-500' : 'bg-red-500'}`} />
                  <span>Speech Recognition: {browserSupport.speechRecognition ? '지원됨' : '지원 안됨'}</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className={`w-3 h-3 rounded-full ${browserSupport.speechSynthesis ? 'bg-green-500' : 'bg-red-500'}`} />
                  <span>Speech Synthesis: {browserSupport.speechSynthesis ? '지원됨' : '지원 안됨'}</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className={`w-3 h-3 rounded-full ${browserSupport.mediaDevices ? 'bg-green-500' : 'bg-red-500'}`} />
                  <span>Media Devices: {browserSupport.mediaDevices ? '지원됨' : '지원 안됨'}</span>
                </div>
              </div>
            </div>
          )}

          {/* 테스트 버튼 */}
          <div className="mb-4 border-t pt-2">
            <h3 className="text-sm font-semibold text-muted mb-2">테스트</h3>
            <div className="flex gap-2 flex-wrap">
              <button
                onClick={testVoiceRecognition}
                className="px-3 py-1 bg-primary text-white rounded text-xs hover:bg-primary/90"
              >
                음성 인식 테스트
              </button>
              <button
                onClick={testMicMode}
                className="px-3 py-1 bg-accent text-primary rounded text-xs hover:bg-accent/90"
              >
                MicMode 테스트
              </button>
            </div>
          </div>

          {/* 도움말 */}
          <div className="text-xs text-muted border-t pt-2">
            <p className="font-semibold mb-1">사용 방법:</p>
            <ul className="list-disc list-inside space-y-1">
              <li>화면을 길게 눌러 음성 인식 시작</li>
              <li>짧게 탭하여 음성 인식 토글</li>
              <li>인식된 텍스트와 이벤트가 실시간으로 표시됩니다</li>
              <li>테스트 버튼으로 음성 인식 기능을 직접 테스트할 수 있습니다</li>
            </ul>
          </div>
        </div>
      )}
    </>
  );
}

