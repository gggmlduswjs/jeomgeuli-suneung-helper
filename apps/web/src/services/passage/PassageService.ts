/**
 * 지문 관련 서비스
 * 지문 분석 및 구조 파악 관련 비즈니스 로직
 */
import { examAPI, type PassageStructure } from '../../lib/api/exam';

export class PassageService {
  /**
   * 지문 분석
   */
  static async analyzePassage(passage: string): Promise<PassageStructure | null> {
    try {
      return await examAPI.analyzePassage(passage);
    } catch (error) {
      console.error('[PassageService] analyzePassage error:', error);
      throw error;
    }
  }
}

