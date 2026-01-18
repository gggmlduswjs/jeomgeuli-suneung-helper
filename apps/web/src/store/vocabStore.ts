import { create } from 'zustand';

interface VocabState {
  // Today's vocab queue
  todayVocab: any[];
  currentVocabIndex: number;
  
  // Sisa words
  todaySisa: any[];
  currentSisaIndex: number;
  
  // Progress
  learnedToday: number;
  totalLearned: number;
  
  // Actions
  setTodayVocab: (vocab: any[]) => void;
  setTodaySisa: (sisa: any[]) => void;
  nextVocab: () => void;
  prevVocab: () => void;
  nextSisa: () => void;
  prevSisa: () => void;
  markLearned: () => void;
  resetProgress: () => void;
}

export const useVocabStore = create<VocabState>((set, get) => ({
  // Initial state
  todayVocab: [],
  currentVocabIndex: 0,
  todaySisa: [],
  currentSisaIndex: 0,
  learnedToday: 0,
  totalLearned: 0,
  
  // Actions
  setTodayVocab: (vocab) => set({
    todayVocab: vocab,
    currentVocabIndex: 0,
  }),
  
  setTodaySisa: (sisa) => set({
    todaySisa: sisa,
    currentSisaIndex: 0,
  }),
  
  nextVocab: () => set((state) => ({
    currentVocabIndex: Math.min(state.currentVocabIndex + 1, state.todayVocab.length - 1)
  })),
  
  prevVocab: () => set((state) => ({
    currentVocabIndex: Math.max(state.currentVocabIndex - 1, 0)
  })),
  
  nextSisa: () => set((state) => ({
    currentSisaIndex: Math.min(state.currentSisaIndex + 1, state.todaySisa.length - 1)
  })),
  
  prevSisa: () => set((state) => ({
    currentSisaIndex: Math.max(state.currentSisaIndex - 1, 0)
  })),
  
  markLearned: () => set((state) => ({
    learnedToday: state.learnedToday + 1,
    totalLearned: state.totalLearned + 1,
  })),
  
  resetProgress: () => set({
    learnedToday: 0,
  }),
}));

