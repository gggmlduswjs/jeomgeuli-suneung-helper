/**
 * Template Method Pattern - LearningFlow Tests
 */
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { LearningFlow } from '../LearningFlow';
import { EventType } from '../../../lib/events/EventTypes';
import getEventBus from '../../../lib/events/EventBus';

// Mock LearningFlow 구현
class TestLearningFlow extends LearningFlow {
  private items: string[] = [];
  private currentItem: string | null = null;

  constructor(items: string[]) {
    super(items.length);
    this.items = items;
  }

  protected async initialize(): Promise<void> {
    // 초기화 로직
  }

  protected async loadContent(): Promise<void> {
    // 콘텐츠 로드
  }

  protected async loadCurrentItem(): Promise<void> {
    if (this.state.currentIndex >= 0 && this.state.currentIndex < this.items.length) {
      this.currentItem = this.items[this.state.currentIndex];
    }
  }

  protected async onComplete(): Promise<void> {
    // 완료 로직
  }

  getCurrentItem(): string | null {
    return this.currentItem;
  }
}

describe('LearningFlow', () => {
  let flow: TestLearningFlow;

  beforeEach(() => {
    vi.clearAllMocks();
    flow = new TestLearningFlow(['item1', 'item2', 'item3']);
  });

  it('should initialize with correct state', () => {
    const progress = flow.getProgress();
    expect(progress.total).toBe(3);
    expect(progress.current).toBe(1);
  });

  it('should move to next item', async () => {
    await flow.start();
    const result = await flow.next();

    expect(result).toBe(true);
    const progress = flow.getProgress();
    expect(progress.current).toBe(2);
  });

  it('should move to previous item', async () => {
    await flow.start();
    await flow.next();
    const result = await flow.prev();

    expect(result).toBe(true);
    const progress = flow.getProgress();
    expect(progress.current).toBe(1);
  });

  it('should not move previous at first item', async () => {
    await flow.start();
    const result = await flow.prev();

    expect(result).toBe(false);
  });

  it('should complete when reaching end', async () => {
    await flow.start();
    await flow.next();
    await flow.next();
    const result = await flow.next();

    expect(result).toBe(true);
    const progress = flow.getProgress();
    expect(progress.percentage).toBe(100);
  });

  it('should calculate progress percentage', () => {
    const progress = flow.getProgress();
    expect(progress.percentage).toBeGreaterThanOrEqual(0);
    expect(progress.percentage).toBeLessThanOrEqual(100);
  });
});


