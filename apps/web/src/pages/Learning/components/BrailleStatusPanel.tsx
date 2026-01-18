/**
 * 점자 출력 상태 패널 (보호자용)
 * 오른쪽 패널에 표시되는 점자 셀 상태
 */
import { Wifi, WifiOff } from 'lucide-react';

interface BrailleStatusPanelProps {
  currentChunk?: {
    id: number;
    text: string;
    cells: number[][];
    semanticType: string;
  };
  isConnected: boolean;
  chunkIndex: number;
  totalChunks: number;
}

export default function BrailleStatusPanel({
  currentChunk,
  isConnected,
  chunkIndex,
  totalChunks
}: BrailleStatusPanelProps) {
  // 점자 셀을 시각적으로 표시
  const renderBrailleCell = (cell: number[]) => {
    // 6-dot braille 패턴
    // [1, 2, 3]
    // [4, 5, 6]
    const dots = [
      cell[0] || 0, // dot 1 (top-left)
      cell[1] || 0, // dot 2 (middle-left)
      cell[2] || 0, // dot 3 (bottom-left)
      cell[3] || 0, // dot 4 (top-right)
      cell[4] || 0, // dot 5 (middle-right)
      cell[5] || 0, // dot 6 (bottom-right)
    ];

    return (
      <div className="relative w-8 h-12 border border-gray-300 rounded bg-white">
        <div className="absolute inset-0 grid grid-cols-2 gap-0.5 p-1">
          {dots.map((dot, idx) => (
            <div
              key={idx}
              className={`w-2 h-2 rounded-full ${
                dot ? 'bg-gray-900' : 'bg-gray-200'
              }`}
            />
          ))}
        </div>
      </div>
    );
  };

  return (
    <div className="h-full flex flex-col">
      {/* 헤더 */}
      <div className="p-4 border-b border-gray-200 bg-gray-50">
        <div className="flex items-center justify-between">
          <h3 className="text-sm font-semibold text-gray-700">점자 출력 상태</h3>
          <div className="flex items-center gap-2">
            {isConnected ? (
              <>
                <Wifi className="w-4 h-4 text-green-600" />
                <span className="text-xs text-green-600">연결됨</span>
              </>
            ) : (
              <>
                <WifiOff className="w-4 h-4 text-gray-400" />
                <span className="text-xs text-gray-400">연결 안 됨</span>
              </>
            )}
          </div>
        </div>
      </div>

      {/* 현재 청크 정보 */}
      <div className="p-4 border-b border-gray-200">
        <div className="text-xs text-gray-600 mb-2">
          청크 {chunkIndex + 1} / {totalChunks}
        </div>
        <div className="text-sm font-medium text-gray-800 mb-1">
          {currentChunk?.semanticType || 'N/A'}
        </div>
        <div className="text-xs text-gray-500 line-clamp-2">
          {currentChunk?.text || '콘텐츠 없음'}
        </div>
      </div>

      {/* 점자 셀 미리보기 */}
      <div className="flex-1 overflow-y-auto p-4">
        {currentChunk?.cells ? (
          <div className="space-y-4">
            <div className="text-xs font-semibold text-gray-700 mb-2">
              3-Cell 패킷
            </div>
            <div className="flex gap-2 flex-wrap">
              {currentChunk.cells.map((packet, packetIdx) => (
                <div key={packetIdx} className="flex gap-1">
                  {packet.map((cell, cellIdx) => (
                    <div key={cellIdx}>
                      {renderBrailleCell(Array.isArray(cell) ? cell : [])}
                    </div>
                  ))}
                </div>
              ))}
            </div>
          </div>
        ) : (
          <div className="flex items-center justify-center h-full text-gray-400 text-sm">
            점자 데이터가 없습니다.
          </div>
        )}
      </div>
    </div>
  );
}

