import React, { useState } from 'react';
import { Question, Choice } from '../../lib/api/pdf';
import { brailleAPI } from '../../lib/api/BrailleAPI';
import useBrailleBLE from '../../hooks/useBrailleBLE';

interface QuestionViewerProps {
  question: Question;
  showBraille?: boolean;
  showImage?: boolean;
}

export function QuestionViewer({ 
  question, 
  showBraille = true,
  showImage = true
}: QuestionViewerProps) {
  const [viewMode, setViewMode] = useState<'text' | 'image' | 'both'>('both');
  const { isConnected, writeCells } = useBrailleBLE();
  
  // 점자 디바이스에 전송
  const sendToBraille = async (text: string) => {
    if (isConnected && showBraille) {
      try {
        const result = await brailleAPI.convertBraille(text, 'word');
        const cells = (result && 'cells' in result ? result.cells : result) as number[][];
        if (cells && Array.isArray(cells)) {
          // 3-cell 패킷으로 전송
          const packets: number[][] = [];
          for (let i = 0; i < cells.length; i += 3) {
            packets.push(cells.slice(i, i + 3).flat());
          }
          for (const packet of packets) {
            if (packet.length > 0) {
              await writeCells([packet]);
            }
          }
        }
      } catch (error) {
        console.error('[QuestionViewer] 점자 변환 실패:', error);
      }
    }
  };

  return (
    <div className="question-viewer space-y-4 p-4 border rounded-lg">
      <h3 className="text-xl font-bold">문제 {question.number}번</h3>
      
      {/* 뷰 모드 선택 */}
      {showImage && question.image && (
        <div className="view-mode-selector flex gap-2">
          <button 
            onClick={() => setViewMode('text')}
            className={`px-3 py-1 rounded ${viewMode === 'text' ? 'bg-blue-500 text-white' : 'bg-gray-200'}`}
            aria-label="텍스트만 보기"
          >
            텍스트
          </button>
          <button 
            onClick={() => setViewMode('image')}
            className={`px-3 py-1 rounded ${viewMode === 'image' ? 'bg-blue-500 text-white' : 'bg-gray-200'}`}
            aria-label="원본 이미지만 보기"
          >
            원본 이미지
          </button>
          <button 
            onClick={() => setViewMode('both')}
            className={`px-3 py-1 rounded ${viewMode === 'both' ? 'bg-blue-500 text-white' : 'bg-gray-200'}`}
            aria-label="텍스트와 이미지 모두 보기"
          >
            둘 다
          </button>
        </div>
      )}
      
      {/* 원본 이미지 표시 */}
      {showImage && question.image && viewMode !== 'text' && (
        <div className="question-image">
          <img 
            src={question.image} 
            alt={`문제 ${question.number}번 원본`}
            className="pdf-capture-image max-w-full h-auto border rounded"
            style={{ maxWidth: '100%', height: 'auto' }}
          />
          {question.page && (
            <p className="image-meta text-sm text-gray-500 mt-2">페이지: {question.page}</p>
          )}
        </div>
      )}
      
      {/* 텍스트 표시 */}
      {viewMode !== 'image' && (
        <>
          {/* 문제 지문 */}
          <div className="question-stem">
            <p className="text-base leading-relaxed">{question.stem}</p>
            {showBraille && question.stem_braille && (
              <div className="mt-2 p-2 bg-gray-100 rounded">
                <p className="text-sm font-mono">{question.stem_braille}</p>
                <button
                  onClick={() => sendToBraille(question.stem)}
                  className="mt-2 px-2 py-1 text-xs bg-blue-500 text-white rounded"
                  disabled={!isConnected}
                >
                  점자 디바이스로 전송
                </button>
              </div>
            )}
          </div>
          
          {/* 선택지 */}
          <div className="question-choices space-y-2">
            {question.choices.map((choice, idx) => (
              <div key={idx} className="choice-item flex items-start gap-2 p-2 border rounded">
                <span className="choice-number font-bold">{choice.number}</span>
                <span className="choice-text flex-1">{choice.text}</span>
                {showBraille && choice.text_braille && (
                  <div className="mt-1 text-sm font-mono text-gray-600">
                    {choice.text_braille}
                  </div>
                )}
              </div>
            ))}
          </div>
        </>
      )}
      
      {/* 정답 및 해설 (학습 모드) */}
      {question.answer && (
        <div className="question-answer p-3 bg-green-50 border border-green-200 rounded">
          <p className="font-bold">정답: {question.answer}</p>
          {question.explanation && (
            <p className="mt-2">해설: {question.explanation}</p>
          )}
        </div>
      )}
    </div>
  );
}
