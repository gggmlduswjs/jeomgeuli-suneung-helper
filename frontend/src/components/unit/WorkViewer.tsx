/**
 * 작품 뷰어 컴포넌트
 * PDF의 작품 섹션을 표시
 */
import { useEffect } from 'react';
import type { Unit } from '../../types/unit';
import TextSearch from './TextSearch';
import RAGRecommendationCard from '../ai/RAGRecommendationCard';

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

  // 이미지 경로 가져오기 (content_image_paths 우선, 없으면 image_path)
  const imagePaths = unit.content_image_paths || (unit.image_path ? [unit.image_path] : []);

  // 전체 작품 재생 핸들러
  const handlePlayFullWork = () => {
    if (unit.braille_text && onSpeak) {
      onSpeak(`전체 작품을 읽습니다. ${unit.title}. ${unit.braille_text}`);
    }
  };

  // 검색 가능한 텍스트 (content_text 또는 braille_text)
  const searchableText = unit.content_text || unit.braille_text || '';

  return (
    <div className="space-y-2" data-search-content>
      {/* 텍스트 검색 기능 (Ctrl+F) */}
      {searchableText && (
        <TextSearch
          content={searchableText}
          onSearchResult={(index, total) => {
            if (onSpeak) {
              onSpeak(`${total}개 중 ${index + 1}번째 결과입니다.`);
            }
          }}
        />
      )}

      {/* 이미지 표시 - 로딩 최적화 */}
      {imagePaths.length > 0 && (
        <div className="space-y-2">
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
                className="relative border border-border/50 rounded-lg overflow-hidden shadow-sm bg-muted/30"
              >
                <img
                  src={normalizedPath}
                  alt={`${unit.title} 이미지 ${index + 1}`}
                  className="w-full h-auto object-contain"
                  loading="eager" // 즉시 로드 (중요한 컨텐츠)
                  decoding="async" // 비동기 디코딩
                  onLoad={(e) => {
                    // 이미지 로드 완료 시 스타일 업데이트
                    (e.target as HTMLImageElement).style.opacity = '1';
                    const placeholder = (e.target as HTMLImageElement).nextElementSibling as HTMLElement;
                    if (placeholder) placeholder.style.display = 'none';
                  }}
                  onError={(e) => {
                    console.error('[WorkViewer] 이미지 로드 실패:', normalizedPath);
                    (e.target as HTMLImageElement).style.display = 'none';
                    const placeholder = (e.target as HTMLImageElement).nextElementSibling as HTMLElement;
                    if (placeholder) placeholder.style.display = 'flex';
                  }}
                  style={{ opacity: 0, transition: 'opacity 0.3s', maxWidth: '100%', height: 'auto' }}
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
          <div className="whitespace-pre-wrap text-base leading-relaxed bg-card border border-border rounded-lg p-4 font-serif">
            {unit.content_text}
          </div>
        </div>
      )} */}

      {/* RAG 기반 유사 콘텐츠 추천 */}
      {searchableText && (
        <RAGRecommendationCard
          query={searchableText.substring(0, 200)} // 처음 200자만 사용
          unitId={unit.unit_id}
          lessonId={unit.lesson_id}
          contentType="passage"
          onSelect={(rec) => {
            // 추천된 콘텐츠로 이동하는 로직
            if (rec.metadata.unit_id && onSpeak) {
              onSpeak(`유사한 본문으로 이동합니다. ${rec.metadata.title || rec.text.substring(0, 50)}`);
              // TODO: 네비게이션 구현
              // navigate(`/unit/${rec.metadata.unit_id}`);
            }
          }}
        />
      )}
    </div>
  );
}
