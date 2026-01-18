/**
 * 복습 API 서비스
 */
import { api } from './api';
import type { ReviewQueueItem, ReviewComplete } from '../types/review';

export const reviewAPI = {
  /**
   * 복습 큐 조회
   */
  async getQueue(userId: string, bookId?: string): Promise<ReviewQueueItem[]> {
    const params = new URLSearchParams({ user_id: userId });
    if (bookId) {
      params.append('book_id', bookId);
    }
    return api.get<ReviewQueueItem[]>(`/review/queue?${params.toString()}`);
  },

  /**
   * 복습 완료
   */
  async complete(data: ReviewComplete): Promise<{ ok: boolean }> {
    return api.post<{ ok: boolean }>('/review/complete', data);
  },
};
