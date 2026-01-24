/**
 * 강의 목록 표시 컴포넌트
 */
import type { Lesson } from '../../types/lesson';

interface LessonListProps {
  lessons: Lesson[];
  onLessonSelect: (lesson: Lesson) => void;
}

export default function LessonList({ lessons, onLessonSelect }: LessonListProps) {
  if (lessons.length === 0) {
    return null;
  }

  return (
    <div className="space-y-2">
      <h3 className="text-lg font-semibold">강 목록</h3>
      {lessons.map((lesson) => {
        const hasContent = (lesson.unit_count && lesson.unit_count > 0) || (lesson.question_count && lesson.question_count > 0);
        return (
          <button
            key={lesson.lesson_id}
            onClick={() => onLessonSelect(lesson)}
            className={`w-full p-4 text-left bg-card border rounded-lg transition-colors ${hasContent
              ? 'border-border hover:border-primary'
              : 'border-warning/50 hover:border-warning'
              }`}
          >
            <div className="font-medium">{lesson.title}</div>
            <div className="text-sm text-muted mt-1">
              단위 {lesson.unit_count || 0}개, 문제 {lesson.question_count || 0}개
              {!hasContent && (
                <span className="ml-2 text-warning text-xs">(콘텐츠 준비 중)</span>
              )}
            </div>
          </button>
        );
      })}
    </div>
  );
}
