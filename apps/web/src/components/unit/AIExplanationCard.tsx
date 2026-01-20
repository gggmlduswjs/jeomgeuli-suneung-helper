/**
 * AI 설명 카드 컴포넌트
 */
import { useEffect } from 'react';

interface AIExplanationCardProps {
  sectionType: string;
  aiExplanation: string | null;
  loadingAI: boolean;
  onSpeak: (text: string) => void;
  onLoadExplanation: () => void;
  hasContent: boolean;
}

export default function AIExplanationCard({
  sectionType,
  aiExplanation,
  loadingAI,
  onSpeak,
  onLoadExplanation,
  hasContent,
}: AIExplanationCardProps) {
  // AI 설명이 생성되면 콘솔에 출력
  useEffect(() => {
    if (aiExplanation) {
      console.log('🤖 [AI 설명]', aiExplanation);
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
      <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
        <p className="text-blue-700">
          🤖 AI가 {isConcept ? '개념을 정리하고' : '내용을 분석하고'} 있습니다...
        </p>
      </div>
    );
  }

  if (aiExplanation) {
    return (
      <div className={`p-4 border-2 rounded-lg shadow-md ${conceptStyles.bg}`}>
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <span className="text-2xl">✨</span>
            <h3 className={`font-bold ${conceptStyles.titleColor}`}>
              AI {isConcept ? '강의' : '내용'} 설명
            </h3>
          </div>
          <span className="text-xs text-gray-500">설명 중 입니다..</span>
        </div>
        {/* AI 설명 텍스트는 콘솔에만 출력, UI에는 표시하지 않음 */}
        <div className="flex gap-2">
          <button
            onClick={() => onSpeak(aiExplanation)}
            className={`flex-1 px-4 py-2 rounded-lg font-semibold transition-colors ${conceptStyles.buttonBg}`}
          >
            🔊 다시 듣기
          </button>
          <button
            onClick={onLoadExplanation}
            className={`flex-1 px-4 py-2 rounded-lg font-semibold transition-colors ${conceptStyles.buttonBg}`}
          >
            🔄 다시 생성
          </button>
        </div>
      </div>
    );
  }

  if (hasContent) {
    return (
      <button
        onClick={onLoadExplanation}
        className={`w-full p-4 border-2 rounded-lg font-semibold transition-colors ${conceptStyles.buttonBg}`}
      >
        🤖 AI {isConcept ? '개념' : '내용'} 설명 생성하기
      </button>
    );
  }

  return null;
}
