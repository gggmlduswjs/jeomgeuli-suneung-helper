import { create } from 'zustand';
import VoiceEventBus, { VoiceEventType } from '../lib/voice/VoiceEventBus';
import micMode from '../lib/voice/MicMode';

// 무한 루프 방지를 위한 플래그
let isUpdatingFromEvent = false;

export interface VoiceState {
  // STT 상태
  isListening: boolean;
  transcript: string;
  alternatives: Array<{ transcript: string; confidence: number }>;
  sttError: string | null;
  
  // TTS 상태
  isSpeaking: boolean;
  isPaused: boolean;
  ttsError: string | null;
  
  // 마이크 모드 상태
  micMode: boolean;
  
  // 중복 방지용
  lastTranscriptTime: number;
  lastTranscriptText: string;
  
  // 액션
  setListening: (isListening: boolean) => void;
  setTranscript: (transcript: string, alternatives?: Array<{ transcript: string; confidence: number }>) => void;
  setSTTError: (error: string | null) => void;
  setSpeaking: (isSpeaking: boolean) => void;
  setPaused: (isPaused: boolean) => void;
  setTTSError: (error: string | null) => void;
  setMicMode: (active: boolean) => void;
  toggleMicMode: () => void;
  resetTranscript: () => void;
  resetAll: () => void;
}

export const useVoiceStore = create<VoiceState>((set, get) => ({
  // 초기 상태
  isListening: false,
  transcript: '',
  alternatives: [],
  sttError: null,
  isSpeaking: false,
  isPaused: false,
  ttsError: null,
  micMode: false,
  lastTranscriptTime: 0,
  lastTranscriptText: '',

  // 액션
  setListening: (isListening: boolean) => {
    set({ isListening });
  },

  setTranscript: (transcript: string, alternatives: Array<{ transcript: string; confidence: number }> = []) => {
    const now = Date.now();
    set({
      transcript,
      alternatives,
      lastTranscriptTime: now,
      lastTranscriptText: transcript,
      sttError: null, // 성공 시 에러 초기화
    });
  },

  setSTTError: (error: string | null) => {
    set({ sttError: error, isListening: false });
  },

  setSpeaking: (isSpeaking: boolean) => {
    set({ isSpeaking, isPaused: false });
  },

  setPaused: (isPaused: boolean) => {
    set({ isPaused });
  },

  setTTSError: (error: string | null) => {
    set({ ttsError: error });
  },

  setMicMode: (active: boolean) => {
    const current = get().micMode;
    // 상태가 이미 동일하면 업데이트하지 않음 (무한 루프 방지)
    if (current === active) {
      return;
    }
    set({ micMode: active });
    // 이벤트에서 업데이트 중이 아닐 때만 이벤트 발생 (무한 루프 방지)
    if (!isUpdatingFromEvent) {
      VoiceEventBus.emit({
        type: VoiceEventType.MIC_MODE,
        detail: { active },
      });
    }
  },

  toggleMicMode: () => {
    const current = get().micMode;
    const next = !current;
    get().setMicMode(next);
  },

  resetTranscript: () => {
    set({
      transcript: '',
      alternatives: [],
      sttError: null,
    });
  },

  resetAll: () => {
    set({
      isListening: false,
      transcript: '',
      alternatives: [],
      sttError: null,
      isSpeaking: false,
      isPaused: false,
      ttsError: null,
      lastTranscriptTime: 0,
      lastTranscriptText: '',
    });
  },
}));

// VoiceEventBus와 동기화
VoiceEventBus.on(VoiceEventType.MIC_MODE, (event) => {
  const detail = event.detail as { active?: boolean };
  if (typeof detail?.active === 'boolean') {
    const current = useVoiceStore.getState().micMode;
    // 상태가 이미 동일하면 업데이트하지 않음 (무한 루프 방지)
    if (current !== detail.active) {
      isUpdatingFromEvent = true;
      try {
        useVoiceStore.getState().setMicMode(detail.active);
      } finally {
        isUpdatingFromEvent = false;
      }
    }
  }
});

VoiceEventBus.on(VoiceEventType.TRANSCRIPT, (event) => {
  const detail = event.detail as { text?: string };
  if (detail?.text) {
    useVoiceStore.getState().setTranscript(detail.text);
  }
});

// MicMode 서비스는 이제 Store 래퍼로 동작 (점진적 마이그레이션)
// Store가 단일 소스이므로, MicMode는 Store를 읽기만 함

// 선택자 함수들 (불필요한 리렌더링 방지)
export const selectIsListening = (state: VoiceState) => state.isListening;
export const selectTranscript = (state: VoiceState) => state.transcript;
export const selectAlternatives = (state: VoiceState) => state.alternatives;
export const selectMicMode = (state: VoiceState) => state.micMode;
export const selectIsSpeaking = (state: VoiceState) => state.isSpeaking;

