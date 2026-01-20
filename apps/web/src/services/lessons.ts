/**
 * 레슨 API 서비스
 */
import { api } from './api';
import type { Lesson } from '../types/lesson';

export const lessonsAPI = {
  /**
   * 레슨 목록 조회
   */
  async list(bookId: string): Promise<Lesson[]> {
    return api.get<Lesson[]>(`/books/${bookId}/lessons`);
  },

  /**
   * 레슨 상세 조회
   */
  async get(lessonId: string): Promise<Lesson> {
    return api.get<Lesson>(`/lessons/${lessonId}`);
  },

  /**
   * 레슨의 강의 대본 조회
   */
  async getScript(lessonId: string) {
    return api.get<{
      lesson_id: string;
      title: string;
      script_text: string;
      estimated_time: number | null;
      key_points: string[];
    }>(`/lessons/${lessonId}/script`);
  },

  /**
   * 레슨 내용 AI 요약
   */
  async getSummary(lessonId: string) {
    return api.get<{
      lesson_id: string;
      summary: string;
      estimated_time: number | null;
    }>(`/lessons/${lessonId}/summary`);
  },
};
