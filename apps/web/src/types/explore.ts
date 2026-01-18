// 정보탐색 모드 타입 정의

export interface SummarizeResult {
  bullets: string[];   // 최대 5
  keywords: string[];  // 최대 3
  longText: string;    // 자세히 설명
  source?: 'news' | 'weather' | 'generic';
}

export type Intent = 'weather' | 'news' | 'detail' | 'braille' | 'next' | 'repeat' | 'stop' | 'generic';

export interface Message {
  id: string;
  type: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  isSummary?: boolean;
  summaryData?: SummarizeResult;
}

export interface WeatherItem {
  location: string;
  temp: number;
  condition: string;
  windspeed: number;
  time: string;
}

export interface NewsItem {
  title: string;
  desc: string;
  link: string;
  date: string;
}

export interface BrailleBLEHook {
  connect: () => Promise<void>;
  disconnect: () => Promise<void>;
  writePattern: (text: string) => Promise<void>;
  isConnected: boolean;
}

export interface TTSEvent {
  isSpeaking: boolean;
  isPaused: boolean;
  currentText?: string;
}

export interface STTEvent {
  isListening: boolean;
  transcript?: string;
  confidence?: number;
}

