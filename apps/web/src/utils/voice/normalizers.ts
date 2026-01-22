/**
 * 음성 명령어 정규화 유틸리티
 */
import { KOREAN_ORDINAL_MAP, MISRECOGNITION_MAP } from './commands';

/** 숫자 표현 → 0-based index */
export function extractIndex(t: string): number | undefined {
  // 1) 한글 서수/기수
  for (const k of Object.keys(KOREAN_ORDINAL_MAP)) {
    if (t.includes(k)) return KOREAN_ORDINAL_MAP[k];
  }
  // 2) 숫자 + (번|번째)
  const m1 = t.match(/(\d+)\s*(번|번째)/);
  if (m1) {
    const n = parseInt(m1[1], 10);
    if (!Number.isNaN(n) && n > 0) return n - 1; // 0-based
  }
  // 3) 단독 숫자 (맥락상 detail일 때 자주 말함)
  const m2 = t.match(/\b(\d{1,2})\b/);
  if (m2) {
    const n = parseInt(m2[1], 10);
    if (!Number.isNaN(n) && n > 0) return n - 1;
  }
  return undefined;
}

/** 입력 전처리: 소문자, 공백 정규화, 기호 제거 + 오인식 보정 */
export function normalize(raw: string): string {
  let t = String(raw ?? "")
    .toLowerCase()
    .replace(/[~!@#$%^&*()_+=[\]{};:"/\\|<>""''，､、。．·ㆍ…]/g, " ")
    .replace(/\s+/g, " ")
    .trim();

  // 오인식 보정
  t = correctMisrecognition(t);

  return t;
}

/** 오인식 패턴 보정 (더 관대한 매칭) */
export function correctMisrecognition(text: string): string {
  let corrected = text;
  
  // 직접 매핑 확인
  if (MISRECOGNITION_MAP[corrected]) {
    return MISRECOGNITION_MAP[corrected];
  }
  
  // 부분 매칭 (텍스트에 오인식 패턴이 포함된 경우)
  for (const [wrong, correct] of Object.entries(MISRECOGNITION_MAP)) {
    if (corrected.includes(wrong)) {
      corrected = corrected.replace(wrong, correct);
    }
  }
  
  return corrected;
}

