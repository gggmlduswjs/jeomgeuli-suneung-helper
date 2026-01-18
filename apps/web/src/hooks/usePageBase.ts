/**
 * 페이지 컴포넌트 공통 로직 훅
 * TTS/STT, Toast, 음성 명령 등 공통 기능을 통합
 */
import { useState, useEffect } from 'react';
import useTTS from './useTTS';
import useSTT from './useSTT';
import useVoiceCommands, { type CommandHandlers } from './useVoiceCommands';

export interface UsePageBaseOptions {
  /** 자동 안내 메시지 (페이지 진입 시 TTS로 재생) */
  autoAnnounce?: string;
  /** 음성 명령 핸들러 */
  voiceCommands?: CommandHandlers;
  /** SpeechBar 표시 여부 */
  showSpeechBar?: boolean;
}

export interface UsePageBaseReturn {
  // TTS
  speak: (text: string) => void;
  stopTTS: () => void;
  
  // STT
  startSTT: () => void;
  stopSTT: () => void;
  isListening: boolean;
  transcript: string;
  
  // Toast
  showToast: boolean;
  toastMessage: string;
  setShowToast: (show: boolean) => void;
  setToastMessage: (message: string) => void;
  showToastMessage: (message: string) => void;
  
  // Voice Commands
  onSpeech: (text: string) => boolean;
}

/**
 * 페이지 컴포넌트 공통 로직 훅
 */
export function usePageBase(options: UsePageBaseOptions = {}): UsePageBaseReturn {
  const { autoAnnounce, voiceCommands = {}, showSpeechBar = true } = options;
  
  // TTS/STT 훅
  const { speak, stop: stopTTS } = useTTS();
  const { start: startSTT, stop: stopSTT, isListening, transcript } = useSTT();
  
  // Toast 상태
  const [showToast, setShowToast] = useState(false);
  const [toastMessage, setToastMessage] = useState('');
  
  // 음성 명령 처리
  const { onSpeech } = useVoiceCommands(voiceCommands);
  
  // 자동 안내 메시지 (페이지 진입 시)
  useEffect(() => {
    if (autoAnnounce) {
      const timer = setTimeout(() => {
        speak(autoAnnounce);
      }, 500);
      return () => clearTimeout(timer);
    }
  }, [speak, autoAnnounce]);
  
  // 음성 명령 처리 (transcript 변경 시)
  useEffect(() => {
    if (!transcript) return;
    onSpeech(transcript);
  }, [transcript, onSpeech]);
  
  // Toast 메시지 표시 헬퍼
  const showToastMessage = (message: string) => {
    setToastMessage(message);
    setShowToast(true);
  };
  
  return {
    speak,
    stopTTS,
    startSTT,
    stopSTT,
    isListening,
    transcript,
    showToast,
    toastMessage,
    setShowToast,
    setToastMessage,
    showToastMessage,
    onSpeech,
  };
}

