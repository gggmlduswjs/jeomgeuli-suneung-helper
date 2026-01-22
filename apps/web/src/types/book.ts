/**
 * 교재 관련 타입 정의
 */
export enum ParseStatus {
  PENDING = "PENDING",
  PROCESSING = "PROCESSING",
  DONE = "DONE",
  FAILED = "FAILED",
}

export enum Subject {
  KOREAN = "KOREAN",
  ENGLISH = "ENGLISH",
  MATH = "MATH",
}

export interface Book {
  book_id: string;
  title: string;
  subject: Subject;
  year?: number;
  parse_status: ParseStatus;
  lesson_count?: number;
}

export interface BookCreate {
  title: string;
  subject: Subject;
  year?: number;
}

export interface BookParseStatus {
  book_id: string;
  status: ParseStatus;
  progress: number;
}

/**
 * AI 처리 옵션
 */
export interface AIProcessingOptions {
  // Level 1: ML
  enable_ml_deduplication?: boolean;
  enable_ml_classification?: boolean;

  // Level 2: DL
  enable_layout_analysis?: boolean;
  enable_math_recognition?: boolean;

  // Level 3: LLM
  enable_llm_metadata?: boolean;
  enable_llm_explanations?: boolean;
  enable_llm_recommendations?: boolean;
  openai_api_key?: string;
  education_level?: 'elementary' | 'middle' | 'high' | 'university';
}

/**
 * AI 처리 통계
 */
export interface AIProcessingStats {
  // ML stats
  ml_deduplication_count?: number;
  ml_classification_count?: number;

  // DL stats
  dl_layout_blocks?: number;
  dl_math_expressions?: number;

  // LLM stats
  llm_metadata_enriched?: number;
  llm_explanations_generated?: number;
  llm_recommendations_built?: boolean;
  llm_api_calls?: number;

  // Processing time
  total_processing_time_ms?: number;
}

/**
 * LLM 메타데이터
 */
export interface LLMMetadata {
  tags: string[];
  keywords: string[];
  difficulty: string;
  learning_objectives: string[];
  subject_area: string;
  estimated_time_minutes: number;
  enrichment_confidence?: number;
}

/**
 * 개념 설명
 */
export interface ConceptExplanation {
  explanation: string;
  examples: string[];
  key_points: string[];
}

/**
 * 유사 콘텐츠 추천
 */
export interface SimilarContent {
  text: string;
  metadata: Record<string, any>;
  score: number;
}

/**
 * AI enriched Book (확장)
 */
export interface BookWithAI extends Book {
  ai_options?: AIProcessingOptions;
  ai_stats?: AIProcessingStats;
}
