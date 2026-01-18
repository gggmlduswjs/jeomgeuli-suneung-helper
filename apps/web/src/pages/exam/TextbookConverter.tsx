import { useState, useCallback, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { FileText, Upload, Loader2 } from 'lucide-react';
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

export default function TextbookConverter() {
  const navigate = useNavigate();
  const { speak, stop: stopTTS } = useTTS();
  const { start: startSTT, stop: stopSTT, isListening, transcript } = useSTT();
  const { writeText, isConnected } = useBrailleBLE();
  const [pdfFile, setPdfFile] = useState<File | null>(null);
  const [isConverting, setIsConverting] = useState(false);
  const [conversionResult, setConversionResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);
  const [showToast, setShowToast] = useState(false);
  const [toastMessage, setToastMessage] = useState('');

  // 페이지 진입 시 정답 목록 비우기
  useEffect(() => {
    VoiceService.setAnswerList([]);
  }, []);

  // 페이지 진입 시 자동 음성 안내
  useEffect(() => {
    const welcomeMessage = '교재 변환 모드입니다. PDF 파일을 업로드하면 점자로 변환됩니다.';
    
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

  // 파일 선택 핸들러
  const handleFileSelect = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      if (file.type === 'application/pdf') {
        setPdfFile(file);
        setError(null);
        speak(`PDF 파일이 선택되었습니다: ${file.name}`);
      } else {
        setError('PDF 파일만 업로드 가능합니다');
        speak('PDF 파일만 업로드 가능합니다');
      }
    }
  }, [speak]);

  // 변환 실행
  const handleConvert = useCallback(async () => {
    if (!pdfFile) {
      setError('PDF 파일을 선택해주세요');
      speak('PDF 파일을 선택해주세요');
      return;
    }

    setIsConverting(true);
    setError(null);

    try {
      const result = await examAPI.convertTextbook(pdfFile);
      setConversionResult(result);
      
      speak(`변환 완료. 총 ${result.pages_count}페이지, ${result.cells_count}개 점자 셀로 변환되었습니다.`);
      
      // 점자 디스플레이로 전송 (처음 100자만)
      if (isConnected && result.braille_text) {
        const previewText = result.braille_text.substring(0, 100);
        await writeText(previewText);
      }
    } catch (err: any) {
      const errorMsg = err.userMessage || err.message || '변환 중 오류가 발생했습니다';
      setError(errorMsg);
      speak(errorMsg);
    } finally {
      setIsConverting(false);
    }
  }, [pdfFile, isConnected, writeText, speak]);

  // 점자 디스플레이로 전체 전송
  const handleSendToBraille = useCallback(async () => {
    if (!conversionResult?.braille_text || !isConnected) {
      speak('점자 디스플레이가 연결되지 않았습니다');
      return;
    }

    try {
      await writeText(conversionResult.braille_text);
      speak('점자 디스플레이로 전송되었습니다');
    } catch (err: any) {
      const errorMsg = err.message || '전송 중 오류가 발생했습니다';
      setError(errorMsg);
      speak(errorMsg);
    }
  }, [conversionResult, isConnected, writeText, speak]);

  return (
    <AppShellMobile title="교재 변환" className="relative">
      <SpeechBar isListening={isListening} transcript={transcript} />
      
      <div className="p-4 space-y-4">
        <div className="bg-white rounded-lg p-4 shadow">
          <h2 className="text-lg font-semibold mb-4">PDF 교재 점자 변환</h2>
          
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              PDF 파일 선택
            </label>
            <input
              type="file"
              accept=".pdf"
              onChange={handleFileSelect}
              className="block w-full text-sm text-gray-500
                file:mr-4 file:py-2 file:px-4
                file:rounded-lg file:border-0
                file:text-sm file:font-semibold
                file:bg-primary file:text-white
                hover:file:bg-primary/90
                disabled:opacity-50"
              disabled={isConverting}
              aria-label="PDF 파일 선택"
            />
          </div>
          
          {pdfFile && (
            <div className="mb-4 p-3 bg-gray-50 rounded-lg">
              <p className="text-sm text-gray-700">
                <FileText className="inline w-4 h-4 mr-2" />
                선택된 파일: {pdfFile.name}
              </p>
              <p className="text-xs text-gray-500 mt-1">
                크기: {(pdfFile.size / 1024 / 1024).toFixed(2)} MB
              </p>
            </div>
          )}
          
          <button
            onClick={handleConvert}
            disabled={!pdfFile || isConverting}
            className="w-full bg-primary text-white py-2 px-4 rounded-lg disabled:opacity-50 flex items-center justify-center gap-2"
            aria-label="점자 변환 실행"
          >
            {isConverting ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                변환 중...
              </>
            ) : (
              <>
                <Upload className="w-4 h-4" />
                점자 변환
              </>
            )}
          </button>
        </div>

        {conversionResult && (
          <div className="bg-white rounded-lg p-4 shadow">
            <h3 className="font-semibold mb-3">변환 결과</h3>
            <div className="space-y-2 text-sm">
              <p className="text-gray-700">
                <span className="font-medium">페이지:</span> {conversionResult.pages_count}페이지
              </p>
              <p className="text-gray-700">
                <span className="font-medium">점자 셀:</span> {conversionResult.cells_count.toLocaleString()}개
              </p>
              <p className="text-gray-700">
                <span className="font-medium">원문 길이:</span> {conversionResult.text_length.toLocaleString()}자
              </p>
            </div>
            
            {isConnected && (
              <button
                onClick={handleSendToBraille}
                className="mt-4 w-full bg-accent text-white py-2 px-4 rounded-lg hover:bg-accent/90 transition-colors"
                aria-label="점자 디스플레이로 전송"
              >
                점자 디스플레이로 전송
              </button>
            )}
            
            {!isConnected && (
              <p className="mt-4 text-sm text-gray-500 text-center">
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

