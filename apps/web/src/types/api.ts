/**
 * 공통 API 타입 정의
 * Facade API들에서 공통으로 사용하는 타입들을 중앙에서 관리
 */

// Exam API Types
export interface Textbook {
  id: number;
  title: string;
  publisher?: string;
  year?: number;
  subject?: string;
}

export interface Unit {
  id: number;
  title: string;
  order: number;
  content: string;
  textbook_id: number;
}

export interface Question {
  id: number;
  question_text: string;
  choice1?: string;
  choice2?: string;
  choice3?: string;
  choice4?: string;
  choice5?: string;
  correct_answer: number;
  explanation?: string;
  difficulty: number;
}

export interface AnswerResult {
  is_correct: boolean;
  correct_answer: number;
  explanation?: string;
}

export interface PassageStructure {
  summary: string;
  characters: string[];
  structure: string;
  keywords: string[];
}

export interface GraphPatterns {
  trend: 'increase' | 'decrease' | 'stable';
  extremum: 'maximum' | 'minimum' | 'none';
  comparison: 'greater' | 'less' | 'equal';
}

export interface TextbookConvertResponse {
  braille_cells: number[][];
  braille_text: string;
  original_text: string;
  text_length: number;
  cells_count: number;
  pages_count: number;
  error?: string;
}

export interface CompressTextResponse {
  compressed_text: string;
  original_length: number;
  compressed_length: number;
  compression_ratio: number;
  mode: string;
  error?: string;
}

export interface SentenceSummaryResponse {
  summary: string;
  original: string;
  error?: string;
}

// Chat API Types
export interface ChatResponse {
  answer: string;
  keywords?: string[];
  ok?: boolean;
  error?: string;
}

export interface ExploreResponse {
  answer: string;
  news: any[];
  query: string;
  ok?: boolean;
  error?: string;
}

// Braille API Types
export interface BrailleConvertResponse {
  cells: number[][];
  ok?: boolean;
  error?: string;
}

// Learn API Types
export interface LearnItem {
  id: number;
  name?: string;
  word?: string;
  sentence?: string;
  char?: string;
  cell?: number[];
  cells?: number[][];
  brailles?: string[];
}

export interface LearnResponse {
  mode?: string;
  title?: string;
  items: LearnItem[];
  ok?: boolean;
}

// Vocab API Types
export interface VocabItem {
  id: number;
  word: string;
  meaning: string;
  example?: string;
  queue_id: number;
}

export interface SisaItem {
  id: number;
  word: string;
  meaning: string;
  example?: string;
}

