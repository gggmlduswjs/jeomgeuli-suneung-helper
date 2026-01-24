/**
 * 개념 설명 표시 컴포넌트
 * Level 3: Concept Explanation Generator 결과 표시
 */
import { useState } from 'react';
import type { ConceptExplanation } from '../../types/book';

interface ConceptExplanationCardProps {
  concept: string;
  explanations: {
    [level: string]: ConceptExplanation;
  };
  defaultLevel?: string;
  onSpeak?: (text: string) => void;
}

export default function ConceptExplanationCard({
  concept,
  explanations,
  defaultLevel = 'high',
  onSpeak,
}: ConceptExplanationCardProps) {
  const [selectedLevel, setSelectedLevel] = useState(defaultLevel);

  const currentExplanation = explanations[selectedLevel];

  if (!currentExplanation) {
    return null;
  }

  const levelLabels: { [key: string]: string } = {
    elementary: '초등',
    middle: '중등',
    high: '고등',
    university: '대학',
  };

  const handleSpeak = (text: string) => {
    onSpeak?.(text);
  };

  return (
    <div className="bg-card border border-border rounded-lg p-4 space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="font-semibold text-lg">💡 개념 설명: {concept}</h3>
        <button
          onClick={() => handleSpeak(`${concept}에 대한 설명입니다. ${currentExplanation.explanation}`)}
          className="text-xs text-primary hover:underline"
        >
          🔊 전체 읽기
        </button>
      </div>

      {/* 수준 선택 */}
      {Object.keys(explanations).length > 1 && (
        <div className="flex gap-2">
          {Object.keys(explanations).map((level) => (
            <button
              key={level}
              onClick={() => setSelectedLevel(level)}
              className={`px-3 py-1 text-sm rounded-full transition-colors ${
                selectedLevel === level
                  ? 'bg-primary text-white'
                  : 'bg-muted text-muted-foreground hover:bg-muted/80'
              }`}
            >
              {levelLabels[level] || level}
            </button>
          ))}
        </div>
      )}

      {/* 설명 */}
      <div className="border-t border-border pt-3">
        <h4 className="text-sm font-medium mb-2">📝 설명</h4>
        <p
          className="text-sm leading-relaxed whitespace-pre-wrap cursor-pointer hover:text-primary/80"
          onClick={() => handleSpeak(currentExplanation.explanation)}
        >
          {currentExplanation.explanation}
        </p>
      </div>

      {/* 예시 */}
      {currentExplanation.examples && currentExplanation.examples.length > 0 && (
        <div className="border-t border-border pt-3">
          <h4 className="text-sm font-medium mb-2">📖 예시</h4>
          <ul className="space-y-2">
            {currentExplanation.examples.map((example, index) => (
              <li
                key={index}
                className="flex items-start gap-2 text-sm cursor-pointer hover:text-primary/80"
                onClick={() => handleSpeak(example)}
              >
                <span className="text-primary font-semibold mt-0.5">{index + 1}.</span>
                <span className="flex-1">{example}</span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* 핵심 포인트 */}
      {currentExplanation.key_points && currentExplanation.key_points.length > 0 && (
        <div className="border-t border-border pt-3">
          <h4 className="text-sm font-medium mb-2">⭐ 핵심 포인트</h4>
          <ul className="space-y-2">
            {currentExplanation.key_points.map((point, index) => (
              <li
                key={index}
                className="flex items-start gap-2 cursor-pointer hover:text-primary/80"
                onClick={() => handleSpeak(point)}
              >
                <span className="text-primary mt-0.5">▸</span>
                <span className="flex-1 text-sm">{point}</span>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
