/**
 * RAG 기반 추천 카드 컴포넌트
 * 유사한 개념/문제/본문 추천 표시
 */
import { useState, useEffect } from 'react';
import { aiAPI } from '../../services/ai';
import { useTTS } from '../../hooks/useTTS';

export interface RAGRecommendation {
  text: string;
  metadata: {
    type: string;
    concept_id?: string;
    problem_id?: string;
    passage_id?: string;
    unit_id?: string;
    lesson_id?: string;
    title?: string;
    [key: string]: any;
  };
  score: number;
}

interface RAGRecommendationCardProps {
  query: string;
  unitId?: string;
  lessonId?: string;
  contentType?: 'concept' | 'problem' | 'passage' | 'all';
  onSelect?: (recommendation: RAGRecommendation) => void;
}

export default function RAGRecommendationCard({
  query,
  unitId,
  lessonId,
  contentType = 'all',
  onSelect,
}: RAGRecommendationCardProps) {
  const [recommendations, setRecommendations] = useState<RAGRecommendation[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isExpanded, setIsExpanded] = useState(false);
  const { speak } = useTTS();

  useEffect(() => {
    if (!query.trim() || !isExpanded) {
      setRecommendations([]);
      return;
    }

    setLoading(true);
    setError(null);

    aiAPI
      .getRecommendations({
        query,
        unit_id: unitId,
        lesson_id: lessonId,
        content_type: contentType,
        top_k: 5,
        min_score: 0.3,
      })
      .then((response) => {
        setRecommendations(response.recommendations);
        // TTS는 사용자가 명시적으로 요청할 때만 재생 (자동 재생 제거)
        // if (response.recommendations.length === 0) {
        //   speak('유사한 콘텐츠를 찾지 못했습니다.');
        // } else {
        //   speak(`${response.recommendations.length}개의 유사한 콘텐츠를 찾았습니다.`);
        // }
      })
      .catch((err) => {
        console.error('[RAGRecommendationCard] 추천 실패:', err);
        setError('추천을 불러오는 중 오류가 발생했습니다.');
        // 에러 메시지도 자동 TTS 제거 (콘솔에만 표시)
        // speak('추천을 불러오는 중 오류가 발생했습니다.');
      })
      .finally(() => {
        setLoading(false);
      });
  }, [query, unitId, lessonId, contentType, isExpanded, speak]);

  const getTypeLabel = (type: string) => {
    switch (type) {
      case 'concept':
        return '개념';
      case 'problem':
        return '문제';
      case 'passage':
        return '본문';
      default:
        return '콘텐츠';
    }
  };

  const getTypeColor = (type: string) => {
    switch (type) {
      case 'concept':
        return 'bg-blue-50 border-blue-300 text-blue-700 hover:bg-blue-100';
      case 'problem':
        return 'bg-green-50 border-green-300 text-green-700 hover:bg-green-100';
      case 'passage':
        return 'bg-purple-50 border-purple-300 text-purple-700 hover:bg-purple-100';
      default:
        return 'bg-gray-50 border-gray-300 text-gray-700 hover:bg-gray-100';
    }
  };

  return (
    <div className="bg-card border border-border rounded-lg">
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full p-2 flex items-center justify-between hover:bg-muted/50 transition-colors"
        aria-label={isExpanded ? '추천 닫기' : '추천 열기'}
      >
        <div className="flex items-center gap-1.5">
          <span className="text-sm">🔍</span>
          <h4 className="font-semibold text-xs">유사 콘텐츠 추천</h4>
        </div>
        <span className="text-xs text-muted-foreground">
          {isExpanded ? '▼' : '▶'}
        </span>
      </button>

      {isExpanded && (
        <div className="px-2 pb-2 space-y-1.5 border-t">
          {loading && (
            <div className="text-xs text-muted-foreground py-1.5">
              유사한 콘텐츠를 찾는 중...
            </div>
          )}

          {error && (
            <div className="text-xs text-destructive py-1.5">{error}</div>
          )}

          {!loading && !error && recommendations.length === 0 && (
            <div className="text-xs text-muted-foreground py-1.5">
              유사한 콘텐츠를 찾지 못했습니다.
            </div>
          )}

          {!loading && !error && recommendations.length > 0 && (
            <div className="space-y-1.5">
              {recommendations.map((rec, index) => (
                <button
                  key={index}
                  onClick={() => {
                    if (onSelect) {
                      onSelect(rec);
                    }
                    const preview = rec.text.length > 50 
                      ? `${rec.text.substring(0, 50)}...` 
                      : rec.text;
                    speak(`${getTypeLabel(rec.metadata.type)}: ${preview}`);
                  }}
                  className={`w-full text-left p-2 rounded-md border transition-colors ${getTypeColor(
                    rec.metadata.type
                  )}`}
                >
                  <div className="flex items-start justify-between gap-1.5">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-1.5 mb-0.5">
                        <span className="text-xs font-semibold px-1.5 py-0.5 rounded bg-white/50">
                          {getTypeLabel(rec.metadata.type)}
                        </span>
                        {rec.metadata.title && (
                          <span className="text-xs font-medium truncate">
                            {rec.metadata.title}
                          </span>
                        )}
                      </div>
                      <p className="text-xs line-clamp-2">
                        {rec.text.length > 80
                          ? `${rec.text.substring(0, 80)}...`
                          : rec.text}
                      </p>
                    </div>
                    <div className="flex-shrink-0">
                      <span className="text-xs text-muted-foreground">
                        {Math.round(rec.score * 100)}%
                      </span>
                    </div>
                  </div>
                </button>
              ))}
            </div>
          )}

          <p className="text-xs text-muted-foreground mt-1.5">
            유사도가 높은 콘텐츠를 클릭하면 해당 내용으로 이동합니다.
          </p>
        </div>
      )}
    </div>
  );
}
