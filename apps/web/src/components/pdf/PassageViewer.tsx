import React, { useState } from 'react';
import { Passage } from '../../lib/api/pdf';
import { brailleAPI } from '../../lib/api/BrailleAPI';
import useBrailleBLE from '../../hooks/useBrailleBLE';

interface PassageViewerProps {
  passage: Passage;
  showBraille?: boolean;
  showImage?: boolean;
}

export function PassageViewer({ 
  passage, 
  showBraille = true,
  showImage = true
}: PassageViewerProps) {
  const [viewMode, setViewMode] = useState<'text' | 'image' | 'both'>('both');
  const { isConnected, writeCells } = useBrailleBLE();
  
  // 점자 디바이스에 전송
  const sendToBraille = async (text: string) => {
    if (isConnected && showBraille) {
      try {
        const result = await brailleAPI.convertBraille(text, 'word');
        const cells = (result && 'cells' in result ? result.cells : result) as number[][];
        if (cells && Array.isArray(cells)) {
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
        console.error('[PassageViewer] 점자 변환 실패:', error);
      }
    }
  };

  return (
    <div className="passage-viewer space-y-4 p-4 border rounded-lg">
      <h3 className="text-xl font-bold">{passage.title || '본문'}</h3>
      
      {/* 뷰 모드 선택 */}
      {showImage && passage.image && (
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
      {showImage && passage.image && viewMode !== 'text' && (
        <div className="passage-image">
          <img 
            src={passage.image} 
            alt={passage.title || '본문 원본'}
            className="pdf-capture-image max-w-full h-auto border rounded"
            style={{ maxWidth: '100%', height: 'auto' }}
          />
          <p className="image-meta text-sm text-gray-500 mt-2">페이지: {passage.page}</p>
        </div>
      )}
      
      {/* 텍스트 표시 */}
      {viewMode !== 'image' && (
        <div className="passage-content">
          <p className="text-base leading-relaxed whitespace-pre-wrap">{passage.content}</p>
          {showBraille && passage.content_braille && (
            <div className="mt-2 p-2 bg-gray-100 rounded">
              <p className="text-sm font-mono">{passage.content_braille}</p>
              <button
                onClick={() => sendToBraille(passage.content)}
                className="mt-2 px-2 py-1 text-xs bg-blue-500 text-white rounded"
                disabled={!isConnected}
              >
                점자 디바이스로 전송
              </button>
            </div>
          )}
        </div>
      )}
      
      <div className="passage-meta text-sm text-gray-500">
        <span>페이지: {passage.page}</span>
      </div>
    </div>
  );
}
