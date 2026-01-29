/**
 * 학습 단위 뷰어 컴포넌트
 * 개념/작품/문제 타입별 통합 표시
 */
import { useEffect, useState } from 'react';
import useBrailleBLE from '../../hooks/useBrailleBLE';
import type { Unit } from '../../types/unit';
import { BrailleCells } from '../braille/BrailleCells';
import ConceptViewer from './ConceptViewer';
import WorkViewer from './WorkViewer';
import MathCalculator from '../math/MathCalculator';
import RAGRecommendationCard from '../ai/RAGRecommendationCard';
import { localToBrailleCells } from '../../lib/braille/converter';
import type { DotArray } from '../../types';

interface UnitViewerProps {
  unit: Unit;
  onSpeak?: (text: string) => void;
}

export default function UnitViewer({ unit, onSpeak }: UnitViewerProps) {
  const { isConnected } = useBrailleBLE();
  const [brailleCells, setBrailleCells] = useState<DotArray[]>([]);

  // 텍스트를 점자로 변환
  useEffect(() => {
    let textToConvert = '';

    if (unit.braille_text) {
      // 점자 텍스트가 있으면 우선 사용
      textToConvert = unit.braille_text;
    } else if (unit.content_text) {
      // 일반 텍스트를 점자로 변환
      textToConvert = unit.content_text;
    }

    if (textToConvert) {
      const cells = localToBrailleCells(textToConvert);
      setBrailleCells(cells);
    }
  }, [unit.braille_text, unit.content_text]);

  // 수학 계산기 표시 여부 (수학 개념일 때)
  const [showCalculator, setShowCalculator] = useState(false);
  const isMathConcept = unit.type === 'CONCEPT_CORE' || unit.type === 'CONCEPT_FORM' || unit.type === 'CONCEPT_CONTENT';

  // 개념 설명 표시
  if (isMathConcept) {
    return (
      <>
        <ConceptViewer unit={unit} onSpeak={onSpeak} />
        {/* 수학 계산기 토글 버튼 - 모바일 최적화 */}
        <div className="flex justify-end mt-2">
          <button
            onClick={() => setShowCalculator(!showCalculator)}
            className="px-3 py-1.5 text-xs bg-primary text-primary-foreground rounded-md shadow-sm hover:bg-primary/90"
            aria-label="수식 계산기 열기"
          >
            {showCalculator ? '계산기 닫기' : '계산기 열기'}
          </button>
        </div>
        {showCalculator && <MathCalculator onClose={() => setShowCalculator(false)} />}
      </>
    );
  }

  // 작품 표시
  if (unit.type === 'PASSAGE') {
    return <WorkViewer unit={unit} onSpeak={onSpeak} />;
  }

  // 요약 표시 (점자 키워드 포함)
  if (unit.type === 'CONCEPT_SUMMARY') {
    return (
      <div className="space-y-4">
        <div className="bg-success/10 border border-success rounded-lg p-4">
          <h3 className="text-xl font-bold mb-2">{unit.title}</h3>
        </div>

        {/* 요약 내용 - 텍스트 표시 제거 (TTS로만 제공) */}
        {/* {unit.content_text && (
          <div className="prose max-w-none">
            <div className="whitespace-pre-wrap text-base leading-relaxed bg-card border border-border rounded-lg p-4">
              {unit.content_text}
            </div>
          </div>
        )} */}

        {/* 점자 키워드 */}
        {unit.braille_keywords && unit.braille_keywords.length > 0 && (
          <div className="bg-info/10 border border-info rounded-lg p-4">
            <h4 className="text-sm font-semibold text-info mb-2">핵심 점자 키워드</h4>
            <div className="flex flex-wrap gap-2">
              {unit.braille_keywords.map((keyword, index) => (
                <span
                  key={index}
                  className="px-3 py-1.5 bg-info/20 text-info border border-info/30 rounded-full text-sm font-medium"
                >
                  {keyword}
                </span>
              ))}
            </div>
          </div>
        )}
      </div>
    );
  }

  // 문제 표시
  if (unit.type === 'QUESTION' && unit.question) {
    // 이미지 경로 가져오기 (content_image_paths 우선, 없으면 image_path)
    const imagePaths = unit.content_image_paths || (unit.image_path ? [unit.image_path] : []);
    
    // 문제 텍스트 (추천 쿼리용)
    const questionText = unit.question.stem || unit.content_text || '';
    
    return (
      <div className="space-y-1.5">
        {/* 문제 이미지 표시 */}
        {imagePaths.length > 0 && (
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
                    loading="eager"
                    decoding="async"
                    onLoad={(e) => {
                      (e.target as HTMLImageElement).style.opacity = '1';
                      const placeholder = (e.target as HTMLImageElement).nextElementSibling as HTMLElement;
                      if (placeholder) placeholder.style.display = 'none';
                    }}
                    onError={(e) => {
                      console.error('[UnitViewer] 문제 이미지 로드 실패:', normalizedPath);
                      (e.target as HTMLImageElement).style.display = 'none';
                      const placeholder = (e.target as HTMLImageElement).nextElementSibling as HTMLElement;
                      if (placeholder) placeholder.style.display = 'flex';
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
        )}
        
        {/* 문제 지문 제거 (이미지에 포함됨) - 선택지만 표시 */}
        <div className="prose max-w-none">
          {/* 선택지 표시 (답안 선택용으로 필요) */}
          {unit.question.choices && unit.question.choices.length > 0 && (
            <div className="space-y-1.5">
              {unit.question.choices.map((choice, index) => (
                <div
                  key={index}
                  className="p-2 border border-border/50 rounded-md hover:bg-accent/10
                             hover:border-accent/30 transition-all duration-200
                             cursor-pointer"
                  style={{ background: 'linear-gradient(135deg, rgb(249, 250, 251) 0%, rgb(255, 255, 255) 100%)' }}
                >
                  <span className="font-semibold text-primary mr-1.5 text-sm">{index + 1}.</span>
                  <span className="text-sm">{choice}</span>
                </div>
              ))}
            </div>
          )}
        </div>
        {brailleCells.length > 0 && isConnected && (
          <BrailleCells data={brailleCells as any} />
        )}

        {/* RAG 기반 유사 문제 추천 */}
        {questionText && (
          <RAGRecommendationCard
            query={questionText.substring(0, 200)}
            unitId={unit.unit_id}
            lessonId={unit.lesson_id}
            contentType="problem"
            onSelect={(rec) => {
              // 추천된 문제로 이동하는 로직
              if (rec.metadata.unit_id && onSpeak) {
                onSpeak(`유사한 문제로 이동합니다. ${rec.text.substring(0, 50)}`);
                // TODO: 네비게이션 구현
                // navigate(`/unit/${rec.metadata.unit_id}`);
              }
            }}
          />
        )}
      </div>
    );
  }

  return (
    <div className="text-center py-8 text-muted">
      <p>내용이 없습니다.</p>
    </div>
  );
}
