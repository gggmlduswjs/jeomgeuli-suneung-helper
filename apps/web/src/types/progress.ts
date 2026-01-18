/**
 * 진도 관련 타입 정의
 */
export interface Progress {
  user_id: string;
  book_id?: string;
  lesson_id?: string;
  unit_id?: string;
  syncpoint_id?: string;
  updated_at?: string;
}

export interface ProgressCreate {
  user_id: string;
  book_id?: string;
  lesson_id?: string;
  unit_id?: string;
  syncpoint_id?: string;
}
