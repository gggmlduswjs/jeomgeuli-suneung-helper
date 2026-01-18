/**
 * 강 API 서비스
 */
import { api } from './api';
import type { Lesson } from '../types/lesson';

export const lessonsAPI = {
  /**
   * 강 목록 조회
   */
  async list(bookId: string): Promise<Lesson[]> {
    return api.get<Lesson[]>(`/books/${bookId}/lessons`);
  },

  /**
   * 강 상세 조회
   */
  async get(lessonId: string): Promise<Lesson> {
    return api.get<Lesson>(`/lessons/${lessonId}`);
  },
};
