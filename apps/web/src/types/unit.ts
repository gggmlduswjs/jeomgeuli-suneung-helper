/**
 * 학습 단위 관련 타입 정의
 */
export enum UnitType {
  CONCEPT_CORE = "CONCEPT_CORE",
  CONCEPT_FORM = "CONCEPT_FORM",
  CONCEPT_CONTENT = "CONCEPT_CONTENT",
  CONCEPT_SUMMARY = "CONCEPT_SUMMARY",  // 단원 요약
  PASSAGE = "PASSAGE",  // 본문/지문
  QUESTION = "QUESTION",
}

export interface UnitQuestion {
  stem: string;
  choices: string[];
  answer?: number;
}

export interface Unit {
  unit_id: string;
  lesson_id: string;
  type: UnitType;
  title: string;
  order: number;
  content_text?: string;
  braille_text?: string;
  image_path?: string;  // 단일 이미지 경로 (하위호환)
  content_image_paths?: string[];  // 여러 이미지 경로 (JSON 배열)
  ai_explanation?: string;  // AI 튜터 설명
  braille_keywords?: string[];  // 점자 키워드 (JSON 배열)
  question?: UnitQuestion;
}
