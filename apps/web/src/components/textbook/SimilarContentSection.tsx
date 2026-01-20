/**
 * 유사 콘텐츠 추천 섹션
 * ML 기반 문장 임베딩을 사용한 유사 콘텐츠 추천
 */
import { useState, useEffect } from 'react';
import { literatureAPI } from '../../services/literature';

interface SimilarContent {
  text: string;
  similarity: number;
  index: number;
}

interface SimilarContentSectionProps {
  queryText: string;
  candidateTexts: string[];
  currentIndex?: number; // 현재 섹션 인덱스 (자기 자신 제외용)
  onSelect?: (index: number) => void;
  topK?: number;
  minSimilarity?: number;
}

export default function SimilarContentSection({
  queryText,
  candidateTexts,
  currentIndex,
  onSelect,
  topK = 3,
  minSimilarity = 0.3,
}: SimilarContentSectionProps) {
  const [similarContents, setSimilarContents] = useState<SimilarContent[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!queryText || candidateTexts.length === 0) {
      setSimilarContents([]);
      return;
    }

    // 현재 섹션은 제외
    const filteredCandidates = candidateTexts.filter((_, idx) => idx !== currentIndex);
    
    if (filteredCandidates.length === 0) {
      setSimilarContents([]);
      return;
    }

    setLoading(true);
    setError(null);

    literatureAPI
      .findSimilarContent(queryText, filteredCandidates, topK, minSimilarity)
      .then((result) => {
        setSimilarContents(result.similar_contents);
      })
      .catch((err) => {
        console.error('[SimilarContentSection] 유사 콘텐츠 찾기 실패:', err);
        setError('유사 콘텐츠를 불러오는 중 오류가 발생했습니다.');
        // ML 서비스가 없어도 앱이 동작하도록 에러만 표시
      })
      .finally(() => {
        setLoading(false);
      });
  }, [queryText, candidateTexts, currentIndex, topK, minSimilarity]);

  if (loading) {
    return (
      <div className="bg-card border border-border rounded-lg p-4">
        <h4 className="text-sm font-semibold mb-2 text-muted-foreground">
          유사한 콘텐츠 찾는 중...
        </h4>
      </div>
    );
  }

  if (error) {
    // ML 서비스가 없어도 앱이 동작하도록 조용히 실패
    return null;
  }

  if (similarContents.length === 0) {
    return null;
  }

  return (
    <div className="bg-card border border-border rounded-lg p-4 space-y-3">
      <h4 className="text-sm font-semibold mb-3">유사한 콘텐츠</h4>
      <div className="space-y-2">
        {similarContents.map((content, idx) => (
          <button
            key={idx}
            onClick={() => {
              if (onSelect && content.index !== undefined) {
                // 원본 인덱스로 변환 (필터링 전 인덱스)
                const originalIndex = candidateTexts.findIndex(
                  (text, i) => i !== currentIndex && text === content.text
                );
                if (originalIndex !== -1) {
                  onSelect(originalIndex);
                }
              }
            }}
            className="w-full text-left p-3 bg-muted/50 hover:bg-muted rounded-lg transition-colors border border-border/50"
          >
            <div className="flex items-start justify-between gap-2">
              <p className="text-sm text-foreground line-clamp-2 flex-1">
                {content.text.length > 100
                  ? `${content.text.substring(0, 100)}...`
                  : content.text}
              </p>
              <div className="flex-shrink-0">
                <span className="text-xs text-muted-foreground">
                  {Math.round(content.similarity * 100)}%
                </span>
              </div>
            </div>
          </button>
        ))}
      </div>
      <p className="text-xs text-muted-foreground mt-2">
        유사도가 높은 콘텐츠를 클릭하면 해당 섹션으로 이동합니다.
      </p>
    </div>
  );
}
