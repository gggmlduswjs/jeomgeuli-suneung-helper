/**
 * subject_metadata 파싱 유틸리티
 * 중복된 subject_metadata 파싱 로직을 통합
 */

export interface SubjectMetadata {
  keywords?: string[];
  ai?: {
    summary_enabled?: boolean;
    lecture_enabled?: boolean;
    lecture_prompt_type?: string;
  };
  interaction?: {
    allowed_commands?: string[];
  };
  problem?: {
    choices?: string[];
    answer?: number | string;
  };
  choices?: string[];
  work_text?: string;
  passage_text?: string;
  question_stem?: string;
  [key: string]: unknown;
}

/**
 * subject_metadata를 파싱
 */
export function parseSubjectMetadata(metadata: unknown): SubjectMetadata | null {
  if (!metadata) return null;

  try {
    if (typeof metadata === 'string') {
      return JSON.parse(metadata);
    }
    return metadata as SubjectMetadata;
  } catch (e) {
    console.warn('[Subject Metadata] 파싱 실패:', e);
    return null;
  }
}

/**
 * 키워드 추출
 */
export function extractKeywords(metadata: unknown): string[] {
  const parsed = parseSubjectMetadata(metadata);
  return parsed?.keywords || [];
}
