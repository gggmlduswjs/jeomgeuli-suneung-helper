/**
 * AI 설명 카드 컴포넌트
 * AI가 생성한 설명을 표시
 */
import useTTS from '../../hooks/useTTS';

interface AIExplanationCardProps {
  explanation: string;
  isLoading?: boolean;
  onReplay?: () => void;
}

export default function AIExplanationCard({ 
  explanation, 
  isLoading,
  onReplay 
}: AIExplanationCardProps) {
  const { speak } = useTTS();

  const handleReplay = () => {
    speak(explanation);
    if (onReplay) {
      onReplay();
    }
  };

  if (isLoading) {
    return (
      <div className="bg-info/10 border border-info rounded-lg p-4">
        <p className="text-info">AI가 설명을 생성하고 있습니다...</p>
      </div>
    );
  }

  if (!explanation) {
    return null;
  }

  return (
    <div className="bg-primary/10 border border-primary rounded-lg p-4">
      <div className="flex justify-between items-start mb-2">
        <h4 className="font-semibold">AI 선생님 설명</h4>
        <button
          onClick={handleReplay}
          className="btn-ghost text-xs"
          aria-label="다시 듣기"
        >
          다시 듣기
        </button>
      </div>
      <p className="text-sm leading-relaxed whitespace-pre-wrap">{explanation}</p>
    </div>
  );
}
