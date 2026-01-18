/**
 * 복습 관련 타입 정의
 */
export interface ReviewQueueItem {
  unit_id: string;
  lesson_id?: string;
  reason: string;
  priority: number;
}

export interface ReviewComplete {
  user_id: string;
  unit_id: string;
}
