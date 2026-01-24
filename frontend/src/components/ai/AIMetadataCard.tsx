/**
 * LLM 메타데이터 표시 컴포넌트
 * Level 3: LLM Metadata Enrichment 결과 표시
 */
import type { LLMMetadata } from '../../types/book';

interface AIMetadataCardProps {
  metadata: LLMMetadata;
  onSpeak?: (text: string) => void;
}

export default function AIMetadataCard({ metadata, onSpeak }: AIMetadataCardProps) {
  const handleSpeak = (text: string) => {
    onSpeak?.(text);
  };

  return (
    <div className="bg-card border border-border rounded-lg p-4 space-y-3">
      <div className="flex items-center justify-between">
        <h3 className="font-semibold text-lg">🤖 AI 메타데이터</h3>
        {metadata.enrichment_confidence !== undefined && (
          <span className="text-xs text-muted-foreground">
            신뢰도: {(metadata.enrichment_confidence * 100).toFixed(0)}%
          </span>
        )}
      </div>

      {/* 태그 */}
      {metadata.tags && metadata.tags.length > 0 && (
        <div>
          <h4 className="text-sm font-medium mb-2">🏷️ 태그</h4>
          <div className="flex flex-wrap gap-2">
            {metadata.tags.map((tag, index) => (
              <span
                key={index}
                className="px-2 py-1 bg-primary/10 text-primary text-xs rounded-full"
                onClick={() => handleSpeak(tag)}
              >
                {tag}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* 키워드 */}
      {metadata.keywords && metadata.keywords.length > 0 && (
        <div>
          <h4 className="text-sm font-medium mb-2">🔑 핵심 키워드</h4>
          <div className="flex flex-wrap gap-2">
            {metadata.keywords.map((keyword, index) => (
              <span
                key={index}
                className="px-2 py-1 bg-secondary/10 text-secondary text-xs rounded border border-secondary/20"
                onClick={() => handleSpeak(keyword)}
              >
                {keyword}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* 난이도 */}
      {metadata.difficulty && (
        <div className="flex items-center justify-between py-2 border-t border-border">
          <span className="text-sm font-medium">📊 난이도</span>
          <span className="text-sm">{metadata.difficulty}</span>
        </div>
      )}

      {/* 과목 영역 */}
      {metadata.subject_area && (
        <div className="flex items-center justify-between py-2 border-t border-border">
          <span className="text-sm font-medium">📚 과목 영역</span>
          <span className="text-sm">{metadata.subject_area}</span>
        </div>
      )}

      {/* 예상 학습 시간 */}
      {metadata.estimated_time_minutes && (
        <div className="flex items-center justify-between py-2 border-t border-border">
          <span className="text-sm font-medium">⏱️ 예상 학습 시간</span>
          <span className="text-sm">{metadata.estimated_time_minutes}분</span>
        </div>
      )}

      {/* 학습 목표 */}
      {metadata.learning_objectives && metadata.learning_objectives.length > 0 && (
        <div className="border-t border-border pt-3">
          <h4 className="text-sm font-medium mb-2">🎯 학습 목표</h4>
          <ul className="space-y-1 text-sm">
            {metadata.learning_objectives.map((objective, index) => (
              <li
                key={index}
                className="flex items-start gap-2 cursor-pointer hover:text-primary"
                onClick={() => handleSpeak(objective)}
              >
                <span className="text-primary mt-0.5">•</span>
                <span>{objective}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
