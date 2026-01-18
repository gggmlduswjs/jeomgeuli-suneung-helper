import { create } from 'zustand';

interface LearnState {
  // Textbook state
  currentTextbook: string | null;
  currentUnit: string | null;
  units: any[];
  
  // Passage state
  currentPassage: string | null;
  passageStructure: any | null;
  
  // Question state
  currentQuestion: any | null;
  wrongAnswers: Array<{
    question: any;
    userAnswer: number;
    correctAnswer: number;
    attemptedAt: string;
  }>;
  
  // Actions
  setTextbook: (textbookId: string) => void;
  setUnit: (unitId: string) => void;
  setUnits: (units: any[]) => void;
  setPassage: (passage: string) => void;
  setPassageStructure: (structure: any) => void;
  setQuestion: (question: any) => void;
  addWrongAnswer: (answer: {
    question: any;
    userAnswer: number;
    correctAnswer: number;
    attemptedAt: string;
  }) => void;
  clearWrongAnswers: () => void;
}

export const useLearnStore = create<LearnState>((set) => ({
  // Initial state
  currentTextbook: null,
  currentUnit: null,
  units: [],
  currentPassage: null,
  passageStructure: null,
  currentQuestion: null,
  wrongAnswers: [],
  
  // Actions
  setTextbook: (textbookId) => set({ currentTextbook: textbookId }),
  setUnit: (unitId) => set({ currentUnit: unitId }),
  setUnits: (units) => set({ units }),
  setPassage: (passage) => set({ currentPassage: passage }),
  setPassageStructure: (structure) => set({ passageStructure: structure }),
  setQuestion: (question) => set({ currentQuestion: question }),
  addWrongAnswer: (answer) => set((state) => ({
    wrongAnswers: [...state.wrongAnswers, answer]
  })),
  clearWrongAnswers: () => set({ wrongAnswers: [] }),
}));

