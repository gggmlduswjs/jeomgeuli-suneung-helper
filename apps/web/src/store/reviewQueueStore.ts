/**
 * 복습 큐 상태 관리 Store
 */
import { create } from 'zustand';
import type { ReviewQueueItem } from '../types/review';

interface ReviewQueueState {
  queue: ReviewQueueItem[];
  completedItems: Set<string>; // unit_id Set
  setQueue: (queue: ReviewQueueItem[]) => void;
  addToQueue: (item: ReviewQueueItem) => void;
  markCompleted: (unitId: string) => void;
  clearCompleted: () => void;
}

export const useReviewQueueStore = create<ReviewQueueState>((set) => ({
  queue: [],
  completedItems: new Set(),
  setQueue: (queue) => set({ queue }),
  addToQueue: (item) =>
    set((state) => ({
      queue: [...state.queue, item],
    })),
  markCompleted: (unitId) =>
    set((state) => ({
      completedItems: new Set([...state.completedItems, unitId]),
      queue: state.queue.filter((item) => item.unit_id !== unitId),
    })),
  clearCompleted: () => set({ completedItems: new Set() }),
}));
