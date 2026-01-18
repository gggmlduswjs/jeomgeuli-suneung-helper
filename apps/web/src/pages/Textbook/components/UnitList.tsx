import { useEffect } from 'react';
import { BraillePatternFactory } from '../../../lib/braillePattern';
import useBrailleBLE from '../../../hooks/useBrailleBLE';

interface Unit {
  id: number;
  title: string;
  order: number;
}

interface UnitListProps {
  units: Unit[];
  selectedId: number | null;
  onSelect: (unit: Unit) => void;
  onSpeak: (text: string) => void;
}

export default function UnitList({ units, selectedId, onSelect, onSpeak }: UnitListProps) {
  const { isConnected, writeCells } = useBrailleBLE();

  // 단원 목록 음성 안내
  useEffect(() => {
    if (units.length > 0) {
      const message = `총 ${units.length}개의 단원이 있습니다.`;
      onSpeak(message);
    }
  }, [units.length, onSpeak]);

  const handleSelect = (unit: Unit, index: number) => {
    onSelect(unit);
    
    // 점자 패턴 전송 (단원 번호)
    if (isConnected && index < 5) {
      const pattern = BraillePatternFactory.createNumberPattern((index + 1) as 1 | 2 | 3 | 4 | 5);
      // writeCells는 2차원 배열을 받으므로 패턴을 배열로 감싸기
      writeCells([pattern]);
    }
    
    // 음성 안내
    onSpeak(`${unit.title}를 선택했습니다.`);
  };

  if (units.length === 0) {
    return (
      <div className="p-4 text-center text-muted">
        <p>단원이 없습니다.</p>
      </div>
    );
  }

  return (
    <div className="space-y-2">
      <h2 className="text-lg font-semibold mb-4">단원 목록</h2>
      {units.map((unit, index) => (
        <button
          key={unit.id}
          onClick={() => handleSelect(unit, index)}
          className={`w-full p-4 text-left rounded-lg border-2 transition-colors ${
            selectedId === unit.id
              ? 'border-primary bg-primary/10'
              : 'border-border hover:border-primary/50'
          }`}
          aria-label={`${index + 1}번 단원: ${unit.title}`}
        >
          <div className="flex items-center justify-between">
            <div>
              <div className="font-medium">{unit.title}</div>
            </div>
            <div className="text-sm text-muted">#{index + 1}</div>
          </div>
        </button>
      ))}
    </div>
  );
}

