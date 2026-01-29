/**
 * AI 설명 카드 컴포넌트
 */
import { useEffect, useState } from 'react';
import { markdownToPlainText } from '../../utils/text/markdownToPlainText';

interface AIExplanationCardProps {
  sectionType: string;
  aiExplanation: string | null;
  loadingAI: boolean;
  onSpeak: (text: string) => void;
  onLoadExplanation: () => void;
}

export default function AIExplanationCard({
  sectionType,
  aiExplanation,
  loadingAI,
  onSpeak,
  onLoadExplanation,
}: AIExplanationCardProps) {
  const [isExpanded, setIsExpanded] = useState(false);
  // AI 설명이 생성되면 콘솔에 출력
  useEffect(() => {
    if (aiExplanation) {
      if (import.meta.env.DEV) console.log('🤖 [AI 설명]', aiExplanation);
    }
  }, [aiExplanation]);
  const isConcept = sectionType === 'concept';
  const conceptStyles = isConcept
    ? {
        bg: 'bg-gradient-to-r from-blue-50 to-indigo-50 border-blue-300',
        titleColor: 'text-blue-800',
        buttonColor: 'text-blue-600 hover:text-blue-800',
        buttonBg: 'bg-blue-50 border-blue-300 text-blue-700 hover:bg-blue-100',
      }
    : {
        bg: 'bg-gradient-to-r from-purple-50 to-pink-50 border-purple-300',
        titleColor: 'text-purple-800',
        buttonColor: 'text-purple-600 hover:text-purple-800',
        buttonBg: 'bg-purple-50 border-purple-300 text-purple-700 hover:bg-purple-100',
      };

  if (loadingAI) {
    return (
      <div className="p-2 bg-blue-50 border border-blue-200 rounded-lg">
        <p className="text-blue-700 text-xs">
          🤖 AI가 {isConcept ? '개념을 정리하고' : '내용을 분석하고'} 있습니다...
        </p>
      </div>
    );
  }

  if (aiExplanation) {
    return (
      <div className={`border rounded-lg shadow-sm ${conceptStyles.bg}`}>
        <button
          onClick={() => setIsExpanded(!isExpanded)}
          className="w-full p-2 flex items-center justify-between hover:bg-muted/30 transition-colors"
        >
          <div className="flex items-center gap-1.5">
            <span className="text-sm">✨</span>
            <h3 className={`font-semibold text-xs ${conceptStyles.titleColor}`}>
              AI {isConcept ? '강의' : '내용'} 설명
            </h3>
          </div>
          <span className="text-xs text-gray-500">
            {isExpanded ? '▼' : '▶'}
          </span>
        </button>
        {isExpanded && (
          <div className="px-2 pb-2 space-y-1.5 border-t">
            <div className="flex gap-1.5">
              <button
                onClick={() => onSpeak(markdownToPlainText(aiExplanation))}
                className={`flex-1 px-2 py-1.5 text-xs rounded-md font-medium transition-colors ${conceptStyles.buttonBg}`}
              >
                🔊 다시 듣기
              </button>
              <button
                onClick={onLoadExplanation}
                className={`flex-1 px-2 py-1.5 text-xs rounded-md font-medium transition-colors ${conceptStyles.buttonBg}`}
              >
                🔄 다시 생성
              </button>
            </div>
          </div>
        )}
      </div>
    );
  }

  // 항상 표시 (hasContent가 false여도 생성 버튼 표시)
  return (
    <button
      onClick={onLoadExplanation}
      className={`w-full p-2 text-xs border rounded-lg font-medium transition-colors ${conceptStyles.buttonBg}`}
    >
      🤖 AI {isConcept ? '개념' : '내용'} 설명 생성하기
    </button>
  );
}
