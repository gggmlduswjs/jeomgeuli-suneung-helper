/**
 * 점자 디스플레이 설정 UI 컴포넌트
 * 음성 안내로 설정 변경 가능
 */
import { useState, useEffect } from 'react';
import { brailleDisplayConfig, type BrailleDisplayConfig } from '../../config/brailleDisplay';
import useTTS from '../../hooks/useTTS';
import useSTT from '../../hooks/useSTT';
import useVoiceCommands from '../../hooks/useVoiceCommands';

interface BrailleDisplaySettingsProps {
  onClose?: () => void;
}

export default function BrailleDisplaySettings({ onClose }: BrailleDisplaySettingsProps) {
  const { speak, stop: stopTTS } = useTTS();
  const { start: startSTT, stop: stopSTT, isListening, transcript } = useSTT();
  const [config, setConfig] = useState<BrailleDisplayConfig>(brailleDisplayConfig.get());

  // 설정 로드
  useEffect(() => {
    setConfig(brailleDisplayConfig.get());
    const welcomeMessage = '점자 디스플레이 설정입니다. 점자 셀 수, 스크롤 모드, 청크 분할 전략을 설정할 수 있습니다.';
    const timer = setTimeout(() => {
      speak(welcomeMessage);
    }, 500);
    return () => clearTimeout(timer);
  }, [speak]);

  // 설정 저장
  const handleSave = () => {
    brailleDisplayConfig.set(config);
    speak('설정이 저장되었습니다.');
    if (onClose) {
      setTimeout(() => onClose(), 2000);
    }
  };

  // 음성 명령 처리
  const { onSpeech } = useVoiceCommands({
    home: () => {
      stopTTS();
      stopSTT();
      if (onClose) onClose();
    },
    back: () => {
      stopTTS();
      stopSTT();
      if (onClose) onClose();
    },
  });

  // STT 결과 처리
  useEffect(() => {
    if (!transcript) return;
    
    const normalized = transcript.toLowerCase().trim();
    
    // 셀 수 변경
    if (normalized.includes('셀') || normalized.includes('cell')) {
      const match = normalized.match(/(\d+)\s*(?:개|셀|cell)/);
      if (match) {
        const cells = parseInt(match[1]);
        if (cells >= 1 && cells <= 20) {
          setConfig(prev => ({ ...prev, maxCells: cells }));
          speak(`${cells}개 셀로 설정되었습니다.`);
          stopSTT();
          return;
        }
      }
    }
    
    // 스크롤 모드 변경
    if (normalized.includes('자동') || normalized.includes('auto')) {
      setConfig(prev => ({ ...prev, scrollMode: 'auto' }));
      speak('자동 스크롤 모드로 설정되었습니다.');
      stopSTT();
      return;
    }
    
    if (normalized.includes('수동') || normalized.includes('manual')) {
      setConfig(prev => ({ ...prev, scrollMode: 'manual' }));
      speak('수동 스크롤 모드로 설정되었습니다.');
      stopSTT();
      return;
    }
    
    // 청크 전략 변경
    if (normalized.includes('단어') || normalized.includes('word')) {
      setConfig(prev => ({ ...prev, chunkStrategy: 'word' }));
      speak('단어 단위 분할로 설정되었습니다.');
      stopSTT();
      return;
    }
    
    if (normalized.includes('문장') || normalized.includes('sentence')) {
      setConfig(prev => ({ ...prev, chunkStrategy: 'sentence' }));
      speak('문장 단위 분할로 설정되었습니다.');
      stopSTT();
      return;
    }
    
    if (normalized.includes('스마트') || normalized.includes('smart')) {
      setConfig(prev => ({ ...prev, chunkStrategy: 'smart' }));
      speak('스마트 분할로 설정되었습니다.');
      stopSTT();
      return;
    }
    
    // 저장 명령
    if (normalized.includes('저장') || normalized.includes('save')) {
      handleSave();
      stopSTT();
      return;
    }
    
    onSpeech(transcript);
  }, [transcript, onSpeech, config, speak, stopSTT]);

  return (
    <div className="p-4 space-y-6">
      <h2 className="text-xl font-semibold mb-4">점자 디스플레이 설정</h2>

      {/* 점자 셀 수 설정 */}
      <div className="bg-card border border-border rounded-lg p-4">
        <label className="block text-sm font-medium mb-2">
          점자 셀 수 (현재: {config.maxCells}개)
        </label>
        <input
          type="range"
          min="1"
          max="20"
          value={config.maxCells}
          onChange={(e) => setConfig(prev => ({ ...prev, maxCells: parseInt(e.target.value) }))}
          className="w-full"
          aria-label="점자 셀 수 조절"
        />
        <div className="flex justify-between text-xs text-muted mt-1">
          <span>1</span>
          <span>10</span>
          <span>20</span>
        </div>
        <p className="text-xs text-muted mt-2">
          음성으로 "{config.maxCells + 1}개 셀"이라고 말하면 설정됩니다.
        </p>
      </div>

      {/* 스크롤 모드 설정 */}
      <div className="bg-card border border-border rounded-lg p-4">
        <label className="block text-sm font-medium mb-2">스크롤 모드</label>
        <div className="space-y-2">
          <label className="flex items-center gap-2">
            <input
              type="radio"
              name="scrollMode"
              value="manual"
              checked={config.scrollMode === 'manual'}
              onChange={() => setConfig(prev => ({ ...prev, scrollMode: 'manual' }))}
              aria-label="수동 스크롤"
            />
            <span>수동 (사용자가 "다음" 명령으로 이동)</span>
          </label>
          <label className="flex items-center gap-2">
            <input
              type="radio"
              name="scrollMode"
              value="auto"
              checked={config.scrollMode === 'auto'}
              onChange={() => setConfig(prev => ({ ...prev, scrollMode: 'auto' }))}
              aria-label="자동 스크롤"
            />
            <span>자동 (일정 시간 후 자동 이동)</span>
          </label>
        </div>
      </div>

      {/* 청크 분할 전략 설정 */}
      <div className="bg-card border border-border rounded-lg p-4">
        <label className="block text-sm font-medium mb-2">청크 분할 전략</label>
        <div className="space-y-2">
          <label className="flex items-center gap-2">
            <input
              type="radio"
              name="chunkStrategy"
              value="word"
              checked={config.chunkStrategy === 'word'}
              onChange={() => setConfig(prev => ({ ...prev, chunkStrategy: 'word' }))}
              aria-label="단어 단위"
            />
            <span>단어 단위 (각 단어를 하나의 청크로)</span>
          </label>
          <label className="flex items-center gap-2">
            <input
              type="radio"
              name="chunkStrategy"
              value="sentence"
              checked={config.chunkStrategy === 'sentence'}
              onChange={() => setConfig(prev => ({ ...prev, chunkStrategy: 'sentence' }))}
              aria-label="문장 단위"
            />
            <span>문장 단위 (각 문장을 하나의 청크로)</span>
          </label>
          <label className="flex items-center gap-2">
            <input
              type="radio"
              name="chunkStrategy"
              value="smart"
              checked={config.chunkStrategy === 'smart'}
              onChange={() => setConfig(prev => ({ ...prev, chunkStrategy: 'smart' }))}
              aria-label="스마트 분할"
            />
            <span>스마트 (의미 단위로 분할, 수식/구 등 고려)</span>
          </label>
        </div>
      </div>

      {/* 저장 버튼 */}
      <div className="flex gap-2">
        <button
          onClick={handleSave}
          className="btn-primary flex-1"
          aria-label="설정 저장"
        >
          저장
        </button>
        {onClose && (
          <button
            onClick={onClose}
            className="btn-ghost flex-1"
            aria-label="닫기"
          >
            닫기
          </button>
        )}
      </div>

      {/* 음성 명령 안내 */}
      <div className="bg-accent/10 border border-accent/20 rounded-lg p-4">
        <p className="text-sm font-medium mb-2">음성 명령:</p>
        <ul className="text-xs space-y-1 list-disc list-inside">
          <li>"X개 셀" - 점자 셀 수 변경</li>
          <li>"자동" 또는 "수동" - 스크롤 모드 변경</li>
          <li>"단어", "문장", "스마트" - 청크 분할 전략 변경</li>
          <li>"저장" - 설정 저장</li>
        </ul>
      </div>
    </div>
  );
}

