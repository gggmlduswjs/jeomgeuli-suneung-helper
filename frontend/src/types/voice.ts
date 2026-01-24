/**
 * voice.ts - 음성 관련 타입 정의
 */

import type { CommandHandlers } from '../lib/voice/CommandRouter';

/**
 * VoiceEventType - 음성 이벤트 타입
 */
export enum VoiceEventType {
  MIC_MODE = 'voice:mic-mode',
  TRANSCRIPT = 'voice:transcript',
  COMMAND = 'voice:command',
  MIC_INTENT = 'voice:mic-intent',
}

/**
 * VoiceEvent - 음성 이벤트 기본 인터페이스
 */
export interface VoiceEvent {
  type: VoiceEventType;
  detail?: Record<string, unknown>;
}

/**
 * MicModeEvent - 마이크 모드 변경 이벤트
 */
export interface MicModeEvent extends VoiceEvent {
  type: VoiceEventType.MIC_MODE;
  detail: {
    active: boolean;
  };
}

/**
 * TranscriptEvent - 음성 인식 결과 이벤트
 */
export interface TranscriptEvent extends VoiceEvent {
  type: VoiceEventType.TRANSCRIPT;
  detail: {
    text: string;
  };
}

/**
 * CommandEvent - 명령 이벤트
 */
export interface CommandEvent extends VoiceEvent {
  type: VoiceEventType.COMMAND;
  detail: {
    type: 'next' | 'prev' | 'repeat' | 'stop' | 'pause' | 'start';
  };
}

/**
 * MicIntentEvent - 마이크 의도 이벤트
 */
export interface MicIntentEvent extends VoiceEvent {
  type: VoiceEventType.MIC_INTENT;
  detail: {
    action: 'start' | 'stop';
  };
}

/**
 * CommandHandler - 명령 핸들러 타입
 */
export type CommandHandler = CommandHandlers[keyof CommandHandlers];

/**
 * STTProvider - STT 프로바이더 인터페이스
 */
export interface STTProvider {
  start(): Promise<void>;
  stop(): void;
  isListening(): boolean;
  onResult(callback: (final: boolean, alternatives: Array<{ transcript: string; confidence?: number }>) => void): void;
  onError(callback: (error: { code: string; message?: string }) => void): void;
}

/**
 * TTSProvider - TTS 프로바이더 인터페이스
 */
export interface TTSProvider {
  speak(text: string | string[], options?: TTSOptions): Promise<void>;
  stop(): void;
  pause(): void;
  resume(): void;
  isSpeaking(): boolean;
}

/**
 * TTSOptions - TTS 옵션
 */
export interface TTSOptions {
  rate?: number;
  pitch?: number;
  volume?: number;
  lang?: string;
  voiceName?: string;
  allowDuringMic?: boolean;
}

/**
 * STTAlternative - STT 대안 결과
 */
export interface STTAlternative {
  transcript: string;
  confidence: number;
}

/**
 * VoiceState - 음성 상태
 */
export interface VoiceState {
  isListening: boolean;
  transcript: string;
  alternatives: STTAlternative[];
  sttError: string | null;
  isSpeaking: boolean;
  isPaused: boolean;
  ttsError: string | null;
  micMode: boolean;
  lastTranscriptTime: number;
  lastTranscriptText: string;
}



