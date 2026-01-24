/**
 * 커리큘럼 관련 타입 정의
 */
export enum CurriculumStatus {
  PENDING = "PENDING",
  GENERATING = "GENERATING",
  DONE = "DONE",
  FAILED = "FAILED",
}

export enum Subject {
  KOREAN = "KOREAN",
  ENGLISH = "ENGLISH",
  MATH = "MATH",
}

export interface LearningUnit {
  unit_id: string;
  curriculum_id: string;
  lesson_id?: string;
  section_type: string;
  content: string;
  order: number;
  break_points?: string;
  pdf_references?: string;
  created_at: string;
}

export interface LessonInfo {
  lesson_number: number;
  title: string;
  learning_units: unknown[];
  sections: unknown[];
  pdf_references: unknown[];
  dependencies: number[];
  estimated_time: number;
}

export interface LearningPathItem {
  lesson: number;
  order: number;
  title: string;
}

export interface ConnectionInfo {
  from_lesson: number;
  to_lesson: number;
  type: string;
  keywords: string[];
}

export interface Curriculum {
  curriculum_id: string;
  book_id?: string;
  subject: Subject;
  title: string;
  status: CurriculumStatus;
  lesson_count: number;
  created_at: string;
  updated_at: string;
}

export interface CurriculumDetail extends Curriculum {
  lessons: LessonInfo[];
  learning_path: LearningPathItem[];
  connections: ConnectionInfo[];
  total_lessons: number;
  total_units: number;
}

/**
 * 커리큘럼 생성 타입 (관리자용)
 * 사용자는 커리큘럼을 생성하지 않음. 관리자가 백엔드에서 처리
 */
export interface CurriculumCreate {
  subject: Subject;
  title: string;
  book_id?: string;
}
