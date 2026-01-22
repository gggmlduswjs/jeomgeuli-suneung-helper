/**
 * 유사 콘텐츠 추천 표시 컴포넌트
 * Level 3: RAG-based Similar Content Finder 결과 표시
 */
import { useState } from 'react';
import type { SimilarContent } from '../../types/book';

interface SimilarContentCardProps {
  title?: string;
  recommendations: SimilarContent[];
  onSpeak?: (text: string) => void;
  onSelectContent?: (content: SimilarContent) => void;
}

export default function SimilarContentCard({
  title = '🔍 유사 콘텐츠',
  recommendations,
  onSpeak,
  onSelectContent,
}: SimilarContentCardProps) {
  const [expandedIndex, setExpandedIndex] = useState<number | null>(null);

  if (!recommendations || recommendations.length === 0) {
    return (
      <div className="bg-card border border-border rounded-lg p-4">
        <h3 className="font-semibold text-lg mb-2">{title}</h3>
        <p className="text-sm text-muted-foreground">추천할 유사 콘텐츠가 없습니다.</p>
      </div>
    );
  }

  const handleToggleExpand = (index: number) => {
    setExpandedIndex(expandedIndex === index ? null : index);
  };

  const handleSpeak = (text: string) => {
    onSpeak?.(text);
  };

  const getScoreColor = (score: number): string => {
    if (score >= 0.9) return 'text-green-600';
    if (score >= 0.7) return 'text-blue-600';
    if (score >= 0.5) return 'text-yellow-600';
    return 'text-gray-600';
  };

  const getScoreLabel = (score: number): string => {
    if (score >= 0.9) return '매우 유사';
    if (score >= 0.7) return '유사';
    if (score >= 0.5) return '약간 유사';
    return '관련 있음';
  };

  return (
    <div className="bg-card border border-border rounded-lg p-4 space-y-3">
      <div className="flex items-center justify-between">
        <h3 className="font-semibold text-lg">{title}</h3>
        <span className="text-xs text-muted-foreground">
          {recommendations.length}개 추천
        </span>
      </div>

      <div className="space-y-2">
        {recommendations.map((content, index) => (
          <div
            key={index}
            className="border border-border rounded-lg p-3 hover:border-primary/50 transition-colors cursor-pointer"
            onClick={() => handleToggleExpand(index)}
          >
            {/* Header */}
            <div className="flex items-start justify-between gap-2">
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-xs font-semibold text-primary">
                    #{index + 1}
                  </span>
                  <span className={`text-xs font-medium ${getScoreColor(content.score)}`}>
                    {getScoreLabel(content.score)} ({(content.score * 100).toFixed(1)}%)
                  </span>
                </div>
                <p className="text-sm line-clamp-2">
                  {content.text}
                </p>
              </div>
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  handleSpeak(content.text);
                }}
                className="text-primary hover:text-primary/80 text-xs"
              >
                🔊
              </button>
            </div>

            {/* Expanded Content */}
            {expandedIndex === index && (
              <div className="mt-3 pt-3 border-t border-border space-y-2">
                {/* Full Text */}
                <div>
                  <h5 className="text-xs font-medium mb-1">전체 내용</h5>
                  <p className="text-sm whitespace-pre-wrap">{content.text}</p>
                </div>

                {/* Metadata */}
                {content.metadata && Object.keys(content.metadata).length > 0 && (
                  <div>
                    <h5 className="text-xs font-medium mb-1">메타데이터</h5>
                    <div className="grid grid-cols-2 gap-2 text-xs">
                      {Object.entries(content.metadata).map(([key, value]) => (
                        <div key={key} className="flex justify-between">
                          <span className="text-muted-foreground">{key}:</span>
                          <span className="font-medium">{String(value)}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Actions */}
                {onSelectContent && (
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      onSelectContent(content);
                    }}
                    className="w-full mt-2 px-3 py-1 text-xs bg-primary text-white rounded hover:bg-primary/90"
                  >
                    이 콘텐츠로 이동
                  </button>
                )}
              </div>
            )}
          </div>
        ))}
      </div>

      {recommendations.length > 5 && (
        <p className="text-xs text-center text-muted-foreground">
          상위 {Math.min(recommendations.length, 10)}개 추천 결과
        </p>
      )}
    </div>
  );
}
