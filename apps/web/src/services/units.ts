/**
 * 학습 단위 API 서비스
 */
import { api } from './api';
import type { Unit } from '../types/unit';

export const unitsAPI = {
  /**
   * 학습 단위 목록 조회
   */
  async list(lessonId: string): Promise<Unit[]> {
    return api.get<Unit[]>(`/lessons/${lessonId}/units`);
  },

  /**
   * 학습 단위 상세 조회
   */
  async get(unitId: string): Promise<Unit> {
    return api.get<Unit>(`/units/${unitId}`);
  },
};
