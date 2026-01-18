import { useEffect } from 'react';
import VoiceService from '../services/VoiceService';
import { useVoiceStore } from '../store/voice';

interface STTHookReturn {
  start: () => void;
  stop: () => void;
  isListening: boolean;
  transcript: string;
  error: string | null;
  alternatives?: Array<{ transcript: string; confidence: number }>;
}

/**
 * useSTT - VoiceService를 사용하는 React 훅 래퍼
 * 기존 API를 유지하면서 VoiceService를 단일 소스로 사용합니다.
 */
export function useSTT(): STTHookReturn {
  // Zustand store에서 상태 가져오기
  const isListening = useVoiceStore(state => state.isListening);
  const transcript = useVoiceStore(state => state.transcript);
  const error = useVoiceStore(state => state.sttError);
  const alternatives = useVoiceStore(state => state.alternatives);

  const start = () => {
    VoiceService.startSTT().catch((err) => {
      console.error('[useSTT] STT 시작 실패:', err);
    });
  };

  const stop = () => {
    VoiceService.stopSTT();
  };

  // 언마운트 시 정리
  useEffect(() => {
    return () => {
      // GlobalVoiceRecognition이 마이크를 관리 중이면 cleanup 스킵
      const micMode = useVoiceStore.getState().micMode;
      if (!micMode) {
        VoiceService.stopSTT();
      }
    };
  }, []);

  return {
    start,
    stop,
    isListening,
    transcript,
    error,
    alternatives,
  };
}

export default useSTT;
