/**
 * 청크 네비게이션 UI 컴포넌트
 * 점자 청크를 순차적으로 탐색할 수 있는 UI
 */
import { useBrailleChunkReader, type UseBrailleChunkReaderReturn } from '../../hooks/useBrailleChunkReader';

interface ChunkNavigationProps {
  chunkReader: UseBrailleChunkReaderReturn;
  label?: string;
  className?: string;
}

export default function ChunkNavigation({ 
  chunkReader, 
  label = '점자 청크',
  className = '' 
}: ChunkNavigationProps) {
  if (chunkReader.totalChunks <= 1) {
    return null; // 청크가 1개 이하면 네비게이션 불필요
  }

  return (
    <div className={`bg-accent/10 border border-accent/20 rounded-lg p-3 ${className}`}>
      <div className="flex items-center justify-between mb-2">
        <span className="text-sm font-medium">{label}</span>
        <span className="text-xs text-muted">
          {chunkReader.currentIndex + 1} / {chunkReader.totalChunks}
        </span>
      </div>
      
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
        {chunkReader.isPlaying ? (
          <button
            onClick={chunkReader.pause}
            className="btn-ghost text-xs px-2 py-1"
            aria-label="일시정지"
          >
            일시정지
          </button>
        ) : (
          <button
            onClick={chunkReader.play}
            className="btn-ghost text-xs px-2 py-1"
            aria-label="자동 재생"
          >
            자동 재생
          </button>
        )}
      </div>
      
      {chunkReader.currentChunk && (
        <p className="text-xs text-muted mt-2">
          현재: {chunkReader.currentChunk.substring(0, 30)}
          {chunkReader.currentChunk.length > 30 ? '...' : ''}
        </p>
      )}
    </div>
  );
}

