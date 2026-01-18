/**
 * 교재 관련 서비스
 * 교재 및 단원 관련 비즈니스 로직
 */
import { examAPI, type Textbook, type Unit } from '../../lib/api/exam';

export class TextbookService {
  /**
   * 교재 목록 조회
   */
  static async loadTextbooks(): Promise<Textbook[]> {
    try {
      return await examAPI.listTextbooks();
    } catch (error) {
      console.error('[TextbookService] loadTextbooks error:', error);
      throw error;
    }
  }
  
  /**
   * 단원 목록 조회
   */
  static async loadUnits(textbookId: number): Promise<Unit[]> {
    try {
      return await examAPI.listUnits(textbookId);
    } catch (error) {
      console.error('[TextbookService] loadUnits error:', error);
      throw error;
    }
  }
  
  /**
   * 단원 상세 조회
   */
  static async loadUnit(unitId: number): Promise<Unit | null> {
    try {
      return await examAPI.getUnit(unitId);
    } catch (error) {
      console.error('[TextbookService] loadUnit error:', error);
      throw error;
    }
  }
}

