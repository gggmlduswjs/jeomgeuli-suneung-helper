/**
 * 알림 포인트 API 서비스
 */
import { api } from './api';
import type { Syncpoint, SyncLogCreate } from '../types/syncpoint';

export const syncpointsAPI = {
  /**
   * 알림 포인트 목록 조회
   */
  async list(lessonId: string): Promise<Syncpoint[]> {
    return api.get<Syncpoint[]>(`/lessons/${lessonId}/syncpoints`);
  },

  /**
   * 알림 로그 전송
   */
  async log(data: SyncLogCreate): Promise<{ ok: boolean }> {
    return api.post<{ ok: boolean }>('/syncpoints/log', data);
  },
};
