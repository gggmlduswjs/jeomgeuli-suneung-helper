/**
 * 문학 강의 목록 페이지
 * 80개 강의를 표시하고 각 강의로 이동
 */
import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import AppShellMobile from '../components/ui/AppShellMobile';
import SpeechBar from '../components/input/SpeechBar';
import ToastA11y from '../components/system/ToastA11y';
import { usePageBase } from '../hooks/usePageBase';
import { literatureAPI, type LiteratureLectureSummary } from '../services/literature';
import { createModuleLogger } from '../utils/logger';
import { useLiteratureProgressStore } from '../store/literatureProgressStore';

const logger = createModuleLogger('LiteratureLectures');

export default function LiteratureLectures() {
  const navigate = useNavigate();
  const [lectures, setLectures] = useState<LiteratureLectureSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // 진도 관리
  const { isLectureCompleted, getProgressPercentage, setTotalLectures } = useLiteratureProgressStore();
  const progressPercentage = getProgressPercentage();

  const {
    speak,
    stopTTS,
    stopSTT,
    isListening,
    transcript,
    showToast,
    toastMessage,
    setShowToast,
    showToastMessage,
  } = usePageBase({
    autoAnnounce: '문학 강의 목록입니다.',
    voiceCommands: {
      home: () => {
        stopTTS();
        navigate('/');
        showToastMessage('홈으로 이동합니다.');
        speak('홈으로 이동합니다.');
        stopSTT();
      },
      back: () => {
        stopTTS();
        navigate(-1);
        showToastMessage('이전 페이지로 이동합니다.');
        speak('이전 페이지로 이동합니다.');
        stopSTT();
      },
    },
  });

  // 강의 목록 로드
  useEffect(() => {
    loadLectures();
  }, []);

  const loadLectures = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await literatureAPI.getLectures();
      setLectures(data);
      setTotalLectures(data.length); // 전체 강의 수 설정
      logger.log(`강의 ${data.length}개 로드됨`);

      // 로드 완료 안내
      showToastMessage(`문학 강의 ${data.length}개를 불러왔습니다.`);
      speak(`문학 강의 ${data.length}개를 불러왔습니다.`);
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : '강의 목록을 불러오지 못했습니다.';
      setError(errorMsg);
      logger.error('강의 로드 실패:', err);
      showToastMessage(errorMsg);
      speak(errorMsg);
    } finally {
      setLoading(false);
    }
  };

  // 강의 선택 핸들러
  const handleLectureSelect = (lecture: LiteratureLectureSummary) => {
    showToastMessage(`${lecture.title}을(를) 선택했습니다.`);
    speak(`${lecture.title}을(를) 선택했습니다.`);
    stopTTS();
    navigate(`/literature/lectures/${lecture.lecture_id}`);
    stopSTT();
  };

  // 강의 카드 읽기
  const handleLectureRead = (lecture: LiteratureLectureSummary) => {
    const message = `${lecture.lecture_id}강. ${lecture.title}`;
    speak(message);
  };

  return (
    <AppShellMobile title="문학 강의 목록" className="relative h-screen flex flex-col">
      <div className="mb-2">
        <SpeechBar isListening={isListening} transcript={transcript} />
      </div>

      <div className="px-2 py-1 space-y-2 flex-1 overflow-y-auto min-h-0">
        {/* 헤더 */}
        <div className="bg-card border border-border rounded-lg p-4">
          <h2 className="text-xl font-bold mb-2">문학 강의</h2>
          <p className="text-sm text-muted mb-2">
            총 {lectures.length}강의 강의가 있습니다.
          </p>
          {/* 진도율 */}
          <div className="mt-3">
            <div className="flex items-center justify-between text-sm mb-1">
              <span className="text-muted">학습 진도</span>
              <span className="font-semibold text-primary">{progressPercentage}%</span>
            </div>
            <div className="w-full bg-secondary/30 rounded-full h-2">
              <div
                className="bg-primary rounded-full h-2 transition-all duration-300"
                style={{ width: `${progressPercentage}%` }}
              />
            </div>
          </div>
        </div>

        {/* 로딩 상태 */}
        {loading && (
          <div className="text-center py-8">
            <div className="text-lg" role="status" aria-live="polite">
              강의 목록을 불러오는 중...
            </div>
          </div>
        )}

        {/* 에러 상태 */}
        {error && !loading && (
          <div className="bg-destructive/10 border border-destructive rounded-lg p-4">
            <h3 className="text-lg font-semibold text-destructive mb-2">오류 발생</h3>
            <p className="text-sm">{error}</p>
            <button
              onClick={loadLectures}
              className="mt-3 px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors"
              aria-label="다시 시도"
            >
              다시 시도
            </button>
          </div>
        )}

        {/* 강의 목록 */}
        {!loading && !error && lectures.length > 0 && (
          <div className="space-y-2" role="list" aria-label="문학 강의 목록">
            {lectures.map((lecture) => (
              <div
                key={lecture.lecture_id}
                className="bg-card border border-border rounded-lg p-4 hover:bg-accent/50 transition-colors cursor-pointer"
                role="listitem"
                tabIndex={0}
                onClick={() => handleLectureSelect(lecture)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    handleLectureSelect(lecture);
                  }
                  if (e.key === 'r' || e.key === 'R') {
                    e.preventDefault();
                    handleLectureRead(lecture);
                  }
                }}
                aria-label={`${lecture.lecture_id}강 ${lecture.title}`}
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="inline-block px-2 py-0.5 bg-primary/10 text-primary text-xs font-semibold rounded">
                        {lecture.lecture_id}강
                      </span>
                      {isLectureCompleted(lecture.lecture_id) && (
                        <span className="inline-block px-2 py-0.5 bg-success/10 text-success text-xs font-semibold rounded">
                          ✓ 완료
                        </span>
                      )}
                      <h3 className="text-base font-semibold">{lecture.title}</h3>
                    </div>
                  </div>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      handleLectureRead(lecture);
                    }}
                    className="ml-2 px-3 py-1 text-xs bg-secondary text-secondary-foreground rounded hover:bg-secondary/80 transition-colors"
                    aria-label={`${lecture.lecture_id}강 제목 읽기`}
                  >
                    읽기
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* 빈 상태 */}
        {!loading && !error && lectures.length === 0 && (
          <div className="text-center py-8">
            <p className="text-muted">강의가 없습니다.</p>
          </div>
        )}
      </div>

      {/* 하단 네비게이션 */}
      <div className="border-t border-border p-2 bg-background">
        <div className="flex gap-2">
          <button
            onClick={() => navigate(-1)}
            className="flex-1 px-4 py-3 bg-secondary text-secondary-foreground rounded-lg hover:bg-secondary/80 transition-colors font-semibold"
            aria-label="이전 페이지로"
          >
            뒤로
          </button>
          <button
            onClick={() => navigate('/')}
            className="flex-1 px-4 py-3 bg-secondary text-secondary-foreground rounded-lg hover:bg-secondary/80 transition-colors font-semibold"
            aria-label="홈으로"
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
