import { create } from 'zustand';

interface ExamState {
  // Exam mode state
  isExamMode: boolean;
  examStartTime: number | null;
  examEndTime: number | null;
  currentQuestionIndex: number;
  totalQuestions: number;
  answers: Record<number, string>;
  
  // Timer state
  remainingTime: number; // in seconds
  isTimerRunning: boolean;
  
  // Actions
  startExam: (totalQuestions: number, duration: number) => void;
  endExam: () => void;
  setAnswer: (questionIndex: number, answer: string) => void;
  nextQuestion: () => void;
  prevQuestion: () => void;
  goToQuestion: (index: number) => void;
  startTimer: (duration: number) => void;
  pauseTimer: () => void;
  resumeTimer: () => void;
  resetTimer: () => void;
  updateTimer: (remaining: number) => void;
  setTimerConfig: (subject: string, allocatedTime: number) => void;
}

export const useExamStore = create<ExamState>((set, get) => ({
  // Initial state
  isExamMode: false,
  examStartTime: null,
  examEndTime: null,
  currentQuestionIndex: 0,
  totalQuestions: 0,
  answers: {},
  remainingTime: 0,
  isTimerRunning: false,
  
  // Actions
  startExam: (totalQuestions, duration) => set({
    isExamMode: true,
    examStartTime: Date.now(),
    examEndTime: Date.now() + duration * 1000,
    currentQuestionIndex: 0,
    totalQuestions,
    answers: {},
    remainingTime: duration,
    isTimerRunning: true,
  }),
  
  endExam: () => set({
    isExamMode: false,
    examStartTime: null,
    examEndTime: null,
    isTimerRunning: false,
  }),
  
  setAnswer: (questionIndex, answer) => set((state) => ({
    answers: { ...state.answers, [questionIndex]: answer }
  })),
  
  nextQuestion: () => set((state) => ({
    currentQuestionIndex: Math.min(state.currentQuestionIndex + 1, state.totalQuestions - 1)
  })),
  
  prevQuestion: () => set((state) => ({
    currentQuestionIndex: Math.max(state.currentQuestionIndex - 1, 0)
  })),
  
  goToQuestion: (index) => set({
    currentQuestionIndex: Math.max(0, Math.min(index, get().totalQuestions - 1))
  }),
  
  startTimer: (duration) => set({
    remainingTime: duration,
    isTimerRunning: true,
  }),
  
  pauseTimer: () => set({ isTimerRunning: false }),
  
  resumeTimer: () => set({ isTimerRunning: true }),
  
  resetTimer: () => set({
    remainingTime: 0,
    isTimerRunning: false,
  }),
  
  updateTimer: (remaining) => set({ remainingTime: remaining }),
  
  setTimerConfig: (subject, allocatedTime) => {
    // Timer config는 로컬 state로 관리
    // 필요시 store에 추가 가능
  },
}));

