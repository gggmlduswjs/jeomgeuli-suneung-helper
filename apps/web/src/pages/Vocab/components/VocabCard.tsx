import { useEffect } from 'react';
import { BraillePatternFactory } from '../../../lib/braillePattern';
import useBrailleBLE from '../../../hooks/useBrailleBLE';

interface Vocab {
  id: number;
  word: string;
  meaning: string;
  example: string;
  queue_id?: number;
}

interface VocabCardProps {
  vocab: Vocab;
  index: number;
  onSpeak: (text: string) => void;
  onMarkLearned?: () => void;
  readingMode?: 'braille-only' | 'audio-first' | 'mixed';
}

export default function VocabCard({ vocab, index, onSpeak, onMarkLearned, readingMode = 'braille-only' }: VocabCardProps) {
  const { isConnected, writeCells, writeText } = useBrailleBLE();

  // 어휘 점자 읽기 모드
  useEffect(() => {
    if (readingMode === 'braille-only' && isConnected) {
      // 어휘를 점자로 먼저 표시
      writeText(vocab.word).catch(console.error);
      // 음성 최소화: 한 번만
      onSpeak('어휘를 점자로 읽어보세요.');
    }
  }, [vocab.word, readingMode, isConnected, writeText, onSpeak]);

  // 어휘 음성 안내 (점자 읽기 모드가 아닐 때만)
  useEffect(() => {
    if (readingMode !== 'braille-only') {
      const message = `${index + 1}번 어휘: ${vocab.word}. 의미: ${vocab.meaning}. 예문: ${vocab.example}`;
      onSpeak(message);
    }

    // 점자 패턴 전송 (어휘 번호)
    if (isConnected && index < 5) {
      const pattern = BraillePatternFactory.createNumberPattern((index + 1) as 1 | 2 | 3 | 4 | 5);
      writeCells([pattern]);
    }
  }, [vocab, index, onSpeak, isConnected, writeCells, readingMode]);

  return (
    <div className="bg-card border border-border rounded-lg p-6 space-y-4">
      <div className="flex items-center justify-between mb-4">
        <span className="text-sm text-muted">#{index + 1}</span>
        {onMarkLearned && (
          <button
            onClick={onMarkLearned}
            className="btn-primary text-sm"
            aria-label="학습 완료 표시"
          >
            학습 완료
          </button>
        )}
      </div>

      <div>
        <h3 className="text-2xl font-bold mb-2">{vocab.word}</h3>
        <p className="text-lg text-muted mb-4">{vocab.meaning}</p>
        {vocab.example && (
          <div className="bg-accent/5 border border-accent/20 rounded-lg p-3">
            <p className="text-sm text-muted mb-1">예문:</p>
            <p className="text-base">{vocab.example}</p>
          </div>
        )}
      </div>
    </div>
  );
}


