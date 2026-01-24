/**
 * 진도 상태 관리 Store
 */
import { create } from 'zustand';
import type { Progress, ProgressCreate } from '../types/progress';
import { progressAPI } from '../services/progress';

interface ProgressState {
  progress: Progress | null;
  setProgress: (progress: Progress | null) => void;
  saveProgress: (data: ProgressCreate) => Promise<void>;
}

export const useProgressStore = create<ProgressState>((set) => ({
  progress: null,
  setProgress: (progress) => set({ progress }),
  saveProgress: async (data) => {
    try {
      await progressAPI.save(data);
      const current = await progressAPI.getContinue(data.user_id);
      set({ progress: current });
    } catch (error) {
      console.error('[progressStore] 진도 저장 실패:', error);
      throw error;
    }
  },
}));
