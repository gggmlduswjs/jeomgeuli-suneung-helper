/**
 * Unit 페이지 헤더 컴포넌트
 */
import type { Unit } from '../../types/unit';
import type { Lesson } from '../../types/lesson';

interface UnitHeaderProps {
  lesson: Lesson | null;
  unit: Unit | null;
  unitTypeLabel: string;
  unitNumber: number;
  totalUnits: number;
  onShowUnitList: () => void;
}

export default function UnitHeader({
  lesson,
  unit,
  unitTypeLabel,
  unitNumber,
  totalUnits,
  onShowUnitList,
}: UnitHeaderProps) {
  return (
    <div className="px-3 py-2 border-b border-border">
      <div className="flex items-center justify-between">
        <div className="flex-1 min-w-0">
          <h2 className="text-sm font-semibold truncate">{lesson?.title || unit?.title}</h2>
          <p className="text-xs text-muted-foreground">
            {unitTypeLabel} {unitNumber} / {totalUnits}
          </p>
        </div>
        <div className="flex items-center gap-1.5 flex-shrink-0">
          <button
            onClick={onShowUnitList}
            className="px-2 py-1 text-xs bg-primary/10 text-primary border border-primary/30 rounded-md hover:bg-primary/20 transition-colors"
            aria-label="학습 단위 목록"
          >
            목록
          </button>
          <div className="text-xs text-muted-foreground">
            {totalUnits > 0 ? Math.round((unitNumber / totalUnits) * 100) : 0}%
          </div>
        </div>
      </div>
    </div>
  );
}
