import { useEffect } from 'react';
import type { Question } from '../../../lib/api';

interface WrongAnswer {
  question: Question;
  userAnswer: number;
  correctAnswer: number;
  attemptedAt: string;
}

interface WrongAnswerListProps {
  wrongAnswers: WrongAnswer[];
  onSelect: (question: Question) => void;
  onSpeak: (text: string) => void;
}

export default function WrongAnswerList({ wrongAnswers, onSelect, onSpeak }: WrongAnswerListProps) {
  useEffect(() => {
    if (wrongAnswers.length > 0) {
      onSpeak(`총 ${wrongAnswers.length}개의 오답이 있습니다.`);
    }
  }, [wrongAnswers.length, onSpeak]);

  if (wrongAnswers.length === 0) {
    return (
      <div className="p-4 text-center text-muted">
        <p>오답이 없습니다.</p>
      </div>
    );
  }

  return (
    <div className="space-y-2">
      <h3 className="text-lg font-semibold mb-4">오답 노트</h3>
      {wrongAnswers.map((item, index) => (
        <button
          key={index}
          onClick={() => onSelect(item.question)}
          className="w-full p-4 text-left bg-error/5 border border-error/20 rounded-lg hover:bg-error/10 transition-colors"
          aria-label={`오답 ${index + 1}: ${item.question.question_text.substring(0, 50)}...`}
        >
          <div className="flex items-start justify-between gap-2">
            <div className="flex-1">
              <p className="font-medium mb-1">
                {item.question.question_text.substring(0, 100)}
                {item.question.question_text.length > 100 ? '...' : ''}
              </p>
              <div className="text-sm text-muted">
                <span>내 답안: {item.userAnswer}번</span>
                <span className="mx-2">|</span>
                <span>정답: {item.correctAnswer}번</span>
              </div>
            </div>
            <span className="text-xs text-muted">#{index + 1}</span>
          </div>
        </button>
      ))}
    </div>
  );
}


