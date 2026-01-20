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

  // 문제 표시
  if (unit.type === 'QUESTION' && unit.question) {
    return (
      <div className="space-y-4">
        <div className="bg-warning/10 border border-warning rounded-lg p-4">
          <h3 className="text-xl font-bold mb-2">{unit.title}</h3>
        </div>
        <div className="prose max-w-none">
          <div className="bg-card border border-border rounded-lg p-4 mb-4">
            <p className="text-base leading-relaxed">{unit.question.stem}</p>
          </div>
          <div className="space-y-2">
            {unit.question.choices.map((choice, index) => (
              <div key={index} className="p-3 border border-border rounded-lg hover:bg-accent/50 transition-colors">
                {choice}
              </div>
            ))}
          </div>
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
