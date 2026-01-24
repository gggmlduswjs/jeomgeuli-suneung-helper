/**
 * Book Selection Screen - Simplified single-flow design
 * Show books as numbered list with keyboard navigation
 */
import { useEffect, useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { booksAPI } from '../services/api/client';
import type { Book } from '../types/book';
import { useKeyboardShortcuts } from '../contexts/KeyboardContext';
import { useAutoGuidance } from '../hooks/useAutoGuidance';
import { useTTS } from '../hooks/useTTS';
import AppShellMobile from '../components/ui/AppShellMobile';
import ToastA11y from '../components/system/ToastA11y';
import BookUpload from '../components/textbook/BookUpload';
import BookListItem from '../components/bookselect/BookListItem';

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
  const [parsingBookId, setParsingBookId] = useState<string | null>(null);
  const parseStatusIntervalRef = useRef<NodeJS.Timeout | null>(null);

  // Load books
  useEffect(() => {
    loadBooks();
    
    // 컴포넌트 언마운트 시 interval 정리
    return () => {
      if (parseStatusIntervalRef.current) {
        clearInterval(parseStatusIntervalRef.current);
        parseStatusIntervalRef.current = null;
      }
    };
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

  // Auto-announce on load (파싱 중이 아닐 때만)
  const autoAnnounceMessage = books.length > 0
    ? `교재 선택. ${books.length}개의 교재가 있습니다. 1부터 ${Math.min(books.length, 9)}까지 번호를 눌러 선택하거나, 플러스 키로 새 교재를 추가하세요.`
    : '교재 선택. 등록된 교재가 없습니다. 플러스 키를 눌러 새 교재를 추가하세요.';

  // 파싱 중이 아니고 로딩이 완료되었을 때만 자동 안내
  const isParsing = parsingBookId !== null || reparsingBookId !== null;
  useAutoGuidance(autoAnnounceMessage, [loading, books.length], {
    enabled: !loading && !isParsing
  });

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
    speak(`${book.title} 교재 상세 페이지로 이동합니다.`);

    // 교재 상세 페이지로 이동
    navigate(`/book/${book.book_id}`);
  };

  const handleAddBook = () => {
    setShowUpload(true);
  };

  const handleUploadComplete = async (uploadedBook: Book) => {
    setShowUpload(false);
    await loadBooks();
    
    // 업로드된 교재가 파싱 중이면 상태 폴링 시작
    if (uploadedBook.parse_status === 'PROCESSING') {
      setParsingBookId(uploadedBook.book_id);
      showToastMsg(`${uploadedBook.title} 교재가 추가되었습니다. 파싱이 진행 중입니다...`);
      speak(`${uploadedBook.title} 교재가 추가되었습니다. 파싱이 진행 중입니다.`);
      
      // 기존 interval 정리
      if (parseStatusIntervalRef.current) {
        clearInterval(parseStatusIntervalRef.current);
      }
      
      // 파싱 상태 폴링 (10초마다 - 중복 요청 방지)
      let lastStatus: string | null = null;
      let checkCount = 0;
      parseStatusIntervalRef.current = setInterval(async () => {
        try {
          checkCount++;
          const status = await booksAPI.getParseStatus(uploadedBook.book_id);

          // 진행 메시지 생성
          const progressMsg = status.message || `${status.progress}%`;

          // 상태가 변경되었을 때만 로그 출력
          if (lastStatus !== status.status) {
            if (import.meta.env.DEV) console.log(`[BookSelect] Upload parse status 변경: ${lastStatus} -> ${status.status} (${progressMsg})`);
            lastStatus = status.status;
            // 상태 변경 시 토스트 메시지 표시
            if (status.status === 'PROCESSING') {
              showToastMsg(`파싱 진행 중... ${progressMsg}`);
            }
          } else if (checkCount % 6 === 0) {
            // 1분마다 상태 로그 (파싱이 진행 중임을 확인)
            if (import.meta.env.DEV) console.log(`[BookSelect] 파싱 진행 중... (${progressMsg}, 체크 횟수: ${checkCount})`);
            showToastMsg(`파싱 진행 중... ${progressMsg}`);
          }

          if (status.status === 'DONE' || status.status === 'FAILED') {
            if (parseStatusIntervalRef.current) {
              clearInterval(parseStatusIntervalRef.current);
              parseStatusIntervalRef.current = null;
            }
            setParsingBookId(null);
            await loadBooks(); // 교재 목록 새로고침

            if (status.status === 'DONE') {
              if (import.meta.env.DEV) console.log(`[BookSelect] 파싱 완료! (총 체크 횟수: ${checkCount})`);
              showToastMsg('파싱이 완료되었습니다!');
              speak('파싱이 완료되었습니다.');
            } else {
              if (import.meta.env.DEV) console.log(`[BookSelect] 파싱 실패 (총 체크 횟수: ${checkCount})`);
              showToastMsg('파싱이 실패했습니다. 재파싱을 시도해보세요.');
              speak('파싱이 실패했습니다.');
            }
          }
        } catch (err: unknown) {
          console.error('[BookSelect] Failed to check parse status:', err);
          // 교재가 삭제되었거나 찾을 수 없는 경우 interval 정리
          const message = err instanceof Error ? err.message : '';
          if (message && message.includes('교재를 찾을 수 없습니다')) {
            if (parseStatusIntervalRef.current) {
              clearInterval(parseStatusIntervalRef.current);
              parseStatusIntervalRef.current = null;
            }
            setParsingBookId(null);
            await loadBooks(); // 교재 목록 새로고침
            showToastMsg('교재를 찾을 수 없습니다.');
          }
        }
      }, 10000); // 10초로 증가
      
      // 컴포넌트 언마운트 시 정리
      setTimeout(() => {
        if (parseStatusIntervalRef.current) {
          clearInterval(parseStatusIntervalRef.current);
          parseStatusIntervalRef.current = null;
        }
        setParsingBookId(null);
      }, 600000); // 10분 후 자동 정리
    } else {
      showToastMsg(`${uploadedBook.title} 교재가 추가되었습니다.`);
      speak(`${uploadedBook.title} 교재가 추가되었습니다.`);
    }
  };

  const handleDelete = async (bookId: string, bookTitle: string) => {
    if (!confirm(`정말 "${bookTitle}" 교재를 삭제하시겠습니까?`)) {
      return;
    }

    showToastMsg('교재를 삭제하는 중...');
    speak('교재를 삭제하는 중입니다.');

    try {
      const result = await booksAPI.deleteBook(bookId);
      if (result && result.ok) {
        showToastMsg(result.message || '교재가 삭제되었습니다.');
        speak(result.message || '교재가 삭제되었습니다.');
        await loadBooks();
      } else {
        throw new Error(result?.message || '삭제 실패');
      }
    } catch (err: unknown) {
      console.error('[BookSelect] Failed to delete book:', err);
      const errorMsg = err instanceof Error ? err.message : '교재 삭제 중 오류가 발생했습니다.';
      showToastMsg(errorMsg);
      speak(errorMsg);
    }
  };

  const handleSyncFromJson = async (bookId: string) => {
    showToastMsg('JSON 파일을 동기화합니다...');
    speak('JSON 파일을 동기화합니다.');

    try {
      const result = await booksAPI.syncFromJson(bookId);
      if (result.ok) {
        showToastMsg(result.message || 'JSON 동기화가 완료되었습니다!');
        speak(result.message || 'JSON 동기화가 완료되었습니다.');
        await loadBooks(); // 교재 목록 새로고침
      } else {
        throw new Error(result.message || 'JSON 동기화 실패');
      }
    } catch (err: unknown) {
      console.error('[BookSelect] Failed to sync from JSON:', err);
      const errorMsg = err instanceof Error ? err.message : 'JSON 동기화 중 오류가 발생했습니다.';
      showToastMsg(errorMsg);
      speak('JSON 동기화 중 오류가 발생했습니다.');
    }
  };

  const handleReparse = async (bookId: string) => {
    setReparsingBookId(bookId);
    showToastMsg('교재를 재파싱합니다. 잠시만 기다려주세요...');
    speak('교재를 재파싱합니다. 잠시만 기다려주세요.');

    try {
      if (import.meta.env.DEV) console.log('[BookSelect] Reparse request for book:', bookId);
      const result = await booksAPI.reparse(bookId);
      if (import.meta.env.DEV) console.log('[BookSelect] Reparse response:', result);

      if (result.ok) {
        showToastMsg('재파싱이 시작되었습니다.');
        speak('재파싱이 시작되었습니다. 완료까지 1-2분 정도 걸립니다.');

        // 기존 interval 정리
        if (parseStatusIntervalRef.current) {
          clearInterval(parseStatusIntervalRef.current);
        }
        
        // 10초마다 상태 체크 (중복 요청 방지)
        let lastStatus: string | null = null;
        let checkCount = 0;
        parseStatusIntervalRef.current = setInterval(async () => {
          try {
            checkCount++;
            const status = await booksAPI.getParseStatus(bookId);

            // 진행 메시지 생성
            const progressMsg = status.message || `${status.progress}%`;

            // 상태가 변경되었을 때만 로그 출력
            if (lastStatus !== status.status) {
              if (import.meta.env.DEV) console.log(`[BookSelect] 재파싱 상태 변경: ${lastStatus} -> ${status.status} (${progressMsg})`);
              lastStatus = status.status;
              // 상태 변경 시 토스트 메시지 표시
              if (status.status === 'PROCESSING') {
                showToastMsg(`재파싱 진행 중... ${progressMsg}`);
              }
            } else if (checkCount % 6 === 0) {
              // 1분마다 상태 로그 (파싱이 진행 중임을 확인)
              if (import.meta.env.DEV) console.log(`[BookSelect] 재파싱 진행 중... (${progressMsg}, 체크 횟수: ${checkCount})`);
              showToastMsg(`재파싱 진행 중... ${progressMsg}`);
            }

            if (status.status === 'DONE') {
              if (parseStatusIntervalRef.current) {
                clearInterval(parseStatusIntervalRef.current);
                parseStatusIntervalRef.current = null;
              }
              setReparsingBookId(null);
              await loadBooks();
              if (import.meta.env.DEV) console.log(`[BookSelect] 재파싱 완료! (총 체크 횟수: ${checkCount})`);
              showToastMsg('재파싱이 완료되었습니다!');
              speak('재파싱이 완료되었습니다.');
            } else if (status.status === 'FAILED') {
              if (parseStatusIntervalRef.current) {
                clearInterval(parseStatusIntervalRef.current);
                parseStatusIntervalRef.current = null;
              }
              setReparsingBookId(null);
              if (import.meta.env.DEV) console.log(`[BookSelect] 재파싱 실패 (총 체크 횟수: ${checkCount})`);
              showToastMsg('재파싱이 실패했습니다.');
              speak('재파싱이 실패했습니다. 관리자에게 문의하세요.');
            }
          } catch (err: unknown) {
            console.error('[BookSelect] Failed to check parse status:', err);
            // 교재가 삭제되었거나 찾을 수 없는 경우 interval 정리
            const message = err instanceof Error ? err.message : '';
            if (message && message.includes('교재를 찾을 수 없습니다')) {
              if (parseStatusIntervalRef.current) {
                clearInterval(parseStatusIntervalRef.current);
                parseStatusIntervalRef.current = null;
              }
              setReparsingBookId(null);
              setParsingBookId(null);
              await loadBooks(); // 교재 목록 새로고침
              showToastMsg('교재를 찾을 수 없습니다.');
            }
          }
        }, 10000); // 10초로 증가

        // 5분 후 타임아웃
        setTimeout(() => {
          if (parseStatusIntervalRef.current) {
            clearInterval(parseStatusIntervalRef.current);
            parseStatusIntervalRef.current = null;
          }
          setReparsingBookId(null);
        }, 300000);
      } else {
        const errorMsg = result.message || '재파싱 실패';
        console.error('[BookSelect] Reparse failed:', errorMsg, result);
        throw new Error(errorMsg);
      }
    } catch (err: unknown) {
      console.error('[BookSelect] Failed to reparse:', err);
      if (err instanceof Error) {
        console.error('[BookSelect] Error details:', {
          message: err.message,
          stack: err.stack
        });
      }
      setReparsingBookId(null);

      // 더 자세한 에러 메시지 표시
      const errorMsg = err instanceof Error ? err.message : '재파싱 중 오류가 발생했습니다.';

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

        {/* 업로드된 교재 */}
        {books.length > 0 && (
          <div className="mb-6">
            <h2 className="text-lg font-semibold mb-3">📖 업로드된 교재</h2>
          </div>
        )}

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
              {books.map((book, index) => (
                <BookListItem
                  key={book.book_id}
                  book={book}
                  index={index}
                  isSelected={selectedIndex === index}
                  isReparsing={reparsingBookId === book.book_id}
                  isParsing={parsingBookId === book.book_id}
                  onSelect={() => handleSelectBook(index)}
                  onReparse={() => handleReparse(book.book_id)}
                  onSyncFromJson={() => handleSyncFromJson(book.book_id)}
                  onDelete={() => handleDelete(book.book_id, book.title)}
                  onMouseEnter={() => setSelectedIndex(index)}
                />
              ))}
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
            <br />
            <span className="text-primary">💡 파싱 완료된 교재는 "JSON 동기화" 버튼을 클릭하세요</span>
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
