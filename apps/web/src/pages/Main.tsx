/**
 * 메인 페이지 (홈)
 * 이어하기, 교재 목록, 과목 선택
 */
import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import AppShellMobile from '../components/ui/AppShellMobile';
import SpeechBar from '../components/input/SpeechBar';
import useTTS from '../hooks/useTTS';
import useSTT from '../hooks/useSTT';
import useVoiceCommands from '../hooks/useVoiceCommands';
import ToastA11y from '../components/system/ToastA11y';
import ContinueLearningCard from './Home/components/ContinueLearningCard';
import SubjectSelectCard from './Home/components/SubjectSelectCard';
import PDFManagementCard from './Home/components/PDFManagementCard';
import BrailleDeviceCard from './Home/components/BrailleDeviceCard';
import { booksAPI } from '../services/books';
import { progressAPI } from '../services/progress';
import type { Book } from '../types/book';
import type { Progress } from '../types/progress';
import { useProgressStore } from '../store/progressStore';
import { useBookStore } from '../store/bookStore';

export default function Main() {
  const navigate = useNavigate();
  const { speak, stop: stopTTS } = useTTS();
  const { start: startSTT, stop: stopSTT, isListening, transcript } = useSTT();
  const [showToast, setShowToast] = useState(false);
  const [toastMessage, setToastMessage] = useState('');
  
  const [books, setBooks] = useState<Book[]>([]);
  const [currentProgress, setCurrentProgress] = useState<Progress | null>(null);
  const [loading, setLoading] = useState(false);
  
  const { setProgress } = useProgressStore();
  const { setBooks: setStoreBooks } = useBookStore();

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

  // 페이지 진입 시 자동 음성 안내
  useEffect(() => {
    const message = currentProgress
      ? `현재 학습 위치: ${currentProgress.lesson_id || '없음'}. 이어하기, 과목 선택, 교재 관리를 사용할 수 있습니다.`
      : '수능 점자 읽기 훈련 앱입니다. 오늘 학습 이어하기, 과목 선택, 교재 관리를 사용할 수 있습니다.';
    
    const timer = setTimeout(() => {
      speak(message);
    }, 500);
    
    return () => clearTimeout(timer);
  }, [speak, currentProgress]);

  // 음성 명령어
  const { onSpeech } = useVoiceCommands({
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
    <AppShellMobile title="점글이" className="relative">
      <div className="mb-4">
        <SpeechBar isListening={isListening} transcript={transcript} />
      </div>

      <div className="p-4 space-y-4">
        {loading && (
          <div className="text-center py-8">
            <p className="text-muted">로딩 중...</p>
          </div>
        )}

        {!loading && (
          <>
            {/* 이어하기 카드 */}
            <ContinueLearningCard
              progress={currentProgress}
              onContinue={() => {
                if (currentProgress?.unit_id) {
                  navigate(`/unit/${currentProgress.unit_id}`);
                }
              }}
              onSpeak={speak}
            />

            {/* 교재 목록 카드 */}
            <PDFManagementCard
              books={books}
              onBookSelect={(book) => {
                navigate(`/book/${book.book_id}`);
              }}
              onSpeak={speak}
            />

            {/* 과목 선택 카드 */}
            <SubjectSelectCard
              onSubjectSelect={(subject) => {
                navigate(`/book?subject=${subject}`);
              }}
              onSpeak={speak}
            />

            {/* 점자 디바이스 카드 */}
            <BrailleDeviceCard onSpeak={speak} />
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
