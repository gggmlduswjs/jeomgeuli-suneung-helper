/**
 * 진도 API 서비스
 */
import { api } from './api';
import type { Progress, ProgressCreate } from '../types/progress';

export const progressAPI = {
  /**
   * 진도 저장
   */
  async save(data: ProgressCreate): Promise<{ ok: boolean }> {
    return api.post<{ ok: boolean }>('/progress', data);
  },

  /**
   * 이어하기 (현재 학습 위치 조회)
   */
  async getContinue(userId: string): Promise<Progress> {
    return api.get<Progress>(`/progress/continue?user_id=${userId}`);
  },
};
