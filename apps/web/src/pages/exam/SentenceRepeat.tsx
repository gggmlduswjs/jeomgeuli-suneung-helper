import { useState, useCallback, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Repeat, Play, Pause } from 'lucide-react';
import AppShellMobile from '../../components/ui/AppShellMobile';
import SpeechBar from '../../components/input/SpeechBar';
import useTTS from '../../hooks/useTTS';
import useSTT from '../../hooks/useSTT';
import useVoiceCommands from '../../hooks/useVoiceCommands';
import { examAPI } from '../../lib/api';
import { brailleAPI } from '../../lib/api/BrailleAPI';
import useBrailleBLE from '../../hooks/useBrailleBLE';
import ToastA11y from '../../components/system/ToastA11y';
import VoiceService from '../../services/VoiceService';
import { useVoiceStore } from '../../store/voice';

export default function SentenceRepeat() {
  const navigate = useNavigate();
  const { speak, stop: stopTTS } = useTTS();
  const { start: startSTT, stop: stopSTT, isListening, transcript } = useSTT();
  const { writeText, isConnected } = useBrailleBLE();
  const [text, setText] = useState('');
  const [sentences, setSentences] = useState<string[]>([]);
  const [currentIndex, setCurrentIndex] = useState(-1);
  const [error, setError] = useState<string | null>(null);
  const [showToast, setShowToast] = useState(false);
  const [toastMessage, setToastMessage] = useState('');

  // 페이지 진입 시 정답 목록 비우기
  useEffect(() => {
    VoiceService.setAnswerList([]);
  }, []);

  // 페이지 진입 시 자동 음성 안내
  useEffect(() => {
    const welcomeMessage = '문장 반복 모드입니다. 문장 단위로 점자와 음성을 동시에 제공합니다.';
    
    const timer = setTimeout(() => {
      speak(welcomeMessage);
    }, 500);

    return () => {
      clearTimeout(timer);
    };
  }, [speak]);

  // 텍스트를 문장 단위로 분리
  useEffect(() => {
    if (text) {
      const split = text.split(/[.!?]\s+/).filter(s => s.trim().length > 0);
      setSentences(split);
    } else {
      setSentences([]);
      setCurrentIndex(-1);
    }
  }, [text]);

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
  });

  // STT 결과 처리 - 문장 반복 명령
  useEffect(() => {
    if (!transcript) return;
    
    // 먼저 기본 명령 처리
    const handled = onSpeech(transcript);
    if (handled) {
      VoiceService.setAnswerList([]);
      const { resetTranscript } = useVoiceStore.getState();
      resetTranscript();
      return;
    }

    // 문장 반복 관련 명령 처리
    const normalized = transcript.toLowerCase().trim();
    
    if (normalized.includes('다시') || normalized.includes('반복')) {
      if (currentIndex >= 0 && currentIndex < sentences.length) {
        repeatSentence(currentIndex);
      }
    } else if (normalized.includes('다음 문장')) {
      if (currentIndex < sentences.length - 1) {
        repeatSentence(currentIndex + 1);
      } else {
        speak('마지막 문장입니다');
      }
    } else if (normalized.includes('이전 문장')) {
      if (currentIndex > 0) {
        repeatSentence(currentIndex - 1);
      } else {
        speak('첫 번째 문장입니다');
      }
    } else {
      // "문장 3번" 같은 패턴 매칭
      const match = normalized.match(/문장\s*(\d+)/);
      if (match) {
        const num = parseInt(match[1]) - 1;
        if (num >= 0 && num < sentences.length) {
          repeatSentence(num);
        } else {
          speak(`문장 ${match[1]}번을 찾을 수 없습니다`);
        }
      }
    }
  }, [transcript, currentIndex, sentences.length, onSpeech]);

  // 문장 반복 (점자 + 음성)
  const repeatSentence = useCallback(async (index: number) => {
    if (index < 0 || index >= sentences.length) return;

    const sentence = sentences[index];
    
    // 1. 점자 디스플레이에 전송
    if (isConnected) {
      try {
        // 점자 변환 후 전송
        await writeText(sentence);
      } catch (err) {
        console.error('[SentenceRepeat] 점자 전송 실패:', err);
      }
    }

    // 2. 음성으로 읽기
    speak(sentence);

    // 3. 요약도 함께 (비동기, 2초 후)
    setTimeout(async () => {
      try {
        const summary = await examAPI.getSentenceSummary(sentence);
        if (summary) {
          speak(`요약: ${summary}`);
        }
      } catch (err) {
        console.error('[SentenceRepeat] 요약 실패:', err);
      }
    }, 2000);

    setCurrentIndex(index);
  }, [sentences, isConnected, writeText, speak]);

  return (
    <AppShellMobile title="문장 반복" className="relative">
      <SpeechBar isListening={isListening} transcript={transcript} />
      
      <div className="p-4 space-y-4">
        <div className="bg-white rounded-lg p-4 shadow">
          <h2 className="text-lg font-semibold mb-4">문장 반복 학습</h2>
          
          <textarea
            value={text}
            onChange={(e) => setText(e.target.value)}
            placeholder="반복할 텍스트를 입력하세요..."
            rows={10}
            className="w-full p-3 border border-gray-300 rounded-lg mb-4 focus:outline-none focus:ring-2 focus:ring-primary"
            aria-label="반복할 텍스트 입력"
          />
          
          {sentences.length > 0 && (
            <div className="mb-4 p-3 bg-blue-50 rounded-lg">
              <p className="text-sm text-blue-800">
                총 {sentences.length}개 문장으로 분리되었습니다.
              </p>
            </div>
          )}
        </div>

        {sentences.length > 0 && (
          <div className="bg-white rounded-lg p-4 shadow">
            <h3 className="font-semibold mb-4">문장 목록</h3>
            <div className="space-y-2 max-h-96 overflow-y-auto">
              {sentences.map((sentence, idx) => (
                <button
                  key={idx}
                  onClick={() => repeatSentence(idx)}
                  className={`w-full text-left p-3 rounded-lg border transition-colors ${
                    idx === currentIndex
                      ? 'bg-primary/10 border-primary'
                      : 'bg-white border-gray-200 hover:bg-gray-50'
                  }`}
                  aria-label={`문장 ${idx + 1} 반복`}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="text-sm font-medium mb-1 text-gray-700">
                        문장 {idx + 1}
                      </div>
                      <div className="text-sm text-gray-600 line-clamp-2">
                        {sentence.length > 50 ? `${sentence.substring(0, 50)}...` : sentence}
                      </div>
                    </div>
                    {idx === currentIndex && (
                      <Repeat className="w-4 h-4 text-primary ml-2 flex-shrink-0" />
                    )}
                  </div>
                </button>
              ))}
            </div>
          </div>
        )}

        <div className="bg-blue-50 p-4 rounded-lg">
          <p className="text-sm text-blue-800 font-medium mb-2">음성 명령:</p>
          <ul className="text-sm text-blue-700 space-y-1 list-disc list-inside">
            <li>"다시" 또는 "반복" - 현재 문장 다시 읽기</li>
            <li>"다음 문장" - 다음 문장으로 이동</li>
            <li>"이전 문장" - 이전 문장으로 이동</li>
            <li>"문장 3번" - 특정 문장으로 이동</li>
          </ul>
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

