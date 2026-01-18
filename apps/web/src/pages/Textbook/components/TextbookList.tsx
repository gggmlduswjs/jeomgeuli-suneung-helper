import { useEffect } from 'react';
import { BraillePatternFactory } from '../../../lib/braillePattern';
import useBrailleBLE from '../../../hooks/useBrailleBLE';

interface Textbook {
  id: number;
  title: string;
  publisher?: string;
  year?: number;
  subject?: string;
}

interface TextbookListProps {
  textbooks: Textbook[];
  selectedId: number | null;
  onSelect: (textbook: Textbook) => void;
  onSpeak: (text: string) => void;
}

export default function TextbookList({ textbooks, selectedId, onSelect, onSpeak }: TextbookListProps) {
  const { isConnected, writeCells } = useBrailleBLE();

  // 교재 목록 음성 안내
  useEffect(() => {
    if (textbooks.length > 0) {
      const message = `총 ${textbooks.length}개의 교재가 있습니다.`;
      onSpeak(message);
    }
  }, [textbooks.length, onSpeak]);

  const handleSelect = (textbook: Textbook, index: number) => {
    onSelect(textbook);
    
    // 점자 패턴 전송 (교재 번호)
    if (isConnected && index < 5) {
      const pattern = BraillePatternFactory.createNumberPattern((index + 1) as 1 | 2 | 3 | 4 | 5);
      // writeCells는 2차원 배열을 받으므로 패턴을 배열로 감싸기
      writeCells([pattern]);
    }
    
    // 음성 안내
    onSpeak(`${textbook.title}를 선택했습니다.`);
  };

  if (textbooks.length === 0) {
    return (
      <div className="p-4 text-center text-muted">
        <p>교재가 없습니다.</p>
      </div>
    );
  }

  return (
    <div className="space-y-2">
      <h2 className="text-lg font-semibold mb-4">교재 목록</h2>
      {textbooks.map((textbook, index) => (
        <button
          key={textbook.id}
          onClick={() => handleSelect(textbook, index)}
          className={`w-full p-4 text-left rounded-lg border-2 transition-colors ${
            selectedId === textbook.id
              ? 'border-primary bg-primary/10'
              : 'border-border hover:border-primary/50'
          }`}
          aria-label={`${index + 1}번 교재: ${textbook.title}`}
        >
          <div className="flex items-center justify-between">
            <div>
              <div className="font-medium">{textbook.title}</div>
              {textbook.publisher && (
                <div className="text-sm text-muted">{textbook.publisher}</div>
              )}
              {textbook.year && (
                <div className="text-xs text-muted">{textbook.year}년</div>
              )}
            </div>
            <div className="text-sm text-muted">#{index + 1}</div>
          </div>
        </button>
      ))}
    </div>
  );
}

