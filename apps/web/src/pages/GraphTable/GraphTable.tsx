import { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import AppShellMobile from '../../components/ui/AppShellMobile';
import SpeechBar from '../../components/input/SpeechBar';
import useTTS from '../../hooks/useTTS';
import useSTT from '../../hooks/useSTT';
import useVoiceCommands from '../../hooks/useVoiceCommands';
import ToastA11y from '../../components/system/ToastA11y';
import { examAPI, type GraphPatterns } from '../../lib/api';
import ImageUpload from './components/ImageUpload';
import GraphPatternsComponent from './components/GraphPatterns';

export default function GraphTable() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { speak, stop: stopTTS } = useTTS();
  const { start: startSTT, stop: stopSTT, isListening, transcript } = useSTT();
  const [showToast, setShowToast] = useState(false);
  const [toastMessage, setToastMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [patterns, setPatterns] = useState<GraphPatterns | null>(null);
  const [selectedImage, setSelectedImage] = useState<File | null>(null);

  // URL 파라미터에서 읽기 모드 확인
  const modeParam = searchParams.get('mode');
  const readingMode: 'braille-only' | 'audio-first' | 'mixed' = modeParam === 'braille-read'
    ? 'braille-only'
    : modeParam === 'audio-first'
    ? 'audio-first'
    : 'braille-only'; // 기본값: 점자 읽기 모드

  // 페이지 진입 시 자동 음성 안내
  useEffect(() => {
    const welcomeMessage = readingMode === 'braille-only'
      ? '그래프 도표 점자 패턴 읽기 모드입니다. 패턴을 점자로 읽어보세요.'
      : '그래프 도표 해석 모드입니다. 이미지를 업로드하면 패턴을 분석해드립니다.';
    const timer = setTimeout(() => {
      speak(welcomeMessage);
    }, 500);
    return () => clearTimeout(timer);
  }, [speak, readingMode]);

  const handleImageSelect = async (file: File) => {
    setSelectedImage(file);
    setLoading(true);
    setError(null);
    setPatterns(null);

    try {
      const result = await examAPI.analyzeGraph(file);
      if (result) {
        setPatterns(result);
        speak('분석이 완료되었습니다.');
      } else {
        const errorMsg = '그래프 분석에 실패했습니다.';
        setError(errorMsg);
        speak(errorMsg);
      }
    } catch (err) {
      const errorMsg = '그래프 분석 중 오류가 발생했습니다.';
      setError(errorMsg);
      speak(errorMsg);
    } finally {
      setLoading(false);
    }
  };

  const handleReset = () => {
    setSelectedImage(null);
    setPatterns(null);
    setError(null);
    speak('새로운 이미지를 업로드할 수 있습니다.');
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
      const helpText = '그래프 도표 해석 모드입니다. 이미지를 업로드하면 추세, 극값, 비교 패턴을 분석하여 점자로 표시합니다.';
      speak(helpText);
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
    <AppShellMobile title="그래프·도표 해석" className="relative">
      <div className="mb-4">
        <SpeechBar isListening={isListening} transcript={transcript} />
      </div>

      <div className="p-4">
        {loading && (
          <div className="text-center py-8">
            <p className="text-muted">분석 중...</p>
            <p className="text-sm text-muted mt-2">이미지를 분석하고 있습니다.</p>
          </div>
        )}

        {error && (
          <div className="bg-error/10 border border-error rounded-lg p-4 mb-4">
            <p className="text-error">{error}</p>
          </div>
        )}

        {!loading && !error && (
          <div className="space-y-6">
            {!patterns ? (
              <ImageUpload
                onImageSelect={handleImageSelect}
                onSpeak={speak}
              />
            ) : (
              <>
                <div className="flex gap-2 mb-4">
                  <button
                    onClick={handleReset}
                    className="btn-ghost"
                    aria-label="새 이미지 업로드"
                  >
                    ← 새 이미지 업로드
                  </button>
                </div>
                <GraphPatternsComponent
                  patterns={patterns}
                  onSpeak={speak}
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
