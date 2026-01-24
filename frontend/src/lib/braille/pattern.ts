/**
 * 점자 패턴 팩토리
 * 숫자 및 답안 패턴 생성
 */

// 점자 숫자 패턴 (한국 점자 규정)
const NUMBER_PATTERNS: Record<1 | 2 | 3 | 4 | 5, number[]> = {
  1: [1],           // 점 1
  2: [1, 2],        // 점 1, 2
  3: [1, 4],        // 점 1, 4
  4: [1, 4, 5],     // 점 1, 4, 5
  5: [1, 5],        // 점 1, 5
};

// 정답/오답 패턴
const CORRECT_PATTERN = [1, 2, 3, 4, 5, 6]; // 전체 점 (표시용)
const WRONG_PATTERN = [1, 4]; // 점 1, 4 (간단한 패턴)

/**
 * 점 번호 배열을 셀 배열로 변환
 * @param dots 점 번호 배열 (1-6)
 * @returns 점자 셀 배열 (6개 점의 비트마스크)
 */
function cellToArray(dots: number[]): number[] {
  const cell = new Array(6).fill(0);
  dots.forEach(dot => {
    if (dot >= 1 && dot <= 6) {
      cell[dot - 1] = 1;
    }
  });
  return cell;
}

export class BraillePatternFactory {
  /**
   * 숫자 패턴 생성 (1-5)
   */
  static createNumberPattern(num: 1 | 2 | 3 | 4 | 5): number[] {
    return NUMBER_PATTERNS[num] || [];
  }

  /**
   * 답안 패턴 생성 (정답/오답)
   */
  static createAnswerPattern(isCorrect: boolean): number[] {
    return isCorrect ? CORRECT_PATTERN : WRONG_PATTERN;
  }

  /**
   * 점 번호 배열을 셀 배열로 변환
   */
  static cellToArray(dots: number[]): number[] {
    return cellToArray(dots);
  }
}
