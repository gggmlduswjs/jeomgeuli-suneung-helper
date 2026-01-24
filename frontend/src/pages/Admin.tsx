/**
 * 관리자 페이지
 * 교재 관리, 업로드, 파싱 상태 모니터링
 */
import { useEffect, useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { booksAPI } from '../services/api/client';
import type { Book, ParseStatus } from '../types/book';
import { useTTS } from '../hooks/useTTS';
import { useBookStats } from '../hooks/useBookStats';
import AppShellMobile from '../components/ui/AppShellMobile';
import ToastA11y from '../components/system/ToastA11y';
import BookUploadWithTemplate from '../components/textbook/BookUploadWithTemplate';
import TemplateManager from '../components/admin/TemplateManager';
import TOCTemplateWizard from '../components/admin/TOCTemplateWizard';
import { 
  Upload, 
  BookOpen, 
  CheckCircle, 
  Clock, 
  AlertCircle, 
  RefreshCw, 
  Trash2,
  BarChart3,
  Home,
  FileText,
  Sparkles
} from 'lucide-react';

export default function Admin() {
  const navigate = useNavigate();
  const { speak } = useTTS();
  const [books, setBooks] = useState<Book[]>([]);
  const [loading, setLoading] = useState(true);
  const [showUpload, setShowUpload] = useState(false);
  const [selectedIndex, setSelectedIndex] = useState(-1);
  const [showToast, setShowToast] = useState(false);
  const [toastMessage, setToastMessage] = useState('');
  const [parsingBookId, setParsingBookId] = useState<string | null>(null);
  const [reparsingBookId, setReparsingBookId] = useState<string | null>(null);
  const [parseProgress, setParseProgress] = useState<Record<string, { progress: number; current_page?: number; total_pages?: number }>>({});
  const parseStatusIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const [showTemplates, setShowTemplates] = useState(false);
  const [showTOCWizard, setShowTOCWizard] = useState(false);

  // 통계 계산
  const stats = useBookStats(books);

  useEffect(() => {
    loadBooks();
    return () => {
      if (parseStatusIntervalRef.current) {
        clearInterval(parseStatusIntervalRef.current);
        parseStatusIntervalRef.current = null;
      }
    };
  }, []);

  // 파싱 중인 교재 자동 모니터링
  useEffect(() => {
    const processingBooks = books.filter(b => b.parse_status === 'PROCESSING');
    
    if (processingBooks.length === 0) {
      return;
    }

    // 각 파싱 중인 교재에 대해 폴링 시작
    const intervals: NodeJS.Timeout[] = [];
    
    processingBooks.forEach(book => {
      if (parsingBookId === book.book_id || reparsingBookId === book.book_id) {
        // 이미 폴링 중이면 건너뛰기
        return;
      }

      const interval = setInterval(async () => {
        try {
          const status = await booksAPI.getParseStatus(book.book_id);
          
          // 진행률 업데이트
          setParseProgress(prev => ({
            ...prev,
            [book.book_id]: {
              progress: status.progress,
              current_page: status.current_page,
              total_pages: status.total_pages
            }
          }));

          // 완료 또는 실패 시 폴링 중지 및 목록 새로고침
          if (status.status === 'DONE' || status.status === 'FAILED') {
            clearInterval(interval);
            await loadBooks();
            // 진행률 정보 제거
            setParseProgress(prev => {
              const next = { ...prev };
              delete next[book.book_id];
              return next;
            });
          }
        } catch (err) {
          console.error(`[Admin] Failed to check parse status for ${book.book_id}:`, err);
        }
      }, 10000); // 10초마다 확인

      intervals.push(interval);
    });

    return () => {
      intervals.forEach(interval => clearInterval(interval));
    };
  }, [books, parsingBookId, reparsingBookId]);

  const loadBooks = async () => {
    setLoading(true);
    try {
      const data = await booksAPI.list();
      setBooks(data);
    } catch (err) {
      console.error('[Admin] Failed to load books:', err);
      showToastMsg('교재를 불러오는 중 오류가 발생했습니다.');
    } finally {
      setLoading(false);
    }
  };

  const handleUploadComplete = async (uploadedBook: Book) => {
    await loadBooks();
    
    if (uploadedBook.parse_status === 'PROCESSING') {
      setParsingBookId(uploadedBook.book_id);
      showToastMsg(`${uploadedBook.title} 교재가 추가되었습니다. 파싱이 진행 중입니다...`);
      speak(`${uploadedBook.title} 교재가 추가되었습니다. 파싱이 진행 중입니다.`);

      // 파싱 상태 폴링
      let checkCount = 0;
      parseStatusIntervalRef.current = setInterval(async () => {
        try {
          checkCount++;
          const status = await booksAPI.getParseStatus(uploadedBook.book_id);
          
          // 진행률 업데이트
          setParseProgress(prev => ({
            ...prev,
            [uploadedBook.book_id]: {
              progress: status.progress,
              current_page: status.current_page,
              total_pages: status.total_pages
            }
          }));
          
          if (status.status === 'DONE' || status.status === 'FAILED') {
            if (parseStatusIntervalRef.current) {
              clearInterval(parseStatusIntervalRef.current);
              parseStatusIntervalRef.current = null;
            }
            setParsingBookId(null);
            // 진행률 정보 제거
            setParseProgress(prev => {
              const next = { ...prev };
              delete next[uploadedBook.book_id];
              return next;
            });
            await loadBooks();
            
            if (status.status === 'DONE') {
              showToastMsg('파싱이 완료되었습니다!');
              speak('파싱이 완료되었습니다.');
            } else {
              showToastMsg('파싱이 실패했습니다. 재파싱을 시도해보세요.');
              speak('파싱이 실패했습니다.');
            }
          } else if (status.status === 'PROCESSING') {
            // 진행 중일 때 진행률 표시
            const pageInfo = status.total_pages && status.current_page 
              ? ` (${status.current_page}/${status.total_pages}페이지)`
              : '';
            if (checkCount % 3 === 0) { // 30초마다 한 번씩만 토스트 표시
              showToastMsg(`파싱 진행 중... ${status.progress}%${pageInfo}`);
            }
          }
        } catch (err: unknown) {
          const message = err instanceof Error ? err.message : '';
          if (message?.includes('교재를 찾을 수 없습니다')) {
            if (parseStatusIntervalRef.current) {
              clearInterval(parseStatusIntervalRef.current);
              parseStatusIntervalRef.current = null;
            }
            setParsingBookId(null);
            await loadBooks();
          }
        }
      }, 10000);
      
      setTimeout(() => {
        if (parseStatusIntervalRef.current) {
          clearInterval(parseStatusIntervalRef.current);
          parseStatusIntervalRef.current = null;
        }
        setParsingBookId(null);
      }, 600000);
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
      const result = await booksAPI.delete(bookId);
      if (result && result.ok) {
        showToastMsg(result.message || '교재가 삭제되었습니다.');
        speak(result.message || '교재가 삭제되었습니다.');
        await loadBooks();
      } else {
        throw new Error(result?.message || '삭제 실패');
      }
    } catch (err: unknown) {
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
        await loadBooks();
      } else {
        throw new Error(result.message || 'JSON 동기화 실패');
      }
    } catch (err: unknown) {
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
      const result = await booksAPI.reparse(bookId);
      if (result.ok) {
        showToastMsg('재파싱이 시작되었습니다.');
        speak('재파싱이 시작되었습니다. 완료까지 1-2분 정도 걸립니다.');

        if (parseStatusIntervalRef.current) {
          clearInterval(parseStatusIntervalRef.current);
        }
        
        let lastStatus: string | null = null;
        let checkCount = 0;
        parseStatusIntervalRef.current = setInterval(async () => {
          try {
            checkCount++;
            const status = await booksAPI.getParseStatus(bookId);

            // 진행률 업데이트
            setParseProgress(prev => ({
              ...prev,
              [bookId]: {
                progress: status.progress,
                current_page: status.current_page,
                total_pages: status.total_pages
              }
            }));

            if (lastStatus !== status.status) {
              lastStatus = status.status;
            }
            
            // 진행률 표시 (상태가 변경되거나 진행률이 업데이트될 때)
            if (status.status === 'PROCESSING') {
              const pageInfo = status.total_pages && status.current_page 
                ? ` (${status.current_page}/${status.total_pages}페이지)`
                : '';
              if (checkCount % 3 === 0) { // 30초마다 한 번씩만 토스트 표시
                showToastMsg(`재파싱 진행 중... ${status.progress}%${pageInfo}`);
              }
            }

            if (status.status === 'DONE') {
              if (parseStatusIntervalRef.current) {
                clearInterval(parseStatusIntervalRef.current);
                parseStatusIntervalRef.current = null;
              }
              setReparsingBookId(null);
              // 진행률 정보 제거
              setParseProgress(prev => {
                const next = { ...prev };
                delete next[bookId];
                return next;
              });
              await loadBooks();
              showToastMsg('재파싱이 완료되었습니다!');
              speak('재파싱이 완료되었습니다.');
            } else if (status.status === 'FAILED') {
              if (parseStatusIntervalRef.current) {
                clearInterval(parseStatusIntervalRef.current);
                parseStatusIntervalRef.current = null;
              }
              setReparsingBookId(null);
              // 진행률 정보 제거
              setParseProgress(prev => {
                const next = { ...prev };
                delete next[bookId];
                return next;
              });
              showToastMsg('재파싱이 실패했습니다.');
              speak('재파싱이 실패했습니다.');
            }
          } catch (err: unknown) {
            const message = err instanceof Error ? err.message : '';
            if (message?.includes('교재를 찾을 수 없습니다')) {
              if (parseStatusIntervalRef.current) {
                clearInterval(parseStatusIntervalRef.current);
                parseStatusIntervalRef.current = null;
              }
              setReparsingBookId(null);
              await loadBooks();
            }
          }
        }, 10000);

        setTimeout(() => {
          if (parseStatusIntervalRef.current) {
            clearInterval(parseStatusIntervalRef.current);
            parseStatusIntervalRef.current = null;
          }
          setReparsingBookId(null);
        }, 300000);
      } else {
        throw new Error(result.message || '재파싱 실패');
      }
    } catch (err: unknown) {
      setReparsingBookId(null);
      const errorMsg = err instanceof Error ? err.message : '재파싱 중 오류가 발생했습니다.';
      showToastMsg(errorMsg);
      speak('재파싱 중 오류가 발생했습니다.');
    }
  };

  const getStatusIcon = (status: ParseStatus) => {
    switch (status) {
      case 'DONE':
        return <CheckCircle className="w-5 h-5 text-green-600" />;
      case 'PROCESSING':
      case 'PENDING':
        return <Clock className="w-5 h-5 text-yellow-600" />;
      case 'FAILED':
        return <AlertCircle className="w-5 h-5 text-red-600" />;
      default:
        return <BookOpen className="w-5 h-5 text-gray-400" />;
    }
  };

  const getStatusText = (status: ParseStatus) => {
    switch (status) {
      case 'DONE':
        return '완료';
      case 'PROCESSING':
        return '파싱 중';
      case 'PENDING':
        return '대기 중';
      case 'FAILED':
        return '실패';
      default:
        return '알 수 없음';
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
        title="교재 업로드"
        className="relative h-screen flex flex-col"
      >
        <div className="p-4 flex-1 overflow-y-auto">
          <button
            onClick={() => setShowUpload(false)}
            className="mb-4 px-4 py-2 text-sm text-muted-foreground hover:text-foreground transition-colors flex items-center gap-2"
          >
            ← 뒤로가기
          </button>
          <BookUploadWithTemplate
            onUploadComplete={handleUploadComplete}
            onSpeak={(msg) => showToastMsg(msg)}
            onCancel={() => setShowUpload(false)}
          />
        </div>
      </AppShellMobile>
    );
  }

  if (showTemplates) {
    return (
      <AppShellMobile 
        title="템플릿 관리"
        className="relative h-screen flex flex-col"
      >
        <div className="p-4 flex-1 overflow-hidden">
          <TemplateManager
            onBack={() => setShowTemplates(false)}
            onSpeak={(msg) => showToastMsg(msg)}
          />
        </div>
      </AppShellMobile>
    );
  }

  if (showTOCWizard) {
    return (
      <AppShellMobile 
        title="목차로 템플릿 생성"
        className="relative h-screen flex flex-col"
      >
        <div className="p-4 flex-1 overflow-hidden">
          <TOCTemplateWizard
            onBack={() => setShowTOCWizard(false)}
            onSaved={() => {
              // 생성 후 바로 템플릿 관리로 이동
              setShowTOCWizard(false);
              setShowTemplates(true);
            }}
            onSpeak={(msg) => showToastMsg(msg)}
          />
        </div>
      </AppShellMobile>
    );
  }

  return (
    <AppShellMobile title="관리자 페이지" className="relative h-screen flex flex-col">
      <div className="flex-1 flex flex-col px-4 py-6 overflow-y-auto">
        {/* 헤더 */}
        <div className="mb-6">
          <div className="flex items-center justify-between mb-2">
            <h1 className="text-2xl font-bold">관리자 페이지</h1>
            <button
              onClick={() => navigate('/')}
              className="flex items-center gap-2 px-3 py-2 text-sm text-muted-foreground hover:text-foreground transition-colors"
            >
              <Home className="w-4 h-4" />
              홈
            </button>
          </div>
          <p className="text-sm text-muted-foreground">교재 관리 및 모니터링</p>
        </div>

        {/* 통계 카드 */}
        <div className="grid grid-cols-2 gap-3 mb-6">
          <div className="bg-card border border-border rounded-lg p-4">
            <div className="flex items-center gap-2 mb-1">
              <BarChart3 className="w-4 h-4 text-primary" />
              <span className="text-sm font-medium text-muted-foreground">전체 교재</span>
            </div>
            <p className="text-2xl font-bold">{stats.total}</p>
          </div>
          <div className="bg-card border border-border rounded-lg p-4">
            <div className="flex items-center gap-2 mb-1">
              <CheckCircle className="w-4 h-4 text-green-600" />
              <span className="text-sm font-medium text-muted-foreground">완료</span>
            </div>
            <p className="text-2xl font-bold text-green-600">{stats.done}</p>
          </div>
          <div className="bg-card border border-border rounded-lg p-4">
            <div className="flex items-center gap-2 mb-1">
              <Clock className="w-4 h-4 text-yellow-600" />
              <span className="text-sm font-medium text-muted-foreground">진행 중</span>
            </div>
            <p className="text-2xl font-bold text-yellow-600">{stats.processing}</p>
          </div>
          <div className="bg-card border border-border rounded-lg p-4">
            <div className="flex items-center gap-2 mb-1">
              <AlertCircle className="w-4 h-4 text-red-600" />
              <span className="text-sm font-medium text-muted-foreground">실패</span>
            </div>
            <p className="text-2xl font-bold text-red-600">{stats.failed}</p>
          </div>
        </div>

        {/* 총 강의 수 */}
        <div className="bg-primary/10 border border-primary/30 rounded-lg p-4 mb-6">
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium">총 강의 수</span>
            <span className="text-2xl font-bold text-primary">{stats.totalLessons}</span>
          </div>
        </div>

        {/* 액션 버튼들 */}
        <div className="grid grid-cols-2 gap-2 mb-6">
          <button
            onClick={() => setShowUpload(true)}
            className="flex-1 px-4 py-3 bg-primary text-white rounded-lg hover:bg-primary/90 transition-colors flex items-center justify-center gap-2 font-medium"
          >
            <Upload className="w-5 h-5" />
            새 교재 업로드
          </button>
          <button
            onClick={() => setShowTemplates(!showTemplates)}
            className="flex-1 px-4 py-3 bg-secondary text-secondary-foreground rounded-lg hover:bg-secondary/80 transition-colors flex items-center justify-center gap-2 font-medium"
          >
            <FileText className="w-5 h-5" />
            템플릿 관리
          </button>
          <button
            onClick={() => setShowTOCWizard(true)}
            className="col-span-2 px-4 py-3 bg-primary/10 text-primary border border-primary/30 rounded-lg hover:bg-primary/20 transition-colors flex items-center justify-center gap-2 font-medium"
          >
            <Sparkles className="w-5 h-5" />
            목차로 템플릿 생성
          </button>
        </div>

        {/* 교재 목록 */}
        <div className="mb-4">
          <h2 className="text-lg font-semibold mb-3">교재 목록</h2>
        </div>

        {books.length === 0 ? (
          <div className="flex-1 flex flex-col items-center justify-center py-12">
            <BookOpen className="w-16 h-16 text-muted-foreground mb-4" />
            <p className="text-muted-foreground mb-4">등록된 교재가 없습니다.</p>
          </div>
        ) : (
          <div className="space-y-3 flex-1">
            {books.map((book, index) => {
              const isParsed = book.parse_status === 'DONE';
              const isProcessing = book.parse_status === 'PROCESSING' || parsingBookId === book.book_id;
              const isFailed = book.parse_status === 'FAILED';
              const isReparsing = reparsingBookId === book.book_id;

              return (
                <div
                  key={book.book_id}
                  className={`bg-card border rounded-lg p-4 transition-all ${
                    selectedIndex === index
                      ? 'border-primary shadow-lg'
                      : 'border-border'
                  }`}
                  onMouseEnter={() => setSelectedIndex(index)}
                >
                  <div className="flex items-start justify-between mb-3">
                    <div className="flex items-start gap-3 flex-1">
                      {getStatusIcon(book.parse_status)}
                      <div className="flex-1 min-w-0">
                        <h3 className="font-semibold text-lg mb-1">{book.title}</h3>
                        <div className="flex items-center gap-3 text-sm text-muted-foreground">
                          <span>{book.subject}</span>
                          {book.year && <span>• {book.year}년</span>}
                          <span>• 강 {book.lesson_count || 0}개</span>
                        </div>
                        <div className="mt-2 flex items-center gap-2 flex-wrap">
                          <span className={`text-xs px-2 py-1 rounded-full ${
                            isProcessing
                              ? 'bg-yellow-100 text-yellow-800'
                              : isFailed
                              ? 'bg-red-100 text-red-800'
                              : isParsed
                              ? 'bg-green-100 text-green-800'
                              : 'bg-gray-100 text-gray-800'
                          }`}>
                            {isReparsing ? '재파싱 중' : getStatusText(book.parse_status)}
                          </span>
                          {isProcessing && parseProgress[book.book_id] && (
                            <span className="text-xs text-muted-foreground">
                              {parseProgress[book.book_id].progress}%
                              {parseProgress[book.book_id].total_pages && parseProgress[book.book_id].current_page
                                ? ` (${parseProgress[book.book_id].current_page}/${parseProgress[book.book_id].total_pages}페이지)`
                                : ''}
                            </span>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* 액션 버튼 */}
                  <div className="flex gap-2 flex-wrap">
                    {isParsed && !isReparsing && (
                      <button
                        onClick={() => handleSyncFromJson(book.book_id)}
                        className="flex-1 px-3 py-2 text-sm bg-primary/10 text-primary border border-primary/30 rounded-lg
                                   hover:bg-primary/20 transition-colors flex items-center justify-center gap-2"
                      >
                        <RefreshCw className="w-4 h-4" />
                        JSON 동기화
                      </button>
                    )}

                    {(isFailed || (book.lesson_count === 0 && isParsed)) && !isReparsing && (
                      <button
                        onClick={() => handleReparse(book.book_id)}
                        disabled={isReparsing}
                        className="flex-1 px-3 py-2 text-sm bg-warning/10 text-warning border border-warning/30 rounded-lg
                                   hover:bg-warning/20 transition-colors flex items-center justify-center gap-2 disabled:opacity-50"
                      >
                        <RefreshCw className="w-4 h-4" />
                        재파싱
                      </button>
                    )}

                    {!isReparsing && (
                      <button
                        onClick={() => handleDelete(book.book_id, book.title)}
                        className="flex-1 px-3 py-2 text-sm bg-danger/10 text-danger border border-danger/30 rounded-lg
                                   hover:bg-danger/20 transition-colors flex items-center justify-center gap-2"
                      >
                        <Trash2 className="w-4 h-4" />
                        삭제
                      </button>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
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
