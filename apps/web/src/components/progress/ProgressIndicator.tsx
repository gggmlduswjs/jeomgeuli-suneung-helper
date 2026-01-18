/**
 * 진도 표시 컴포넌트
 */
import type { Progress } from '../../types/progress';

interface ProgressIndicatorProps {
  progress: Progress;
}

export default function ProgressIndicator({ progress }: ProgressIndicatorProps) {
  return (
    <div className="bg-accent/10 border border-accent/20 rounded-lg p-3">
      <h3 className="text-sm font-semibold mb-2">현재 학습 위치</h3>
      <div className="space-y-1 text-xs">
        {progress.book_id && (
          <div>
            <span className="text-muted">교재:</span> {progress.book_id}
          </div>
        )}
        {progress.lesson_id && (
          <div>
            <span className="text-muted">강:</span> {progress.lesson_id}
          </div>
        )}
        {progress.unit_id && (
          <div>
            <span className="text-muted">단위:</span> {progress.unit_id}
          </div>
        )}
        {progress.updated_at && (
          <div className="text-muted mt-2">
            마지막 업데이트: {new Date(progress.updated_at).toLocaleString('ko-KR')}
          </div>
        )}
      </div>
    </div>
  );
}
