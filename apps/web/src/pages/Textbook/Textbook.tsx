import { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import AppShellMobile from '../../components/ui/AppShellMobile';
import SpeechBar from '../../components/input/SpeechBar';
import useTTS from '../../hooks/useTTS';
import useSTT from '../../hooks/useSTT';
import useVoiceCommands from '../../hooks/useVoiceCommands';
import ToastA11y from '../../components/system/ToastA11y';
import { examAPI, type Textbook, type Unit } from '../../lib/api';
import { useLearnStore } from '../../store/learnStore';
import TextbookList from './components/TextbookList';
import UnitList from './components/UnitList';
import UnitContent from './components/UnitContent';
import PDFUpload from './components/PDFUpload';

type ViewMode = 'textbooks' | 'units' | 'content';
type ReadingMode = 'braille-only' | 'audio-first' | 'mixed';

export default function Textbook() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { speak, stop: stopTTS } = useTTS();
  const { start: startSTT, stop: stopSTT, isListening, transcript } = useSTT();
  const [showToast, setShowToast] = useState(false);
  const [toastMessage, setToastMessage] = useState('');
  
  // State
  const [textbooks, setTextbooks] = useState<Textbook[]>([]);
  const [units, setUnits] = useState<Unit[]>([]);
  const [currentUnit, setCurrentUnit] = useState<Unit | null>(null);
  const [viewMode, setViewMode] = useState<ViewMode>('textbooks');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showPDFUpload, setShowPDFUpload] = useState(false);
  
  // URL 파라미터에서 읽기 모드 확인
  const readingModeParam = searchParams.get('mode');
  const readingMode: ReadingMode = readingModeParam === 'braille-read' 
    ? 'braille-only' 
    : readingModeParam === 'audio-first'
    ? 'audio-first'
    : 'braille-only'; // 기본값: 점자 읽기 모드
  
  // Store
  const { currentTextbook, setTextbook, setUnit, setUnits: setStoreUnits } = useLearnStore();

  // 페이지 진입 시 교재 목록 로드
  useEffect(() => {
    loadTextbooks();
  }, []);

  // 페이지 진입 시 자동 음성 안내
  useEffect(() => {
    const welcomeMessage = readingMode === 'braille-only'
      ? '수능특강 점자 읽기 모드입니다. 교재를 선택하여 점자로 읽어보세요.'
      : '수능특강 학습 모드입니다. 교재를 선택하여 단원을 학습할 수 있습니다.';
    const timer = setTimeout(() => {
      speak(welcomeMessage);
    }, 500);
    return () => clearTimeout(timer);
  }, [speak, readingMode]);

  const loadTextbooks = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await examAPI.listTextbooks();
      setTextbooks(data);
      if (data.length === 0) {
        speak('등록된 교재가 없습니다.');
      }
    } catch (err) {
      const errorMsg = '교재 목록을 불러오는 중 오류가 발생했습니다.';
      setError(errorMsg);
      speak(errorMsg);
    } finally {
      setLoading(false);
    }
  };

  const handleTextbookSelect = async (textbook: Textbook) => {
    setTextbook(textbook.id.toString());
    setViewMode('units');
    setLoading(true);
    setError(null);
    
    try {
      const unitList = await examAPI.listUnits(textbook.id);
      setUnits(unitList);
      setStoreUnits(unitList);
      
      if (unitList.length === 0) {
        speak(`${textbook.title}에 등록된 단원이 없습니다.`);
      } else {
        speak(`${textbook.title}에 ${unitList.length}개의 단원이 있습니다.`);
      }
    } catch (err) {
      const errorMsg = '단원 목록을 불러오는 중 오류가 발생했습니다.';
      setError(errorMsg);
      speak(errorMsg);
    } finally {
      setLoading(false);
    }
  };

  const handlePDFUploadComplete = async (textbookId: number) => {
    setShowPDFUpload(false);
    // 새로 업로드된 교재 선택
    await loadTextbooks();
    const uploadedTextbook = textbooks.find(t => t.id === textbookId);
    if (uploadedTextbook) {
      await handleTextbookSelect(uploadedTextbook);
    }
  };

  const handleUnitSelect = async (unit: Unit) => {
    setUnit(unit.id.toString());
    setViewMode('content');
    setLoading(true);
    setError(null);
    
    try {
      const unitData = await examAPI.getUnit(unit.id);
      if (unitData) {
        setCurrentUnit(unitData);
      } else {
        const errorMsg = '단원 내용을 불러올 수 없습니다.';
        setError(errorMsg);
        speak(errorMsg);
      }
    } catch (err) {
      const errorMsg = '단원 내용을 불러오는 중 오류가 발생했습니다.';
      setError(errorMsg);
      speak(errorMsg);
    } finally {
      setLoading(false);
    }
  };

  const handleBack = () => {
    if (viewMode === 'content') {
      setViewMode('units');
      setCurrentUnit(null);
      speak('단원 목록으로 돌아갑니다.');
    } else if (viewMode === 'units') {
      setViewMode('textbooks');
      setUnits([]);
      speak('교재 목록으로 돌아갑니다.');
    } else {
      navigate('/');
    }
  };

  const handleNextUnit = () => {
    if (viewMode === 'units' && units.length > 0) {
      const currentIndex = units.findIndex(u => u.id.toString() === currentTextbook);
      if (currentIndex >= 0 && currentIndex < units.length - 1) {
        handleUnitSelect(units[currentIndex + 1]);
      } else {
        speak('마지막 단원입니다.');
      }
    }
  };

  const handlePrevUnit = () => {
    if (viewMode === 'units' && units.length > 0) {
      const currentIndex = units.findIndex(u => u.id.toString() === currentTextbook);
      if (currentIndex > 0) {
        handleUnitSelect(units[currentIndex - 1]);
      } else {
        speak('첫 번째 단원입니다.');
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
    back: handleBack,
    help: () => {
      stopTTS();
      const helpText = '수능특강 학습 모드입니다. 교재를 선택하고 단원을 선택하여 학습할 수 있습니다. 음성으로 "다음 단원", "이전 단원"을 말할 수 있습니다.';
      speak(helpText);
    },
  });

  useEffect(() => {
    if (!transcript) return;
    
    const normalized = transcript.toLowerCase().trim();
    
    // 음성 명령 처리
    if (normalized.includes('다음 단원') || normalized.includes('다음단원')) {
      stopTTS();
      handleNextUnit();
      stopSTT();
      return;
    }
    
    if (normalized.includes('이전 단원') || normalized.includes('이전단원')) {
      stopTTS();
      handlePrevUnit();
      stopSTT();
      return;
    }
    
    if (normalized.includes('첫 번째 교재') || normalized.includes('첫번째 교재')) {
      stopTTS();
      if (textbooks.length > 0) {
        handleTextbookSelect(textbooks[0]);
      }
      stopSTT();
      return;
    }
    
    // 숫자로 교재/단원 선택
    const numberMatch = normalized.match(/(\d+)\s*(번|번째|번 교재|번 단원)/);
    if (numberMatch) {
      const num = parseInt(numberMatch[1]);
      stopTTS();
      if (viewMode === 'textbooks' && num > 0 && num <= textbooks.length) {
        handleTextbookSelect(textbooks[num - 1]);
      } else if (viewMode === 'units' && num > 0 && num <= units.length) {
        handleUnitSelect(units[num - 1]);
      }
      stopSTT();
      return;
    }
    
    onSpeech(transcript);
  }, [transcript, onSpeech]);

  const showToastMessage = (message: string) => {
    setToastMessage(message);
    setShowToast(true);
  };

  return (
    <AppShellMobile title="수능특강 학습" className="relative">
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
          <>
            {viewMode === 'textbooks' && (
              <div className="space-y-4">
                {showPDFUpload ? (
                  <PDFUpload
                    onUploadComplete={handlePDFUploadComplete}
                    onSpeak={speak}
                  />
                ) : (
                  <>
                    <div className="flex justify-between items-center mb-4">
                      <h2 className="text-lg font-semibold">교재 목록</h2>
                      <button
                        onClick={() => setShowPDFUpload(true)}
                        className="btn-primary text-sm"
                        aria-label="PDF 업로드"
                      >
                        PDF 업로드
                      </button>
                    </div>
                    <TextbookList
                      textbooks={textbooks}
                      selectedId={currentTextbook ? parseInt(currentTextbook) : null}
                      onSelect={handleTextbookSelect}
                      onSpeak={speak}
                    />
                  </>
                )}
              </div>
            )}

            {viewMode === 'units' && (
              <div className="space-y-4">
                <button
                  onClick={handleBack}
                  className="btn-ghost mb-4"
                  aria-label="교재 목록으로 돌아가기"
                >
                  ← 교재 목록
                </button>
                <UnitList
                  units={units}
                  selectedId={null}
                  onSelect={handleUnitSelect}
                  onSpeak={speak}
                />
              </div>
            )}

            {viewMode === 'content' && (
              <div className="space-y-4">
                <button
                  onClick={handleBack}
                  className="btn-ghost mb-4"
                  aria-label="단원 목록으로 돌아가기"
                >
                  ← 단원 목록
                </button>
                {units.length > 0 && (
                  <div className="flex gap-2 mb-4">
                    <button
                      onClick={handlePrevUnit}
                      className="btn-ghost"
                      aria-label="이전 단원"
                    >
                      ← 이전
                    </button>
                    <button
                      onClick={handleNextUnit}
                      className="btn-ghost"
                      aria-label="다음 단원"
                    >
                      다음 →
                    </button>
                  </div>
                )}
                <UnitContent
                  unit={currentUnit}
                  onSpeak={speak}
                  readingMode={readingMode}
                />
              </div>
            )}
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

