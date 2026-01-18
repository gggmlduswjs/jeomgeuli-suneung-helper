/**
 * 알림 포인트 관련 타입 정의
 */
export interface Syncpoint {
  syncpoint_id: string;
  timestamp_sec: number;
  hint_type?: string;
  unit_id?: string;
}

export interface SyncLogCreate {
  user_id: string;
  lesson_id?: string;
  syncpoint_id?: string;
  event: string;
}
