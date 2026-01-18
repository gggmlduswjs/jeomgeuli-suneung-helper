import { useCallback, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import VoiceService from '../services/VoiceService';
import CommandService from '../services/CommandService';
import { useVoiceStore } from '../store/voice';
import type { CommandHandlers } from '../lib/voice/CommandRouter';
import VoiceEventBus, { VoiceEventType } from '../lib/voice/VoiceEventBus';

export interface UseVoiceControlOptions {
  handlers?: CommandHandlers;
  onTranscript?: (text: string) => void;
}

export interface UseVoiceControlReturn {
  startSTT: () => Promise<void>;
  stopSTT: () => void;
  speak: (text: string | string[], options?: { rate?: number; pitch?: number; volume?: number; lang?: string; allowDuringMic?: boolean }) => Promise<void>;
  stopTTS: () => void;
  isListening: boolean;
  transcript: string;
  alternatives: Array<{ transcript: string; confidence: number }>;
  isSpeaking: boolean;
}

/**
 * useVoiceControl - 음성 제어 통합 훅
 * VoiceService와 CommandService를 통합하여 음성 제어 기능을 제공합니다.
 */
export function useVoiceControl(options: UseVoiceControlOptions = {}): UseVoiceControlReturn {
  const { handlers = {}, onTranscript } = options;
  const navigate = useNavigate();
  const location = useLocation();
  
  const isListening = useVoiceStore(store => store.isListening);
  const transcript = useVoiceStore(store => store.transcript);
  const alternatives = useVoiceStore(store => store.alternatives);
  const isSpeaking = useVoiceStore(store => store.isSpeaking);

  const startSTT = useCallback(async () => {
    try {
      await VoiceService.startSTT();
    } catch (error) {
      console.error('[useVoiceControl] STT 시작 실패:', error);
    }
  }, []);

  const stopSTT = useCallback(() => {
    VoiceService.stopSTT();
  }, []);

  const speak = useCallback(async (text: string | string[], options?: { rate?: number; pitch?: number; volume?: number; lang?: string; allowDuringMic?: boolean }) => {
    try {
      await VoiceService.speak(text, options);
    } catch (error) {
      console.error('[useVoiceControl] TTS 재생 실패:', error);
    }
  }, []);

  const stopTTS = useCallback(() => {
    VoiceService.stopTTS();
  }, []);

  // 음성 명령 처리
  useEffect(() => {
    if (!transcript) return;

    // CommandService를 통한 명령 처리
    const handled = CommandService.processCommand(transcript, handlers);
    
    if (!handled && alternatives.length > 0) {
      // 대안 시도
      const handledAlt = CommandService.processCommandWithAlternatives(alternatives, handlers);
      if (handledAlt) return;
    }

    if (!handled) {
      // 명령이 매칭되지 않으면 onTranscript 콜백 호출
      onTranscript?.(transcript);
    }
  }, [transcript, alternatives, handlers, onTranscript]);

  // 전역 명령 이벤트 처리
  useEffect(() => {
    const unsubscribe = VoiceEventBus.on(VoiceEventType.COMMAND, (event) => {
      const detail = event.detail as { type?: string };
      const commandType = detail?.type;
      
      if (commandType && handlers[commandType as keyof CommandHandlers]) {
        const handler = handlers[commandType as keyof CommandHandlers];
        handler?.();
      }
    });

    return () => {
      unsubscribe();
    };
  }, [handlers]);

  return {
    startSTT,
    stopSTT,
    speak,
    stopTTS,
    isListening,
    transcript,
    alternatives,
    isSpeaking,
  };
}



