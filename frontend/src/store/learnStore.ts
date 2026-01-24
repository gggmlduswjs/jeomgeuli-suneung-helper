import { create } from 'zustand';

export interface SessionSummary {
  questionsAnswered: number;
  correctAnswers: number;
  accuracy: number;
  timeSpent: number; // in milliseconds
  sessionStartTime: Date;
  sessionEndTime: Date;
}

interface LearnState {
  // Textbook state
  currentTextbook: string | null;
  currentUnit: string | null;
  units: unknown[];

  // Passage state
  currentPassage: string | null;
  passageStructure: unknown | null;

  // Question state
  currentQuestion: unknown | null;
  wrongAnswers: Array<{
    question: unknown;
    userAnswer: number;
    correctAnswer: number;
    attemptedAt: string;
  }>;

  // Session tracking (NEW)
  sessionStartTime: Date | null;
  answeredQuestions: Set<string>;
  correctAnswers: Set<string>;

  // Actions
  setTextbook: (textbookId: string) => void;
  setUnit: (unitId: string) => void;
  setUnits: (units: unknown[]) => void;
  setPassage: (passage: string) => void;
  setPassageStructure: (structure: unknown) => void;
  setQuestion: (question: unknown) => void;
  addWrongAnswer: (answer: {
    question: unknown;
    userAnswer: number;
    correctAnswer: number;
    attemptedAt: string;
  }) => void;
  clearWrongAnswers: () => void;
  clearAll: () => void;

  // Session actions (NEW)
  startSession: () => void;
  endSession: () => SessionSummary;
  recordAnswer: (questionId: string, isCorrect: boolean) => void;
  getSessionStats: () => {
    questionsAnswered: number;
    correctAnswers: number;
    accuracy: number;
    timeSpent: number;
  };
}

export const useLearnStore = create<LearnState>((set, get) => ({
  // Initial state
  currentTextbook: null,
  currentUnit: null,
  units: [],
  currentPassage: null,
  passageStructure: null,
  currentQuestion: null,
  wrongAnswers: [],

  // Session state (NEW)
  sessionStartTime: null,
  answeredQuestions: new Set(),
  correctAnswers: new Set(),

  // Actions
  setTextbook: (textbookId) => set({ currentTextbook: textbookId }),
  setUnit: (unitId) => set({ currentUnit: unitId }),
  setUnits: (units) => set({ units }),
  setPassage: (passage) => set({ currentPassage: passage }),
  setPassageStructure: (structure) => set({ passageStructure: structure }),
  setQuestion: (question) => set({ currentQuestion: question }),
  addWrongAnswer: (answer) =>
    set((state) => ({
      wrongAnswers: [...state.wrongAnswers, answer],
    })),
  clearWrongAnswers: () => set({ wrongAnswers: [] }),
  clearAll: () =>
    set({
      currentTextbook: null,
      currentUnit: null,
      units: [],
      currentPassage: null,
      passageStructure: null,
      currentQuestion: null,
      wrongAnswers: [],
      sessionStartTime: null,
      answeredQuestions: new Set(),
      correctAnswers: new Set(),
    }),

  // Session actions (NEW)
  startSession: () =>
    set({
      sessionStartTime: new Date(),
      answeredQuestions: new Set(),
      correctAnswers: new Set(),
    }),

  endSession: () => {
    const state = get();
    const sessionEndTime = new Date();
    const timeSpent = state.sessionStartTime
      ? sessionEndTime.getTime() - state.sessionStartTime.getTime()
      : 0;

    const summary: SessionSummary = {
      questionsAnswered: state.answeredQuestions.size,
      correctAnswers: state.correctAnswers.size,
      accuracy:
        state.answeredQuestions.size > 0
          ? (state.correctAnswers.size / state.answeredQuestions.size) * 100
          : 0,
      timeSpent,
      sessionStartTime: state.sessionStartTime || new Date(),
      sessionEndTime,
    };

    // Reset session state
    set({
      sessionStartTime: null,
      answeredQuestions: new Set(),
      correctAnswers: new Set(),
    });

    return summary;
  },

  recordAnswer: (questionId, isCorrect) =>
    set((state) => {
      const newAnswered = new Set(state.answeredQuestions);
      newAnswered.add(questionId);

      const newCorrect = new Set(state.correctAnswers);
      if (isCorrect) {
        newCorrect.add(questionId);
      }

      return {
        answeredQuestions: newAnswered,
        correctAnswers: newCorrect,
      };
    }),

  getSessionStats: () => {
    const state = get();
    const timeSpent = state.sessionStartTime
      ? Date.now() - state.sessionStartTime.getTime()
      : 0;

    return {
      questionsAnswered: state.answeredQuestions.size,
      correctAnswers: state.correctAnswers.size,
      accuracy:
        state.answeredQuestions.size > 0
          ? (state.correctAnswers.size / state.answeredQuestions.size) * 100
          : 0,
      timeSpent,
    };
  },
}));

