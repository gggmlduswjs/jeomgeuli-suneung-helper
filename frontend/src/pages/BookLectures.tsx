/**
 * 교재 강의 목록 페이지
 * 간단 파싱으로 생성된 강의 목록 표시
 */
import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import AppShellMobile from '../components/ui/AppShellMobile';
import ToastA11y from '../components/system/ToastA11y';
import { booksAPI, unitsAPI } from '../services/api/client';
import useTTS from '../hooks/useTTS';
import { useToast } from '../hooks/useToast';
import { createModuleLogger } from '../utils/logger';
import type { Book } from '../types/book';

const logger = createModuleLogger('BookLectures');

interface Lecture {
  lecture_id: number;
  title: string;
  start_page?: number;
  end_page?: number;
  lesson_id_str?: string; // Backend에서 생성된 실제 lesson_id
}

export default function BookLectures() {
  const { bookId } = useParams<{ bookId: string }>();
  const navigate = useNavigate();
  const { speak } = useTTS();
  const { showToast, toastMessage, setShowToast, showToastMessage } = useToast();

  const [book, setBook] = useState<Book | null>(null);
  const [lectures, setLectures] = useState<Lecture[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!bookId) return;

    const loadData = async () => {
      try {
        // 교재 정보 로드
        const bookData = await booksAPI.get(bookId);
        setBook(bookData);

        // 강의 목록 로드 (구조 파싱 데이터 사용)
        // backend/data/literature/lectures/에서 직접 로드
        const cacheBuster = `?t=${Date.now()}`;
        const response = await fetch(`/api/v1/literature/lectures${cacheBuster}`);

        if (!response.ok) {
          throw new Error('강의 목록을 찾을 수 없습니다.');
        }

        const data = await response.json();
        // 형식 지원: 배열 또는 {lectures: []} 객체
        const lecturesList = Array.isArray(data) ? data : (data.lectures || []);
        // lecture_id가 있는지 확인하고 없으면 lecture_number나 인덱스로 생성
        const processedLectures = lecturesList.map((lecture: any, index: number) => ({
          ...lecture,
          lecture_id: lecture.lecture_id || lecture.lecture_number || (index + 1)
        }));
        setLectures(processedLectures);
        logger.log(`강의 ${processedLectures.length}개 로드 완료`);
      } catch (err) {
        logger.error('데이터 로드 실패:', err);
        showToastMessage('강의 목록을 불러올 수 없습니다.');
      } finally {
        setLoading(false);
      }
    };

    loadData();
  }, [bookId]);

  const handleLectureClick = async (lecture: Lecture) => {
    try {
      // 구조 파싱 데이터 사용: LiteratureLectureDetail 페이지로 이동
      if (lecture.lecture_id) {
        logger.log(`문학 강의 상세 페이지로 이동: ${lecture.lecture_id}`);
        navigate(`/literature/lectures/${lecture.lecture_id}`);
        return;
      }

      // lecture_id가 없으면 경고 메시지
      showToastMessage('이 강의는 구조 파싱 데이터가 없어 학습할 수 없습니다.');
    } catch (err) {
      logger.error('강의 이동 실패:', err);
      const errorMessage = err instanceof Error ? err.message : String(err);
      showToastMessage(`학습 자료를 불러올 수 없습니다: ${errorMessage}`);
    }
  };

  if (loading) {
    return (
      <AppShellMobile title="강의 목록" className="relative h-screen flex flex-col">
        <div className="flex items-center justify-center flex-1">
          <p className="text-muted">로딩 중...</p>
        </div>
      </AppShellMobile>
    );
  }

  return (
    <AppShellMobile
      title={book?.title || '강의 목록'}
      className="relative h-screen flex flex-col"
    >
      <div className="flex-1 overflow-y-auto p-4 space-y-3">
        {/* 교재 정보 */}
        {book && (
          <div className="bg-card border border-border rounded-lg p-4 mb-4">
            <h2 className="text-lg font-semibold mb-2">{book.title}</h2>
            <div className="flex gap-2 text-xs">
              <span className="px-2 py-1 bg-primary/10 text-primary rounded">
                {book.subject}
              </span>
              <span className="px-2 py-1 bg-secondary/50 rounded">
                {book.year}
              </span>
              <span className="px-2 py-1 bg-secondary/50 rounded">
                {lectures.length}개 강의
              </span>
            </div>
          </div>
        )}

        {/* 강의 목록 */}
        {lectures.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-12">
            <p className="text-muted-foreground mb-2">강의가 없습니다.</p>
            <p className="text-sm text-muted-foreground">
              Admin 페이지에서 목차를 입력하여 강의를 생성하세요.
            </p>
          </div>
        ) : (
          <div className="space-y-2">
            {lectures.map((lecture, index) => (
              <button
                key={lecture.lesson_id_str || `lecture-${lecture.lecture_id}-${index}`}
                onClick={() => handleLectureClick(lecture)}
                className="w-full bg-card border border-border rounded-lg p-4 hover:bg-accent/50 transition-colors text-left"
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <h3 className="font-semibold mb-1">{lecture.title}</h3>
                    {lecture.start_page && (
                      <p className="text-sm text-muted-foreground">
                        페이지 {lecture.start_page}
                        {lecture.end_page && ` ~ ${lecture.end_page}`}
                      </p>
                    )}
                  </div>
                  <div className="text-2xl flex-shrink-0 ml-2">📖</div>
                </div>
              </button>
            ))}
          </div>
        )}
      </div>

      {/* 하단 네비게이션 */}
      <div className="border-t border-border p-4 bg-background">
        <div className="flex gap-2">
          <button
            onClick={() => navigate('/admin')}
            className="flex-1 px-4 py-3 bg-secondary text-secondary-foreground rounded-lg hover:bg-secondary/80 transition-colors font-semibold"
          >
            Admin
          </button>
          <button
            onClick={() => navigate('/')}
            className="flex-1 px-4 py-3 bg-secondary text-secondary-foreground rounded-lg hover:bg-secondary/80 transition-colors font-semibold"
          >
            홈으로
          </button>
        </div>
      </div>

      <ToastA11y
        message={toastMessage}
        isVisible={showToast}
        duration={3000}
        onClose={() => setShowToast(false)}
      />
    </AppShellMobile>
  );
}
