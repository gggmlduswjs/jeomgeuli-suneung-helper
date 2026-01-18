import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import AppShellMobile from '../components/ui/AppShellMobile';
import SpeechBar from '../components/input/SpeechBar';
import useTTS from '../hooks/useTTS';
import useSTT from '../hooks/useSTT';
import useVoiceCommands from '../hooks/useVoiceCommands';
import micMode from '../lib/voice/MicMode';
import ToastA11y from '../components/system/ToastA11y';
import ContinueLearningCard from './Home/components/ContinueLearningCard';
import SubjectSelectCard from './Home/components/SubjectSelectCard';
import PDFManagementCard from './Home/components/PDFManagementCard';
import BrailleDeviceCard from './Home/components/BrailleDeviceCard';

export default function Home() {
  const navigate = useNavigate();
  const { speak, stop: stopTTS } = useTTS();
  const { start: startSTT, stop: stopSTT, isListening, transcript } = useSTT();
  const [showToast, setShowToast] = useState(false);
  const [toastMessage, setToastMessage] = useState('');
  
  // 현재 학습 상태 (실제로는 API에서 가져와야 함)
  const [currentLearning, setCurrentLearning] = useState<{
    subject: 'korean' | 'english' | 'math' | null;
    textbook: string;
    progress: { passages: number; questions: number };
  } | null>(null);
  
  // PDF 목록 (실제로는 API에서 가져와야 함)
  const [recentPDFs, setRecentPDFs] = useState<Array<{
    id: number;
    filename: string;
    status: 'pending' | 'analyzing' | 'completed' | 'failed';
    progress: number;
  }>>([]);

  // 페이지 진입 시 자동 음성 안내 (듀얼 UI/UX)
  useEffect(() => {
    const onboardingMessage = currentLearning
      ? `현재 학습 중인 내용: ${currentLearning.textbook}. 지문 ${currentLearning.progress.passages}개, 문항 ${currentLearning.progress.questions}개 완료했습니다. 이어하기, 과목 선택, 교재 관리, 점자 디바이스를 사용할 수 있습니다.`
      : '수능 점자 읽기 훈련 앱입니다. 오늘 학습 이어하기, 과목 선택, 교재 관리, 점자 디바이스 연결을 사용할 수 있습니다.';

    // 페이지 진입 시 즉시 안내 음성 재생
    const timer = setTimeout(() => {
      speak(onboardingMessage);
    }, 500);

    return () => {
      clearTimeout(timer);
    };
  }, [speak, currentLearning]);

  // 음성 명령어 시스템
  const { onSpeech } = useVoiceCommands({
    // 네비게이션
    home: () => {
      showToastMessage('이미 홈 화면입니다.');
      speak('이미 홈 화면입니다.');
    },
    back: () => {
      showToastMessage('홈 화면에서는 뒤로 갈 수 없습니다.');
      speak('홈 화면에서는 뒤로 갈 수 없습니다.');
    },
    
    // 이어하기 명령
    continue: () => {
      if (currentLearning) {
        stopTTS();
        navigate(`/textbook?subject=${currentLearning.subject}`);
        showToastMessage('학습을 이어갑니다.');
        speak('학습을 이어갑니다.');
        stopSTT();
      } else {
        showToastMessage('진행 중인 학습이 없습니다.');
        speak('진행 중인 학습이 없습니다.');
      }
    },
    이어하기: () => {
      if (currentLearning) {
        stopTTS();
        navigate(`/textbook?subject=${currentLearning.subject}`);
        showToastMessage('학습을 이어갑니다.');
        speak('학습을 이어갑니다.');
        stopSTT();
      } else {
        showToastMessage('진행 중인 학습이 없습니다.');
        speak('진행 중인 학습이 없습니다.');
      }
    },
    
    // 과목별 점자 읽기 메뉴 항목
    math: () => {
      stopTTS();
      navigate('/textbook?subject=math&mode=braille-read');
      showToastMessage('수학 점자 읽기 모드로 이동합니다.');
      speak('수학 점자 읽기 모드로 이동합니다.');
      stopSTT();
    },
    수학: () => {
      stopTTS();
      navigate('/textbook?subject=math&mode=braille-read');
      showToastMessage('수학 점자 읽기 모드로 이동합니다.');
      speak('수학 점자 읽기 모드로 이동합니다.');
      stopSTT();
    },
    korean: () => {
      stopTTS();
      navigate('/textbook?subject=korean&mode=braille-read');
      showToastMessage('국어 점자 읽기 모드로 이동합니다.');
      speak('국어 점자 읽기 모드로 이동합니다.');
      stopSTT();
    },
    국어: () => {
      stopTTS();
      navigate('/textbook?subject=korean&mode=braille-read');
      showToastMessage('국어 점자 읽기 모드로 이동합니다.');
      speak('국어 점자 읽기 모드로 이동합니다.');
      stopSTT();
    },
    english: () => {
      stopTTS();
      navigate('/textbook?subject=english&mode=braille-read');
      showToastMessage('영어 점자 읽기 모드로 이동합니다.');
      speak('영어 점자 읽기 모드로 이동합니다.');
      stopSTT();
    },
    영어: () => {
      stopTTS();
      navigate('/textbook?subject=english&mode=braille-read');
      showToastMessage('영어 점자 읽기 모드로 이동합니다.');
      speak('영어 점자 읽기 모드로 이동합니다.');
      stopSTT();
    },
    science: () => {
      stopTTS();
      navigate('/textbook?subject=science&mode=braille-read');
      showToastMessage('과학 점자 읽기 모드로 이동합니다.');
      speak('과학 점자 읽기 모드로 이동합니다.');
      stopSTT();
    },
    social: () => {
      stopTTS();
      navigate('/textbook?subject=social&mode=braille-read');
      showToastMessage('사회 점자 읽기 모드로 이동합니다.');
      speak('사회 점자 읽기 모드로 이동합니다.');
      stopSTT();
    },
    vocab: () => {
      stopTTS();
      navigate('/vocab?mode=braille-read');
      showToastMessage('어휘 점자 읽기 모드로 이동합니다.');
      speak('어휘 점자 읽기 모드로 이동합니다.');
      stopSTT();
    },
    brailleSpeed: () => {
      stopTTS();
      navigate('/braille-speed');
      showToastMessage('점자 속도 훈련 모드로 이동합니다.');
      speak('점자 속도 훈련 모드로 이동합니다.');
      stopSTT();
    },
    
    // 레거시 호환 (기존 명령어도 지원)
    learn: () => {
      stopTTS();
      navigate('/textbook');
      showToastMessage('수능특강 학습 모드로 이동합니다.');
      speak('수능특강 학습 모드로 이동합니다.');
      stopSTT();
    },
    explore: () => {
      stopTTS();
      navigate('/vocab');
      showToastMessage('어휘 시사 학습 모드로 이동합니다.');
      speak('어휘 시사 학습 모드로 이동합니다.');
      stopSTT();
    },
    quiz: () => {
      stopTTS();
      navigate('/question');
      showToastMessage('문항 풀이 모드로 이동합니다.');
      speak('문항 풀이 모드로 이동합니다.');
      stopSTT();
    },
    
    // 도움말
    help: () => {
      stopTTS();
      const helpText = '사용 가능한 음성 명령어: 수학 읽기, 국어 읽기, 영어 읽기, 과학 읽기, 사회 읽기, 어휘 읽기, 속도 훈련, 도움말, 앱소개듣기';
      speak(helpText);
      showToastMessage('도움말을 음성으로 안내합니다.');
    },
    
    // TTS 제어
    speak: (text: string) => {
      stopTTS();
      speak(text);
    },
    mute: () => {
      stopTTS();
      showToastMessage('음성이 비활성화되었습니다.');
    },
    unmute: () => {
      showToastMessage('음성이 활성화되었습니다.');
      speak('음성이 활성화되었습니다.');
    },
  });

  // 음성 명령 처리
  useEffect(() => {
    if (!transcript) return;
    onSpeech(transcript);
  }, [transcript, onSpeech]);

  const showToastMessage = (message: string) => {
    setToastMessage(message);
    setShowToast(true);
  };

  // PDF 업로드 핸들러
  const handlePDFUpload = async (file: File) => {
    try {
      const formData = new FormData();
      formData.append('pdf', file);
      
      // TODO: API 호출
      // const response = await fetch('/api/exam/textbook/upload-pdf/', {
      //   method: 'POST',
      //   body: formData,
      // });
      
      showToastMessage('PDF 업로드가 시작되었습니다.');
      speak('PDF 업로드가 시작되었습니다. 분석이 완료되면 알려드리겠습니다.');
    } catch (error) {
      showToastMessage('PDF 업로드 중 오류가 발생했습니다.');
      speak('PDF 업로드 중 오류가 발생했습니다.');
    }
  };

  // 과목 선택 핸들러
  const handleSubjectSelect = (subject: 'korean' | 'english' | 'math') => {
    stopTTS();
    navigate(`/textbook?subject=${subject}`);
    showToastMessage(`${subject === 'korean' ? '국어' : subject === 'english' ? '영어' : '수학'} 학습을 시작합니다.`);
    speak(`${subject === 'korean' ? '국어' : subject === 'english' ? '영어' : '수학'} 학습을 시작합니다.`);
    stopSTT();
  };

  return (
    <AppShellMobile title="점글이 수능" className="relative">
      {/* 음성 명령 표시줄 */}
      <div className="mb-4">
        <SpeechBar isListening={isListening} transcript={transcript} />
      </div>

      {/* 듀얼 UI/UX 홈 화면 - 4개 핵심 모듈 */}
      <div className="space-y-4 px-4 pb-6">
        {/* 1. 오늘 학습 이어하기 */}
        <ContinueLearningCard
          currentLearning={currentLearning || undefined}
          onContinue={() => {
            if (currentLearning) {
              stopTTS();
              navigate(`/textbook?subject=${currentLearning.subject}`);
              showToastMessage('학습을 이어갑니다.');
              speak('학습을 이어갑니다.');
              stopSTT();
            }
          }}
        />

        {/* 2. 과목 선택 */}
        <SubjectSelectCard onSubjectSelect={handleSubjectSelect} />

        {/* 3. 교재 관리 (PDF 업로드) */}
        <PDFManagementCard
          onUpload={handlePDFUpload}
          recentPDFs={recentPDFs}
        />

        {/* 4. 점자 디바이스 연결 */}
        <BrailleDeviceCard
          onConnect={() => {
            showToastMessage('점자 디바이스가 연결되었습니다.');
            speak('점자 디바이스가 연결되었습니다.');
          }}
          onDisconnect={() => {
            showToastMessage('점자 디바이스 연결이 해제되었습니다.');
            speak('점자 디바이스 연결이 해제되었습니다.');
          }}
        />
      </div>

      {/* 음성 명령 안내 */}
      <div className="mt-6 text-center px-4">
        <p className="text-sm text-muted mb-3">
          음성 명령: "이어하기", "국어 시작", "수학 시작", "영어 시작" 등
        </p>
        <button
          onClick={() =>
            speak(
              '시각장애인 수능 학습 앱, 점글이 수능입니다. 홈 화면에서 오늘 학습 이어하기, 과목 선택, 교재 관리, 점자 디바이스 연결을 사용할 수 있습니다. 음성으로 "이어하기", "국어 시작" 등으로 명령할 수 있습니다.'
            )
          }
          className="text-sm text-primary hover:text-primary/80 underline transition-colors"
          aria-label="앱 소개 음성 안내 듣기"
        >
          🔊 앱 소개 듣기
        </button>
      </div>

      {/* 토스트 알림 */}
      <ToastA11y
        message={toastMessage}
        isVisible={showToast}
        duration={3000}
        onClose={() => setShowToast(false)}
      />
    </AppShellMobile>
  );
}
