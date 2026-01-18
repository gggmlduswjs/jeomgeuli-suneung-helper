import { useEffect } from 'react';
import { BraillePatternFactory } from '../../../lib/braillePattern';
import useBrailleBLE from '../../../hooks/useBrailleBLE';
import type { AnswerResult } from '../../../lib/api';

interface AnswerResultProps {
  result: AnswerResult | null;
  userAnswer: number;
  onSpeak: (text: string) => void;
}

export default function AnswerResult({ result, userAnswer, onSpeak }: AnswerResultProps) {
  const { isConnected, writeCells } = useBrailleBLE();

  // 결과 음성 안내 및 점자 패턴 전송
  useEffect(() => {
    if (!result) return;

    const isCorrect = result.is_correct;
    const message = isCorrect
      ? `정답입니다! 정답은 ${result.correct_answer}번입니다.`
      : `오답입니다. 정답은 ${result.correct_answer}번입니다. ${result.explanation}`;

    onSpeak(message);

    // 점자 패턴 전송
    if (isConnected) {
      const pattern = BraillePatternFactory.createAnswerPattern(isCorrect);
      writeCells([pattern]);
    }
  }, [result, onSpeak, isConnected, writeCells]);

  if (!result) {
    return null;
  }

  return (
    <div className={`rounded-lg p-4 border-2 ${
      result.is_correct
        ? 'bg-success/10 border-success'
        : 'bg-error/10 border-error'
    }`}>
      <div className="flex items-center gap-2 mb-2">
        <span className={`text-2xl ${result.is_correct ? 'text-success' : 'text-error'}`}>
          {result.is_correct ? '✓' : '✗'}
        </span>
        <h3 className={`text-lg font-semibold ${
          result.is_correct ? 'text-success' : 'text-error'
        }`}>
          {result.is_correct ? '정답입니다!' : '오답입니다'}
        </h3>
      </div>

      <div className="space-y-2">
        <p>
          <span className="font-medium">내 답안:</span> {userAnswer}번
        </p>
        <p>
          <span className="font-medium">정답:</span> {result.correct_answer}번
        </p>
        {result.explanation && (
          <div className="mt-3 pt-3 border-t border-border">
            <p className="font-medium mb-1">해설:</p>
            <p className="text-sm text-muted whitespace-pre-wrap">
              {result.explanation}
            </p>
          </div>
        )}
      </div>
    </div>
  );
}


