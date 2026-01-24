/**
 * Braille Safe Utilities
 * 점자 셀 안전하게 정규화하는 유틸리티
 */

type DotArray = boolean[];

/**
 * 다양한 형태의 점자 셀 데이터를 안전하게 정규화
 * @param cells 원본 셀 데이터 (다양한 형태 가능)
 * @returns 정규화된 boolean 배열 배열
 */
export function normalizeCells(cells: unknown): DotArray[] {
  if (!cells) {
    return [];
  }

  if (!Array.isArray(cells)) {
    return [];
  }

  const normalized: DotArray[] = [];

  for (const cell of cells) {
    if (!cell) {
      normalized.push([false, false, false, false, false, false]);
      continue;
    }

    let dots: boolean[] = [];

    // Case 1: boolean 배열
    if (Array.isArray(cell) && cell.length > 0 && typeof cell[0] === 'boolean') {
      dots = cell.slice(0, 6).map(d => Boolean(d));
    }
    // Case 2: number 배열 (0 or 1)
    else if (Array.isArray(cell) && cell.length > 0 && typeof cell[0] === 'number') {
      dots = cell.slice(0, 6).map(d => d !== 0);
    }
    // Case 3: 숫자 하나 (비트 패턴)
    else if (typeof cell === 'number') {
      dots = [];
      for (let i = 0; i < 6; i++) {
        dots.push(((cell >> i) & 1) === 1);
      }
    }
    // Case 4: 객체 형태 { dots: number }
    else if (typeof cell === 'object' && cell !== null && 'dots' in cell) {
      const dotValue = (cell as { dots: number }).dots;
      dots = [];
      for (let i = 0; i < 6; i++) {
        dots.push(((dotValue >> i) & 1) === 1);
      }
    }
    // Case 5: 알 수 없는 형태 - 빈 셀로 처리
    else {
      dots = [false, false, false, false, false, false];
    }

    // 6개로 패딩
    while (dots.length < 6) {
      dots.push(false);
    }

    normalized.push(dots.slice(0, 6) as DotArray);
  }

  return normalized;
}