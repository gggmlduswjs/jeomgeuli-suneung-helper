/**
 * 강(단원) 관련 타입 정의
 */
export interface Lesson {
  lesson_id: string;
  book_id: string;
  index: number;
  title: string;
  unit_count?: number;
  question_count?: number;
}
