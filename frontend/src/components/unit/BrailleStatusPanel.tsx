/**
 * 점자 상태 표시 패널 컴포넌트
 */
interface BrailleStatusPanelProps {
  brailleStatus: 'pending' | 'converting' | 'completed' | 'failed';
  isConnected: boolean;
  chunkReader: {
    currentIndex: number;
    totalChunks: number;
    next: () => void;
    prev: () => void;
    reset: () => void;
  };
}

export default function BrailleStatusPanel({
  brailleStatus,
  isConnected,
  chunkReader,
}: BrailleStatusPanelProps) {
  return (
    <div className="bg-accent/10 border border-accent/20 rounded-lg p-3">
      {brailleStatus === 'pending' && (
        <p className="text-sm text-muted">점자 변환 대기 중...</p>
      )}
      {brailleStatus === 'converting' && (
        <p className="text-sm text-muted">점자 변환 중입니다. 잠시만 기다려주세요.</p>
      )}
      {brailleStatus === 'completed' && (
        <div className="space-y-2">
          <p className="text-sm font-medium">점자 읽기 모드</p>
          {isConnected && chunkReader.totalChunks > 1 && (
            <div className="flex items-center justify-between">
              <span className="text-xs text-muted">
                {chunkReader.currentIndex + 1} / {chunkReader.totalChunks}
              </span>
              <div className="flex gap-2">
                <button
                  onClick={chunkReader.prev}
                  disabled={chunkReader.currentIndex === 0}
                  className="btn-ghost text-xs px-2 py-1 disabled:opacity-50"
                  aria-label="이전 청크"
                >
                  ← 이전
                </button>
                <button
                  onClick={chunkReader.next}
                  disabled={chunkReader.currentIndex >= chunkReader.totalChunks - 1}
                  className="btn-ghost text-xs px-2 py-1 disabled:opacity-50"
                  aria-label="다음 청크"
                >
                  다음 →
                </button>
                <button
                  onClick={chunkReader.reset}
                  className="btn-ghost text-xs px-2 py-1"
                  aria-label="처음으로"
                >
                  처음
                </button>
              </div>
            </div>
          )}
        </div>
      )}
      {brailleStatus === 'failed' && (
        <p className="text-sm text-error">점자 변환에 실패했습니다. 다시 시도해주세요.</p>
      )}
    </div>
  );
}
