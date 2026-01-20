/**
 * 개념 설명 뷰어 컴포넌트
 * PDF의 개념 설명 섹션을 표시
 */
import { useEffect } from 'react';
import type { Unit } from '../../types/unit';

interface ConceptViewerProps {
  unit: Unit;
  onSpeak?: (text: string) => void;
}

export default function ConceptViewer({ unit, onSpeak }: ConceptViewerProps) {
  useEffect(() => {
    // 개념 설명 자동 읽기
    if (unit.content_text && onSpeak) {
      onSpeak(`${unit.title}입니다. ${unit.content_text.substring(0, 100)}...`);
    }
  }, [unit, onSpeak]);

  // 이미지 경로 가져오기 (content_image_paths 우선, 없으면 image_path)
  const imagePaths = unit.content_image_paths || (unit.image_path ? [unit.image_path] : []);

  return (
    <div className="space-y-4">
      <div className="bg-primary/10 border border-primary rounded-lg p-4">
        <h3 className="text-xl font-bold mb-2">{unit.title}</h3>
      </div>

      {/* 이미지 표시 */}
      {imagePaths.length > 0 && (
        <div className="space-y-4">
          {imagePaths.map((imagePath, index) => (
            <div
              key={index}
              className="border border-border/50 rounded-lg overflow-hidden shadow-sm"
            >
              <img
                src={imagePath}
                alt={`${unit.title} 이미지 ${index + 1}`}
                className="w-full h-auto"
                onError={(e) => {
                  (e.target as HTMLImageElement).style.display = 'none';
                }}
              />
            </div>
          ))}
        </div>
      )}

      {unit.content_text && (
        <div className="prose max-w-none">
          <div className="whitespace-pre-wrap text-base leading-relaxed bg-card border border-border rounded-lg p-4">
            {unit.content_text}
          </div>
        </div>
      )}
    </div>
  );
}
