/**
 * PDF 실시간 학습 페이지
 * PDF 페이지 보기 + 실시간 텍스트 추출 + AI 튜터
 */
import { useEffect, useState } from 'react';
import { useParams, useNavigate, useSearchParams } from 'react-router-dom';
import AppShellMobile from '../components/ui/AppShellMobile';
import ToastA11y from '../components/system/ToastA11y';
import { booksAPI } from '../services/api/client';
import useTTS from '../hooks/useTTS';
import { useToast } from '../hooks/useToast';
import { createModuleLogger } from '../utils/logger';

const logger = createModuleLogger('PDFStudy');

interface PageTextData {
  page_num: number;
  text: string;
  paragraphs: string[];
}

interface Lecture {
  lecture_id: number;
  title: string;
  start_page?: number;
  end_page?: number;
}

export default function PDFStudy() {
  const { bookId } = useParams<{ bookId: string }>();
  const [searchParams, setSearchParams] = useSearchParams();
  const navigate = useNavigate();
  const { speak } = useTTS();
  const { showToast, toastMessage, setShowToast, showToastMessage } = useToast();

  // PDF 상태
  const [currentPage, setCurrentPage] = useState<number>(1);
  const [pdfUrl, setPdfUrl] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  // 텍스트 상태
  const [pageText, setPageText] = useState<PageTextData | null>(null);
  const [loadingText, setLoadingText] = useState(false);

  // 강의 정보
  const [lectures, setLectures] = useState<Lecture[]>([]);
  const [currentLecture, setCurrentLecture] = useState<Lecture | null>(null);
  const [aiExplanation, setAiExplanation] = useState<string>('');
  const [aiExplanationLoading, setAiExplanationLoading] = useState(false);

  // AI 튜터 (전체 페이지용)
  const [aiQuestion, setAiQuestion] = useState('');
  const [aiAnswer, setAiAnswer] = useState('');
  const [aiLoading, setAiLoading] = useState(false);

  // 단락별 AI 튜터
  const [currentParagraphIndex, setCurrentParagraphIndex] = useState<number>(0);
  const [paragraphQuestions, setParagraphQuestions] = useState<Record<number, string>>({});
  const [paragraphAnswers, setParagraphAnswers] = useState<Record<number, string>>({});
  const [paragraphLoading, setParagraphLoading] = useState<Record<number, boolean>>({});
  const [paragraphExplanations, setParagraphExplanations] = useState<Record<number, string>>({});
  const [paragraphExplanationLoading, setParagraphExplanationLoading] = useState<Record<number, boolean>>({});

  // 교재 정보 및 강의 목록 로드
  useEffect(() => {
    if (!bookId) return;

    const loadBook = async () => {
      try {
        const book = await booksAPI.get(bookId);
        // PDF URL 구성
        const subject = book.subject.toLowerCase().replace('korean', 'literature');
        const url = `/api/data/${subject}/${bookId}/original.pdf`;
        setPdfUrl(url);

        // 강의 목록 로드 (캐시 방지를 위해 타임스탬프 추가)
        try {
          const cacheBuster = `?t=${Date.now()}`;
          const lecturesResponse = await fetch(`/api/data/${subject}/${bookId}/lectures/lectures.json${cacheBuster}`);
          if (lecturesResponse.ok) {
            const lecturesData = await lecturesResponse.json();
            const lecturesList = Array.isArray(lecturesData) ? lecturesData : (lecturesData.lectures || []);
            setLectures(lecturesList);
          }
        } catch (err) {
          logger.warn('강의 목록 로드 실패:', err);
        }

        setLoading(false);
      } catch (err) {
        logger.error('교재 로드 실패:', err);
        const errorMessage = err instanceof Error ? err.message : String(err);
        if (errorMessage.includes('교재를 찾을 수 없습니다')) {
          showToastMessage(`교재를 찾을 수 없습니다. 데이터베이스에 등록되어 있는지 확인해주세요. (ID: ${bookId})`);
        } else {
          showToastMessage('교재를 불러올 수 없습니다: ' + errorMessage);
        }
        setLoading(false);
      }
    };

    loadBook();
  }, [bookId]);

  // URL 파라미터에서 페이지 읽기
  // URL의 page 파라미터는 실제 PDF 페이지 번호를 의미
  useEffect(() => {
    const pageParam = searchParams.get('page');
    if (pageParam) {
      const page = parseInt(pageParam);
      if (!isNaN(page) && page >= 1) {
        setCurrentPage(page);
      }
    }
  }, [searchParams]);

  // 페이지 변경 시 텍스트 로드 및 현재 강의 찾기
  useEffect(() => {
    if (!bookId || currentPage < 1) return;

    // 현재 페이지에 해당하는 강의 찾기
    const lecture = lectures.find(l => 
      l.start_page && l.start_page <= currentPage && 
      (!l.end_page || l.end_page >= currentPage)
    ) || lectures.find(l => l.start_page === currentPage);
    setCurrentLecture(lecture || null);

    const loadPageText = async () => {
      setLoadingText(true);
      try {
        const response = await fetch(`/api/v1/books/${bookId}/pages/${currentPage}/text`);
        if (!response.ok) {
          throw new Error(`텍스트 추출 실패: ${response.status} ${response.statusText}`);
        }
        const data: PageTextData = await response.json();
        setPageText(data);
        // 페이지가 변경되면 첫 번째 단락으로 리셋 및 설명 초기화
        setCurrentParagraphIndex(0);
        setParagraphExplanations({});
        setParagraphExplanationLoading({});
        logger.log(`페이지 ${currentPage} 텍스트 로드 완료`);
        
        // 첫 번째 단락의 AI 설명 자동 생성
        if (data.paragraphs && data.paragraphs.length > 0) {
          generateParagraphExplanation(0, data.paragraphs[0]);
        }
      } catch (err) {
        logger.error('페이지 텍스트 로드 실패:', err);
        setPageText(null);
      } finally {
        setLoadingText(false);
      }
    };

    loadPageText();
  }, [bookId, currentPage, lectures]);

  // 페이지 이동
  const handlePageChange = (newPage: number) => {
    if (newPage < 1) newPage = 1;
    setCurrentPage(newPage);
    setSearchParams({ page: newPage.toString() });
  };

  // AI 질문하기 (전체 페이지)
  const handleAskAI = async () => {
    if (!aiQuestion.trim() || !pageText) {
      showToastMessage('질문을 입력하세요.');
      return;
    }

    setAiLoading(true);
    setAiAnswer('');

    try {
      const response = await fetch('/api/v1/ai/ask', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          question: aiQuestion,
          context: pageText.text,
          page_num: currentPage
        })
      });

      if (!response.ok) {
        throw new Error('AI 응답 실패');
      }

      const data = await response.json();
      setAiAnswer(data.answer || '답변을 생성하지 못했습니다.');
      speak(data.answer);
    } catch (err) {
      logger.error('AI 질문 실패:', err);
      showToastMessage('AI 응답 실패');
      setAiAnswer('죄송합니다. 답변을 생성할 수 없습니다.');
    } finally {
      setAiLoading(false);
    }
  };

  // 단락별 AI 질문하기
  const handleAskParagraphAI = async (paragraphIndex: number) => {
    if (!pageText || paragraphIndex >= pageText.paragraphs.length) return;

    const question = paragraphQuestions[paragraphIndex]?.trim();
    if (!question) {
      showToastMessage('질문을 입력하세요.');
      return;
    }

    setParagraphLoading({ ...paragraphLoading, [paragraphIndex]: true });
    setParagraphAnswers({ ...paragraphAnswers, [paragraphIndex]: '' });

    try {
      const paragraphText = pageText.paragraphs[paragraphIndex];
      const response = await fetch('/api/v1/ai/ask', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          question: question,
          context: paragraphText,
          page_num: currentPage
        })
      });

      if (!response.ok) {
        throw new Error('AI 응답 실패');
      }

      const data = await response.json();
      setParagraphAnswers({
        ...paragraphAnswers,
        [paragraphIndex]: data.answer || '답변을 생성하지 못했습니다.'
      });
      speak(data.answer);
    } catch (err) {
      logger.error('단락 AI 질문 실패:', err);
      showToastMessage('AI 응답 실패');
      setParagraphAnswers({
        ...paragraphAnswers,
        [paragraphIndex]: '죄송합니다. 답변을 생성할 수 없습니다.'
      });
    } finally {
      setParagraphLoading({ ...paragraphLoading, [paragraphIndex]: false });
    }
  };

  // 페이지 텍스트 읽기 (AI 설명 읽기)
  const handleReadPage = async () => {
    if (pageText && paragraphExplanations[currentParagraphIndex]) {
      speak(paragraphExplanations[currentParagraphIndex]);
    } else if (pageText && pageText.paragraphs[currentParagraphIndex]) {
      // 설명이 없으면 현재 단락 설명 생성 후 읽기
      await generateParagraphExplanation(currentParagraphIndex, pageText.paragraphs[currentParagraphIndex]);
      // 설명이 생성되면 읽기
      setTimeout(() => {
        if (paragraphExplanations[currentParagraphIndex]) {
          speak(paragraphExplanations[currentParagraphIndex]);
        }
      }, 500);
    }
  };

  // 단락별 AI 설명 생성
  const generateParagraphExplanation = async (paragraphIndex: number, paragraphText: string) => {
    // 이미 로딩 중이거나 설명이 있으면 스킵
    if (paragraphExplanationLoading[paragraphIndex] || paragraphExplanations[paragraphIndex]) {
      return;
    }

    setParagraphExplanationLoading({ ...paragraphExplanationLoading, [paragraphIndex]: true });

    try {
      const response = await fetch('/api/v1/ai/ask', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          question: '이 단락의 내용을 자세히 설명해주세요.',
          context: paragraphText,
          page_num: currentPage
        })
      });

      if (!response.ok) {
        throw new Error('AI 응답 실패');
      }

      const data = await response.json();
      setParagraphExplanations({
        ...paragraphExplanations,
        [paragraphIndex]: data.answer || '설명을 생성하지 못했습니다.'
      });
    } catch (err) {
      logger.error('단락 AI 설명 생성 실패:', err);
      setParagraphExplanations({
        ...paragraphExplanations,
        [paragraphIndex]: '죄송합니다. 설명을 생성할 수 없습니다.'
      });
    } finally {
      setParagraphExplanationLoading({ ...paragraphExplanationLoading, [paragraphIndex]: false });
    }
  };

  // 단락 변경 시 해당 단락의 AI 설명 자동 생성
  useEffect(() => {
    if (pageText && pageText.paragraphs[currentParagraphIndex]) {
      const paragraphText = pageText.paragraphs[currentParagraphIndex];
      if (!paragraphExplanations[currentParagraphIndex] && !paragraphExplanationLoading[currentParagraphIndex]) {
        generateParagraphExplanation(currentParagraphIndex, paragraphText);
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [currentParagraphIndex, pageText]);

  // AI 내용 설명 생성하기
  const handleGenerateExplanation = async () => {
    if (!pageText) {
      showToastMessage('페이지 텍스트가 없습니다.');
      return;
    }

    setAiExplanationLoading(true);
    setAiExplanation('');

    try {
      const response = await fetch('/api/v1/ai/ask', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          question: '이 페이지의 내용을 자세히 설명해주세요.',
          context: pageText.text,
          page_num: currentPage
        })
      });

      if (!response.ok) {
        throw new Error('AI 응답 실패');
      }

      const data = await response.json();
      setAiExplanation(data.answer || '설명을 생성하지 못했습니다.');
      speak(data.answer);
    } catch (err) {
      logger.error('AI 설명 생성 실패:', err);
      showToastMessage('AI 설명 생성 실패');
      setAiExplanation('죄송합니다. 설명을 생성할 수 없습니다.');
    } finally {
      setAiExplanationLoading(false);
    }
  };

  if (loading) {
    return (
      <AppShellMobile title="PDF 학습" className="relative h-screen flex flex-col">
        <div className="flex items-center justify-center flex-1">
          <p className="text-muted">로딩 중...</p>
        </div>
      </AppShellMobile>
    );
  }

  // 교재를 찾을 수 없는 경우
  if (!pdfUrl && !loading) {
    return (
      <AppShellMobile title="PDF 학습" className="relative h-screen flex flex-col">
        <div className="flex items-center justify-center flex-1 px-4">
          <div className="bg-destructive/10 border border-destructive rounded-lg p-6 max-w-md">
            <h3 className="text-lg font-semibold text-destructive mb-2">교재를 찾을 수 없습니다</h3>
            <p className="text-sm mb-4">
              교재 ID: <code className="bg-muted px-2 py-1 rounded text-xs">{bookId}</code>
            </p>
            <p className="text-sm text-muted-foreground mb-4">
              이 교재가 데이터베이스에 등록되어 있지 않습니다. Admin 페이지에서 교재를 먼저 업로드해주세요.
            </p>
            <button
              onClick={() => navigate('/admin')}
              className="w-full px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors font-semibold"
            >
              Admin 페이지로 이동
            </button>
          </div>
        </div>
      </AppShellMobile>
    );
  }

  return (
    <AppShellMobile 
      title={currentLecture?.title || `PDF 학습 - 페이지 ${currentPage}`} 
      className="relative h-screen flex flex-col"
    >
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* 강의 정보 및 페이지 표시 */}
        {currentLecture && (
          <div className="bg-card border-b border-border px-4 py-2">
            <div className="flex items-center justify-between">
              <div className="flex-1">
                <h2 className="text-sm font-semibold">{currentLecture.title}</h2>
                <div className="flex items-center gap-2 mt-1">
                  <span className="text-xs text-muted-foreground">본문 페이지</span>
                  <span className="text-xs px-2 py-0.5 bg-primary/10 text-primary rounded">
                    페이지 {currentPage}
                  </span>
                </div>
              </div>
              <button
                onClick={handleGenerateExplanation}
                disabled={!pageText || aiExplanationLoading || loadingText}
                className="px-3 py-1.5 text-xs bg-purple-500 text-white rounded hover:bg-purple-600 disabled:opacity-50 flex items-center gap-1"
              >
                <span>🤖</span>
                <span>📓</span>
                <span>AI 내용 설명 생성하기</span>
              </button>
            </div>
          </div>
        )}

        {/* AI 설명 표시 */}
        {aiExplanation && (
          <div className="bg-purple-50 border-b border-purple-200 px-4 py-3">
            <p className="text-sm whitespace-pre-wrap">{aiExplanation}</p>
          </div>
        )}

        {/* 페이지 이미지 영역 (해당 페이지만 표시, 스크롤 없음) */}
        <div 
          className="flex-1 overflow-hidden bg-gray-50 flex items-center justify-center p-2" 
          style={{ 
            height: '50vh',
            minHeight: '400px',
            maxHeight: '600px'
          }}
        >
          {pdfUrl ? (
            <img
              src={`/api/v1/books/${bookId}/pages/${currentPage}/image`}
              alt={`PDF 페이지 ${currentPage}`}
              className="max-w-full max-h-full object-contain"
              style={{
                width: 'auto',
                height: 'auto',
                maxWidth: '100%',
                maxHeight: '100%'
              }}
              onError={(e) => {
                // 이미지 로드 실패 시 iframe으로 fallback
                const target = e.target as HTMLImageElement;
                const container = target.parentElement;
                if (container) {
                  target.style.display = 'none';
                  const iframe = document.createElement('iframe');
                  iframe.src = `${pdfUrl}#page=${currentPage}&zoom=page-fit&toolbar=0&navpanes=0&scrollbar=0`;
                  iframe.className = 'w-full h-full border-0';
                  iframe.style.overflow = 'hidden';
                  iframe.scrolling = 'no';
                  iframe.title = `PDF 페이지 ${currentPage}`;
                  container.appendChild(iframe);
                }
              }}
            />
          ) : (
            <div className="flex items-center justify-center h-full">
              <p className="text-muted">페이지를 불러올 수 없습니다.</p>
            </div>
          )}
        </div>

        {/* 페이지 네비게이션 */}
        <div className="border-t border-border bg-background px-4 py-2">
          <div className="flex items-center justify-between">
            <button
              onClick={() => handlePageChange(currentPage - 1)}
              disabled={currentPage <= 1}
              className="px-4 py-2 bg-secondary text-secondary-foreground rounded hover:bg-secondary/80 disabled:opacity-50"
            >
              이전
            </button>

            <div className="flex items-center gap-2">
              <input
                type="number"
                value={currentPage}
                onChange={(e) => {
                  const page = parseInt(e.target.value);
                  if (!isNaN(page)) handlePageChange(page);
                }}
                className="w-16 px-2 py-1 text-center border border-border rounded"
                min={1}
              />
              <button
                onClick={handleReadPage}
                disabled={!pageText || loadingText}
                className="ml-2 px-3 py-1 bg-primary/10 text-primary rounded hover:bg-primary/20 disabled:opacity-50"
              >
                읽기
              </button>
            </div>

            <button
              onClick={() => handlePageChange(currentPage + 1)}
              className="px-4 py-2 bg-secondary text-secondary-foreground rounded hover:bg-secondary/80"
            >
              다음
            </button>
          </div>
        </div>

        {/* 단락별 Unit 영역 (한 번에 하나씩만 표시) */}
        <div className="border-t border-border bg-background">
          {loadingText ? (
            <div className="p-4 text-center text-muted-foreground">
              텍스트 추출 중...
            </div>
          ) : !pageText ? (
            <div className="p-4 text-center">
              <p className="text-sm text-muted-foreground mb-2">
                텍스트를 추출할 수 없습니다.
              </p>
            </div>
          ) : pageText.paragraphs.length > 0 ? (
            <div className="p-4">
              {/* 단락 네비게이션 헤더 */}
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-sm font-semibold">
                  📝 단락 {currentParagraphIndex + 1} / {pageText.paragraphs.length}
                </h3>
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => setCurrentParagraphIndex(Math.max(0, currentParagraphIndex - 1))}
                    disabled={currentParagraphIndex === 0}
                    className="px-3 py-1 text-xs bg-secondary text-secondary-foreground rounded hover:bg-secondary/80 disabled:opacity-50"
                  >
                    이전
                  </button>
                  <button
                    onClick={() => setCurrentParagraphIndex(Math.min(pageText.paragraphs.length - 1, currentParagraphIndex + 1))}
                    disabled={currentParagraphIndex >= pageText.paragraphs.length - 1}
                    className="px-3 py-1 text-xs bg-secondary text-secondary-foreground rounded hover:bg-secondary/80 disabled:opacity-50"
                  >
                    다음
                  </button>
                </div>
              </div>

              {/* 현재 단락 표시 - AI 설명만 표시 */}
              {pageText.paragraphs[currentParagraphIndex] && (
                <div className="bg-white border-2 border-green-500 rounded-lg p-3 space-y-2">
                  {/* AI 설명 */}
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-2">
                        <span className="text-xs font-medium text-primary">📚 단락 {currentParagraphIndex + 1} 설명</span>
                        {paragraphExplanationLoading[currentParagraphIndex] && (
                          <span className="text-xs text-muted-foreground">생성 중...</span>
                        )}
                      </div>
                      {paragraphExplanationLoading[currentParagraphIndex] ? (
                        <div className="p-4 text-center text-muted-foreground text-sm">
                          AI가 설명을 생성하고 있습니다...
                        </div>
                      ) : paragraphExplanations[currentParagraphIndex] ? (
                        <div className="space-y-2">
                          <p className="text-sm text-foreground whitespace-pre-wrap">
                            {paragraphExplanations[currentParagraphIndex]}
                          </p>
                          <button
                            onClick={() => speak(paragraphExplanations[currentParagraphIndex])}
                            className="text-xs px-2 py-1 bg-primary/10 text-primary rounded hover:bg-primary/20"
                          >
                            🔊 읽기
                          </button>
                        </div>
                      ) : (
                        <div className="p-4 text-center text-muted-foreground text-sm">
                          설명을 생성할 수 없습니다.
                        </div>
                      )}
                    </div>
                  </div>

                  {/* 단락별 AI 질문하기 */}
                  <div className="border-t border-border pt-2 space-y-2">
                    <div className="text-xs font-medium mb-1">AI에게 질문하기</div>
                    <div className="flex gap-2">
                      <input
                        type="text"
                        value={paragraphQuestions[currentParagraphIndex] || ''}
                        onChange={(e) => {
                          setParagraphQuestions({
                            ...paragraphQuestions,
                            [currentParagraphIndex]: e.target.value
                          });
                        }}
                        onKeyDown={(e) => {
                          if (e.key === 'Enter' && !paragraphLoading[currentParagraphIndex]) {
                            handleAskParagraphAI(currentParagraphIndex);
                          }
                        }}
                        placeholder="질문을 입력하세요..."
                        disabled={paragraphLoading[currentParagraphIndex]}
                        className="flex-1 px-2 py-1 text-xs border border-border rounded focus:outline-none focus:ring-2 focus:ring-primary/50"
                      />
                      <button
                        onClick={() => handleAskParagraphAI(currentParagraphIndex)}
                        disabled={!paragraphQuestions[currentParagraphIndex]?.trim() || paragraphLoading[currentParagraphIndex]}
                        className="px-3 py-1 text-xs bg-blue-500 text-white rounded hover:bg-blue-600 disabled:opacity-50"
                      >
                        {paragraphLoading[currentParagraphIndex] ? '...' : '질문하기'}
                      </button>
                    </div>

                    {/* AI 답변 */}
                    {paragraphAnswers[currentParagraphIndex] && (
                      <div className="bg-blue-50 rounded p-2 mt-2">
                        <p className="text-xs whitespace-pre-wrap">{paragraphAnswers[currentParagraphIndex]}</p>
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>
          ) : pageText ? (
            <div className="p-4 text-center text-muted-foreground text-sm">
              이 페이지에는 추출된 텍스트가 없습니다.
            </div>
          ) : null}
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
