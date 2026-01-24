/**
 * Web Speech API 기반 TTS Provider
 */
import { useVoiceStore } from '../../../store/voice';
import micMode from '../../../lib/voice/MicMode';
import type { TTSProvider } from '../types';

/**
 * Web Speech API 기반 TTS Provider 생성
 */
export function createWebSpeechTTSProvider(): TTSProvider {
  if (typeof window === 'undefined' || !('speechSynthesis' in window)) {
    throw new Error('브라우저가 음성 합성을 지원하지 않습니다.');
  }

  let utteranceQueue: string[] = [];
  let isProcessing = false;
  let isSpeaking = false;
  let isPaused = false;

  const processQueue = async (options: { rate?: number; pitch?: number; volume?: number; lang?: string } = {}) => {
    if (isProcessing || !utteranceQueue.length) return;

    isProcessing = true;
    const text = utteranceQueue.shift()!;
    const utt = new SpeechSynthesisUtterance(text);

    utt.rate = options.rate ?? 0.9;
    utt.pitch = options.pitch ?? 1.0;
    utt.volume = options.volume ?? 1.0;
    utt.lang = options.lang || 'ko-KR';

    utt.onstart = () => {
      // Track current utteranceutt;
      isSpeaking = true;
      isPaused = false;
      useVoiceStore.getState().setSpeaking(true);
    };

    utt.onend = () => {
      // Track current utterancenull;
      isSpeaking = false;
      isPaused = false;
      isProcessing = false;
      useVoiceStore.getState().setSpeaking(false);

      if (utteranceQueue.length) {
        setTimeout(() => processQueue(options), 60);
      }
    };

    utt.onerror = () => {
      // Track current utterancenull;
      isSpeaking = false;
      isPaused = false;
      isProcessing = false;
      useVoiceStore.getState().setSpeaking(false);

      if (utteranceQueue.length) {
        setTimeout(() => processQueue(options), 60);
      }
    };

    try {
      window.speechSynthesis.speak(utt);
    } catch (error) {
      isProcessing = false;
      // Track current utterancenull;
      if (utteranceQueue.length) {
        setTimeout(() => processQueue(options), 60);
      }
    }
  };

  return {
    speak: async (text: string | string[], options = {}) => {
      // Mic Mode 체크
      if (micMode.isActive() && !(options as any)?.allowDuringMic) {
        return;
      }

      const texts = (Array.isArray(text) ? text : [text])
        .map(t => String(t ?? '').trim())
        .filter(Boolean);

      if (!texts.length) return;

      // 기존 재생 정리
      try {
        window.speechSynthesis.cancel();
      } catch {}

      utteranceQueue = texts;
      useVoiceStore.getState().setTTSError(null);
      processQueue(options);
    },

    stop: () => {
      try {
        window.speechSynthesis.cancel();
      } catch {}
      utteranceQueue = [];
      // Track current utterancenull;
      isProcessing = false;
      isSpeaking = false;
      isPaused = false;
      useVoiceStore.getState().setSpeaking(false);
    },

    pause: () => {
      if (!isSpeaking || isPaused) return;
      try {
        window.speechSynthesis.pause();
        isPaused = true;
        useVoiceStore.getState().setPaused(true);
      } catch {}
    },

    resume: () => {
      if (!isSpeaking || !isPaused) return;
      try {
        window.speechSynthesis.resume();
        isPaused = false;
        useVoiceStore.getState().setPaused(false);
      } catch {}
    },

    isSpeaking: () => isSpeaking,
  };
}
