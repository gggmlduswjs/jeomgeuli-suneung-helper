/**
 * 홈 화면 상태 관리 (Zustand)
 * 현재 학습 상태, 점자 디바이스 상태, PDF 분석 상태 관리
 */
import { create } from 'zustand';

interface CurrentLearning {
  subject: 'korean' | 'english' | 'math' | null;
  textbook: string;
  progress: {
    passages: number;
    questions: number;
  };
}

interface PDFDocument {
  id: number;
  filename: string;
  status: 'pending' | 'analyzing' | 'completed' | 'failed';
  progress: number;
}

interface BrailleDevice {
  isConnected: boolean;
  batteryLevel: number | null;
  deviceName: string | null;
}

interface HomeState {
  // 현재 학습 상태
  currentLearning: CurrentLearning | null;
  setCurrentLearning: (learning: CurrentLearning | null) => void;
  
  // PDF 목록
  recentPDFs: PDFDocument[];
  setRecentPDFs: (pdfs: PDFDocument[]) => void;
  addPDF: (pdf: PDFDocument) => void;
  updatePDF: (id: number, updates: Partial<PDFDocument>) => void;
  
  // 점자 디바이스 상태
  brailleDevice: BrailleDevice;
  setBrailleDevice: (device: Partial<BrailleDevice>) => void;
  
  // TTS 메시지 생성
  generateTTSMessage: () => string;
}

export const useHomeStore = create<HomeState>((set, get) => ({
  // 초기 상태
  currentLearning: null,
  recentPDFs: [],
  brailleDevice: {
    isConnected: false,
    batteryLevel: null,
    deviceName: null,
  },

  // 현재 학습 상태 설정
  setCurrentLearning: (learning) => set({ currentLearning: learning }),

  // PDF 목록 관리
  setRecentPDFs: (pdfs) => set({ recentPDFs: pdfs }),
  addPDF: (pdf) => set((state) => ({
    recentPDFs: [pdf, ...state.recentPDFs].slice(0, 10) // 최대 10개
  })),
  updatePDF: (id, updates) => set((state) => ({
    recentPDFs: state.recentPDFs.map((pdf) =>
      pdf.id === id ? { ...pdf, ...updates } : pdf
    )
  })),

  // 점자 디바이스 상태 설정
  setBrailleDevice: (device) => set((state) => ({
    brailleDevice: { ...state.brailleDevice, ...device }
  })),

  // TTS 메시지 생성
  generateTTSMessage: () => {
    const state = get();
    const parts: string[] = [];

    if (state.currentLearning) {
      const subjectNames = {
        korean: '국어',
        english: '영어',
        math: '수학'
      };
      const subjectName = subjectNames[state.currentLearning.subject || 'korean'];
      parts.push(
        `현재 학습 중인 내용: ${subjectName} ${state.currentLearning.textbook}. ` +
        `지문 ${state.currentLearning.progress.passages}개, ` +
        `문항 ${state.currentLearning.progress.questions}개 완료했습니다.`
      );
    } else {
      parts.push('진행 중인 학습이 없습니다.');
    }

    parts.push('이어하기, 과목 선택, 교재 관리, 점자 디바이스를 사용할 수 있습니다.');

    if (state.brailleDevice.isConnected) {
      parts.push(`점자 디바이스가 연결되어 있습니다.`);
      if (state.brailleDevice.batteryLevel !== null) {
        parts.push(`배터리 ${state.brailleDevice.batteryLevel}퍼센트입니다.`);
      }
    } else {
      parts.push('점자 디바이스가 연결되지 않았습니다.');
    }

    return parts.join(' ');
  },
}));

