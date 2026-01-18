/**
 * Strategy Pattern - 과목별 학습 전략
 * 수학, 국어, 영어 등 과목별로 다른 학습 방식을 적용
 */

import { brailleDisplayConfig } from '../config/brailleDisplay';

export type SubjectType = 'math' | 'korean' | 'english' | 'science' | 'social';

export interface SubjectLearningStrategy {
  subject: SubjectType;
  
  readQuestion: {
    primary: 'braille-chunk' | 'audio' | 'mixed';
    chunkStrategy: 'word' | 'sentence' | 'smart';
    audioFallback: boolean;
    extractKey: boolean; // 핵심만 추출
  };
  
  displayContent: {
    useBraille: boolean;
    useAudio: boolean;
    extractKey: boolean;
  };
  
  specialHandling?: {
    math?: 'formula-braille' | 'graph-pattern';
    korean?: 'passage-braille' | 'literature-analysis';
    english?: 'audio-first' | 'braille-second';
  };
}

/**
 * 과목별 학습 전략 정의
 */
export const SUBJECT_STRATEGIES: Record<SubjectType, SubjectLearningStrategy> = {
  math: {
    subject: 'math',
    readQuestion: {
      primary: 'braille-chunk',
      chunkStrategy: 'smart', // 수식 단위로 분할
      audioFallback: true,
      extractKey: true, // 수식 핵심만
    },
    displayContent: {
      useBraille: true,
      useAudio: true,
      extractKey: true,
    },
    specialHandling: {
      math: 'formula-braille',
    },
  },
  korean: {
    subject: 'korean',
    readQuestion: {
      primary: 'mixed',
      chunkStrategy: 'sentence',
      audioFallback: true,
      extractKey: false,
    },
    displayContent: {
      useBraille: true,
      useAudio: true,
      extractKey: false,
    },
    specialHandling: {
      korean: 'passage-braille',
    },
  },
  english: {
    subject: 'english',
    readQuestion: {
      primary: 'mixed',
      chunkStrategy: 'word',
      audioFallback: true,
      extractKey: true,
    },
    displayContent: {
      useBraille: true,
      useAudio: true,
      extractKey: true,
    },
    specialHandling: {
      english: 'audio-first',
    },
  },
  science: {
    subject: 'science',
    readQuestion: {
      primary: 'braille-chunk',
      chunkStrategy: 'smart',
      audioFallback: true,
      extractKey: true,
    },
    displayContent: {
      useBraille: true,
      useAudio: true,
      extractKey: true,
    },
  },
  social: {
    subject: 'social',
    readQuestion: {
      primary: 'mixed',
      chunkStrategy: 'sentence',
      audioFallback: true,
      extractKey: false,
    },
    displayContent: {
      useBraille: true,
      useAudio: true,
      extractKey: false,
    },
  },
};

/**
 * 과목별 학습 전략 조회
 * @param subject 과목 (또는 과목명 문자열)
 */
export function getSubjectStrategy(subject: string | SubjectType): SubjectLearningStrategy {
  const config = brailleDisplayConfig.get();
  
  // 문자열을 SubjectType으로 변환
  let subjectType: SubjectType = 'math';
  const subjectLower = subject.toLowerCase();
  
  if (subjectLower.includes('수학') || subjectLower === 'math') {
    subjectType = 'math';
  } else if (subjectLower.includes('국어') || subjectLower === 'korean') {
    subjectType = 'korean';
  } else if (subjectLower.includes('영어') || subjectLower === 'english') {
    subjectType = 'english';
  } else if (subjectLower.includes('과학') || subjectLower === 'science') {
    subjectType = 'science';
  } else if (subjectLower.includes('사회') || subjectLower === 'social') {
    subjectType = 'social';
  }
  
  const baseStrategy = SUBJECT_STRATEGIES[subjectType] || SUBJECT_STRATEGIES.math;
  
  // maxCells에 따라 전략 자동 조정
  if (config.maxCells === 3) {
    return {
      ...baseStrategy,
      readQuestion: {
        ...baseStrategy.readQuestion,
        audioFallback: true, // 3-cell은 음성 보완 필수
      },
    };
  }
  
  // 6-cell 이상이면 더 많은 내용을 점자로 표시 가능
  if (config.maxCells >= 6) {
    return {
      ...baseStrategy,
      readQuestion: {
        ...baseStrategy.readQuestion,
        extractKey: false, // 더 많은 내용 표시 가능
      },
    };
  }
  
  return baseStrategy;
}

/**
 * 과목명에서 과목 타입 추출
 */
export function extractSubjectType(subjectName: string): SubjectType {
  const lower = subjectName.toLowerCase();
  
  if (lower.includes('수학')) return 'math';
  if (lower.includes('국어')) return 'korean';
  if (lower.includes('영어')) return 'english';
  if (lower.includes('과학')) return 'science';
  if (lower.includes('사회')) return 'social';
  
  return 'math'; // 기본값
}

