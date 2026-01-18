/**
 * 현재 출력 중인 내용 패널 (공통)
 * 가운데 패널에 표시되는 현재 청크 내용
 */
import { ChevronLeft, ChevronRight, Repeat } from 'lucide-react';

interface CurrentContentPanelProps {
  chunk?: {
    id: number;
    text: string;
    cells: number[][];
    semanticType: string;
  };
  chunkIndex: number;
  totalChunks: number;
  onNext: () => void;
  onPrev: () => void;
  onRepeat: () => void;
}

export default function CurrentContentPanel({
  chunk,
  chunkIndex,
  totalChunks,
  onNext,
  onPrev,
  onRepeat
}: CurrentContentPanelProps) {
  if (!chunk) {
    return (
      <div className="flex-1 flex items-center justify-center bg-gray-50">
        <p className="text-gray-400">콘텐츠가 없습니다.</p>
      </div>
    );
  }

  return (
    <div className="flex-1 flex flex-col bg-white">
      {/* 진행도 표시 */}
      <div className="px-6 py-4 border-b border-gray-200 bg-gray-50">
        <div className="flex items-center justify-between">
          <span className="text-sm text-gray-600">
            현재 청크: {chunkIndex + 1} / {totalChunks}
          </span>
          <span className="text-xs text-gray-500">
            {chunk.semanticType}
          </span>
        </div>
        <div className="mt-2 w-full bg-gray-200 rounded-full h-2">
          <div
            className="bg-blue-600 h-2 rounded-full transition-all"
            style={{ width: `${((chunkIndex + 1) / totalChunks) * 100}%` }}
          />
        </div>
      </div>

      {/* 현재 내용 */}
      <div className="flex-1 overflow-y-auto px-6 py-8">
        <div className="max-w-3xl mx-auto">
          <div className="prose prose-lg">
            <p className="text-gray-800 leading-relaxed whitespace-pre-wrap">
              {chunk.text}
            </p>
          </div>
        </div>
      </div>

      {/* 탐색 버튼 (시각장애인용) */}
      <div className="px-6 py-4 border-t border-gray-200 bg-gray-50">
        <div className="flex items-center justify-center gap-4">
          <button
            onClick={onPrev}
            disabled={chunkIndex === 0}
            className="flex items-center gap-2 px-4 py-2 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            aria-label="이전 청크"
          >
            <ChevronLeft className="w-5 h-5" />
            <span>이전</span>
          </button>

          <button
            onClick={onRepeat}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            aria-label="반복"
          >
            <Repeat className="w-5 h-5" />
            <span>반복</span>
          </button>

          <button
            onClick={onNext}
            disabled={chunkIndex >= totalChunks - 1}
            className="flex items-center gap-2 px-4 py-2 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            aria-label="다음 청크"
          >
            <span>다음</span>
            <ChevronRight className="w-5 h-5" />
          </button>
        </div>
      </div>
    </div>
  );
}

