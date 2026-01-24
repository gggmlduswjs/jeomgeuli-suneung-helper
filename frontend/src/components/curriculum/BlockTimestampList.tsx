/**
 * 블록 타임스탬프 목록 컴포넌트
 * 각 블록의 타임스탬프를 표시하고 클릭 시 해당 위치로 이동
 */
import { timestampManager, type BlockTimestamp } from '../../utils/audioNotification';
import { playNotificationSound } from '../../utils/audioNotification';

interface BlockTimestampListProps {
  onJumpToBlock: (blockId: string) => void;
  currentBlockId?: string;
}

export default function BlockTimestampList({ 
  onJumpToBlock, 
  currentBlockId 
}: BlockTimestampListProps) {
  const timestamps = timestampManager.getAllTimestamps();

  if (timestamps.length === 0) {
    return null;
  }

  const formatTime = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const getTextTypeLabel = (textType?: string): string => {
    switch (textType) {
      case 'explanation':
        return '해설';
      case 'note':
        return '필기';
      case 'instruction':
        return '지시';
      default:
        return '';
    }
  };

  return (
    <div className="bg-card border border-border rounded-lg p-4">
      <h3 className="font-semibold text-sm mb-3">블록 목록</h3>
      <div className="space-y-2 max-h-64 overflow-y-auto">
        {timestamps.map((timestamp) => {
          const isCurrent = timestamp.block_id === currentBlockId || 
                           timestamp.unit_id === currentBlockId;
          
          return (
            <button
              key={timestamp.block_id || timestamp.unit_id}
              onClick={() => {
                playNotificationSound('section');
                onJumpToBlock(timestamp.block_id || timestamp.unit_id);
              }}
              className={`
                w-full text-left px-3 py-2 rounded-lg border transition-colors
                ${isCurrent 
                  ? 'bg-primary/10 border-primary text-primary' 
                  : 'bg-muted/50 border-border hover:bg-muted'
                }
              `}
            >
              <div className="flex items-center justify-between">
                <div className="flex-1">
                  <div className="text-sm font-medium">
                    {formatTime(timestamp.timestamp)}
                  </div>
                  <div className="text-xs text-muted mt-1">
                    {timestamp.block_type}
                    {timestamp.text_type && (
                      <span className="ml-2 text-primary">
                        [{getTextTypeLabel(timestamp.text_type)}]
                      </span>
                    )}
                  </div>
                </div>
                {isCurrent && (
                  <span className="text-xs text-primary font-bold">현재</span>
                )}
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
}
