import { useEffect } from 'react';

interface SisaWord {
  id: number;
  word: string;
  meaning: string;
  context?: string;
  source?: string;
  date?: string;
}

interface SisaWordsProps {
  words: SisaWord[];
  onSpeak: (text: string) => void;
}

export default function SisaWords({ words, onSpeak }: SisaWordsProps) {
  useEffect(() => {
    if (words.length > 0) {
      onSpeak(`오늘의 시사 용어 ${words.length}개가 있습니다.`);
    }
  }, [words.length, onSpeak]);

  if (words.length === 0) {
    return (
      <div className="p-4 text-center text-muted">
        <p>오늘의 시사 용어가 없습니다.</p>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      <h3 className="text-lg font-semibold mb-4">시사 용어</h3>
      {words.map((word) => (
        <div
          key={word.id}
          className="bg-accent/5 border border-accent/20 rounded-lg p-4"
        >
          <div className="flex items-start justify-between gap-2 mb-2">
            <h4 className="font-semibold text-lg">{word.word}</h4>
            {word.date && (
              <span className="text-xs text-muted">{word.date}</span>
            )}
          </div>
          <p className="text-base text-muted mb-2">{word.meaning}</p>
          {word.context && (
            <div className="mt-2 pt-2 border-t border-border">
              <p className="text-sm text-muted">{word.context}</p>
            </div>
          )}
          {word.source && (
            <p className="text-xs text-muted mt-2">출처: {word.source}</p>
          )}
        </div>
      ))}
    </div>
  );
}


