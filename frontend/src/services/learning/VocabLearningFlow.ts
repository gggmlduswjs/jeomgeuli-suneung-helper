/**
 * Template Method Pattern - Vocab Learning Flow
 * 어휘 학습 플로우 구현
 */
import { LearningFlow } from './LearningFlow';
import { vocabAPI, type VocabItem } from '../../lib/api';

export class VocabLearningFlow extends LearningFlow {
  private vocabItems: VocabItem[] = [];
  private currentItem: VocabItem | null = null;
  private learnedItems: Set<number> = new Set();

  constructor() {
    super(0);
  }

  protected async initialize(): Promise<void> {
    // 초기화 로직
  }

  protected async loadContent(): Promise<void> {
    const data = await vocabAPI.getTodayVocab();
    if (data) {
      this.vocabItems = data.vocab;
      this.state.totalItems = this.vocabItems.length;

      if (this.vocabItems.length > 0) {
        await this.loadCurrentItem();
      }
    }
  }

  protected async loadCurrentItem(): Promise<void> {
    if (this.state.currentIndex < 0 || this.state.currentIndex >= this.vocabItems.length) {
      return;
    }

    this.currentItem = this.vocabItems[this.state.currentIndex];
  }

  protected async onComplete(): Promise<void> {
    // 학습 완료 로직
    console.log('[VocabLearningFlow] 학습 완료');
  }

  /**
   * 현재 어휘 조회
   */
  getCurrentItem(): VocabItem | null {
    return this.currentItem;
  }

  /**
   * 어휘 학습 완료 표시
   */
  async markLearned(grade: number = 3): Promise<boolean> {
    if (!this.currentItem) {
      return false;
    }

    const success = await vocabAPI.markLearned(this.currentItem.queue_id, grade);
    if (success) {
      this.learnedItems.add(this.currentItem.id);
    }
    return success;
  }

  /**
   * 학습 완료된 항목 수
   */
  getLearnedCount(): number {
    return this.learnedItems.size;
  }
}


