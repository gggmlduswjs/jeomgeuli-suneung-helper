/**
 * Voice service type definitions
 */

/**
 * STT Provider 인터페이스
 */
export interface STTProvider {
  start(): Promise<void>;
  stop(): void;
  isListening(): boolean;
  onResult(callback: (final: boolean, alternatives: Array<{ transcript: string; confidence?: number }>) => void): void;
  onError(callback: (error: { code: string; message?: string }) => void): void;
}

/**
 * STT 시작 옵션
 */
export interface StartSTTOptions {
  onResult?: (text: string, alternatives?: Array<{ transcript: string; confidence: number }>) => void;
  onError?: (error: string) => void;
  autoStop?: boolean; // 결과 수신 후 자동 중지 여부
}

/**
 * TTS Provider 인터페이스
 */
export interface TTSProvider {
  speak(text: string | string[], options?: { rate?: number; pitch?: number; volume?: number; lang?: string }): Promise<void>;
  stop(): void;
  pause(): void;
  resume(): void;
  isSpeaking(): boolean;
}
