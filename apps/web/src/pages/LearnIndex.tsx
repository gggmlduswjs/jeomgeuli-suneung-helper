import { useEffect } from "react";
import { useNavigate } from "react-router-dom";
import AppShellMobile from "../components/ui/AppShellMobile";
import SpeechBar from "../components/input/SpeechBar";
import useTTS from "../hooks/useTTS";
import useSTT from "../hooks/useSTT";
import useVoiceCommands from "../hooks/useVoiceCommands";
import { useVoiceStore } from '../store/voice';

export default function LearnIndex() {
  const navigate = useNavigate();
  const { speak, stop: stopTTS } = useTTS();
  const { start: startSTT, stop: stopSTT, isListening, transcript } = useSTT();

  // 페이지 진입 안내 (원치 않으면 이 useEffect 제거해도 됨)
  useEffect(() => {
    speak("점자 학습 메뉴입니다. 자모, 단어, 문장, 자유 변환 중에서 선택하세요.");
  }, [speak]);

  // 뒤로가기 버튼 클릭 시 홈으로 이동
  const handleBack = () => {
    navigate('/');
  };

  const items = [
    { to: "/learn/char", label: "자모 학습", desc: "한글 자음/모음의 점자 패턴", command: "자모" },
    { to: "/learn/word", label: "단어 학습", desc: "자모 조합으로 단어 학습", command: "단어" },
    { to: "/learn/sentence", label: "문장 학습", desc: "문장 단위 점자 연습", command: "문장" },
    { to: "/learn/free", label: "자유 변환", desc: "임의 텍스트 점자 변환", command: "자유변환" },
    { to: "/review", label: "복습하기", desc: "틀린 문제/키워드 복습", highlight: true, command: "복습" },
  ];

  // 음성 명령 처리
  const { onSpeech } = useVoiceCommands({
    home: () => {
      stopTTS();
      navigate('/');
      stopSTT();
    },
    back: handleBack,
    learn: () => {
      // 이미 학습 메뉴에 있음
      speak("이미 점자 학습 메뉴입니다.");
    },
    // 각 항목 선택 (더 유연한 매칭)
    speak: (text: string) => {
      let normalized = text.toLowerCase().trim();
      
      // 오인식 패턴 보정
      const misrecognitionMap: Record<string, string> = {
        "자무": "자모",
        "자모.": "자모",
        "참호": "자모",
        "단어.": "단어",
        "다워": "단어",
        "문장.": "문장",
      };
      
      for (const [wrong, correct] of Object.entries(misrecognitionMap)) {
        if (normalized.includes(wrong)) {
          normalized = normalized.replace(wrong, correct);
        }
      }
      
      // 자모 학습 (매우 관대한 매칭)
      if (/(자모|자음|모음|자무|참호)/.test(normalized) || 
          normalized.startsWith('자') || 
          normalized.includes('자모') || 
          normalized.includes('자음') || 
          normalized.includes('모음') ||
          (normalized.length <= 3 && normalized[0] === '자')) {
        stopTTS();
        navigate('/learn/char');
        stopSTT();
        return;
      }
      // 단어 학습 (매우 관대한 매칭)
      if (/(단어|워드|다워)/.test(normalized) || 
          normalized.startsWith('단') || 
          normalized.includes('단어') ||
          (normalized.length <= 3 && normalized[0] === '단')) {
        stopTTS();
        navigate('/learn/word');
        stopSTT();
        return;
      }
      // 문장 학습 (매우 관대한 매칭)
      if (/(문장|센턴스)/.test(normalized) || 
          normalized.startsWith('문') || 
          normalized.includes('문장') ||
          (normalized.length <= 3 && normalized[0] === '문')) {
        stopTTS();
        navigate('/learn/sentence');
        stopSTT();
        return;
      }
      // 자유 변환 (매우 관대한 매칭)
      if (/(자유\s*변환|자유변환|변환)/.test(normalized) || 
          normalized.includes('변환') || 
          normalized.includes('자유')) {
        stopTTS();
        navigate('/learn/free');
        stopSTT();
        return;
      }
      // 복습하기 (매우 관대한 매칭)
      if (/(복습|리뷰|다시\s*보기)/.test(normalized) || 
          normalized.startsWith('복') || 
          normalized.includes('복습') || 
          normalized.includes('리뷰')) {
        stopTTS();
        navigate('/review');
        stopSTT();
        return;
      }
    },
  });

  // 음성 명령 처리 (transcript 감지)
  useEffect(() => {
    if (!transcript) return;
    onSpeech(transcript);
    // 처리 후 transcript 초기화 - 이전 페이지의 transcript가 남지 않도록
    useVoiceStore.getState().resetTranscript();
  }, [transcript, onSpeech]);

  return (
    <AppShellMobile title="점자 학습" showBackButton onBack={handleBack}>
      <div className="space-y-4 pb-6">
        {/* 음성 명령 표시줄 */}
        <div className="mb-3">
          <SpeechBar isListening={isListening} transcript={transcript} />
        </div>

        <nav
          className="w-full md:max-w-[560px] md:mx-auto space-y-2"
          aria-label="학습 카테고리"
        >
          <h2 className="text-lg font-bold mb-2">점자 학습</h2>

        {items.map(({ to, label, desc, highlight, command }) => (
          <div
            key={to}
            className={[
              "block rounded-2xl bg-white px-5 py-2 border shadow transition-colors",
              highlight ? "border-sky-200 text-sky-700" : "border-border text-fg",
              "pointer-events-none", // 터치 이벤트 차단
            ].join(" ")}
            aria-label={`${label} - ${desc} (음성으로 "${command}"라고 말하세요)`}
            role="button"
            tabIndex={-1}
          >
            <div className="font-semibold text-base">{label}</div>
            <div className="text-sm text-secondary mt-0.5">{desc}</div>
            <div className="text-xs text-muted mt-1.5">💬 "{command}"라고 말하세요</div>
          </div>
        ))}
        </nav>
      </div>
    </AppShellMobile>
  );
}
