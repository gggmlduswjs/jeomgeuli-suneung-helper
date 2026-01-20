/**
 * Braille Map Types
 * 점자 맵 관련 타입 정의
 */

// Cell type: 6-dot braille cell represented as boolean array
export type Cell = [boolean, boolean, boolean, boolean, boolean, boolean];

// Alternative Cell type: number array (0 or 1)
export type CellNumber = [0 | 1, 0 | 1, 0 | 1, 0 | 1, 0 | 1, 0 | 1];

// Convert number array to boolean array
export function cellNumberToBoolean(cell: CellNumber): Cell {
  return cell.map(dot => dot === 1) as Cell;
}

// Convert boolean array to number array
export function cellBooleanToNumber(cell: Cell): CellNumber {
  return cell.map(dot => (dot ? 1 : 0)) as CellNumber;
}