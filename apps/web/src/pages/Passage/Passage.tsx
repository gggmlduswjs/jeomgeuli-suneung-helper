import { useEffect, useState, useRef } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import AppShellMobile from '../../components/ui/AppShellMobile';
import SpeechBar from '../../components/input/SpeechBar';
import useTTS from '../../hooks/useTTS';
import useSTT from '../../hooks/useSTT';
import useVoiceCommands from '../../hooks/useVoiceCommands';
import ToastA11y from '../../components/system/ToastA11y';
import { examAPI, type PassageStructure } from '../../lib/api';
import { useLearnStore } from '../../store/learnStore';
import PassageInput from './components/PassageInput';
import PassageStructureComponent from './components/PassageStructure';

export default function Passage() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { speak, stop: stopTTS } = useTTS();
  const { start: startSTT, stop: stopSTT, isListening, transcript } = useSTT();
  const [showToast, setShowToast] = useState(false);
  const [toastMessage, setToastMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [passageText, setPassageText] = useState('');
  const [structure, setStructure] = useState<PassageStructure | null>(null);

  // URL 파라미터에서 읽기 모드 확인
  const modeParam = searchParams.get('mode');
  const readingMode: 'braille-only' | 'audio-first' | 'mixed' = modeParam === 'braille-read'
    ? 'braille-only'
    : modeParam === 'audio-first'
    ? 'audio-first'
    : 'braille-only'; // 기본값: 점자 읽기 모드

  // Store
  const { setPassage, setPassageStructure } = useLearnStore();

  // 청크 네비게이션을 위한 ref (PassageStructure에서 접근)
  const chunkNavigationRef = useRef<{ next: () => void; prev: () => void; reset: () => void } | null>(null);

  // 페이지 진입 시 자동 음성 안내
  useEffect(() => {
    const welcomeMessage = readingMode === 'braille-only'
      ? '국어 지문 점자 읽기 모드입니다. 지문을 점자로 읽어보세요.'
      : '국어 지문 연습 모드입니다. 지문을 입력하면 구조와 요약을 분석해드립니다.';
    const timer = setTimeout(() => {
      speak(welcomeMessage);
    }, 500);
    return () => clearTimeout(timer);
  }, [speak, readingMode]);

  const handleAnalyze = async (text: string) => {
    setPassage(text);
    setLoading(true);
    setError(null);
    setStructure(null);

    try {
      const result = await examAPI.analyzePassage(text);
      if (result) {
        setStructure(result);
        setPassageStructure(result);
        speak('분석이 완료되었습니다.');
      } else {
        const errorMsg = '지문 분석에 실패했습니다.';
        setError(errorMsg);
        speak(errorMsg);
      }
    } catch (err) {
      const errorMsg = '지문 분석 중 오류가 발생했습니다.';
      setError(errorMsg);
      speak(errorMsg);
    } finally {
      setLoading(false);
    }
  };

  const handleReset = () => {
    setPassageText('');
    setStructure(null);
    setError(null);
    speak('새로운 지문을 입력할 수 있습니다.');
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
      const helpText = '국어 지문 연습 모드입니다. 지문을 입력하거나 음성으로 말씀해주시면 구조와 요약을 분석해드립니다. "다음", "이전", "반복" 명령으로 점자 키워드 청크를 이동할 수 있습니다.';
      speak(helpText);
    },
    // 청크 네비게이션 명령
    next: () => {
      if (chunkNavigationRef.current) {
        chunkNavigationRef.current.next();
        speak('다음 키워드로 이동했습니다.');
      }
    },
    prev: () => {
      if (chunkNavigationRef.current) {
        chunkNavigationRef.current.prev();
        speak('이전 키워드로 이동했습니다.');
      }
    },
    repeat: () => {
      if (chunkNavigationRef.current) {
        chunkNavigationRef.current.reset();
        speak('첫 번째 키워드로 이동했습니다.');
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
    <AppShellMobile title="국어 지문 연습" className="relative">
      <div className="mb-4">
        <SpeechBar isListening={isListening} transcript={transcript} />
      </div>

      <div className="p-4">
        {loading && (
          <div className="text-center py-8">
            <p className="text-muted">분석 중...</p>
            <p className="text-sm text-muted mt-2">잠시만 기다려주세요.</p>
          </div>
        )}

        {error && (
          <div className="bg-error/10 border border-error rounded-lg p-4 mb-4">
            <p className="text-error">{error}</p>
          </div>
        )}

        {!loading && !error && (
          <div className="space-y-6">
            {!structure ? (
              <PassageInput
                onAnalyze={handleAnalyze}
                onSpeak={speak}
              />
            ) : (
              <>
                <div className="flex gap-2 mb-4">
                  <button
                    onClick={handleReset}
                    className="btn-ghost"
                    aria-label="새 지문 입력"
                  >
                    ← 새 지문 입력
                  </button>
                </div>
                <PassageStructureComponent
                  structure={structure}
                  onSpeak={speak}
                  chunkNavigationRef={chunkNavigationRef}
                  readingMode={readingMode}
                />
              </>
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
