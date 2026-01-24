/**
 * Template Method Pattern - Textbook Learning Flow
 * 교재 학습 플로우 구현
 */
import { LearningFlow, LearningFlowState } from './LearningFlow';
import { examAPI, type Unit } from '../../lib/api';

export class TextbookLearningFlow extends LearningFlow {
  private textbookId: number | null = null;
  private units: Unit[] = [];
  private currentUnit: Unit | null = null;

  constructor(textbookId: number) {
    super(0);
    this.textbookId = textbookId;
  }

  protected async initialize(): Promise<void> {
    if (!this.textbookId) {
      throw new Error('Textbook ID is required');
    }
  }

  protected async loadContent(): Promise<void> {
    if (!this.textbookId) return;

    const units = await examAPI.listUnits(this.textbookId);
    this.units = units;
    this.state.totalItems = units.length;

    if (units.length > 0) {
      await this.loadCurrentItem();
    }
  }

  protected async loadCurrentItem(): Promise<void> {
    if (this.state.currentIndex < 0 || this.state.currentIndex >= this.units.length) {
      return;
    }

    const unitId = this.units[this.state.currentIndex].id;
    const unit = await examAPI.getUnit(unitId);
    this.currentUnit = unit;
  }

  protected async onComplete(): Promise<void> {
    // 학습 완료 로직 (예: 진행 상황 저장)
    console.log('[TextbookLearningFlow] 학습 완료');
  }

  /**
   * 현재 단원 조회
   */
  getCurrentUnit(): Unit | null {
    return this.currentUnit;
  }

  /**
   * 단원 목록 조회
   */
  getUnits(): Unit[] {
    return this.units;
  }
}


