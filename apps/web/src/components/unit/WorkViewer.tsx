/**
 * 작품 뷰어 컴포넌트
 * PDF의 작품 섹션을 표시
 */
import { useEffect } from 'react';
import type { Unit } from '../../types/unit';

interface WorkViewerProps {
  unit: Unit;
  onSpeak?: (text: string) => void;
}

export default function WorkViewer({ unit, onSpeak }: WorkViewerProps) {
  useEffect(() => {
    // 작품 자동 읽기
    if (unit.content_text && onSpeak) {
      const preview = unit.content_text.substring(0, 150);
      onSpeak(`${unit.title} 작품입니다. ${preview}...`);
    }
  }, [unit, onSpeak]);

  return (
    <div className="space-y-4">
      <div className="bg-accent/10 border border-accent rounded-lg p-4">
        <h3 className="text-xl font-bold mb-2">{unit.title}</h3>
      </div>
      
      {unit.content_text && (
        <div className="prose max-w-none">
          <div className="whitespace-pre-wrap text-base leading-relaxed bg-card border border-border rounded-lg p-4 font-serif">
            {unit.content_text}
          </div>
        </div>
      )}
    </div>
  );
}
