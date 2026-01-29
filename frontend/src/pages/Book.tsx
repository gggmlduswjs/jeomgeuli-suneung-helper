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
import BookInfo from '../components/book/BookInfo';
import LessonList from '../components/book/LessonList';
import { booksAPI, lessonsAPI, curriculumAPI, unitsAPI } from '../services/api/client';
import { literatureAPI, type LiteratureLectureSummary } from '../services/literature';
import { Subject } from '../types/book';
import type { Book } from '../types/book';
import type { Lesson } from '../types/lesson';
import { useBookStore } from '../store/bookStore';

export default function Book() {
  const navigate = useNavigate();
  const { bookId } = useParams<{ bookId: string }>();
  const [searchParams] = useSearchParams();
  const { speak, stop: stopTTS } = useTTS();
  const { stop: stopSTT, isListening, transcript } = useSTT();
  const [showToast, setShowToast] = useState(false);
  const [toastMessage, setToastMessage] = useState('');
  
  const [book, setBook] = useState<Book | null>(null);
  const [books, setBooks] = useState<Book[]>([]);
  const [lessons, setLessons] = useState<Lesson[]>([]);
  const [literatureLectures, setLiteratureLectures] = useState<LiteratureLectureSummary[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showUpload, setShowUpload] = useState(false);
  const [parseProgress, setParseProgress] = useState(0);
  
  const { setBook: setStoreBook } = useBookStore();

  // URL 파라미터에서 subject 확인 및 변환
  const subjectParamRaw = searchParams.get('subject');
  const subjectParam: Subject | null = subjectParamRaw 
    ? (subjectParamRaw.toUpperCase() as Subject)
    : null;


  // 교재 ID가 있으면 강의 목록 페이지로 리다이렉트
  useEffect(() => {
    if (bookId) {
      // 강의 목록 페이지로 이동 (목차 텍스트 입력으로 만들어진 강의 목록)
      navigate(`/lectures/${bookId}`, { replace: true });
      return;
    }
    
    // 교재 ID가 없으면 기존 로직 유지 (교재 목록 표시)
    if (subjectParam) {
      // 이전 데이터 완전히 클리어
      setLessons([]);
      setLiteratureLectures([]);
      setError(null);
      setBook(null); // 이전 교재 정보도 클리어
      
      // 국어(KOREAN) 선택 시 문학 강의 목록 표시
      if (subjectParam === Subject.KOREAN) {
        loadLiteratureLectures();
      } else {
        // 다른 과목은 교재 목록 로드
        loadBooksBySubject(subjectParam);
      }
    } else {
      setShowUpload(true);
    }
  }, [bookId, subjectParam, searchParams, navigate]);

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
      const data = await lessonsAPI.listByBook(id);
      setLessons(data);
      if (import.meta.env.DEV) console.log(`[Book] 강 목록 로드 완료: ${data.length}개`);
      // 강의가 있지만 일부가 섹션이 없는 경우 로그
      if (data.length > 0) {
        const lessonsWithoutContent = data.filter((lesson: Lesson) => !lesson.unit_count || lesson.unit_count === 0);
        if (lessonsWithoutContent.length > 0) {
          console.warn(`[Book] 콘텐츠가 없는 강의 ${lessonsWithoutContent.length}개:`, 
            lessonsWithoutContent.map((l: Lesson) => l.title));
        }
      }
    } catch (err) {
      console.error('[Book] 강 목록 로드 실패:', err);
      // 에러가 발생해도 빈 배열로 설정하여 UI에서 적절히 처리
      setLessons([]);
    }
  };

  const loadLiteratureLectures = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await literatureAPI.getLectures();
      setLiteratureLectures(data);
      if (data.length === 0) {
        const message = '등록된 문학 강의가 없습니다.';
        speak(message);
      } else {
        speak(`문학 강의 ${data.length}개가 있습니다.`);
      }
    } catch (err) {
      const errorMsg = '문학 강의 목록을 불러오는 중 오류가 발생했습니다.';
      setError(errorMsg);
      speak(errorMsg);
    } finally {
      setLoading(false);
    }
  };

  const loadBooksBySubject = async (subject: Subject) => {
    setLoading(true);
    setError(null);
    try {
      const data = await booksAPI.list(subject);
      
      // 중복 제거: 제목이 같은 교재는 가장 최근 것 하나만 표시
      const bookMap = new Map<string, Book>();
      data.forEach((book: Book) => {
        const key = book.title; // 제목만으로 중복 판단
        const existing = bookMap.get(key);
        if (!existing || (book.year && existing.year && book.year > existing.year)) {
          // 같은 제목이 없거나, 더 최근 연도면 교체
          bookMap.set(key, book);
        }
      });
      
      const uniqueBooks = Array.from(bookMap.values());
      setBooks(uniqueBooks);
      if (uniqueBooks.length === 0) {
        const message = `${subject === Subject.KOREAN ? '국어' : subject === Subject.ENGLISH ? '영어' : '수학'} 과목의 교재가 없습니다.`;
        speak(message);
      }
    } catch (err) {
      const errorMsg = '교재 목록을 불러오는 중 오류가 발생했습니다.';
      setError(errorMsg);
      speak(errorMsg);
    } finally {
      setLoading(false);
    }
  };

  const handleBookSelect = async (selectedBook: Book) => {
    // 문학 강의 목록으로 이동 (구조 파싱 데이터 사용)
    if (selectedBook.subject === 'KOREAN') {
      navigate('/literature/lectures');
    } else {
      navigate(`/lectures/${selectedBook.book_id}`);
    }
  };

  const handleUploadComplete = async (uploadedBook: Book) => {
    setShowUpload(false);
    // 문학 강의 목록으로 이동 (구조 파싱 데이터 사용)
    if (uploadedBook.subject === 'KOREAN') {
      navigate('/literature/lectures');
    } else {
      navigate(`/lectures/${uploadedBook.book_id}`);
    }
  };

  const handleLessonSelect = async (lesson: Lesson) => {
    try {
      // 문학 강의 목록으로 이동 (구조 파싱 데이터 사용)
      if (lesson.subject === 'KOREAN') {
        navigate('/literature/lectures');
      } else {
        navigate(`/lectures/${lesson.book_id}`);
      }
      showToastMessage(`${lesson.title} 학습을 시작합니다.`);
      speak(`${lesson.title} 학습을 시작합니다.`);
    } catch (err) {
      console.error('[Book] 강의 선택 실패:', err);
      showToastMessage('강의를 불러오는 중 오류가 발생했습니다.');
    }
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
        // 파싱 상태 폴링 재시작 (5초마다 - 중복 요청 방지)
        let lastStatus: string | null = null;
        const interval = setInterval(async () => {
          try {
            const status = await booksAPI.getParseStatus(bookId);
            setParseProgress(status.progress);
            
            // 상태가 변경되었을 때만 로그 출력
            if (lastStatus !== status.status && import.meta.env.DEV) {
              if (import.meta.env.DEV) console.log('[Book] Reparse status:', status);
              lastStatus = status.status;
            }
            
            if (status.status === 'DONE' || status.status === 'FAILED') {
              clearInterval(interval);
              await loadBook(bookId);
              if (status.status === 'DONE') {
                await loadLessons(bookId);
                
                // 재파싱 완료 후에도 강의가 없으면 자동 JSON 동기화 시도
                const currentLessons = await lessonsAPI.listByBook(bookId);
                if (currentLessons.length === 0) {
                  if (import.meta.env.DEV) console.log('[Book] 재파싱 완료되었지만 강의가 없음. 자동 JSON 동기화 시도...');
                  try {
                    const syncResult = await booksAPI.syncFromJson(bookId);
                    if (syncResult.ok) {
                      if (import.meta.env.DEV) console.log('[Book] ✅ 자동 JSON 동기화 성공:', syncResult.message);
                      await loadLessons(bookId);
                      await loadBook(bookId);
                      showToastMessage('JSON 파일이 자동으로 동기화되었습니다.');
                    }
                  } catch (syncErr) {
                    console.error('[Book] 자동 JSON 동기화 중 오류:', syncErr);
                  }
                }
              } else if (status.status === 'FAILED') {
                // 재파싱 중 실패한 경우
                const errorMsg = '재파싱이 실패했습니다.';
                setError(errorMsg);
                showToastMessage(errorMsg);
              }
            }
          } catch (err) {
            console.error('[Book] 파싱 상태 조회 실패:', err);
            clearInterval(interval);
          }
        }, 5000); // 5초로 증가
        
        // 30초 후 타임아웃
        setTimeout(() => clearInterval(interval), 30000);
      }
    } catch (err: unknown) {
      const errorMsg = err instanceof Error ? err.message : '재파싱 중 오류가 발생했습니다.';
      setError(errorMsg);
      showToastMessage(errorMsg);
    } finally {
      setLoading(false);
    }
  };

  const handleRecreateCurriculum = async () => {
    if (!bookId) return;
    
    setLoading(true);
    setError(null);
    try {
      const result = await booksAPI.createCurriculumFromData(bookId);
      showToastMessage(result.message);
      if (result.ok) {
        // 교재 정보 새로고침
        await loadBook(bookId);
        // 강의 목록 새로고침
        await loadLessons(bookId);
        // 페이지 새로고침하여 커리큘럼 반영
        window.location.reload();
      }
    } catch (err: unknown) {
      const errorMsg = err instanceof Error ? err.message : '커리큘럼 재생성 중 오류가 발생했습니다.';
      setError(errorMsg);
      showToastMessage(errorMsg);
    } finally {
      setLoading(false);
    }
  };

  const handleSyncFromJson = async () => {
    if (!bookId) return;
    
    setLoading(true);
    setError(null);
    try {
      const result = await booksAPI.syncFromJson(bookId);
      showToastMessage(result.message);
      speak(result.message);
      if (result.ok) {
        // 강의 목록 새로고침
        await loadLessons(bookId);
        // 교재 정보 새로고침
        await loadBook(bookId);
      }
    } catch (err: unknown) {
      const errorMsg = err instanceof Error ? err.message : 'JSON 동기화 중 오류가 발생했습니다.';
      setError(errorMsg);
      showToastMessage(errorMsg);
      speak(errorMsg);
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
            ) : subjectParam && !bookId ? (
              // subject만 있고 bookId가 없으면 교재/강의 목록 표시
              <div className="space-y-4">
                {/* 국어 선택 시 문학 강의 목록 표시 */}
                {subjectParam === Subject.KOREAN ? (
                  <>
                    <div className="bg-gradient-to-r from-blue-50 to-indigo-50 border-2 border-blue-300 rounded-lg p-4 mb-4">
                      <h2 className="text-xl font-bold mb-2 text-blue-900">📚 문학 강의</h2>
                      <p className="text-sm text-blue-700">문학 강의를 선택하여 학습을 시작하세요.</p>
                    </div>
                    {literatureLectures.length > 0 ? (
                      <div className="space-y-2">
                        <h3 className="text-lg font-semibold mb-2">문학 강의 목록</h3>
                        {literatureLectures.map((lecture) => (
                          <button
                            key={lecture.lecture_id}
                            onClick={async () => {
                              stopTTS();
                              // 문학 강의는 이미 Unit으로 변환되어 있으므로 해당 Lesson의 첫 번째 Unit으로 이동
                              try {
                                // lecture_id에 해당하는 Lesson 찾기
                                const lessons = await lessonsAPI.listByBook(book!.book_id);
                                const targetLesson = lessons.find(l => 
                                  l.title.includes(`${lecture.lecture_id}강`) || 
                                  l.title.includes(lecture.title)
                                );
                                
                                if (targetLesson) {
                                  const units = await unitsAPI.listByLesson(targetLesson.lesson_id);
                                  if (units.length > 0) {
                                    navigate(`/unit/${units[0].unit_id}`);
                                    showToastMessage(`${lecture.title} 학습을 시작합니다.`);
                                  } else {
                                    showToastMessage('학습 단위가 없습니다.');
                                  }
                                } else {
                                  showToastMessage('해당 강의를 찾을 수 없습니다.');
                                }
                              } catch (err) {
                                console.error('[Book] 문학 강의 이동 실패:', err);
                                showToastMessage('강의를 불러오는 중 오류가 발생했습니다.');
                              }
                            }}
                            className="w-full p-4 text-left bg-card border-2 border-blue-200 rounded-lg hover:border-blue-400 hover:bg-blue-50 transition-colors"
                          >
                            <div className="font-medium text-gray-900">{lecture.title}</div>
                            <div className="text-sm text-gray-600 mt-1">
                              강의 ID: {lecture.lecture_id}
                            </div>
                          </button>
                        ))}
                      </div>
                    ) : (
                      <div className="text-center py-8 text-muted">
                        <p>등록된 문학 강의가 없습니다.</p>
                      </div>
                    )}
                  </>
                ) : (
                  <>
                    {/* 다른 과목은 교재 목록 표시 */}
                    <h2 className="text-xl font-bold mb-4">
                      {subjectParam === Subject.ENGLISH ? '영어' : '수학'} 교재 목록
                    </h2>
                    {books.length > 0 ? (
                      <div className="space-y-2">
                        {books.map((book) => (
                          <button
                            key={book.book_id}
                            onClick={() => handleBookSelect(book)}
                            className="w-full p-4 text-left bg-card border border-border rounded-lg hover:border-primary transition-colors"
                          >
                            <div className="font-medium">{book.title}</div>
                            <div className="text-sm text-muted mt-1">
                              {book.year && `${book.year}년 • `}
                              강 {book.lesson_count || 0}개
                            </div>
                          </button>
                        ))}
                      </div>
                    ) : (
                      <div className="text-center py-8 text-muted">
                        <p>등록된 교재가 없습니다.</p>
                      </div>
                    )}
                  </>
                )}
              </div>
            ) : book ? (
              <div className="space-y-4">
                <BookInfo
                  book={book}
                  parseProgress={parseProgress}
                  onReparse={handleReparse}
                  onSyncFromJson={handleSyncFromJson}
                  onRecreateCurriculum={handleRecreateCurriculum}
                  loading={loading}
                />

                <LessonList lessons={lessons} onLessonSelect={handleLessonSelect} />

                {lessons.length === 0 && book.parse_status === 'DONE' && (
                  <div className="bg-warning/10 border border-warning rounded-lg p-4 text-center">
                    <p className="text-warning font-medium mb-2">강의 데이터를 찾을 수 없습니다.</p>
                    <p className="text-xs text-muted mb-3">
                      파싱은 완료되었지만 강의가 생성되지 않았을 수 있습니다.
                      JSON 파일에서 DB로 동기화를 시도해보세요.
                    </p>
                    <div className="flex gap-2 justify-center">
                      <button
                        onClick={handleSyncFromJson}
                        disabled={loading}
                        className="px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed transition-colors text-sm"
                      >
                        {loading ? '동기화 중...' : 'JSON 동기화'}
                      </button>
                      <button
                        onClick={handleRecreateCurriculum}
                        disabled={loading}
                        className="px-4 py-2 bg-warning/20 text-warning border border-warning rounded-lg hover:bg-warning/30 disabled:opacity-50 disabled:cursor-not-allowed transition-colors text-sm"
                      >
                        {loading ? '재생성 중...' : '커리큘럼 재생성'}
                      </button>
                    </div>
                    <p className="text-xs text-muted mt-2">
                      JSON 동기화: JSON 파일을 읽어서 DB에 저장 (빠름)<br/>
                      커리큘럼 재생성: 전체 파이프라인 데이터로부터 재생성
                    </p>
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
