/**
 * 강 목록 컴포넌트
 */
import { BraillePatternFactory } from '../lib/braillePattern';
import useBrailleBLE from '../../hooks/useBrailleBLE';
import type { Unit } from '../../types/unit';

interface LessonListProps {
  units: Unit[];
  onSelect: (unit: Unit) => void;
  onSpeak?: (text: string) => void;
}

export default function LessonList({ units, onSelect, onSpeak }: LessonListProps) {
  const { isConnected, writeCells } = useBrailleBLE();

  const handleSelect = (unit: Unit, index: number) => {
    onSelect(unit);
    
    // 점자 패턴 전송 (단위 번호)
    if (isConnected && index < 5) {
      const pattern = BraillePatternFactory.createNumberPattern((index + 1) as 1 | 2 | 3 | 4 | 5);
      const cellArray = BraillePatternFactory.cellToArray(pattern);
      writeCells([cellArray]);
    }
    
    // 음성 안내
    onSpeak?.(`${unit.title}를 선택했습니다.`);
  };

  if (units.length === 0) {
    return (
      <div className="p-4 text-center text-muted">
        <p>학습 단위가 없습니다.</p>
      </div>
    );
  }

  return (
    <div className="space-y-2">
      <h2 className="text-lg font-semibold mb-4">학습 단위 목록</h2>
      {units.map((unit, index) => (
        <button
          key={unit.unit_id}
          onClick={() => handleSelect(unit, index)}
          className="w-full p-4 text-left rounded-lg border-2 border-border hover:border-primary/50 transition-colors"
          aria-label={`${index + 1}번 단위: ${unit.title}`}
        >
          <div className="flex items-center justify-between">
            <div>
              <div className="font-medium">{unit.title}</div>
              <div className="text-sm text-muted mt-1">타입: {unit.type}</div>
            </div>
            <div className="text-sm text-muted">#{index + 1}</div>
          </div>
        </button>
      ))}
    </div>
  );
}
