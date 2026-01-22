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

      {/* 이미지 표시 - 로딩 최적화 */}
      {imagePaths.length > 0 && (
        <div className="space-y-4">
          {imagePaths.map((imagePath, index) => {
            // 이미지 경로 정규화 (상대 경로 처리)
            const normalizedPath = imagePath.startsWith('/') 
              ? imagePath 
              : imagePath.startsWith('http') 
                ? imagePath 
                : `/api/data/${imagePath}`;
            
            return (
              <div
                key={index}
                className="relative border border-border/50 rounded-lg overflow-hidden shadow-sm bg-muted/30 min-h-[200px]"
              >
                <img
                  src={normalizedPath}
                  alt={`${unit.title} 이미지 ${index + 1}`}
                  className="w-full h-auto"
                  loading="eager" // 즉시 로드 (중요한 컨텐츠)
                  decoding="async" // 비동기 디코딩
                  onLoad={(e) => {
                    // 이미지 로드 완료 시 스타일 업데이트
                    (e.target as HTMLImageElement).style.opacity = '1';
                    const placeholder = (e.target as HTMLImageElement).nextElementSibling as HTMLElement;
                    if (placeholder) placeholder.style.display = 'none';
                  }}
                  onError={(e) => {
                    console.error('[ConceptViewer] 이미지 로드 실패:', normalizedPath);
                    (e.target as HTMLImageElement).style.display = 'none';
                    const placeholder = (e.target as HTMLImageElement).nextElementSibling as HTMLElement;
                    if (placeholder) placeholder.style.display = 'flex';
                  }}
                  style={{ opacity: 0, transition: 'opacity 0.3s' }}
                />
                {/* 로딩 플레이스홀더 */}
                <div className="absolute inset-0 flex items-center justify-center bg-muted/50">
                  <p className="text-muted-foreground text-sm">이미지 로딩 중...</p>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* 텍스트 표시 제거 (시각 장애인용 - TTS로만 제공) */}
      {/* {unit.content_text && (
        <div className="prose max-w-none">
          <div className="whitespace-pre-wrap text-base leading-relaxed bg-card border border-border rounded-lg p-4">
            {unit.content_text}
          </div>
        </div>
      )} */}
    </div>
  );
}
