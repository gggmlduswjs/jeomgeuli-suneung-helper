import React from 'react';
import { QuestionViewer } from '../../../components/pdf/QuestionViewer';
import { PassageViewer } from '../../../components/pdf/PassageViewer';
import UnitContent from './UnitContent';
import type { Unit } from '../../../lib/api';
import type { StructuredContent } from '../../../lib/api/pdf';

interface PDFStructuredViewerProps {
  unit: Unit | null;
  structuredContent?: StructuredContent;
  onSpeak?: (text: string) => void;
  readingMode?: 'braille-only' | 'audio-first' | 'mixed';
}

export function PDFStructuredViewer({ 
  unit, 
  structuredContent,
  onSpeak,
  readingMode = 'braille-only'
}: PDFStructuredViewerProps) {
  // 구조화된 콘텐츠가 있으면 구조화된 뷰어 사용
  if (structuredContent) {
    return (
      <div className="pdf-structured-viewer space-y-6">
        {/* 본문 먼저 표시 */}
        {structuredContent.passages?.map((passage, idx) => (
          <PassageViewer 
            key={idx} 
            passage={passage}
            showBraille={readingMode !== 'audio-first'}
            showImage={true}
          />
        ))}
        
        {/* 문제 표시 */}
        {structuredContent.questions?.map((question) => (
          <QuestionViewer 
            key={question.number || `q-${question.page}-${question.position}`}
            question={question}
            showBraille={readingMode !== 'audio-first'}
            showImage={true}
          />
        ))}
      </div>
    );
  }
  
  // 기존 UnitContent 사용 (fallback)
  return <UnitContent unit={unit} onSpeak={onSpeak || (() => {})} readingMode={readingMode} />;
}
