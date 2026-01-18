/**
 * 교재 페이지
 * 교재 상세 정보, PDF 업로드, 파싱 상태 표시
 */
import { useEffect, useState } from 'react';
import { useNavigate, useParams, useSearchParams } from 'react-router-dom';
import AppShellMobile from '../components/ui/AppShellMobile';
import SpeechBar from '../components/input/SpeechBar';
import useTTS from '../hooks/useTTS';
import useSTT from '../hooks/useSTT';
import useVoiceCommands from '../hooks/useVoiceCommands';
import ToastA11y from '../components/system/ToastA11y';
import BookUpload from '../components/textbook/BookUpload';
import { booksAPI } from '../services/books';
import { lessonsAPI } from '../services/lessons';
import type { Book } from '../types/book';
import type { Lesson } from '../types/lesson';
import { useBookStore } from '../store/bookStore';

export default function Book() {
  const navigate = useNavigate();
  const { bookId } = useParams<{ bookId: string }>();
  const [searchParams] = useSearchParams();
  const { speak, stop: stopTTS } = useTTS();
  const { start: startSTT, stop: stopSTT, isListening, transcript } = useSTT();
  const [showToast, setShowToast] = useState(false);
  const [toastMessage, setToastMessage] = useState('');
  
  const [book, setBook] = useState<Book | null>(null);
  const [lessons, setLessons] = useState<Lesson[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showUpload, setShowUpload] = useState(false);
  const [parseProgress, setParseProgress] = useState(0);
  
  const { setBook: setStoreBook } = useBookStore();

  // 교재 ID가 있으면 상세 조회, 없으면 업로드 모드
  useEffect(() => {
    if (bookId) {
      loadBook(bookId);
      loadLessons(bookId);
      
      // 파싱 중이면 상태 폴링
      const interval = setInterval(async () => {
        try {
          const status = await booksAPI.getParseStatus(bookId);
          setParseProgress(status.progress);
          if (status.status === 'DONE' || status.status === 'FAILED') {
            clearInterval(interval);
            if (status.status === 'DONE') {
              loadLessons(bookId); // 강 목록 새로고침
            }
          }
        } catch (err) {
          console.error('[Book] 파싱 상태 조회 실패:', err);
        }
      }, 2000);
      
      return () => clearInterval(interval);
    } else {
      setShowUpload(true);
    }
  }, [bookId]);

  const loadBook = async (id: string) => {
    setLoading(true);
    setError(null);
    try {
      const data = await booksAPI.get(id);
      setBook(data);
      setStoreBook(data);
    } catch (err) {
      const errorMsg = '교재를 불러오는 중 오류가 발생했습니다.';
      setError(errorMsg);
      speak(errorMsg);
    } finally {
      setLoading(false);
    }
  };

  const loadLessons = async (id: string) => {
    try {
      const data = await lessonsAPI.list(id);
      setLessons(data);
    } catch (err) {
      console.error('[Book] 강 목록 로드 실패:', err);
    }
  };

  const handleUploadComplete = async (uploadedBook: Book) => {
    setShowUpload(false);
    navigate(`/book/${uploadedBook.book_id}`);
    await loadBook(uploadedBook.book_id);
  };

  const handleLessonSelect = (lesson: Lesson) => {
    navigate(`/lesson/${lesson.lesson_id}`);
  };

  const handleReparse = async () => {
    if (!bookId) return;
    
    setLoading(true);
    setError(null);
    try {
      const result = await booksAPI.reparse(bookId);
      showToastMessage(result.message);
      if (result.ok) {
        // 교재 정보 새로고침
        await loadBook(bookId);
        // 파싱 상태 폴링 재시작
        const interval = setInterval(async () => {
          try {
            const status = await booksAPI.getParseStatus(bookId);
            setParseProgress(status.progress);
            if (status.status === 'DONE' || status.status === 'FAILED') {
              clearInterval(interval);
              await loadBook(bookId);
              if (status.status === 'DONE') {
                loadLessons(bookId);
              }
            }
          } catch (err) {
            console.error('[Book] 파싱 상태 조회 실패:', err);
            clearInterval(interval);
          }
        }, 2000);
        
        // 30초 후 타임아웃
        setTimeout(() => clearInterval(interval), 30000);
      }
    } catch (err: any) {
      const errorMsg = err.message || '재파싱 중 오류가 발생했습니다.';
      setError(errorMsg);
      showToastMessage(errorMsg);
    } finally {
      setLoading(false);
    }
  };

  // 음성 명령어
  const { onSpeech } = useVoiceCommands({
    home: () => {
      stopTTS();
      navigate('/');
      stopSTT();
    },
    back: () => {
      navigate('/');
    },
  });

  useEffect(() => {
    if (!transcript) return;
    onSpeech(transcript);
  }, [transcript, onSpeech]);

  const showToastMessage = (message: string) => {
    setToastMessage(message);
    setShowToast(true);
  };

  return (
    <AppShellMobile title="교재" className="relative">
      <div className="mb-4">
        <SpeechBar isListening={isListening} transcript={transcript} />
      </div>

      <div className="p-4">
        {loading && (
          <div className="text-center py-8">
            <p className="text-muted">로딩 중...</p>
          </div>
        )}

        {error && (
          <div className="bg-error/10 border border-error rounded-lg p-4 mb-4">
            <p className="text-error">{error}</p>
          </div>
        )}

        {!loading && !error && (
          <>
            {showUpload ? (
              <BookUpload
                onUploadComplete={handleUploadComplete}
                onSpeak={speak}
              />
            ) : book ? (
              <div className="space-y-4">
                {/* 교재 정보 */}
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
                        onClick={handleReparse}
                        disabled={loading}
                        className="w-full px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed"
                      >
                        {loading ? '재파싱 중...' : '재파싱 시도'}
                      </button>
                    </div>
                  )}
                </div>

                {/* 강 목록 */}
                {lessons.length > 0 && (
                  <div className="space-y-2">
                    <h3 className="text-lg font-semibold">강 목록</h3>
                    {lessons.map((lesson) => (
                      <button
                        key={lesson.lesson_id}
                        onClick={() => handleLessonSelect(lesson)}
                        className="w-full p-4 text-left bg-card border border-border rounded-lg hover:border-primary transition-colors"
                      >
                        <div className="font-medium">{lesson.title}</div>
                        <div className="text-sm text-muted mt-1">
                          단위 {lesson.unit_count || 0}개, 문제 {lesson.question_count || 0}개
                        </div>
                      </button>
                    ))}
                  </div>
                )}

                {lessons.length === 0 && book.parse_status === 'DONE' && (
                  <div className="text-center py-8 text-muted">
                    <p>등록된 강이 없습니다.</p>
                  </div>
                )}
              </div>
            ) : (
              <div className="text-center py-8">
                <p className="text-muted">교재를 선택해주세요.</p>
              </div>
            )}
          </>
        )}
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
