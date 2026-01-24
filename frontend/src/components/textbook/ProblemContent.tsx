/**
 * 문제 섹션 전용 컴포넌트
 * 객관식/서술형 문제를 모두 지원
 */
import { useState } from 'react';
import type { Unit } from '../../types/api';
import {
  parseProblemContent,
  createProblemFromMetadata,
  isMultipleChoice,
  type ParsedProblem,
  type ProblemMetadata,
} from '../../utils/problemParser';

interface ProblemContentProps {
  unit: Unit | null;
  onSpeak: (text: string) => void;
  readingMode?: 'braille-only' | 'audio-first' | 'mixed';
  problemNumber?: string;
  problemMetadata?: ProblemMetadata | null;
}

export default function ProblemContent({
  unit,
  onSpeak,
  problemNumber,
  problemMetadata,
}: ProblemContentProps) {
  const [selectedAnswer, setSelectedAnswer] = useState<number | null>(null);
  const [showAnswer, setShowAnswer] = useState(false);
  const [isCorrect, setIsCorrect] = useState<boolean | null>(null);
  const [userAnswer, setUserAnswer] = useState<string>('');

  // 문제 데이터 파싱
  const parsedProblem: ParsedProblem | null = problemMetadata
    ? createProblemFromMetadata(problemMetadata, unit?.content || '', problemNumber)
    : unit?.content
    ? parseProblemContent(unit.content, problemNumber)
    : null;

  const hasChoices = isMultipleChoice(parsedProblem);
  const choices = parsedProblem?.choices || [];
  const questionText = parsedProblem?.questionText || unit?.content || '문제 내용이 없습니다.';
  const displayNumber = parsedProblem?.problemNumber || problemNumber || '01';

  // 객관식 정답 확인
  const handleCheckAnswer = () => {
    if (!hasChoices || selectedAnswer === null) return;

    const correctAnswer = parsedProblem?.correctAnswer;
    if (correctAnswer !== undefined) {
      const isAnswerCorrect = selectedAnswer === correctAnswer;
      setIsCorrect(isAnswerCorrect);
      setShowAnswer(true);
      onSpeak(isAnswerCorrect ? '정답입니다!' : `오답입니다. 정답은 ${['①', '②', '③', '④', '⑤'][correctAnswer - 1] || `${correctAnswer}번`}입니다.`);
    } else {
      setIsCorrect(true);
      setShowAnswer(true);
      onSpeak('정답입니다!');
    }
  };

  // 서술형 답안 제출
  const handleSubmitAnswer = () => {
    if (!userAnswer.trim()) return;
    setShowAnswer(true);
    onSpeak('답안이 제출되었습니다.');
  };

  if (!unit) {
    return (
      <div className="p-4 text-center text-muted">
        <p>문제를 불러올 수 없습니다.</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* 문제 지문 */}
      <div className="bg-card border border-border rounded-lg p-6">
        <div className="flex items-start gap-3">
          <span className="text-2xl font-bold text-primary min-w-[3rem]">
            {displayNumber}
          </span>
          <p className="flex-1 text-base leading-relaxed whitespace-pre-wrap">
            {questionText}
          </p>
        </div>
      </div>

      {/* 객관식: 선택지 */}
      {hasChoices && (
        <div className="space-y-3">
          <h3 className="text-lg font-semibold">선택지</h3>
          {choices.map((choice, index) => {
            const choiceNumber = index + 1;
            const isSelected = selectedAnswer === choiceNumber;
            const symbol = ['①', '②', '③', '④', '⑤'][index] || `${choiceNumber}.`;

            return (
              <button
                key={index}
                onClick={() => setSelectedAnswer(choiceNumber)}
                className={`w-full text-left p-4 border-2 rounded-lg transition-all ${
                  isSelected
                    ? 'border-primary bg-primary/10'
                    : 'border-border hover:border-primary/50 hover:bg-accent/10'
                }`}
                aria-label={`선택지 ${choiceNumber}: ${choice}`}
              >
                <div className="flex items-start gap-3">
                  <span className="text-lg font-semibold text-primary min-w-[2rem]">
                    {symbol}
                  </span>
                  <span className="flex-1 text-base leading-relaxed">{choice}</span>
                </div>
              </button>
            );
          })}
        </div>
      )}

      {/* 서술형: 답안 입력 */}
      {!hasChoices && !showAnswer && (
        <div className="space-y-3">
          <h3 className="text-lg font-semibold">답안 작성</h3>
          <textarea
            value={userAnswer}
            onChange={(e) => setUserAnswer(e.target.value)}
            placeholder="답안을 입력하세요..."
            className="w-full p-4 border-2 border-border rounded-lg resize-none min-h-[120px] text-base"
            rows={5}
          />
        </div>
      )}

      {/* 제출 버튼 */}
      {!showAnswer && (
        <button
          onClick={hasChoices ? handleCheckAnswer : handleSubmitAnswer}
          disabled={hasChoices ? selectedAnswer === null : !userAnswer.trim()}
          className="w-full px-6 py-3 bg-primary text-white rounded-lg hover:bg-primary/90 transition-colors font-semibold disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {hasChoices ? '정답 확인' : '답안 제출'}
        </button>
      )}

      {/* 결과 표시 */}
      {showAnswer && (
        <div
          className={`p-4 rounded-lg border-2 ${
            hasChoices && isCorrect === false
              ? 'bg-error/10 border-error text-error'
              : 'bg-success/10 border-success text-success'
          }`}
        >
          {hasChoices ? (
            <>
              <p className="font-semibold mb-2">
                {isCorrect ? '정답입니다!' : '오답입니다.'}
              </p>
              {!isCorrect && parsedProblem?.correctAnswer && (
                <p className="text-sm">
                  정답: {['①', '②', '③', '④', '⑤'][parsedProblem.correctAnswer - 1] || `${parsedProblem.correctAnswer}번`}
                </p>
              )}
            </>
          ) : (
            <p className="font-semibold">답안이 제출되었습니다.</p>
          )}
        </div>
      )}
    </div>
  );
}
