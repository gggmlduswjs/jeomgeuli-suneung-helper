/**
 * 학습 단위 뷰어 컴포넌트
 * 개념/작품/문제 타입별 통합 표시
 */
import { useEffect, useState } from 'react';
import { useBrailleChunkReader } from '../../hooks/useBrailleChunkReader';
import useBrailleBLE from '../../hooks/useBrailleBLE';
import type { Unit, UnitType } from '../../types/unit';
import { BrailleCells } from '../braille/BrailleCells';
import ConceptViewer from './ConceptViewer';
import WorkViewer from './WorkViewer';

interface UnitViewerProps {
  unit: Unit;
  onSpeak?: (text: string) => void;
  readingMode?: 'braille-only' | 'audio-first' | 'mixed';
}

export default function UnitViewer({ unit, onSpeak, readingMode = 'braille-only' }: UnitViewerProps) {
  const { isConnected, writeCells } = useBrailleBLE();
  const [brailleCells, setBrailleCells] = useState<number[][]>([]);

  // 텍스트를 점자로 변환
  useEffect(() => {
    if (unit.braille_text) {
      // 점자 텍스트가 있으면 사용
      // TODO: 점자 텍스트를 셀 배열로 변환
    } else if (unit.content_text) {
      // 텍스트를 점자로 변환
      // TODO: text_to_cells 함수 사용
    }
  }, [unit]);

  // 개념 설명 표시
  if (unit.type === 'CONCEPT_CORE' || unit.type === 'CONCEPT_FORM' || unit.type === 'CONCEPT_CONTENT') {
    return <ConceptViewer unit={unit} onSpeak={onSpeak} />;
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

        {/* 요약 내용 */}
        {unit.content_text && (
          <div className="prose max-w-none">
            <div className="whitespace-pre-wrap text-base leading-relaxed bg-card border border-border rounded-lg p-4">
              {unit.content_text}
            </div>
          </div>
        )}

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
    return (
      <div className="space-y-4">
        <div className="bg-gradient-to-br from-warning/10 to-warning/5 border border-warning/30 rounded-2xl p-5 shadow-soft">
          <h3 className="text-xl font-bold mb-2 text-fg">{unit.title}</h3>
        </div>
        
        {/* 문제 이미지 표시 */}
        {unit.image_path && (
          <div className="border border-border/50 rounded-2xl p-4 shadow-soft overflow-hidden"
               style={{ background: 'linear-gradient(135deg, rgb(249, 250, 251) 0%, rgb(255, 255, 255) 100%)' }}>
            <img 
              src={unit.image_path} 
              alt={unit.title}
              className="w-full h-auto rounded-lg"
              onError={(e) => {
                // 이미지 로드 실패 시 숨김
                (e.target as HTMLImageElement).style.display = 'none';
              }}
            />
          </div>
        )}
        
        <div className="prose max-w-none">
          {/* 문제 지문 표시 (이미지가 없거나 텍스트가 더미가 아닌 경우) */}
          {unit.question.stem && !unit.question.stem.includes('(페이지') && (
            <div 
              className="border border-border/50 rounded-2xl p-5 mb-4 shadow-soft"
              style={{ background: 'linear-gradient(135deg, rgb(249, 250, 251) 0%, rgb(255, 255, 255) 100%)' }}
            >
              <p className="text-base leading-relaxed text-fg whitespace-pre-wrap">{unit.question.stem}</p>
            </div>
          )}
          
          {/* 선택지 표시 */}
          {unit.question.choices && unit.question.choices.length > 0 && (
            <div className="space-y-3">
              {unit.question.choices.map((choice, index) => (
                <div 
                  key={index} 
                  className="p-4 border border-border/50 rounded-xl hover:bg-accent/10 
                             hover:border-accent/30 transition-all duration-300 hover:shadow-soft
                             cursor-pointer hover:scale-[1.01]"
                  style={{ background: 'linear-gradient(135deg, rgb(249, 250, 251) 0%, rgb(255, 255, 255) 100%)' }}
                >
                  <span className="font-semibold text-primary mr-2">{index + 1}.</span>
                  {choice}
                </div>
              ))}
            </div>
          )}
        </div>
        {brailleCells.length > 0 && isConnected && (
          <BrailleCells data={brailleCells} />
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
