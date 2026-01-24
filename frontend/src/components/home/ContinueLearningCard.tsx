/**
 * 오늘 학습 이어하기 카드
 * 보호자용 시각 UI + 시각장애인용 음성 안내
 */
import { useEffect, useState } from 'react';
import { BookOpen, Play } from 'lucide-react';
import { booksAPI, lessonsAPI, unitsAPI } from '../../services/api/client';
import type { Progress } from '../../types/progress';
import type { Book } from '../../types/book';
import type { Lesson } from '../../types/lesson';
import type { Unit } from '../../types/unit';

interface ContinueLearningCardProps {
  progress?: Progress | null;
  onContinue?: () => void;
}

export default function ContinueLearningCard({
  progress,
  onContinue,
}: ContinueLearningCardProps) {
  const [book, setBook] = useState<Book | null>(null);
  const [lesson, setLesson] = useState<Lesson | null>(null);
  const [unit, setUnit] = useState<Unit | null>(null);
  const [loading, setLoading] = useState(false);

  // progress가 변경되면 실제 데이터 로드
  useEffect(() => {
    if (progress?.unit_id) {
      loadProgressData();
    } else {
      setBook(null);
      setLesson(null);
      setUnit(null);
    }
  }, [progress?.unit_id, progress?.lesson_id, progress?.book_id]);

  const loadProgressData = async () => {
    if (!progress) return;
    
    setLoading(true);
    try {
      // Unit 정보 로드
      if (progress.unit_id) {
        try {
          const unitData = await unitsAPI.get(progress.unit_id);
          setUnit(unitData);
          
          // Lesson 정보 로드
          if (unitData.lesson_id) {
            try {
              const lessonData = await lessonsAPI.get(unitData.lesson_id);
              setLesson(lessonData);
              
              // Book 정보 로드
              if (lessonData.book_id) {
                try {
                  const bookData = await booksAPI.get(lessonData.book_id);
                  setBook(bookData);
                } catch (err) {
                  console.error('[ContinueLearningCard] Book 로드 실패:', err);
                }
              }
            } catch (err) {
              console.error('[ContinueLearningCard] Lesson 로드 실패:', err);
            }
          }
        } catch (err) {
          console.error('[ContinueLearningCard] Unit 로드 실패:', err);
        }
      }
    } catch (err) {
      console.error('[ContinueLearningCard] 데이터 로드 실패:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleContinue = () => {
    if (onContinue) {
      onContinue();
    } else if (progress?.unit_id) {
      // Unit 페이지로 이동
      window.location.href = `/unit/${progress.unit_id}`;
    }
  };

  if (!progress || !progress.unit_id) {
    return (
      <div className="bg-card border border-border rounded-lg p-4">
        <div className="flex items-center gap-3 mb-2">
          <BookOpen className="w-5 h-5 text-muted-foreground" />
          <h3 className="text-base font-semibold text-foreground">오늘 학습 이어하기</h3>
        </div>
        <p className="text-muted-foreground text-sm">진행 중인 학습이 없습니다.</p>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="bg-card border border-border rounded-lg p-4">
        <div className="flex items-center gap-3 mb-2">
          <BookOpen className="w-5 h-5 text-primary" />
          <h3 className="text-base font-semibold">오늘 학습 이어하기</h3>
        </div>
        <p className="text-muted-foreground text-sm">로딩 중...</p>
      </div>
    );
  }

  return (
    <div className="bg-primary/10 border border-primary/30 rounded-lg p-4">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <BookOpen className="w-5 h-5 text-primary" />
          <h3 className="text-base font-semibold">오늘 학습 이어하기</h3>
        </div>
        <button
          onClick={handleContinue}
          className="flex items-center gap-2 px-3 py-1.5 bg-primary text-white rounded-lg hover:bg-primary/90 transition-colors text-sm"
          aria-label="학습 이어하기"
        >
          <Play className="w-4 h-4" />
          <span>계속하기</span>
        </button>
      </div>
      
      <div className="space-y-1">
        {book && (
          <p className="text-sm font-medium text-foreground">
            {book.title}
          </p>
        )}
        {lesson && (
          <p className="text-sm text-muted-foreground">
            {lesson.title}
          </p>
        )}
        {unit && (
          <p className="text-xs text-muted-foreground">
            {unit.title}
          </p>
        )}
        {!book && !lesson && !unit && (
          <p className="text-sm text-muted-foreground">
            학습 위치를 불러오는 중...
          </p>
        )}
      </div>
    </div>
  );
}

