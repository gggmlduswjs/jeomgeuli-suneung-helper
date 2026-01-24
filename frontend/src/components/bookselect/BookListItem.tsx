/**
 * 교재 목록 아이템 컴포넌트
 */
import type { Book } from '../../types/book';

interface BookListItemProps {
  book: Book;
  index: number;
  isSelected: boolean;
  isReparsing: boolean;
  isParsing: boolean;
  onSelect: () => void;
  onReparse: () => void;
  onSyncFromJson: () => void;
  onDelete: () => void;
  onMouseEnter: () => void;
}

export default function BookListItem({
  book,
  index,
  isSelected,
  isReparsing,
  isParsing,
  onSelect,
  onReparse,
  onSyncFromJson,
  onDelete,
  onMouseEnter
}: BookListItemProps) {
  const isParsed = book.parse_status === 'DONE';
  const isProcessing = book.parse_status === 'PROCESSING' || isParsing;
  const isFailed = book.parse_status === 'FAILED';

  return (
    <div
      onMouseEnter={onMouseEnter}
      className={`w-full rounded-2xl transition-all duration-300 ${!isParsed && !isFailed
        ? 'bg-muted/50 border border-border/50 opacity-60'
        : isSelected
          ? 'border-2 border-primary shadow-soft-lg scale-[1.01]'
          : 'border border-border/50 shadow-soft hover:shadow-soft-lg hover:border-primary/30'
        }`}
      style={!isParsed && !isFailed ? {} : isSelected
        ? { background: 'rgba(49, 130, 246, 0.1)' }
        : { background: 'linear-gradient(135deg, rgb(249, 250, 251) 0%, rgb(255, 255, 255) 100%)' }}
    >
      <button
        onClick={() => isParsed && onSelect()}
        disabled={!isParsed || isReparsing}
        className="w-full p-5 text-left"
        aria-label={`${index + 1}번: ${book.title}${!isParsed ? ' (사용 불가)' : ''}`}
      >
        <div className="flex items-center justify-between mb-2">
          <span className="text-lg font-semibold">
            [{index + 1}] {book.title}
          </span>
          {isProcessing && (
            <span className="text-xs px-3 py-1.5 bg-primary/10 text-primary rounded-full font-medium border border-primary/20 animate-pulse-slow">
              {isReparsing ? '재파싱 중' : '파싱 중'}
            </span>
          )}
          {isFailed && !isReparsing && (
            <span className="text-xs px-3 py-1.5 bg-danger/10 text-danger rounded-full font-medium border border-danger/20">
              실패
            </span>
          )}
        </div>
        <div className="text-sm opacity-90">
          <p>강 {book.lesson_count || 0}개</p>
          {book.year && <p>{book.year}년</p>}
          {!isParsed && !isReparsing && (
            <p className="text-xs text-warning mt-1">
              {isProcessing
                ? '교재 처리 중입니다'
                : '교재를 사용할 수 없습니다'}
            </p>
          )}
        </div>
      </button>

      {/* Action buttons */}
      <div className="px-4 pb-4 flex gap-2 flex-wrap">
        {/* JSON 동기화 버튼 (파싱 완료된 모든 교재에 표시) */}
        {isParsed && !isReparsing && (
          <button
            onClick={(e) => {
              e.stopPropagation();
              onSyncFromJson();
            }}
            className="flex-1 px-4 py-2.5 text-sm bg-primary/10 text-primary border border-primary/30 rounded-xl
                       hover:bg-primary/20 hover:border-primary/50 transition-all duration-300
                       hover:shadow-soft font-medium min-w-[120px]"
            aria-label="JSON 동기화"
          >
            JSON 동기화
          </button>
        )}

        {/* Reparse button for failed books or when no lessons */}
        {(isFailed || (book.lesson_count === 0 && isParsed)) && !isReparsing && (
          <button
            onClick={(e) => {
              e.stopPropagation();
              onReparse();
            }}
            className="flex-1 px-4 py-2.5 text-sm bg-warning/10 text-warning border border-warning/30 rounded-xl
                       hover:bg-warning/20 hover:border-warning/50 transition-all duration-300
                       hover:shadow-soft font-medium min-w-[120px]"
            aria-label="R키: 재파싱"
          >
            [R] 재파싱
          </button>
        )}

        {/* Delete button for all books (when selected) */}
        {!isReparsing && isSelected && (
          <button
            onClick={(e) => {
              e.stopPropagation();
              onDelete();
            }}
            className="flex-1 px-4 py-2.5 text-sm bg-danger/10 text-danger border border-danger/30 rounded-xl
                       hover:bg-danger/20 hover:border-danger/50 transition-all duration-300
                       hover:shadow-soft font-medium min-w-[120px]"
            aria-label="D키: 삭제"
          >
            [D] 삭제
          </button>
        )}
      </div>
    </div>
  );
}
