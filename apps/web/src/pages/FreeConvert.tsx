import { useState, useEffect, useRef } from "react";
import { useNavigate } from "react-router-dom";
import AppShellMobile from "../components/ui/AppShellMobile";
import SpeechBar from "../components/input/SpeechBar";
import ToastA11y from "../components/system/ToastA11y";
import { brailleAPI } from "../lib/api/BrailleAPI";
import { learningAPI } from "../lib/api/LearningAPI";
import { useTTS } from "../hooks/useTTS";
import useSTT from "../hooks/useSTT";
import useVoiceCommands from "../hooks/useVoiceCommands";
import { useVoiceStore } from "../store/voice";
import VoiceService from "../services/VoiceService";
import { normalizeCells } from "@/lib/brailleSafe";
import { maskToGrid6 } from "@/lib/brailleGrid";
import type { Cell } from "@/lib/brailleMap"; // [0|1,0|1,0|1,0|1,0|1,0|1]

// 간단한 유사도 계산 함수 (오인식 보정용)
function calculateSimilarity(s1: string, s2: string): number {
  if (!s1 || !s2) return 0;
  if (s1 === s2) return 1;
  
  const len1 = s1.length;
  const len2 = s2.length;
  if (len1 === 0 || len2 === 0) return 0;
  
  // 첫 글자 일치
  if (s1[0] === s2[0] && len1 <= 3 && len2 <= 3) return 0.6;
  
  // 간단한 편집 거리 (최대 1글자 차이)
  if (Math.abs(len1 - len2) <= 1) {
    let diff = 0;
    const minLen = Math.min(len1, len2);
    for (let i = 0; i < minLen; i++) {
      if (s1[i] !== s2[i]) diff++;
    }
    if (diff <= 1) return 0.7;
  }
  
  // 부분 포함
  if (s1.includes(s2) || s2.includes(s1)) return 0.5;
  
  return 0;
}

function Dot({ on }: { on: boolean }) {
  return (
    <span
      className={`inline-block w-5 h-5 rounded-full mx-0.5 my-0.5 border-2 transition-all duration-200 ${
        on ? "bg-blue-600 border-blue-600 shadow-md" : "bg-gray-100 border-gray-300"
      }`}
    />
  );
}

function CellView({ c }: { c: Cell }) {
  const [a, b, c2, d, e, f] = c || [0, 0, 0, 0, 0, 0];
  return (
    <div className="inline-flex flex-col px-3 py-2 rounded-lg border-2 bg-white shadow-sm hover:shadow-md transition-shadow">
      <div className="flex">
        <Dot on={!!a} />
        <Dot on={!!d} />
      </div>
      <div className="flex">
        <Dot on={!!b} />
        <Dot on={!!e} />
      </div>
      <div className="flex">
        <Dot on={!!c2} />
        <Dot on={!!f} />
      </div>
    </div>
  );
}

type Conversion = {
  original: string;
  cells: Cell[];
  bins?: number[]; // 서버가 bins를 주면 이걸로 격자 재계산
  // 서버가 단어/토큰별 세그먼트를 주면 여기에 담아 표시 (옵션)
  segments?: Array<{ original: string; cells: Cell[] }>;
};

