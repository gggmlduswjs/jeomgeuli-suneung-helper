/**
 * Template Method Pattern - Learning Flow
 * 학습 플로우의 템플릿 메서드 패턴 구현
 */
import { EventType } from '../../lib/events/EventTypes';
import getEventBus from '../../lib/events/EventBus';

export interface LearningFlowState {
  currentIndex: number;
  totalItems: number;
  isCompleted: boolean;
  startTime: number;
  endTime?: number;
}

export abstract class LearningFlow {
  protected state: LearningFlowState;

  constructor(totalItems: number = 0) {
    this.state = {
      currentIndex: 0,
      totalItems,
      isCompleted: false,
      startTime: Date.now(),
    };
  }

  /**
   * 템플릿 메서드: 학습 플로우 실행
   */
  async start(): Promise<void> {
    this.onStart();
    await this.initialize();
    await this.loadContent();
    this.onReady();
  }

  /**
   * 다음 항목으로 이동
   */
  async next(): Promise<boolean> {
    if (this.state.currentIndex >= this.state.totalItems - 1) {
      return await this.complete();
    }

    this.state.currentIndex++;
    await this.loadCurrentItem();
    this.onItemChanged();
    return true;
  }

  /**
   * 이전 항목으로 이동
   */
  async prev(): Promise<boolean> {
    if (this.state.currentIndex <= 0) {
      return false;
    }

    this.state.currentIndex--;
    await this.loadCurrentItem();
    this.onItemChanged();
    return true;
  }

  /**
   * 학습 완료
   */
  async complete(): Promise<boolean> {
    this.state.isCompleted = true;
    this.state.endTime = Date.now();
    await this.onComplete();
    this.onFinished();
    return true;
  }

  /**
   * 현재 진행 상황 조회
   */
  getProgress(): { current: number; total: number; percentage: number } {
    return {
      current: this.state.currentIndex + 1,
      total: this.state.totalItems,
      percentage: this.state.totalItems > 0
        ? Math.round(((this.state.currentIndex + 1) / this.state.totalItems) * 100)
        : 0,
    };
  }

  // 추상 메서드: 하위 클래스에서 구현
  protected abstract initialize(): Promise<void>;
  protected abstract loadContent(): Promise<void>;
  protected abstract loadCurrentItem(): Promise<void>;
  protected abstract onComplete(): Promise<void>;

  // 훅 메서드: 하위 클래스에서 선택적으로 오버라이드
  protected onStart(): void {
    getEventBus().publish(EventType.PAGE_LOADED, { type: 'learning' });
  }

  protected onReady(): void {
    // 기본 구현: 빈 메서드
  }

  protected onItemChanged(): void {
    getEventBus().publish(EventType.NAVIGATION_CHANGED, {
      index: this.state.currentIndex,
      total: this.state.totalItems,
    });
  }

  protected onFinished(): void {
    getEventBus().publish(EventType.UNIT_COMPLETED, {
      duration: this.state.endTime! - this.state.startTime,
      totalItems: this.state.totalItems,
    });
  }
}


