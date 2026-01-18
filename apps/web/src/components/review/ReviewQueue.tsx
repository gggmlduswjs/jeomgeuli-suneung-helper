/**
 * 복습 큐 컴포넌트
 */
import { BraillePatternFactory } from '../../lib/braillePattern';
import useBrailleBLE from '../../hooks/useBrailleBLE';
import type { ReviewQueueItem } from '../../types/review';

interface ReviewQueueProps {
  items: ReviewQueueItem[];
  onSelect: (item: ReviewQueueItem) => void;
  onComplete: (unitId: string) => void;
  onSpeak?: (text: string) => void;
}

export default function ReviewQueue({ items, onSelect, onComplete, onSpeak }: ReviewQueueProps) {
  const { isConnected, writeCells } = useBrailleBLE();

  const handleSelect = (item: ReviewQueueItem, index: number) => {
    onSelect(item);
    
    // 점자 패턴 전송
    if (isConnected && index < 5) {
      const pattern = BraillePatternFactory.createNumberPattern((index + 1) as 1 | 2 | 3 | 4 | 5);
      writeCells([pattern]);
    }
    
    onSpeak?.(`${index + 1}번 복습 항목을 선택했습니다.`);
  };

  if (items.length === 0) {
    return (
      <div className="p-4 text-center text-muted">
        <p>복습할 항목이 없습니다.</p>
      </div>
    );
  }

  return (
    <div className="space-y-2">
      <h2 className="text-lg font-semibold mb-4">복습 큐</h2>
      {items.map((item, index) => (
        <div
          key={item.unit_id}
          className="p-4 rounded-lg border-2 border-border hover:border-primary/50 transition-colors"
        >
          <div className="flex items-center justify-between mb-2">
            <div>
              <div className="font-medium">복습 항목 {index + 1}</div>
              <div className="text-sm text-muted">
                이유: {item.reason === 'WRONG' ? '오답' : '반복 오답'}
              </div>
            </div>
            <div className="flex items-center gap-2">
              {item.priority > 0 && (
                <span className="text-xs bg-primary/20 text-primary px-2 py-1 rounded">
                  우선순위 높음
                </span>
              )}
              <button
                onClick={() => handleSelect(item, index)}
                className="px-3 py-1 bg-primary text-white rounded text-sm hover:bg-primary/90"
              >
                복습하기
              </button>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}
