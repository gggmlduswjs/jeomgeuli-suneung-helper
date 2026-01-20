/**
 * Book Selection Screen - Simplified single-flow design
 * Show books as numbered list with keyboard navigation
 */
import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { booksAPI } from '../services/books';
import { lessonsAPI } from '../services/lessons';
import { unitsAPI } from '../services/units';
import type { Book } from '../types/book';
import { useKeyboardShortcuts } from '../contexts/KeyboardContext';
import { useAutoGuidance } from '../hooks/useAutoGuidance';
import { useTTS } from '../hooks/useTTS';
import AppShellMobile from '../components/ui/AppShellMobile';
import ToastA11y from '../components/system/ToastA11y';
import BookUpload from '../components/textbook/BookUpload';

export default function BookSelect() {
  const navigate = useNavigate();
  const { speak } = useTTS();
  const [books, setBooks] = useState<Book[]>([]);
  const [loading, setLoading] = useState(true);
  const [showUpload, setShowUpload] = useState(false);
  const [selectedIndex, setSelectedIndex] = useState(-1);
  const [showToast, setShowToast] = useState(false);
  const [toastMessage, setToastMessage] = useState('');
  const [reparsingBookId, setReparsingBookId] = useState<string | null>(null);

  // Load books
  useEffect(() => {
    loadBooks();
  }, []);

  const loadBooks = async () => {
    setLoading(true);
    try {
      const data = await booksAPI.list();
      // Show all books, not just parsed ones
      setBooks(data);
    } catch (err) {
      console.error('[BookSelect] Failed to load books:', err);
      showToastMsg('교재를 불러오는 중 오류가 발생했습니다.');
    } finally {
      setLoading(false);
    }
  };

  // Auto-announce on load
  const autoAnnounceMessage = books.length > 0
    ? `교재 선택. ${books.length}개의 교재가 있습니다. 1부터 ${Math.min(books.length, 9)}까지 번호를 눌러 선택하거나, 플러스 키로 새 교재를 추가하세요.`
    : '교재 선택. 등록된 교재가 없습니다. 플러스 키를 눌러 새 교재를 추가하세요.';

  useAutoGuidance(autoAnnounceMessage, [loading, books.length]);

  // Keyboard shortcuts
  const shortcuts: Record<string, () => void> = {
    'b': () => navigate('/'),
    '+': () => handleAddBook(),
    'r': () => {
      if (selectedIndex >= 0 && selectedIndex < books.length) {
        const book = books[selectedIndex];
        if (book.parse_status === 'FAILED' || book.parse_status === 'PENDING') {
          handleReparse(book.book_id);
        }
      }
    },
    'd': () => {
      if (selectedIndex >= 0 && selectedIndex < books.length) {
        const book = books[selectedIndex];
        handleDelete(book.book_id, book.title);
      }
    },
    'arrowup': () => handleNavigateUp(),
    'arrowdown': () => handleNavigateDown(),
    'enter': () => handleSelectCurrent(),
  };

  // Add number shortcuts (1-9)
  for (let i = 1; i <= 9; i++) {
    shortcuts[i.toString()] = () => handleSelectBook(i - 1);
  }

  useKeyboardShortcuts(shortcuts, [books, selectedIndex, reparsingBookId]);

  const handleNavigateUp = () => {
    if (selectedIndex > 0) {
      const newIndex = selectedIndex - 1;
      setSelectedIndex(newIndex);
      announceBook(newIndex);
    }
  };

  const handleNavigateDown = () => {
    if (selectedIndex < books.length - 1) {
      const newIndex = selectedIndex + 1;
      setSelectedIndex(newIndex);
      announceBook(newIndex);
    }
  };

  const announceBook = (index: number) => {
    const book = books[index];
    if (book) {
      showToastMsg(`${index + 1}번: ${book.title}`);
    }
  };

  const handleSelectCurrent = () => {
    if (selectedIndex >= 0 && selectedIndex < books.length) {
      handleSelectBook(selectedIndex);
    }
  };

  const handleSelectBook = async (index: number) => {
    if (index < 0 || index >= books.length) {
      showToastMsg('잘못된 번호입니다.');
      return;
    }

    const book = books[index];

    // Check if book is parsed
    if (book.parse_status !== 'DONE') {
      const statusMsg = book.parse_status === 'PROCESSING'
        ? '교재가 아직 파싱 중입니다. 잠시 후 다시 시도하세요.'
        : book.parse_status === 'FAILED'
        ? '교재 파싱이 실패했습니다.'
        : '교재가 준비되지 않았습니다.';
      showToastMsg(statusMsg);
      return;
    }

    showToastMsg(`${book.title} 선택`);

    try {
      // Get lessons for this book
      const lessons = await lessonsAPI.list(book.book_id);

      if (lessons.length === 0) {
        showToastMsg('강의가 없습니다.');
        return;
      }

      // Get first lesson
      const firstLesson = lessons[0];

      // Get units in first lesson
      const units = await unitsAPI.list(firstLesson.lesson_id);

      // Find first question
      const firstQuestion = units.find(u => u.type === 'QUESTION');

      if (!firstQuestion) {
        showToastMsg('문제가 없습니다.');
        return;
      }

      // Navigate to first question
      navigate(`/learn/${book.book_id}/${firstLesson.lesson_id}/${firstQuestion.unit_id}`);
    } catch (err) {
      console.error('[BookSelect] Failed to select book:', err);
      showToastMsg('교재 선택 중 오류가 발생했습니다.');
    }
  };

  const handleAddBook = () => {
    setShowUpload(true);
  };

  const handleUploadComplete = async (uploadedBook: Book) => {
    setShowUpload(false);
    await loadBooks();
    showToastMsg(`${uploadedBook.title} 교재가 추가되었습니다.`);
  };

  const handleDelete = async (bookId: string, bookTitle: string) => {
    if (!confirm(`정말 "${bookTitle}" 교재를 삭제하시겠습니까?`)) {
      return;
    }

    showToastMsg('교재를 삭제하는 중...');
    speak('교재를 삭제하는 중입니다.');

    try {
      const result = await booksAPI.delete(bookId);
      if (result.ok) {
        showToastMsg('교재가 삭제되었습니다.');
        speak('교재가 삭제되었습니다.');
        await loadBooks();
      } else {
        throw new Error(result.message || '삭제 실패');
      }
    } catch (err: any) {
      console.error('[BookSelect] Failed to delete book:', err);
      const errorMsg = err.message || '교재 삭제 중 오류가 발생했습니다.';
      showToastMsg(errorMsg);
      speak(errorMsg);
    }
  };

  const handleReparse = async (bookId: string) => {
    setReparsingBookId(bookId);
    showToastMsg('교재를 재파싱합니다. 잠시만 기다려주세요...');
    speak('교재를 재파싱합니다. 잠시만 기다려주세요.');

    try {
      console.log('[BookSelect] Reparse request for book:', bookId);
      const result = await booksAPI.reparse(bookId);
      console.log('[BookSelect] Reparse response:', result);

      if (result.ok) {
        showToastMsg('재파싱이 시작되었습니다.');
        speak('재파싱이 시작되었습니다. 완료까지 1-2분 정도 걸립니다.');

        // 5초마다 상태 체크
        const checkInterval = setInterval(async () => {
          try {
            const status = await booksAPI.getParseStatus(bookId);
            console.log('[BookSelect] Parse status:', status);

            if (status.status === 'DONE') {
              clearInterval(checkInterval);
              setReparsingBookId(null);
              await loadBooks();
              showToastMsg('재파싱이 완료되었습니다!');
              speak('재파싱이 완료되었습니다.');
            } else if (status.status === 'FAILED') {
              clearInterval(checkInterval);
              setReparsingBookId(null);
              showToastMsg('재파싱이 실패했습니다.');
              speak('재파싱이 실패했습니다. 관리자에게 문의하세요.');
            }
          } catch (err) {
            console.error('[BookSelect] Failed to check parse status:', err);
          }
        }, 5000);

        // 5분 후 타임아웃
        setTimeout(() => {
          clearInterval(checkInterval);
          setReparsingBookId(null);
        }, 300000);
      } else {
        const errorMsg = result.message || '재파싱 실패';
        console.error('[BookSelect] Reparse failed:', errorMsg, result);
        throw new Error(errorMsg);
      }
    } catch (err: any) {
      console.error('[BookSelect] Failed to reparse:', err);
      console.error('[BookSelect] Error details:', {
        message: err.message,
        response: err.response,
        stack: err.stack
      });
      setReparsingBookId(null);

      // 더 자세한 에러 메시지 표시
      const errorMsg = err.response?.data?.message
        || err.response?.data?.detail
        || err.message
        || '재파싱 중 오류가 발생했습니다.';

      showToastMsg(errorMsg);
      speak('재파싱 중 오류가 발생했습니다.');
    }
  };

  const showToastMsg = (message: string) => {
    setToastMessage(message);
    setShowToast(true);
  };

  if (loading) {
    return (
      <AppShellMobile 
        className="relative h-screen flex flex-col"
        showHeader={false}
        showFooter={false}
      >
        <div className="flex items-center justify-center flex-1">
          <p className="text-muted">로딩 중...</p>
        </div>
      </AppShellMobile>
    );
  }

  if (showUpload) {
    return (
      <AppShellMobile 
        className="relative h-screen flex flex-col"
        showHeader={false}
        showFooter={false}
      >
        <div className="p-4">
          <button
            onClick={() => setShowUpload(false)}
            className="mb-4 px-4 py-2 text-sm text-muted-foreground hover:text-foreground transition-colors"
          >
            ← 뒤로가기
          </button>
          <BookUpload
            onUploadComplete={handleUploadComplete}
            onSpeak={(msg) => showToastMsg(msg)}
          />
        </div>
      </AppShellMobile>
    );
  }

  return (
    <AppShellMobile title="교재 선택" className="relative h-screen flex flex-col">
      <div className="flex-1 flex flex-col px-6 py-8 overflow-y-auto">
        <div className="mb-6">
          <h1 className="text-3xl font-extrabold mb-2 gradient-text">
            교재 선택
          </h1>
          <p className="text-sm text-muted">학습할 교재를 선택하세요</p>
        </div>

        {books.length === 0 ? (
          <div className="flex-1 flex flex-col items-center justify-center">
            <p className="text-muted mb-4">등록된 교재가 없습니다.</p>
            <button
              onClick={handleAddBook}
              className="px-6 py-3.5 text-white rounded-2xl 
                         shadow-lg hover:shadow-glow transition-all duration-300 
                         hover:scale-[1.02] active:scale-[0.98] font-semibold"
              style={{ background: 'linear-gradient(135deg, rgb(49, 130, 246) 0%, rgb(96, 165, 250) 100%)' }}
              aria-label="플러스 키: 새 교재 추가"
            >
              [+] 새 교재 추가
            </button>
          </div>
        ) : (
          <>
            <div className="space-y-3 flex-1">
              {books.map((book, index) => {
                const isParsed = book.parse_status === 'DONE';
                const isProcessing = book.parse_status === 'PROCESSING';
                const isFailed = book.parse_status === 'FAILED';
                const isReparsing = reparsingBookId === book.book_id;

                return (
                  <div
                    key={book.book_id}
                    onMouseEnter={() => setSelectedIndex(index)}
                    className={`w-full rounded-2xl transition-all duration-300 ${
                      !isParsed && !isFailed
                        ? 'bg-muted/50 border border-border/50 opacity-60'
                        : selectedIndex === index
                        ? 'border-2 border-primary shadow-soft-lg scale-[1.01]'
                        : 'border border-border/50 shadow-soft hover:shadow-soft-lg hover:border-primary/30'
                    }`}
                    style={!isParsed && !isFailed ? {} : selectedIndex === index 
                      ? { background: 'rgba(49, 130, 246, 0.1)' }
                      : { background: 'linear-gradient(135deg, rgb(249, 250, 251) 0%, rgb(255, 255, 255) 100%)' }}
                  >
                    <button
                      onClick={() => isParsed && handleSelectBook(index)}
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
                    <div className="px-4 pb-4 flex gap-2">
                      {/* Delete button for processing/failed books */}
                      {(isProcessing || isFailed || (book.lesson_count === 0 && isParsed)) && !isReparsing && (
                        <button
                          onClick={() => handleDelete(book.book_id, book.title)}
                          className="flex-1 px-4 py-2.5 text-sm bg-danger/10 text-danger border border-danger/30 rounded-xl 
                                     hover:bg-danger/20 hover:border-danger/50 transition-all duration-300 
                                     hover:shadow-soft font-medium"
                          aria-label="D키: 삭제"
                        >
                          [D] 삭제
                        </button>
                      )}
                      
                      {/* Reparse button for failed books */}
                      {(isFailed || (book.lesson_count === 0 && isParsed)) && !isReparsing && (
                        <button
                          onClick={() => handleReparse(book.book_id)}
                          className="flex-1 px-4 py-2.5 text-sm bg-warning/10 text-warning border border-warning/30 rounded-xl 
                                     hover:bg-warning/20 hover:border-warning/50 transition-all duration-300 
                                     hover:shadow-soft font-medium"
                          aria-label="R키: 재파싱"
                        >
                          [R] 재파싱
                        </button>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>

            {/* Add book button */}
            <div className="mt-4 pt-4 border-t border-border">
              <button
                onClick={handleAddBook}
                className="w-full p-5 border border-border/50 rounded-2xl 
                           shadow-soft hover:shadow-soft-lg hover:border-primary/30
                           transition-all duration-300 hover:scale-[1.01] active:scale-[0.99] text-left
                           hover:bg-card-hover"
                style={{ background: 'linear-gradient(135deg, rgb(249, 250, 251) 0%, rgb(255, 255, 255) 100%)' }}
                aria-label="플러스 키: 새 교재 추가"
              >
                <span className="text-lg font-semibold">[+] 새 교재 추가</span>
                <p className="text-sm opacity-90 mt-1">PDF 파일 업로드</p>
              </button>
            </div>

            {/* Back button */}
            <div className="mt-2">
              <button
                onClick={() => navigate('/')}
                className="w-full px-4 py-2 text-sm text-muted-foreground hover:text-foreground transition-colors"
                aria-label="B키: 뒤로가기"
              >
                [B] 뒤로가기
              </button>
            </div>
          </>
        )}

        {/* Keyboard hints */}
        <div className="mt-4 text-xs text-muted-foreground text-center">
          <p>
            키보드로 조작: 1-{Math.min(books.length, 9)} (선택), + (추가), D (삭제), R (재파싱),
            <br />
            ↑↓ (이동), Enter (선택), B (뒤로)
          </p>
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
