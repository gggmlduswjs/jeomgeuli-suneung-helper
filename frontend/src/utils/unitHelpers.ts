/**
 * Unit 관련 유틸리티 함수
 */
import type { Unit } from '../types/unit';

/**
 * Unit 타입에 따른 라벨 반환
 */
export function getUnitTypeLabel(unit: Unit | null): string {
  if (!unit) return '유닛';
  
  switch (unit.type) {
    case 'CONCEPT_CORE':
    case 'CONCEPT_FORM':
    case 'CONCEPT_CONTENT':
      return '개념';
    case 'PASSAGE':
      return '본문';
    case 'QUESTION':
      return '문제';
    case 'CONCEPT_SUMMARY':
      return '요약';
    default:
      return '유닛';
  }
}

/**
 * Unit 번호 계산
 */
export function getUnitNumber(unit: Unit | null, allUnits: Unit[]): number {
  if (!unit) return 0;
  
  const questions = allUnits.filter(u => u.type === 'QUESTION');
  if (unit.type === 'QUESTION') {
    return questions.findIndex(q => q.unit_id === unit.unit_id) + 1;
  }
  return allUnits.findIndex(u => u.unit_id === unit.unit_id) + 1;
}

/**
 * 총 Unit 개수 계산
 */
export function getTotalUnits(unit: Unit | null, allUnits: Unit[]): number {
  if (!unit) return 0;
  
  const questions = allUnits.filter(u => u.type === 'QUESTION');
  return unit.type === 'QUESTION' ? questions.length : allUnits.length;
}
