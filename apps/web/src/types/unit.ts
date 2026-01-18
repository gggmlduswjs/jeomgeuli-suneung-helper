/**
 * 학습 단위 관련 타입 정의
 */
export enum UnitType {
  CONCEPT_CORE = "CONCEPT_CORE",
  CONCEPT_FORM = "CONCEPT_FORM",
  CONCEPT_CONTENT = "CONCEPT_CONTENT",
  PASSAGE = "PASSAGE",
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
  question?: UnitQuestion;
}
