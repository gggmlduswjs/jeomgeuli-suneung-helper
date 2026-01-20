/**
 * 점자 변환 유틸리티
 * 한글 텍스트를 점자 셀 배열로 변환
 */

import type { DotArray } from '@/types';

// DotArray는 boolean[]로 정의되어 있으므로, number[]를 boolean[]로 변환
type DotArrayNumber = [number, number, number, number, number, number];

/**
 * 한글 문자를 점자 셀로 변환
 * @param text 변환할 텍스트
 * @returns 점자 셀 배열
 */
export function localToBrailleCells(text: string): DotArray[] {
  if (!text || text.length === 0) {
    return [];
  }

  const cells: DotArray[] = [];
  
  // 모든 문자를 처리
  for (let i = 0; i < text.length; i++) {
    const char = text[i];
    
    // 공백 처리
    if (char === ' ' || char === '\n' || char === '\t') {
      // 공백은 빈 셀로 표시 (또는 스킵)
      continue;
    }
    
    // 한글 유니코드 범위: 0xAC00 (가) ~ 0xD7A3 (힣)
    const charCode = char.charCodeAt(0);
    
    if (charCode >= 0xAC00 && charCode <= 0xD7A3) {
      // 완성형 한글: 초성/중성/종성 분리
      const base = charCode - 0xAC00;
      const cho = Math.floor(base / (21 * 28)); // 초성
      const jung = Math.floor((base % (21 * 28)) / 28); // 중성
      const jong = base % 28; // 종성
      
      // 초성 점자 패턴 (간단한 매핑)
      const choPattern = getChoPattern(cho);
      // 중성 점자 패턴
      const jungPattern = getJungPattern(jung);
      // 종성 점자 패턴 (있을 경우)
      const jongPattern = jong > 0 ? getJongPattern(jong) : [0, 0, 0, 0, 0, 0];
      
      // number[]를 boolean[]로 변환
      const toBooleanArray = (arr: number[]): DotArray => {
        return arr.map(v => v !== 0) as DotArray;
      };
      
      // 첫 셀: 초성
      cells.push(toBooleanArray(choPattern));
      // 두 번째 셀: 중성
      cells.push(toBooleanArray(jungPattern));
      // 세 번째 셀: 종성 (있을 경우)
      if (jong > 0) {
        cells.push(toBooleanArray(jongPattern));
      }
    } else {
      // 한글이 아닌 경우 빈 셀 반환
      cells.push([false, false, false, false, false, false] as DotArray);
    }
  }
  
  return cells;
}

/**
 * 초성 인덱스를 점자 패턴으로 변환
 * @param cho 초성 인덱스 (0: ㄱ, 1: ㄲ, 2: ㄴ, ...)
 */
function getChoPattern(cho: number): DotArrayNumber {
  // 간단한 매핑 (표준 점자 규칙 기반)
  const patterns: { [key: number]: number[] } = {
    0: [0, 0, 0, 1, 0, 0], // ㄱ
    1: [0, 0, 0, 1, 0, 0], // ㄲ (ㄱ과 동일)
    2: [1, 0, 0, 1, 0, 0], // ㄴ
    3: [0, 1, 0, 1, 0, 0], // ㄷ
    4: [0, 1, 0, 0, 1, 0], // ㄹ
    5: [1, 0, 0, 0, 1, 0], // ㅁ
    6: [0, 0, 0, 1, 1, 0], // ㅂ
    7: [0, 0, 0, 0, 0, 1], // ㅅ
    8: [0, 0, 0, 0, 0, 0], // ㅇ (점 없음)
    9: [0, 0, 0, 1, 0, 1], // ㅈ
    10: [0, 0, 0, 0, 1, 1], // ㅊ
    11: [1, 1, 0, 1, 0, 0], // ㅋ
    12: [1, 1, 0, 0, 1, 0], // ㅌ
    13: [1, 0, 0, 1, 1, 0], // ㅍ
    14: [0, 1, 0, 1, 1, 0], // ㅎ
  };
  
  return (patterns[cho] || [0, 0, 0, 0, 0, 0]) as DotArrayNumber;
}

/**
 * 중성 인덱스를 점자 패턴으로 변환
 * @param jung 중성 인덱스 (0: ㅏ, 1: ㅐ, ...)
 */
function getJungPattern(jung: number): DotArrayNumber {
  // 간단한 매핑
  const patterns: { [key: number]: number[] } = {
    0: [1, 1, 0, 0, 0, 1], // ㅏ
    1: [1, 1, 1, 0, 1, 0], // ㅐ
    2: [0, 1, 1, 1, 0, 0], // ㅑ
    3: [0, 1, 1, 0, 1, 1], // ㅒ
    4: [0, 1, 1, 1, 0, 0], // ㅓ
    5: [1, 0, 0, 0, 1, 1], // ㅔ
    6: [1, 0, 0, 0, 1, 1], // ㅕ
    7: [1, 0, 0, 0, 1, 1], // ㅖ
    8: [1, 0, 0, 1, 0, 1], // ㅗ
    9: [1, 0, 0, 1, 1, 0], // ㅘ
    10: [1, 0, 0, 1, 1, 1], // ㅙ
    11: [1, 0, 0, 0, 1, 1], // ㅚ
    12: [0, 1, 1, 1, 0, 1], // ㅛ
    13: [1, 0, 0, 1, 1, 0], // ㅜ
    14: [1, 0, 0, 1, 1, 1], // ㅝ
    15: [1, 0, 0, 1, 1, 1], // ㅞ
    16: [1, 0, 0, 0, 1, 1], // ㅟ
    17: [1, 0, 0, 1, 0, 1], // ㅠ
    18: [0, 1, 0, 1, 0, 1], // ㅡ
    19: [1, 0, 1, 0, 1, 0], // ㅢ
    20: [1, 0, 1, 0, 1, 0], // ㅣ
  };
  
  return (patterns[jung] || [0, 0, 0, 0, 0, 0]) as DotArrayNumber;
}

/**
 * 종성 인덱스를 점자 패턴으로 변환
 * @param jong 종성 인덱스 (0: 없음, 1: ㄱ, ...)
 */
function getJongPattern(jong: number): DotArrayNumber {
  // 종성은 초성과 다른 패턴을 사용
  const patterns: { [key: number]: number[] } = {
    1: [1, 0, 0, 0, 0, 0], // ㄱ
    2: [0, 1, 0, 1, 0, 0], // ㄴ
    3: [1, 1, 0, 0, 0, 0], // ㄷ
    4: [0, 1, 0, 0, 0, 0], // ㄹ
    5: [0, 1, 0, 0, 0, 1], // ㅁ
    6: [1, 1, 0, 0, 0, 0], // ㅂ
    7: [1, 1, 0, 0, 0, 0], // ㅅ
    8: [0, 1, 0, 0, 1, 0], // ㅇ
    9: [1, 1, 0, 0, 1, 0], // ㅈ
    10: [1, 1, 1, 0, 0, 1], // ㅊ
    11: [0, 1, 1, 0, 0, 1], // ㅋ
    12: [0, 1, 1, 0, 1, 0], // ㅌ
    13: [0, 1, 0, 0, 1, 1], // ㅍ
    14: [0, 1, 1, 0, 1, 1], // ㅎ
  };
  
  return (patterns[jong] || [0, 0, 0, 0, 0, 0]) as DotArrayNumber;
}
