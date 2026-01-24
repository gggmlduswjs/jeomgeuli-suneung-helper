/**
 * 메인 페이지 (홈)
 * 이어하기, 교재 목록, 과목 선택
 */
import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import AppShellMobile from '../components/ui/AppShellMobile';
import SpeechBar from '../components/input/SpeechBar';
import ToastA11y from '../components/system/ToastA11y';
import { usePageBase } from '../hooks/usePageBase';
import ContinueLearningCard from '../components/home/ContinueLearningCard';
import SubjectSelectCard from '../components/home/SubjectSelectCard';
import PDFManagementCard from '../components/home/PDFManagementCard';
import BrailleDeviceCard from '../components/home/BrailleDeviceCard';
import { booksAPI } from '../services/api/client';
import { progressAPI } from '../services/progress';
import type { Book } from '../types/book';
import type { Progress } from '../types/progress';
import { useProgressStore } from '../store/progressStore';
import { useBookStore } from '../store/bookStore';
import { useLessonStore } from '../store/lessonStore';
import { useLearnStore } from '../store/learnStore';

export default function Main() {
  const navigate = useNavigate();
  const [books, setBooks] = useState<Book[]>([]);
  const [currentProgress, setCurrentProgress] = useState<Progress | null>(null);
  const [loading, setLoading] = useState(false);
  
  const { setProgress } = useProgressStore();
  const { setBooks: setStoreBooks, clearBooks } = useBookStore();
  const { clearLessons } = useLessonStore();
  const { clearAll: clearLearnStore } = useLearnStore();

  // 페이지 진입 시 자동 음성 안내 메시지 생성
  const autoAnnounce = currentProgress
    ? `현재 학습 위치: ${currentProgress.lesson_id || '없음'}. 이어하기, 과목 선택, 교재 관리를 사용할 수 있습니다.`
    : '수능 점자 읽기 훈련 앱입니다. 오늘 학습 이어하기, 과목 선택, 교재 관리를 사용할 수 있습니다.';

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
    autoAnnounce,
    voiceCommands: {
      home: () => {
        showToastMessage('이미 홈 화면입니다.');
        speak('이미 홈 화면입니다.');
      },
      continue: () => {
        if (currentProgress?.unit_id) {
          stopTTS();
          navigate(`/unit/${currentProgress.unit_id}`);
          showToastMessage('학습을 이어갑니다.');
          speak('학습을 이어갑니다.');
          stopSTT();
        } else {
          showToastMessage('진행 중인 학습이 없습니다.');
          speak('진행 중인 학습이 없습니다.');
        }
      },
      이어하기: () => {
        if (currentProgress?.unit_id) {
          stopTTS();
          navigate(`/unit/${currentProgress.unit_id}`);
          showToastMessage('학습을 이어갑니다.');
          speak('학습을 이어갑니다.');
          stopSTT();
        } else {
          showToastMessage('진행 중인 학습이 없습니다.');
          speak('진행 중인 학습이 없습니다.');
        }
      },
    },
  });

  // 페이지 진입 시 데이터 로드
  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      // 교재 목록 로드
      const booksData = await booksAPI.list();
      setBooks(booksData);
      setStoreBooks(booksData);
      
      // 이어하기 진도 로드
      const progress = await progressAPI.getContinue('u_demo');
      setCurrentProgress(progress);
      setProgress(progress);
    } catch (err) {
      console.error('[Main] 데이터 로드 실패:', err);
    } finally {
      setLoading(false);
    }
  };

  // 교재 및 강의 데이터 초기화
  const handleClearData = () => {
    clearBooks();
    clearLessons();
    clearLearnStore();
    setBooks([]);
    setCurrentProgress(null);
    showToastMessage('모든 교재 및 강의 데이터가 초기화되었습니다.');
    speak('모든 교재 및 강의 데이터가 초기화되었습니다.');
    console.log('[Main] 모든 교재 및 강의 데이터 초기화됨');
  };

  return (
    <AppShellMobile title="점글이" className="relative h-screen flex flex-col">
      <div className="mb-2">
        <SpeechBar isListening={isListening} transcript={transcript} />
      </div>

      <div className="px-2 py-1 space-y-2 flex-1 overflow-y-auto min-h-0">
        {loading && (
          <div className="text-center py-4">
            <p className="text-muted text-sm">로딩 중...</p>
          </div>
        )}

        {!loading && (
          <>
            {/* 이어서 학습하기 카드 */}
            <ContinueLearningCard
              progress={currentProgress}
              onContinue={() => {
                if (currentProgress?.unit_id) {
                  navigate(`/unit/${currentProgress.unit_id}`);
                  showToastMessage('학습을 이어갑니다.');
                  speak('학습을 이어갑니다.');
                } else {
                  showToastMessage('진행 중인 학습이 없습니다.');
                  speak('진행 중인 학습이 없습니다.');
                }
              }}
              onSpeak={speak}
            />

            {/* 과목 선택 카드 */}
            <SubjectSelectCard
              onSubjectSelect={(subject) => {
                // 교재 선택 페이지로 이동 (BookSelect로 통합)
                navigate('/books');
              }}
            />

            {/* 교재 관리 (PDF 업로드) */}
            <PDFManagementCard
              books={books}
              onSpeak={speak}
            />

            {/* 점자 디바이스 연결 */}
            <BrailleDeviceCard
              onConnect={() => {
                showToastMessage('점자 디바이스가 연결되었습니다.');
                speak('점자 디바이스가 연결되었습니다.');
              }}
              onDisconnect={() => {
                showToastMessage('점자 디바이스 연결이 해제되었습니다.');
                speak('점자 디바이스 연결이 해제되었습니다.');
              }}
            />

            {/* 데이터 초기화 버튼 */}
            <div className="bg-card border border-border rounded-lg p-4">
              <h3 className="text-lg font-semibold mb-2">데이터 관리</h3>
              <button
                onClick={handleClearData}
                className="w-full px-4 py-2 bg-warning/10 text-warning border border-warning rounded-lg hover:bg-warning/20 transition-colors"
                aria-label="교재 및 강의 데이터 초기화"
              >
                데이터 초기화
              </button>
              <p className="text-xs text-muted mt-2">
                모든 교재 및 강의 데이터를 초기화합니다.
              </p>
            </div>
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
