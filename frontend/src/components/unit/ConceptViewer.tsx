/**
 * 개념 설명 뷰어 컴포넌트
 * PDF의 개념 설명 섹션을 표시
 */
import { useEffect } from 'react';
import type { Unit } from '../../types/unit';
import TextSearch from './TextSearch';
import RAGRecommendationCard from '../ai/RAGRecommendationCard';

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

  // 디버깅: 이미지 경로 로그
  useEffect(() => {
    if (imagePaths.length > 0) {
      console.log('[ConceptViewer] 이미지 경로:', imagePaths);
    } else {
      console.log('[ConceptViewer] 이미지 경로 없음:', {
        content_image_paths: unit.content_image_paths,
        image_path: unit.image_path,
        unit_id: unit.unit_id,
        title: unit.title
      });
    }
  }, [imagePaths, unit]);

  // 검색 가능한 텍스트
  const searchableText = unit.content_text || unit.braille_text || '';

  return (
    <div className="space-y-1.5" data-search-content>
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
      {imagePaths.length > 0 ? (
        <div className="space-y-1.5">
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
                className="relative border border-border/50 rounded-md overflow-hidden shadow-sm bg-muted/30"
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
                    console.error('[ConceptViewer] 이미지 로드 실패:', {
                      normalizedPath,
                      originalPath: imagePath,
                      unit_id: unit.unit_id,
                      title: unit.title
                    });
                    (e.target as HTMLImageElement).style.display = 'none';
                    const placeholder = (e.target as HTMLImageElement).nextElementSibling as HTMLElement;
                    if (placeholder) {
                      placeholder.style.display = 'flex';
                      placeholder.innerHTML = '<p class="text-muted-foreground text-xs">이미지를 불러올 수 없습니다.</p>';
                    }
                  }}
                  style={{ opacity: 0, transition: 'opacity 0.3s' }}
                />
                {/* 로딩 플레이스홀더 */}
                <div className="absolute inset-0 flex items-center justify-center bg-muted/50">
                  <p className="text-muted-foreground text-xs">이미지 로딩 중...</p>
                </div>
              </div>
            );
          })}
        </div>
      ) : (
        // 이미지 경로가 없을 때 디버깅 정보 표시 (개발 모드에서만)
        process.env.NODE_ENV === 'development' && (
          <div className="border border-dashed border-muted-foreground/30 rounded-md p-2 bg-muted/20">
            <p className="text-xs text-muted-foreground">
              이미지 경로 없음 (개발 모드)
            </p>
          </div>
        )
      )}

      {/* 텍스트 표시 제거 (시각 장애인용 - TTS로만 제공) */}
      {/* {unit.content_text && (
        <div className="prose max-w-none">
          <div className="whitespace-pre-wrap text-base leading-relaxed bg-card border border-border rounded-lg p-4">
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
          contentType="concept"
          onSelect={(rec) => {
            // 추천된 콘텐츠로 이동하는 로직
            if (rec.metadata.unit_id && onSpeak) {
              onSpeak(`유사한 개념으로 이동합니다. ${rec.metadata.title || rec.text.substring(0, 50)}`);
              // TODO: 네비게이션 구현
              // navigate(`/unit/${rec.metadata.unit_id}`);
            }
          }}
        />
      )}
    </div>
  );
}
