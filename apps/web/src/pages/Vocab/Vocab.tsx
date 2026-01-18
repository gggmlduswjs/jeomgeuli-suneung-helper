import { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import AppShellMobile from '../../components/ui/AppShellMobile';
import SpeechBar from '../../components/input/SpeechBar';
import useTTS from '../../hooks/useTTS';
import useSTT from '../../hooks/useSTT';
import useVoiceCommands from '../../hooks/useVoiceCommands';
import ToastA11y from '../../components/system/ToastA11y';
import { vocabAPI } from '../../lib/api';
import { useVocabStore } from '../../store/vocabStore';
import VocabCard from './components/VocabCard';
import SisaWords from './components/SisaWords';

type ViewMode = 'vocab' | 'sisa';

export default function Vocab() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { speak, stop: stopTTS } = useTTS();
  const { start: startSTT, stop: stopSTT, isListening, transcript } = useSTT();
  const [showToast, setShowToast] = useState(false);
  const [toastMessage, setToastMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [viewMode, setViewMode] = useState<ViewMode>('vocab');

  // URL 파라미터에서 읽기 모드 확인
  const modeParam = searchParams.get('mode');
  const readingMode: 'braille-only' | 'audio-first' | 'mixed' = modeParam === 'braille-read'
    ? 'braille-only'
    : modeParam === 'audio-first'
    ? 'audio-first'
    : 'braille-only'; // 기본값: 점자 읽기 모드

  // Store
  const {
    todayVocab,
    todaySisa,
    currentVocabIndex,
    currentSisaIndex,
    setTodayVocab,
    setTodaySisa,
    nextVocab,
    prevVocab,
    nextSisa,
    prevSisa,
    markLearned,
  } = useVocabStore();

  // 페이지 진입 시 어휘 로드
  useEffect(() => {
    loadTodayVocab();
  }, []);

  // 페이지 진입 시 자동 음성 안내
  useEffect(() => {
    const welcomeMessage = readingMode === 'braille-only'
      ? '어휘 점자 읽기 모드입니다. 어휘를 점자로 읽어보세요.'
      : '어휘 시사 학습 모드입니다. 오늘의 어휘와 시사 용어를 학습할 수 있습니다.';
    const timer = setTimeout(() => {
      speak(welcomeMessage);
    }, 500);
    return () => clearTimeout(timer);
  }, [speak, readingMode]);

  const loadTodayVocab = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await vocabAPI.getTodayVocab();
      if (data) {
        setTodayVocab(data.vocab || []);
        setTodaySisa(data.sisa || []);
        
        if (data.vocab.length === 0 && data.sisa.length === 0) {
          speak('오늘 학습할 어휘와 시사 용어가 없습니다.');
        } else {
          const vocabCount = data.vocab.length;
          const sisaCount = data.sisa.length;
          speak(`오늘의 어휘 ${vocabCount}개와 시사 용어 ${sisaCount}개가 있습니다.`);
        }
      }
    } catch (err) {
      const errorMsg = '어휘 목록을 불러오는 중 오류가 발생했습니다.';
      setError(errorMsg);
      speak(errorMsg);
    } finally {
      setLoading(false);
    }
  };

  const handleMarkLearned = async (queueId?: number) => {
    if (queueId) {
      // TODO: API 호출하여 학습 완료 표시
      // await markVocabLearned(queueId, 3);
    }
    markLearned();
    speak('학습 완료로 표시했습니다.');
    
    // 다음 어휘로 이동
    if (currentVocabIndex < todayVocab.length - 1) {
      nextVocab();
    }
  };

  const handleNext = () => {
    if (viewMode === 'vocab') {
      if (currentVocabIndex < todayVocab.length - 1) {
        nextVocab();
      } else {
        speak('마지막 어휘입니다.');
      }
    } else {
      if (currentSisaIndex < todaySisa.length - 1) {
        nextSisa();
      } else {
        speak('마지막 시사 용어입니다.');
      }
    }
  };

  const handlePrev = () => {
    if (viewMode === 'vocab') {
      if (currentVocabIndex > 0) {
        prevVocab();
      } else {
        speak('첫 번째 어휘입니다.');
      }
    } else {
      if (currentSisaIndex > 0) {
        prevSisa();
      } else {
        speak('첫 번째 시사 용어입니다.');
      }
    }
  };

  // 음성 명령 처리
  const { onSpeech } = useVoiceCommands({
    home: () => {
      stopTTS();
      navigate('/');
      stopSTT();
    },
    back: () => {
      stopTTS();
      navigate('/');
      stopSTT();
    },
    help: () => {
      stopTTS();
      const helpText = '어휘 시사 학습 모드입니다. 매일 새로운 어휘와 시사 용어를 제공합니다. 음성으로 "다음", "이전", "학습 완료"를 말할 수 있습니다.';
      speak(helpText);
    },
  });

  useEffect(() => {
    if (!transcript) return;
    
    const normalized = transcript.toLowerCase().trim();
    
    if (normalized.includes('다음') || normalized.includes('다음 어휘') || normalized.includes('다음 용어')) {
      stopTTS();
      handleNext();
      stopSTT();
      return;
    }
    
    if (normalized.includes('이전') || normalized.includes('이전 어휘') || normalized.includes('이전 용어')) {
      stopTTS();
      handlePrev();
      stopSTT();
      return;
    }
    
    if (normalized.includes('학습 완료') || normalized.includes('완료')) {
      stopTTS();
      const currentVocab = todayVocab[currentVocabIndex];
      if (currentVocab) {
        handleMarkLearned(currentVocab.queue_id);
      }
      stopSTT();
      return;
    }
    
    if (normalized.includes('시사') || normalized.includes('시사 용어')) {
      stopTTS();
      setViewMode('sisa');
      speak('시사 용어 모드로 전환했습니다.');
      stopSTT();
      return;
    }
    
    if (normalized.includes('어휘')) {
      stopTTS();
      setViewMode('vocab');
      speak('어휘 모드로 전환했습니다.');
      stopSTT();
      return;
    }
    
    onSpeech(transcript);
  }, [transcript, onSpeech]);

  const showToastMessage = (message: string) => {
    setToastMessage(message);
    setShowToast(true);
  };

  const currentVocab = todayVocab[currentVocabIndex];
  const currentSisa = todaySisa[currentSisaIndex];

  return (
    <AppShellMobile title="어휘·시사 학습" className="relative">
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
          <div className="space-y-4">
            <div className="flex gap-2 mb-4">
              <button
                onClick={() => setViewMode('vocab')}
                className={`flex-1 ${viewMode === 'vocab' ? 'btn-primary' : 'btn-ghost'}`}
                aria-label="어휘 모드"
              >
                어휘 ({todayVocab.length})
              </button>
              <button
                onClick={() => setViewMode('sisa')}
                className={`flex-1 ${viewMode === 'sisa' ? 'btn-primary' : 'btn-ghost'}`}
                aria-label="시사 용어 모드"
              >
                시사 ({todaySisa.length})
              </button>
            </div>

            {viewMode === 'vocab' ? (
              <div className="space-y-4">
                {currentVocab ? (
                  <>
                    <div className="flex gap-2">
                      <button
                        onClick={handlePrev}
                        className="btn-ghost"
                        disabled={currentVocabIndex === 0}
                        aria-label="이전 어휘"
                      >
                        ← 이전
                      </button>
                      <span className="flex-1 text-center text-muted">
                        {currentVocabIndex + 1} / {todayVocab.length}
                      </span>
                      <button
                        onClick={handleNext}
                        className="btn-ghost"
                        disabled={currentVocabIndex === todayVocab.length - 1}
                        aria-label="다음 어휘"
                      >
                        다음 →
                      </button>
                    </div>
                    <VocabCard
                      vocab={currentVocab}
                      index={currentVocabIndex}
                      onSpeak={speak}
                      onMarkLearned={() => handleMarkLearned(currentVocab.queue_id)}
                      readingMode={readingMode}
                    />
                  </>
                ) : (
                  <div className="p-4 text-center text-muted">
                    <p>오늘의 어휘가 없습니다.</p>
                  </div>
                )}
              </div>
            ) : (
              <SisaWords words={todaySisa} onSpeak={speak} />
            )}
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
