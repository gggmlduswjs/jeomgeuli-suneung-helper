// 통합 타입 정의 파일

// API 응답 타입
export interface ApiResponse {
  answer?: string;
  chat_markdown?: string;
  keywords?: string[];
  braille_words?: string[];
  mode?: string;
  actions?: Record<string, any>;
  meta?: Record<string, any>;
  error?: string;
  news?: any[];
  query?: string;
  ok?: boolean;
  data?: any;
}

// 점자 관련 타입
export type Cell = [0 | 1, 0 | 1, 0 | 1, 0 | 1, 0 | 1, 0 | 1];
export type Cells = Cell[];
export type DotArray = boolean[];

// 학습 관련 타입
export interface LessonItem {
  char?: string;
  word?: string;
  sentence?: string;
  name?: string;
  cells?: Cells;
  brailles?: Cells;
  examples?: string[];
  tts?: string | string[];
  ttsIntro?: string;
  decomposeTTS?: string[];
  text?: string;
  desc?: string;
  hint?: string;
  cell?: Cell;
}

export interface LearnList {
  items: LessonItem[];
}

// 채팅 관련 타입
export type Role = 'user' | 'assistant' | 'system';
export type ChatMode = 'qa' | 'news' | 'explain';

export interface ChatMessage {
  id: string;
  role: Role;
  type: 'text' | 'card';
  text?: string;
  payload?: any;
  keywords?: string[]; // 메시지별 키워드 추가
  createdAt: number;
}

// TTS 관련 타입
export interface TTSOptions {
  rate?: number;
  pitch?: number;
  volume?: number;
  lang?: string;
  voiceName?: string;
}

export interface TTSHookReturn {
  speak: (text: string | string[], options?: TTSOptions) => Promise<void>;
  stop: () => void;
  pause: () => void;
  resume: () => void;
  isSpeaking: boolean;
  isPaused: boolean;
  isSupported: boolean;
  isLoading: boolean;
  error: string | null;
}

// 점자 재생 관련 타입
export interface UseBraillePlaybackOptions {
  ble?: {
    serviceUUID: string;
    characteristicUUID: string;
    maxPacketSize?: number;
  } | null;
  delayMs?: number;
  previewMode?: 'local' | 'none';
  onEnd?: () => void;
  onBeforePlay?: (word: string, index: number) => void;
  onAfterPlay?: (word: string, index: number) => void;
}

// API 요청 타입
export interface AskAIParams {
  q: string;
  mode?: string;
  topic?: string;
}

export interface EnqueuePayload {
  text?: string;
  braille?: unknown;
  segments?: unknown;
}

export interface BrailleConvertResult {
  ok?: boolean;
  cells?: unknown;
  error?: string;
}

// 학습 모드 타입
export type LearnMode = "char" | "word" | "sentence" | "keyword";
