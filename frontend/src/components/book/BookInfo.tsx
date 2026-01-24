/**
 * 교재 정보 표시 컴포넌트
 */
import type { Book } from '../../types/book';

interface BookInfoProps {
  book: Book;
  parseProgress: number;
  onReparse: () => void;
  onSyncFromJson: () => void;
  onRecreateCurriculum: () => void;
  loading: boolean;
}

export default function BookInfo({
  book,
  parseProgress,
  onReparse,
  onSyncFromJson,
  onRecreateCurriculum,
  loading
}: BookInfoProps) {
  return (
    <div className="bg-card border border-border rounded-lg p-4">
      <h2 className="text-xl font-bold mb-2">{book.title}</h2>
      <div className="text-sm text-muted space-y-1">
        <p>과목: {book.subject}</p>
        {book.year && <p>연도: {book.year}</p>}
        <p>강 수: {book.lesson_count || 0}개</p>
        <p>상태: {book.parse_status}</p>
      </div>

      {/* 파싱 진행 상태 */}
      {book.parse_status === 'PROCESSING' && (
        <div className="mt-4">
          <div className="flex justify-between text-xs text-muted mb-1">
            <span>파싱 중...</span>
            <span>{parseProgress}%</span>
          </div>
          <div className="w-full bg-muted rounded-full h-2">
            <div
              className="bg-primary h-2 rounded-full transition-all"
              style={{ width: `${parseProgress}%` }}
            />
          </div>
        </div>
      )}

      {/* 파싱 실패 시 재파싱 버튼 */}
      {book.parse_status === 'FAILED' && (
        <div className="mt-4">
          <div className="bg-error/10 border border-error rounded-lg p-3 mb-3">
            <p className="text-error text-sm mb-2">파싱에 실패했습니다.</p>
            <p className="text-xs text-muted">파일을 확인하거나 재파싱을 시도해보세요.</p>
          </div>
          <button
            onClick={onReparse}
            disabled={loading}
            className="w-full px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? '재파싱 중...' : '재파싱 시도'}
          </button>
        </div>
      )}

      {/* 커리큘럼 재생성 및 JSON 동기화 버튼 */}
      {book.parse_status === 'DONE' && (
        <div className="mt-4 space-y-2">
          <div className="flex gap-2">
            <button
              onClick={onSyncFromJson}
              disabled={loading}
              className="flex-1 px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {loading ? '동기화 중...' : 'JSON 동기화'}
            </button>
            <button
              onClick={onRecreateCurriculum}
              disabled={loading}
              className="flex-1 px-4 py-2 bg-warning/10 text-warning border border-warning rounded-lg hover:bg-warning/20 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {loading ? '재생성 중...' : '커리큘럼 재생성'}
            </button>
          </div>
          <p className="text-xs text-muted">
            <strong>JSON 동기화:</strong> JSON 파일을 읽어서 DB에 저장 (빠름)<br />
            <strong>커리큘럼 재생성:</strong> 전체 파이프라인 데이터로부터 재생성
          </p>
        </div>
      )}
    </div>
  );
}
