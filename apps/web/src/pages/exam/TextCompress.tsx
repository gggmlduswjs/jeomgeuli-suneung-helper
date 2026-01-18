import { useState, useCallback, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Minimize2, FileText } from 'lucide-react';
import AppShellMobile from '../../components/ui/AppShellMobile';
import SpeechBar from '../../components/input/SpeechBar';
import useTTS from '../../hooks/useTTS';
import useSTT from '../../hooks/useSTT';
import useVoiceCommands from '../../hooks/useVoiceCommands';
import { examAPI } from '../../lib/api';
import useBrailleBLE from '../../hooks/useBrailleBLE';
import ToastA11y from '../../components/system/ToastA11y';
import VoiceService from '../../services/VoiceService';
import { useVoiceStore } from '../../store/voice';

export default function TextCompress() {
  const navigate = useNavigate();
  const { speak, stop: stopTTS } = useTTS();
  const { start: startSTT, stop: stopSTT, isListening, transcript } = useSTT();
  const { writeText, isConnected } = useBrailleBLE();
  const [inputText, setInputText] = useState('');
  const [compressedText, setCompressedText] = useState('');
  const [compressionMode, setCompressionMode] = useState<'compressed' | 'outline'>('compressed');
  const [isCompressing, setIsCompressing] = useState(false);
  const [compressionRatio, setCompressionRatio] = useState<number>(0);
  const [error, setError] = useState<string | null>(null);
  const [showToast, setShowToast] = useState(false);
  const [toastMessage, setToastMessage] = useState('');

  // 페이지 진입 시 정답 목록 비우기
  useEffect(() => {
    VoiceService.setAnswerList([]);
  }, []);

  // 페이지 진입 시 자동 음성 안내
  useEffect(() => {
    const welcomeMessage = '텍스트 압축 모드입니다. 긴 지문을 압축하여 읽기 시간을 단축합니다.';
    
    const timer = setTimeout(() => {
      speak(welcomeMessage);
    }, 500);

    return () => {
      clearTimeout(timer);
    };
  }, [speak]);

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

  // STT 결과 처리
  useEffect(() => {
    if (!transcript) return;
    
    const handled = onSpeech(transcript);
    if (handled) {
      VoiceService.setAnswerList([]);
      const { resetTranscript } = useVoiceStore.getState();
      resetTranscript();
      return;
    }
  }, [transcript, onSpeech]);

  // 압축 실행
  const handleCompress = useCallback(async () => {
    if (!inputText.trim()) {
      setError('텍스트를 입력해주세요');
      speak('텍스트를 입력해주세요');
      return;
    }

    setIsCompressing(true);
    setError(null);

    try {
      const result = await examAPI.compressText(
        inputText,
        compressionMode,
        compressionMode === 'compressed' ? 0.3 : 0.1
      );
      
      setCompressedText(result.compressed_text);
      setCompressionRatio(result.compression_ratio);
      
      const ratioPercent = Math.round(result.compression_ratio * 100);
      speak(`압축 완료. 원문의 ${ratioPercent}% 길이로 줄였습니다.`);
      
      // 점자 디스플레이로 전송
      if (isConnected) {
        await writeText(result.compressed_text);
      }
    } catch (err: any) {
      const errorMsg = err.userMessage || err.message || '압축 중 오류가 발생했습니다';
      setError(errorMsg);
      speak(errorMsg);
    } finally {
      setIsCompressing(false);
    }
  }, [inputText, compressionMode, isConnected, writeText, speak]);

  // 점자 디스플레이로 전송
  const handleSendToBraille = useCallback(async () => {
    if (!compressedText || !isConnected) {
      speak('점자 디스플레이가 연결되지 않았습니다');
      return;
    }

    try {
      await writeText(compressedText);
      speak('점자 디스플레이로 전송되었습니다');
    } catch (err: any) {
      const errorMsg = err.message || '전송 중 오류가 발생했습니다';
      setError(errorMsg);
      speak(errorMsg);
    }
  }, [compressedText, isConnected, writeText, speak]);

  return (
    <AppShellMobile title="텍스트 압축" className="relative">
      <SpeechBar isListening={isListening} transcript={transcript} />
      
      <div className="p-4 space-y-4">
        <div className="bg-white rounded-lg p-4 shadow">
          <h2 className="text-lg font-semibold mb-4">텍스트 압축</h2>
          
          <textarea
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            placeholder="압축할 텍스트를 입력하세요..."
            rows={10}
            className="w-full p-3 border border-gray-300 rounded-lg mb-4 focus:outline-none focus:ring-2 focus:ring-primary"
            aria-label="압축할 텍스트 입력"
          />
          
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              압축 모드 선택
            </label>
            <select
              value={compressionMode}
              onChange={(e) => setCompressionMode(e.target.value as 'compressed' | 'outline')}
              className="w-full p-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
              aria-label="압축 모드 선택"
            >
              <option value="compressed">압축 모드 (30% 길이)</option>
              <option value="outline">요약 모드 (10% 길이)</option>
            </select>
          </div>
          
          <button
            onClick={handleCompress}
            disabled={!inputText.trim() || isCompressing}
            className="w-full bg-primary text-white py-2 px-4 rounded-lg disabled:opacity-50 flex items-center justify-center gap-2"
            aria-label="압축 실행"
          >
            {isCompressing ? (
              <>
                <Minimize2 className="w-4 h-4 animate-pulse" />
                압축 중...
              </>
            ) : (
              <>
                <Minimize2 className="w-4 h-4" />
                압축하기
              </>
            )}
          </button>
        </div>

        {compressedText && (
          <div className="bg-white rounded-lg p-4 shadow">
            <h3 className="font-semibold mb-2">
              압축 결과 ({Math.round(compressionRatio * 100)}%)
            </h3>
            <div className="p-3 bg-gray-50 rounded-lg mb-3">
              <p className="text-sm text-gray-700 whitespace-pre-wrap">{compressedText}</p>
            </div>
            
            {isConnected && (
              <button
                onClick={handleSendToBraille}
                className="w-full bg-accent text-white py-2 px-4 rounded-lg hover:bg-accent/90 transition-colors"
                aria-label="점자 디스플레이로 전송"
              >
                점자 디스플레이로 전송
              </button>
            )}
            
            {!isConnected && (
              <p className="text-sm text-gray-500 text-center">
                점자 디스플레이를 연결하면 전송할 수 있습니다
              </p>
            )}
          </div>
        )}

        {error && (
          <div className="bg-red-50 text-red-700 p-4 rounded-lg">
            <p className="font-medium">오류</p>
            <p className="text-sm mt-1">{error}</p>
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