export default function FreeConvert() {
  const navigate = useNavigate();
  const { speak, stop: stopTTS } = useTTS();
  const { start: startSTT, stop: stopSTT, isListening, transcript } = useSTT();
  const alternatives = useVoiceStore(state => state.alternatives);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const lastTextRef = useRef<string>('');
  const lastTimeRef = useRef<number>(0);
  const [inputText, setInputText] = useState("");
  const [conversion, setConversion] = useState<Conversion | null>(null);
  const [isConverting, setIsConverting] = useState(false);
  const [isEnqueuing, setIsEnqueuing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [lastCommand, setLastCommand] = useState<string>('');
  const [showToast, setShowToast] = useState(false);
  const [toastMessage, setToastMessage] = useState('');
  const lastConvertedTextRef = useRef<string>(''); // 마지막 변환한 텍스트 추적
  const isConvertingRef = useRef<boolean>(false); // 변환 중 플래그

  // 페이지 진입 시 정답 목록 비우기 (자유변환 모드는 임의 텍스트 입력이므로 제어어 등록 불필요)
  useEffect(() => {
    VoiceService.setAnswerList([]);
    console.log('[FreeConvert] 정답 목록 비움 (자유변환 모드는 제어어 등록 불필요)');
  }, []);

  // 페이지 진입 시 자동 음성 안내
  useEffect(() => {
    const welcomeMessage = '자유 변환 모드입니다. 원하는 텍스트를 입력하면 점자로 변환됩니다.';
    
    const timer = setTimeout(() => {
      speak(welcomeMessage);
    }, 500);

    return () => {
      clearTimeout(timer);
    };
  }, [speak]);

  // 뒤로가기 버튼 클릭 시 홈으로 이동
  const handleBack = () => {
    VoiceService.setAnswerList([]); // 정답 목록 비우기
    navigate('/');
  };

  const handleConvert = async () => {
    const text = inputText.trim();
    if (!text) {
      setError("변환할 텍스트를 입력하세요.");
      return;
    }

    // 이미 변환 중이거나 같은 텍스트를 이미 변환했으면 무시
    if (isConvertingRef.current) {
      console.log('[FreeConvert] 이미 변환 중 - 무시');
      return;
    }
    
    if (text === lastConvertedTextRef.current && conversion?.original === text) {
      console.log('[FreeConvert] 이미 변환된 텍스트 - 무시:', text);
      return;
    }

    try {
      isConvertingRef.current = true;
      setIsConverting(true);
      setError(null);

      // 백엔드 점자 변환 API 사용
      const res = await brailleAPI.convertBraille(text);
      console.log('[FreeConvert] API response:', res);
      const raw = (res as any)?.cells ?? res;
      console.log('[FreeConvert] Raw cells:', raw);
      const cells = normalizeCells(raw) as unknown as Cell[];
      console.log('[FreeConvert] Normalized cells:', cells);
      const bins = (res as any)?.bins;

      const next: Conversion = {
        original: text,
        cells,
        bins, // 서버가 bins를 주면 이걸로 격자 재계산
        // 서버가 세그먼트를 응답한다면 아래처럼 파싱해서 넣으세요.
        // segments: (res as any)?.segments?.map((s: any) => ({
        //   original: s.original,
        //   cells: normalizeCells(s.cells) as unknown as Cell[],
        // })),
      };

      setConversion(next);
      lastConvertedTextRef.current = text; // 마지막 변환한 텍스트 저장
      speak(`변환 완료. ${text}의 점자 변환이 완료되었습니다.`);
    } catch (e: any) {
      console.error("[FreeConvert] Conversion error:", e);
      setError(e?.message || "점자 변환 중 오류가 발생했습니다.");
      setConversion(null);
    } finally {
      setIsConverting(false);
      isConvertingRef.current = false;
    }
  };

  const handleEnqueueForReview = async () => {
    if (!conversion) return;
    try {
      setIsEnqueuing(true);
      setError(null);

      // 백엔드에 복습 항목 저장
      const payload = {
        type: "braille",
        content: conversion.original,
        text: conversion.original,
        word: conversion.original,
        cells: conversion.cells,
        bins: conversion.bins,
        segments: conversion.segments,
      };

      const result = await learningAPI.saveReview("keyword", payload);
      
      if (result) {
        // 성공 시 팝업 표시
        const successMessage = `"${conversion.original}"이(가) 복습 목록에 추가되었습니다.`;
        setToastMessage(successMessage);
        setShowToast(true);
        speak(successMessage);
      } else {
        throw new Error("복습 목록 추가 실패");
      }
    } catch (e: any) {
      console.error("Enqueue error:", e);
      const errorMessage = e?.message || "복습 목록 추가 중 오류가 발생했습니다.";
      setError(errorMessage);
      speak(errorMessage);
      setToastMessage(errorMessage);
      setShowToast(true);
    } finally {
      setIsEnqueuing(false);
    }
  };

  const handleRepeat = () => {
    if (!conversion) return;
    // 점자 패턴 자체를 읽는 대신 결과 안내만 자연어로 읽어줍니다.
    speak(`변환 결과. ${conversion.original}의 점자 셀 ${conversion.cells.length}개가 생성되었습니다.`);
  };

  // 음성 명령 처리
  const { onSpeech } = useVoiceCommands({
    home: () => {
      stopTTS();
      VoiceService.setAnswerList([]); // 정답 목록 비우기
      navigate('/');
      stopSTT();
    },
    back: () => {
      stopSTT();
      VoiceService.setAnswerList([]); // 정답 목록 비우기
      handleBack();
    },
    clear: () => {
      setInputText("");
      setError(null);
      setConversion(null);
      speak("입력 내용이 지워졌습니다.");
    },
    submit: () => {
      if (inputText.trim()) {
        handleConvert();
      } else {
        speak("변환할 텍스트를 입력하거나 말해주세요.");
      }
    },
    repeat: () => {
      if (conversion) {
        handleRepeat();
      } else if (inputText.trim()) {
        handleConvert();
      } else {
        speak("변환할 텍스트를 입력하거나 말해주세요.");
      }
    },
  });

  // 전역 Global STT에서 오는 문장을 입력란에 누적 (명령 우선 처리, 1.5s 중복 방지)
  useEffect(() => {
    const onVoiceTranscript = (e: Event) => {
      const detail = (e as CustomEvent)?.detail as { text?: string } | undefined;
      const text = detail?.text?.trim();
      if (!text) return;

      // 1) 명령 우선 처리
      const handled = onSpeech(text);
      if (handled) return;

      // 2) 1.5초 내 동일 문장 차단
      const now = Date.now();
      if (text === lastTextRef.current && now - lastTimeRef.current < 1500) return;
      
      // 3) alternatives가 있으면 confidence가 높은 것을 우선 사용 (오인식 개선)
      let finalText = text;
      const currentAlternatives = useVoiceStore.getState().alternatives;
      if (currentAlternatives && currentAlternatives.length > 0) {
        // confidence가 0.75 이상인 대안이 있고, 원본과 다르면 사용
        const highConfidenceAlt = currentAlternatives.find(alt => 
          alt.confidence >= 0.75 && alt.transcript !== text
        );
        if (highConfidenceAlt) {
          console.log(`[FreeConvert] 오인식 보정: "${text}" → "${highConfidenceAlt.transcript}" (confidence: ${highConfidenceAlt.confidence.toFixed(2)})`);
          finalText = highConfidenceAlt.transcript;
        } else {
          // confidence가 가장 높은 대안 사용 (원본보다 높은 경우만)
          const bestAlt = currentAlternatives[0]; // 이미 confidence 순으로 정렬됨
          if (bestAlt && bestAlt.confidence > 0.6 && bestAlt.transcript !== text) {
            // 원본과 유사도가 낮고 confidence가 높으면 사용
            const similarity = calculateSimilarity(text, bestAlt.transcript);
            if (similarity < 0.7 && bestAlt.confidence > 0.7) {
              console.log(`[FreeConvert] 오인식 보정 (유사도 낮음): "${text}" → "${bestAlt.transcript}" (confidence: ${bestAlt.confidence.toFixed(2)}, similarity: ${similarity.toFixed(2)})`);
              finalText = bestAlt.transcript;
            }
          }
        }
      }
      
      lastTextRef.current = finalText;
      lastTimeRef.current = now;

      // 4) 입력 누적
      setInputText(prev => (prev && prev.trim() ? prev + ' ' + finalText : finalText));
    };
    window.addEventListener('voice:transcript', onVoiceTranscript as EventListener);
    return () => window.removeEventListener('voice:transcript', onVoiceTranscript as EventListener);
  }, [onSpeech]);

  // 자동 변환 디바운스 타이머
  const autoTimer = useRef<number | undefined>(undefined);
  useEffect(() => {
    if (!inputText || !inputText.trim()) return;
    
    // 이미 변환 중이면 무시
    if (isConvertingRef.current) return;
    
    // 같은 텍스트를 이미 변환했으면 무시
    const trimmedText = inputText.trim();
    if (trimmedText === lastConvertedTextRef.current && conversion?.original === trimmedText) {
      return;
    }
    
    window.clearTimeout(autoTimer.current);
    autoTimer.current = window.setTimeout(() => {
      setError(null);
      // 에코 방지: 듣는 중이면 잠시 중단
      if (isListening) {
        try { stopSTT(); } catch {}
      }
      handleConvert();
    }, 600);
    return () => window.clearTimeout(autoTimer.current);
  }, [inputText, isListening, stopSTT, conversion]);

  return (
    <AppShellMobile title="자유 변환" showBackButton onBack={handleBack}>
      <div className="space-y-4 pb-6">
        {/* 음성 명령 표시줄 */}
        <div className="mb-3">
          <SpeechBar isListening={isListening} transcript={transcript} />
        </div>

        {/* 입력 영역 */}
        <div className="card">
          <div className="mb-3">
            <label className="block text-sm font-semibold text-gray-700 mb-1.5">변환할 텍스트</label>
            <textarea
              ref={inputRef}
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              className="w-full p-2.5 border rounded-xl resize-none"
              rows={3}
              placeholder="한글 텍스트를 입력하거나 음성으로 말하세요"
            />
            {/* 전역 롱프레스/탭으로 STT 제어 (마이크 버튼 제거) */}
          </div>

          <button onClick={handleConvert} disabled={isConverting || !inputText.trim()} className="btn-primary w-full">
            {isConverting ? "변환 중..." : "점자로 변환"}
          </button>
        </div>

        {/* 오류 표시 */}
        {error && (
          <div className="card bg-red-50 border-red-200">
            <div className="text-red-600">{error}</div>
          </div>
        )}

        {/* 변환 결과 */}
        {conversion && conversion.original && (
          <div className="space-y-3">
            {/* 전체 결과 */}
            <div className="card">
              <div className="text-sm font-semibold text-gray-700 mb-2">전체 변환 결과</div>
              <div className="space-y-2">
                <div className="text-center">
                  <div className="text-2xl font-bold text-gray-800 mb-1.5">{conversion.original}</div>

                  {/* 간단 텍스트 비주얼 (●/○) */}
                  <div className="text-3xl font-mono text-blue-600 mb-2">
                    {conversion.cells
                      .map((cell) => cell.map((d) => (d ? "●" : "○")).join(""))
                      .join(" ")}
                  </div>

                  {/* 6점 점자 셀 UI - bins 우선 사용 */}
                  <div className="flex flex-wrap justify-center gap-1">
                    {(conversion.bins || []).length > 0 ? (
                      // 서버 응답 { bins: number[] } 사용 권장 (없으면 클라 계산)
                      conversion.bins?.map((mask: any, idx: number) => {
                        const grid = maskToGrid6(mask as any);
                        return (
                          <div className="inline-flex flex-col px-3 py-2 rounded-lg border-2 bg-white shadow-sm hover:shadow-md transition-shadow" key={idx}>
                            {grid.map((row, rowIdx) => (
                              <div className="flex" key={rowIdx}>
                                {row.map((on, colIdx) => (
                                  <Dot key={colIdx} on={on} />
                                ))}
                              </div>
                            ))}
                          </div>
                        );
                      })
                    ) : (
                      // 폴백: 기존 cells 사용
                      conversion.cells.map((cell, idx) => (
                        <CellView key={idx} c={cell} />
                      ))
                    )}
                  </div>
                </div>
              </div>
            </div>

            {/* 세그먼트별 결과(옵션) */}
            {!!conversion.segments?.length && (
              <div className="card">
                <div className="text-sm font-semibold text-gray-700 mb-2">단어별 변환</div>
                <div className="space-y-3">
                  {conversion.segments.map((segment, index) => (
                    <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                      <div className="flex-1">
                        <div className="text-lg font-semibold text-gray-800">{segment.original}</div>
                        <div className="text-sm text-gray-500">클릭하여 듣기</div>
                      </div>
                      <button
                        onClick={() => speak(`${segment.original} 변환 결과가 준비되었습니다.`)}
                        className="flex items-center gap-2 bg-white hover:bg-gray-100 px-3 py-1.5 rounded-lg border transition-colors"
                      >
                        <div className="flex gap-1">
                          {segment.cells.map((cell, idx) => (
                            <CellView key={idx} c={cell} />
                          ))}
                        </div>
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* 액션 버튼들 */}
            <div className="grid grid-cols-2 gap-3">
              <button onClick={handleRepeat} className="btn-dark">
                다시 듣기
              </button>

              <button onClick={handleEnqueueForReview} disabled={isEnqueuing} className="btn-primary">
                {isEnqueuing ? "추가 중..." : "복습하기"}
              </button>
            </div>
          </div>
        )}
      </div>

      {/* 토스트 알림 */}
      <ToastA11y
        message={toastMessage}
        isVisible={showToast}
        duration={3000}
        onClose={() => setShowToast(false)}
        position="top"
      />
    </AppShellMobile>
  );
}
