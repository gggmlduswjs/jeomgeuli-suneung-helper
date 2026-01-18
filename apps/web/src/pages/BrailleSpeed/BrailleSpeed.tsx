import { useEffect, useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import AppShellMobile from '../../components/ui/AppShellMobile';
import SpeechBar from '../../components/input/SpeechBar';
import useTTS from '../../hooks/useTTS';
import useSTT from '../../hooks/useSTT';
import useVoiceCommands from '../../hooks/useVoiceCommands';
import ToastA11y from '../../components/system/ToastA11y';
import { BraillePatternFactory } from '../../lib/braillePattern';
import useBrailleBLE from '../../hooks/useBrailleBLE';
import { analyticsAPI } from '../../lib/api/AnalyticsAPI';

type TrainingStatus = 'idle' | 'playing' | 'paused';

export default function BrailleSpeed() {
  const navigate = useNavigate();
  const { speak, stop: stopTTS } = useTTS();
  const { start: startSTT, stop: stopSTT, isListening, transcript } = useSTT();
  const [showToast, setShowToast] = useState(false);
  const [toastMessage, setToastMessage] = useState('');
  
  const [status, setStatus] = useState<TrainingStatus>('idle');
  const [currentPattern, setCurrentPattern] = useState<number[] | null>(null);
  const [patternSequence, setPatternSequence] = useState<number[][]>([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [speed, setSpeed] = useState(0); // 패턴/분
  const [accuracy, setAccuracy] = useState(100); // 정확도 (%)
  const [startTime, setStartTime] = useState<number | null>(null);
  const [patternCount, setPatternCount] = useState(0);
  
  const { isConnected, writeCells } = useBrailleBLE();
  const intervalRef = useRef<NodeJS.Timeout | null>(null);

  // 페이지 진입 시 자동 음성 안내
  useEffect(() => {
    const welcomeMessage = '점자 속도 훈련 모드입니다. 짧은 패턴을 읽는 속도를 측정합니다.';
    const timer = setTimeout(() => {
      speak(welcomeMessage);
    }, 500);
    return () => clearTimeout(timer);
  }, [speak]);

  // 패턴 시퀀스 생성
  const generatePatternSequence = (count: number = 10) => {
    const patterns: number[][] = [];
    const patternTypes = ['number', 'trend', 'status'] as const;
    
    for (let i = 0; i < count; i++) {
      const type = patternTypes[Math.floor(Math.random() * patternTypes.length)];
      let pattern: number[];
      
      if (type === 'number') {
        const num = (Math.floor(Math.random() * 5) + 1) as 1 | 2 | 3 | 4 | 5;
        pattern = BraillePatternFactory.createNumberPattern(num);
      } else if (type === 'trend') {
        const trends: ('increase' | 'decrease' | 'stable')[] = ['increase', 'decrease', 'stable'];
        const trend = trends[Math.floor(Math.random() * trends.length)];
        pattern = BraillePatternFactory.createTrendPattern(trend);
      } else {
        const statuses: ('start' | 'stop' | 'pause')[] = ['start', 'stop', 'pause'];
        const status = statuses[Math.floor(Math.random() * statuses.length)];
        pattern = BraillePatternFactory.createStatusPattern(status);
      }
      
      patterns.push(pattern);
    }
    
    return patterns;
  };

  const startTraining = () => {
    const sequence = generatePatternSequence(10);
    setPatternSequence(sequence);
    setCurrentIndex(0);
    setPatternCount(0);
    setStartTime(Date.now());
    setStatus('playing');
    setCurrentPattern(sequence[0]);
    
    // 점자 패턴 전송
    if (isConnected) {
      writeCells([sequence[0]]);
    }
    
    speak('훈련을 시작합니다.');
    
    // 다음 패턴으로 자동 이동 (3초마다)
    intervalRef.current = setInterval(() => {
      setCurrentIndex(prev => {
        const next = prev + 1;
        if (next >= sequence.length) {
          stopTraining();
          return prev;
        }
        setCurrentPattern(sequence[next]);
        if (isConnected) {
          writeCells([sequence[next]]);
        }
        setPatternCount(prev => prev + 1);
        return next;
      });
    }, 3000);
  };

  const stopTraining = () => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
    
    if (startTime) {
      const elapsed = (Date.now() - startTime) / 1000; // 초
      const speedPerMinute = patternCount / (elapsed / 60);
      setSpeed(Math.round(speedPerMinute));
      
      // 로깅
      analyticsAPI.logAnalytics('speed', {
        pattern_count: patternCount,
        time_seconds: elapsed,
        speed_per_minute: speedPerMinute,
        accuracy: accuracy,
      });
      
      speak(`훈련이 완료되었습니다. 속도는 분당 ${Math.round(speedPerMinute)}개 패턴입니다.`);
    }
    
    setStatus('idle');
    setCurrentPattern(null);
    setStartTime(null);
  };

  const pauseTraining = () => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
    setStatus('paused');
    speak('훈련을 일시정지했습니다.');
  };

  const resumeTraining = () => {
    setStatus('playing');
    speak('훈련을 재개합니다.');
    
    // 다음 패턴으로 계속
    intervalRef.current = setInterval(() => {
      setCurrentIndex(prev => {
        const next = prev + 1;
        if (next >= patternSequence.length) {
          stopTraining();
          return prev;
        }
        setCurrentPattern(patternSequence[next]);
        if (isConnected) {
          writeCells([patternSequence[next]]);
        }
        setPatternCount(prev => prev + 1);
        return next;
      });
    }, 3000);
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
      const helpText = '점자 속도 훈련 모드입니다. 짧은 패턴을 읽는 속도를 측정합니다. 음성으로 "시작", "정지", "일시정지"를 말할 수 있습니다.';
      speak(helpText);
    },
  });

  useEffect(() => {
    if (!transcript) return;
    
    const normalized = transcript.toLowerCase().trim();
    
    if (normalized.includes('시작') || normalized.includes('시작하기')) {
      stopTTS();
      if (status === 'idle') {
        startTraining();
      } else if (status === 'paused') {
        resumeTraining();
      }
      stopSTT();
      return;
    }
    
    if (normalized.includes('정지') || normalized.includes('멈춰') || normalized.includes('중지')) {
      stopTTS();
      stopTraining();
      stopSTT();
      return;
    }
    
    if (normalized.includes('일시정지') || normalized.includes('일시 정지')) {
      stopTTS();
      if (status === 'playing') {
        pauseTraining();
      }
      stopSTT();
      return;
    }
    
    onSpeech(transcript);
  }, [transcript, onSpeech, status]);

  const showToastMessage = (message: string) => {
    setToastMessage(message);
    setShowToast(true);
  };

  return (
    <AppShellMobile title="점자 속도 훈련" className="relative">
      <div className="mb-4">
        <SpeechBar isListening={isListening} transcript={transcript} />
      </div>

      <div className="p-4">
        <div className="space-y-6">
          <div className="bg-card border border-border rounded-lg p-6 text-center">
            <h3 className="text-lg font-semibold mb-4">현재 상태</h3>
            <p className="text-2xl font-bold mb-2">
              {status === 'idle' && '대기 중'}
              {status === 'playing' && '훈련 중'}
              {status === 'paused' && '일시정지'}
            </p>
            {currentPattern && (
              <div className="mt-4">
                <p className="text-sm text-muted mb-2">현재 패턴</p>
                <div className="text-4xl">
                  {currentPattern.map((dot, i) => (
                    <span key={i}>{dot ? '●' : '○'}</span>
                  ))}
                </div>
              </div>
            )}
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div className="bg-card border border-border rounded-lg p-4 text-center">
              <p className="text-sm text-muted mb-1">속도</p>
              <p className="text-2xl font-bold">{speed} 패턴/분</p>
            </div>
            <div className="bg-card border border-border rounded-lg p-4 text-center">
              <p className="text-sm text-muted mb-1">정확도</p>
              <p className="text-2xl font-bold">{accuracy}%</p>
            </div>
          </div>

          <div className="flex gap-2">
            {status === 'idle' && (
              <button
                onClick={startTraining}
                className="btn-primary flex-1"
                aria-label="훈련 시작"
              >
                시작
              </button>
            )}
            {status === 'playing' && (
              <>
                <button
                  onClick={pauseTraining}
                  className="btn-ghost flex-1"
                  aria-label="일시정지"
                >
                  일시정지
                </button>
                <button
                  onClick={stopTraining}
                  className="btn-error flex-1"
                  aria-label="정지"
                >
                  정지
                </button>
              </>
            )}
            {status === 'paused' && (
              <>
                <button
                  onClick={resumeTraining}
                  className="btn-primary flex-1"
                  aria-label="재개"
                >
                  재개
                </button>
                <button
                  onClick={stopTraining}
                  className="btn-error flex-1"
                  aria-label="정지"
                >
                  정지
                </button>
              </>
            )}
          </div>

          {patternSequence.length > 0 && (
            <div className="bg-card border border-border rounded-lg p-4">
              <p className="text-sm text-muted mb-2">진행 상황</p>
              <p className="text-base">
                {currentIndex + 1} / {patternSequence.length}
              </p>
            </div>
          )}
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
