/**
 * AI 질문 입력 컴포넌트
 * 사용자가 질문을 입력하면 AI가 답변
 */
import { useState } from 'react';
import { useAILearningAssistant } from '../../hooks/useAILearningAssistant';
import MicButton from '../input/MicButton';

interface AIQuestionInputProps {
  unitId?: string;
  lessonId?: string;
  onAnswer?: (answer: string) => void;
}

export default function AIQuestionInput({
  unitId,
  lessonId,
  onAnswer
}: AIQuestionInputProps) {
  const [question, setQuestion] = useState('');
  const [isExpanded, setIsExpanded] = useState(false);
  const { askQuestion, isAnswering } = useAILearningAssistant(unitId, lessonId);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!question.trim() || isAnswering) return;

    const answer = await askQuestion(question);
    if (answer && onAnswer) {
      onAnswer(answer);
    }
    setQuestion('');
  };

  return (
    <div className="bg-card border border-border rounded-lg">
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full p-2 flex items-center justify-between hover:bg-muted/50 transition-colors"
      >
        <h4 className="font-semibold text-xs">AI에게 질문하기</h4>
        <span className="text-xs text-muted-foreground">
          {isExpanded ? '▼' : '▶'}
        </span>
      </button>
      
      {isExpanded && (
        <div className="px-2 pb-2 space-y-2 border-t">
          <form onSubmit={handleSubmit} className="space-y-2">
            <div className="flex gap-1.5">
              <input
                type="text"
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                placeholder="질문을 입력하세요..."
                className="flex-1 px-2 py-1.5 text-xs border border-border rounded-md"
                disabled={isAnswering}
              />
              <MicButton
                onResult={(text) => setQuestion(text)}
              />
            </div>
            
            <div className="flex gap-1.5">
              <button
                type="submit"
                disabled={!question.trim() || isAnswering}
                className="flex-1 btn-primary text-xs py-1.5 px-2"
              >
                {isAnswering ? '답변 생성 중...' : '질문하기'}
              </button>
            </div>
          </form>
        </div>
      )}
    </div>
  );
}
