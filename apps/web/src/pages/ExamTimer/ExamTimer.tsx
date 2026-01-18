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
import { useExamStore } from '../../store/examStore';

type TimerStatus = 'idle' | 'running' | 'paused' | 'finished';

export default function ExamTimer() {
  const navigate = useNavigate();
  const { speak, stop: stopTTS } = useTTS();
  const { start: startSTT, stop: stopSTT, isListening, transcript } = useSTT();
  const [showToast, setShowToast] = useState(false);
  const [toastMessage, setToastMessage] = useState('');
  
  const [status, setStatus] = useState<TimerStatus>('idle');
  const [allocatedTime, setAllocatedTime] = useState(90); // 분 단위
  const [remainingTime, setRemainingTime] = useState(90 * 60); // 초 단위
  const [subject, setSubject] = useState('국어');
  const [warnings, setWarnings] = useState<number[]>([]); // 경고 시간 (분)
  
  const { isConnected, writeCells } = useBrailleBLE();
  const intervalRef = useRef<NodeJS.Timeout | null>(null);
  const startTimeRef = useRef<number | null>(null);

  // Store
  const { setTimerConfig } = useExamStore();

  // 페이지 진입 시 자동 음성 안내
  useEffect(() => {
    const welcomeMessage = '시험시간 관리 모드입니다. 과목별 시간을 할당하고 타이머를 관리할 수 있습니다.';
    const timer = setTimeout(() => {
      speak(welcomeMessage);
    }, 500);
    return () => clearTimeout(timer);
  }, [speak]);

  // 타이머 실행
  useEffect(() => {
    if (status === 'running') {
      intervalRef.current = setInterval(() => {
        setRemainingTime(prev => {
          if (prev <= 0) {
            stopTimer();
            return 0;
          }
          
          const remainingMinutes = Math.floor(prev / 60);
          
          // 경고 (10분, 5분, 1분)
          if (!warnings.includes(remainingMinutes)) {
            if (remainingMinutes === 10) {
              speak('10분 남았습니다.');
              setWarnings(prev => [...prev, 10]);
            } else if (remainingMinutes === 5) {
              speak('5분 남았습니다.');
              setWarnings(prev => [...prev, 5]);
            } else if (remainingMinutes === 1) {
              speak('1분 남았습니다.');
              setWarnings(prev => [...prev, 1]);
            }
          }
          
          return prev - 1;
        });
      }, 1000);
    } else {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
    }

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, [status, warnings, speak]);

  const startTimer = () => {
    if (remainingTime <= 0) {
      speak('시간이 모두 소진되었습니다.');
      return;
    }
    
    setStatus('running');
    startTimeRef.current = Date.now();
    setWarnings([]);
    
    // 시작 패턴 전송
    if (isConnected) {
      const pattern = BraillePatternFactory.createStatusPattern('start');
      writeCells([pattern]);
    }
    
    speak('타이머를 시작했습니다.');
    
    // 로깅
    analyticsAPI.logAnalytics('timing', {
      exam_type: 'practice',
      subject: subject,
      allocated_time: allocatedTime,
      used_time: 0,
      remaining_time: remainingTime,
    });
  };

  const stopTimer = () => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
    
    const usedTime = startTimeRef.current 
      ? Math.floor((Date.now() - startTimeRef.current) / 1000)
      : 0;
    
    setStatus('finished');
    
    // 정지 패턴 전송
    if (isConnected) {
      const pattern = BraillePatternFactory.createStatusPattern('stop');
      writeCells([pattern]);
    }
    
    speak('타이머가 종료되었습니다.');
    
    // 로깅
    analyticsAPI.logAnalytics('timing', {
      exam_type: 'practice',
      subject: subject,
      allocated_time: allocatedTime,
      used_time: usedTime,
      remaining_time: remainingTime,
    });
  };

  const pauseTimer = () => {
    setStatus('paused');
    
    // 일시정지 패턴 전송
    if (isConnected) {
      const pattern = BraillePatternFactory.createStatusPattern('pause');
      writeCells([pattern]);
    }
    
    speak('타이머를 일시정지했습니다.');
  };

  const resumeTimer = () => {
    setStatus('running');
    speak('타이머를 재개했습니다.');
  };

  const resetTimer = () => {
    setRemainingTime(allocatedTime * 60);
    setStatus('idle');
    setWarnings([]);
    speak('타이머를 초기화했습니다.');
  };

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
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
      const helpText = '시험시간 관리 모드입니다. 과목별 시간을 할당하고 타이머를 시작할 수 있습니다. 음성으로 "시작", "정지", "일시정지"를 말할 수 있습니다.';
      speak(helpText);
    },
  });

  useEffect(() => {
    if (!transcript) return;
    
    const normalized = transcript.toLowerCase().trim();
    
    if (normalized.includes('시작') || normalized.includes('시작하기')) {
      stopTTS();
      if (status === 'idle' || status === 'paused') {
        if (status === 'paused') {
          resumeTimer();
        } else {
          startTimer();
        }
      }
      stopSTT();
      return;
    }
    
    if (normalized.includes('정지') || normalized.includes('멈춰') || normalized.includes('중지')) {
      stopTTS();
      stopTimer();
      stopSTT();
      return;
    }
    
    if (normalized.includes('일시정지') || normalized.includes('일시 정지')) {
      stopTTS();
      if (status === 'running') {
        pauseTimer();
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
    <AppShellMobile title="시험시간 관리" className="relative">
      <div className="mb-4">
        <SpeechBar isListening={isListening} transcript={transcript} />
      </div>

      <div className="p-4">
        <div className="space-y-6">
          {status === 'idle' && (
            <div className="bg-card border border-border rounded-lg p-4 space-y-4">
              <h3 className="text-lg font-semibold mb-4">시간 설정</h3>
              
              <div>
                <label className="block text-sm font-medium mb-2">과목</label>
                <select
                  value={subject}
                  onChange={(e) => setSubject(e.target.value)}
                  className="w-full px-4 py-2 border border-border rounded-lg"
                  aria-label="과목 선택"
                >
                  <option value="국어">국어</option>
                  <option value="수학">수학</option>
                  <option value="영어">영어</option>
                  <option value="한국사">한국사</option>
                  <option value="사회">사회</option>
                  <option value="과학">과학</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium mb-2">할당 시간 (분)</label>
                <input
                  type="number"
                  min="1"
                  max="180"
                  value={allocatedTime}
                  onChange={(e) => {
                    const mins = parseInt(e.target.value) || 90;
                    setAllocatedTime(mins);
                    setRemainingTime(mins * 60);
                  }}
                  className="w-full px-4 py-2 border border-border rounded-lg"
                  aria-label="할당 시간 입력"
                />
              </div>

              <button
                onClick={startTimer}
                className="btn-primary w-full"
                aria-label="타이머 시작"
              >
                시작
              </button>
            </div>
          )}

          {status !== 'idle' && (
            <>
              <div className="bg-card border border-border rounded-lg p-6 text-center">
                <h3 className="text-lg font-semibold mb-2">{subject}</h3>
                <p className="text-4xl font-bold mb-2">
                  {formatTime(remainingTime)}
                </p>
                <p className="text-sm text-muted">
                  할당: {allocatedTime}분
                </p>
              </div>

              <div className="flex gap-2">
                {status === 'running' && (
                  <>
                    <button
                      onClick={pauseTimer}
                      className="btn-ghost flex-1"
                      aria-label="일시정지"
                    >
                      일시정지
                    </button>
                    <button
                      onClick={stopTimer}
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
                      onClick={resumeTimer}
                      className="btn-primary flex-1"
                      aria-label="재개"
                    >
                      재개
                    </button>
                    <button
                      onClick={stopTimer}
                      className="btn-error flex-1"
                      aria-label="정지"
                    >
                      정지
                    </button>
                  </>
                )}
                {status === 'finished' && (
                  <button
                    onClick={resetTimer}
                    className="btn-primary w-full"
                    aria-label="초기화"
                  >
                    초기화
                  </button>
                )}
              </div>
            </>
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
