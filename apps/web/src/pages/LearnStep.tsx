// src/pages/LearnStep.tsx
import { useEffect, useMemo, useState, useRef } from "react";
import { ArrowLeft, SkipForward, RotateCcw } from "lucide-react";
import { brailleAPI } from '@/lib/api/BrailleAPI';
import { learningAPI } from '@/lib/api/LearningAPI';
// import { api } from '@/api';
// import { asStr, asStrArr } from '@/lib/safe';
import { useNavigate, useSearchParams, useLocation } from "react-router-dom";
import type { Cell as CellTuple } from "@/lib/brailleSafe";
import { normalizeCells } from "@/lib/brailleSafe";
import { localToBrailleCells } from "@/lib/braille";
import type { LessonItem } from "@/lib/normalize";
import type { LessonMode } from "@/store/lessonSession";
import { saveLessonSession } from "@/store/lessonSession";
import type { LearnItem } from "@/types/api";
import useTTS from '../hooks/useTTS';
import useSTT from '../hooks/useSTT';
import useVoiceCommands from '../hooks/useVoiceCommands';
import { useVoiceStore } from '../store/voice';
import SpeechBar from '../components/input/SpeechBar';
import AppShellMobile from '../components/ui/AppShellMobile';

import BrailleDot from '../components/braille/BrailleDot';
const Dot = BrailleDot;

// LearnItem을 LessonItem으로 변환
function convertLearnItemToLessonItem(item: LearnItem): LessonItem {
  const cells: CellTuple[] = [];
  
  // cell이 있으면 변환
  if (item.cell && Array.isArray(item.cell) && item.cell.length === 6) {
    cells.push(item.cell.map(v => (v ? 1 : 0)) as CellTuple);
  }
  
  // cells가 있으면 변환
  if (item.cells && Array.isArray(item.cells)) {
    item.cells.forEach(cell => {
      if (Array.isArray(cell) && cell.length === 6) {
        cells.push(cell.map(v => (v ? 1 : 0)) as CellTuple);
      }
    });
  }
  
  return {
    char: item.char,
    word: item.word,
    sentence: item.sentence,
    name: item.name,
    cells: cells.length > 0 ? cells : undefined,
  };
}

function CellView({ c }: { c: CellTuple }) {
  const [a, b, c2, d, e, f] = c || [0, 0, 0, 0, 0, 0];
  return (
    <div className="inline-flex flex-col px-3 py-2 rounded-xl border border-border bg-white shadow-toss hover:shadow-toss-lg transition-shadow">
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

type Item = LessonItem & {
  name?: string;
  tts?: string | string[];
  decomposeTTS?: string[];
  ttsIntro?: string;

  // 점자 데이터(서버가 주는 경우, 튜플 6개 기준)
  cell?: CellTuple;
  cells?: CellTuple[];
  braille?: CellTuple | string | string[]; // 유연성 유지
  brailles?: CellTuple[];

  examples?: string[];
};

export default function LearnStep() {
  const [sp] = useSearchParams();
  const { pathname } = useLocation();
  const navigate = useNavigate();
  const { speak, stop } = useTTS();
  const { start: startSTT, stop: stopSTT, isListening, transcript } = useSTT();

  // 경로(/learn/char|word|sentence) 우선, 없으면 ?mode=, 그래도 없으면 'char'
  const pathTail = pathname.split('/').pop() || '';
  const fromPath = (['char','word','sentence'] as LessonMode[]).includes(pathTail as any)
    ? (pathTail as LessonMode)
    : undefined;

  const mode = (fromPath || (sp.get('mode') as LessonMode) || 'char');

  const [title, setTitle] = useState('');
  const [items, setItems] = useState<Item[]>([]);
  const [idx, setIdx] = useState<number>(-1); // -1이면 아직 시작 전
  const [loading, setLoading] = useState(true);
  const current = useMemo(() => (idx >= 0 && idx < items.length ? items[idx] : null), [idx, items]);

  // 문항별 캐시 (Map)
  const cacheRef = useRef<Record<string, CellTuple[]>>({});

  useEffect(() => {
    let alive = true;
    setLoading(true);
    setIdx(-1);
    (async () => {
      try {
        console.log("[LearnStep] Starting to fetch learn data for mode:", mode);
        const { title, items } = await learningAPI.fetchLearn(mode);
        if (!alive) return;
        
        console.log("[LearnStep] fetched", { title, items });
        if (title) setTitle(title);
        const convertedItems = Array.isArray(items) 
          ? items.map(convertLearnItemToLessonItem)
          : [];
        setItems(convertedItems);
        // ✅ 로드되면 바로 0번 아이템부터 시작
        setIdx(convertedItems.length ? 0 : -1);
        saveLessonSession({ mode, items: convertedItems, createdAt: Date.now() });
      } finally {
        if (alive) setLoading(false);
      }
    })();
    return () => { alive = false; };
  }, [mode]);

  // 문제가 변경될 때마다 음성 재생
  useEffect(() => {
    if (current && idx >= 0) {
      // 이전 음성 중지
      stop();
      
      // 새 문제 음성 재생
      const ttsText = current.tts || current.name || current.char || current.word || current.sentence || '';
      if (ttsText) {
        const timer = setTimeout(() => {
          speak(ttsText);
        }, 300); // 0.3초 후 재생 (음성 중지 후)
        
        return () => clearTimeout(timer);
      }
    }
  }, [current, idx, speak, stop]);

  const heading = current?.word || current?.sentence || current?.char || current?.name || '';
  const key = `${mode}:${heading}`;

  // 비동기 셀 계산 (항목별 캐싱 + 취소)
  const [computed, setComputed] = useState<CellTuple[]>([]);
  useEffect(() => {
    if (!heading) { setComputed([]); return; }

    const cached = cacheRef.current[key];
    if (cached) { setComputed(cached); return; }

    let cancelled = false;
    (async () => {
      try {
        const res = await brailleAPI.convertBraille(heading, 'word');
        const norm = normalizeCells(res.cells);
        if (!cancelled && norm.length) {
          cacheRef.current[key] = norm;
          setComputed(norm);
          return;
        }
      } catch {}

      try {
        const boolCells = localToBrailleCells(heading);
        const toTuple = (b:boolean[]): CellTuple => [b[0]?1:0,b[1]?1:0,b[2]?1:0,b[3]?1:0,b[4]?1:0,b[5]?1:0];
        const norm = boolCells.map((b: any) => toTuple(b));
        if (!cancelled) {
          cacheRef.current[key] = norm;
          setComputed(norm);
        }
      } catch { if (!cancelled) setComputed([]); }
    })();

    return () => { cancelled = true; };
  }, [key]);

  // 최종 cells 선택 (서버 제공 > 캐시/계산)
  const cells: CellTuple[] = useMemo(() => {
    if (!current) return [];
    if (Array.isArray(current.cells) && current.cells.length) return current.cells;
    if (Array.isArray(current.brailles) && current.brailles.length) return current.brailles;
    if (current.cell) return [current.cell];
    return cacheRef.current[key] || computed || [];
  }, [current, computed, key]);

  // 간단 TTS
  const say = (t: string) => {
    try {
      const u = new SpeechSynthesisUtterance(t);
      u.lang = "ko-KR";
      window.speechSynthesis.speak(u);
    } catch {}
  };

  useEffect(() => {
    let t = "";
    if (current?.decomposeTTS && Array.isArray(current.decomposeTTS)) {
      t = current.decomposeTTS.join(" ");
    } else if (current?.ttsIntro) {
      t = current.ttsIntro;
    } else if (Array.isArray(current?.tts)) {
      t = current.tts.join(" ");
    } else if (current?.tts) {
      t = current.tts;
    } else {
      t = heading;
    }
    if (t) say(t);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [idx, heading, current]);

  const onNext = () => {
    // 이전 TTS 중단 (다음으로 넘어갈 때 이전 음성이 겹치지 않도록)
    stop();
    
    if (idx < items.length - 1) {
      // ✅ 함수형 업데이트로 오프바이원 방지
      setIdx((i) => i + 1);
    } else {
      // 마지막 → 퀴즈 자동 이동
      navigate(`/quiz?mode=${mode}`, { replace: true });
    }
  };
  
  const prev = () => {
    // 이전 TTS 중단
    stop();
    setIdx(Math.max(0, idx - 1));
  };
  const repeat = () => {
    let t = "";
    if (current?.decomposeTTS && Array.isArray(current.decomposeTTS)) {
      t = current.decomposeTTS.join(" ");
    } else if (current?.ttsIntro) {
      t = current.ttsIntro;
    } else if (Array.isArray(current?.tts)) {
      t = current.tts.join(" ");
    } else if (current?.tts) {
      t = current.tts;
    } else {
      t = heading;
    }
    if (t) say(t);
  };

  // 뒤로가기 버튼 클릭 시 학습 인덱스로 이동
  const handleBack = () => {
    navigate('/learn');
  };

  // 마지막 명령 실행 시간 추적 (debounce용)
  const lastCommandTimeRef = useRef<number>(0);
  const lastCommandRef = useRef<string>('');
  const MIN_COMMAND_INTERVAL = 800; // 최소 0.8초 간격

  // 음성 명령 처리
  const { onSpeech } = useVoiceCommands({
    home: () => {
      stop();
      navigate('/');
      stopSTT();
    },
    back: () => {
      stopSTT();
      handleBack();
    },
    next: () => {
      const now = Date.now();
      // 같은 명령이 너무 빠르게 연속으로 들어오면 무시
      if (now - lastCommandTimeRef.current < MIN_COMMAND_INTERVAL && lastCommandRef.current === 'next') {
        return;
      }
      lastCommandTimeRef.current = now;
      lastCommandRef.current = 'next';
      onNext();
    },
    prev: () => {
      const now = Date.now();
      if (now - lastCommandTimeRef.current < MIN_COMMAND_INTERVAL && lastCommandRef.current === 'prev') {
        return;
      }
      lastCommandTimeRef.current = now;
      lastCommandRef.current = 'prev';
      prev();
    },
    repeat: () => {
      const now = Date.now();
      if (now - lastCommandTimeRef.current < MIN_COMMAND_INTERVAL && lastCommandRef.current === 'repeat') {
        return;
      }
      lastCommandTimeRef.current = now;
      lastCommandRef.current = 'repeat';
      repeat();
    },
    start: () => {
      if (idx < 0 && items.length > 0) {
        setIdx(0);
      } else {
        repeat();
      }
    },
    stop: () => {
      stop();
      if (isListening) stopSTT();
    },
    pause: () => {
      stop();
    },
  });

  // 음성 명령 처리 (transcript 감지)
  useEffect(() => {
    if (!transcript) return;
    onSpeech(transcript);
    // 처리 후 transcript 초기화 - 이전 페이지의 transcript가 남지 않도록
    useVoiceStore.getState().resetTranscript();
  }, [transcript, onSpeech]);

  // 전역 음성 이벤트 수신 (next/prev/repeat)
  // ref를 사용하여 최신 함수를 참조하도록 보장
  const onNextRef = useRef(onNext);
  const prevRef = useRef(prev);
  const repeatRef = useRef(repeat);
  
  useEffect(() => {
    onNextRef.current = onNext;
    prevRef.current = prev;
    repeatRef.current = repeat;
  }, [onNext, prev, repeat]);

  useEffect(() => {
    const onVoice = (e: Event) => {
      const detail = (e as CustomEvent)?.detail;
      if (!detail?.type) return;
      console.log('[LearnStep] 음성 명령 이벤트 수신:', detail.type);
      
      const now = Date.now();
      // debounce 체크 (중복 처리 방지)
      if (now - lastCommandTimeRef.current < MIN_COMMAND_INTERVAL && lastCommandRef.current === detail.type) {
        console.log(`[LearnStep] ${detail.type} 명령 debounce - 무시`);
        return;
      }
      lastCommandTimeRef.current = now;
      lastCommandRef.current = detail.type;
      
      if (detail.type === 'next') {
        onNextRef.current();
      } else if (detail.type === 'prev') {
        prevRef.current();
      } else if (detail.type === 'repeat') {
        repeatRef.current();
      }
    };
    window.addEventListener('voice:command', onVoice as EventListener);
    return () => window.removeEventListener('voice:command', onVoice as EventListener);
  }, []);

  // 제목과 진행률 표시
  const headerTitle = `${title} (${idx + 1}/${items.length})`;

  if (loading)
    return (
      <AppShellMobile title="로딩 중..." showBackButton onBack={handleBack}>
        <div className="flex items-center justify-center min-h-[400px]">
          <div className="text-center">
            <div className="animate-spin w-8 h-8 border-2 border-primary border-t-transparent rounded-full mx-auto mb-4"></div>
            <div className="text-muted">불러오는 중…</div>
          </div>
        </div>
      </AppShellMobile>
    );

  if (!current)
    return (
      <AppShellMobile title={title || "학습"} showBackButton onBack={handleBack}>
        <div className="flex items-center justify-center min-h-[400px]">
          <div className="text-center">
            <div className="text-muted">학습 항목이 없습니다.</div>
          </div>
        </div>
      </AppShellMobile>
    );

  return (
    <AppShellMobile title={headerTitle} showBackButton onBack={handleBack}>
      <div className="space-y-4 pb-20">
        {/* 음성 명령 표시줄 */}
        <div className="mb-3">
          <SpeechBar isListening={isListening} transcript={transcript} />
        </div>

        {/* 진척도 바 */}
        <div className="bg-white rounded-2xl p-3 shadow-toss">
          <div className="flex justify-between text-sm text-muted mb-1.5">
            <span>진척도</span>
            <span>{Math.round(((idx + 1) / items.length) * 100)}%</span>
          </div>
          <div className="w-full bg-border rounded-full h-2">
            <div
              className="bg-primary h-2 rounded-full transition-all duration-300"
              style={{ width: `${((idx + 1) / items.length) * 100}%` }}
            />
          </div>
        </div>

        {/* 안내 카드 */}
        <div className="bg-white rounded-2xl p-3 shadow-toss">
          <div className="text-sm text-primary font-medium mb-1.5">💡 학습 안내</div>
          <div className="text-base leading-relaxed">
            {current?.decomposeTTS && Array.isArray(current.decomposeTTS)
              ? current.decomposeTTS.join(" ")
              : current?.ttsIntro
              ? current.ttsIntro
              : Array.isArray(current?.tts)
              ? current.tts.join(" ")
              : current?.tts || heading}
          </div>
          {!!current?.examples?.length && (
            <div className="text-sm text-muted mt-2 p-2.5 bg-card rounded-xl">
              <strong>예시:</strong> {current.examples.join(", ")}
            </div>
          )}
        </div>

        {/* 점자 표시 카드 */}
        <div className="bg-white rounded-2xl p-5 text-center shadow-toss">
          <div className="text-3xl font-bold text-fg mb-3">{heading}</div>
          <div className="inline-flex flex-wrap justify-center gap-3">
            {cells.length ? (
              cells.map((c, idx) => <CellView key={idx} c={c} />)
            ) : (
              <div className="text-muted text-sm py-6">
                점자 데이터를 불러오는 중...
              </div>
            )}
          </div>
          {cells.length > 0 && (
            <div className="text-xs text-muted mt-3">{cells.length}개 점자 셀로 구성</div>
          )}
        </div>

        {/* 하단 액션 바 (고정 위치, 네비게이션 바 위) */}
        <div className="fixed bottom-24 left-0 right-0 z-40 bg-white/98 backdrop-blur-xl border-t border-border/60 shadow-lg">
          <div className="w-full md:max-w-md md:mx-auto px-4 py-2">
            <div className="flex items-center justify-between gap-2">
              <button
                onClick={prev}
                disabled={idx === 0}
                className="flex items-center gap-2 px-4 py-2 rounded-xl bg-card text-fg hover:bg-border disabled:opacity-50 disabled:cursor-not-allowed focus:outline-none focus:ring-2 focus:ring-primary transition-all duration-200 active:scale-95 flex-1"
                aria-label="이전 항목"
              >
                <ArrowLeft className="w-4 h-4" />
                <span>이전</span>
              </button>

              <button
                onClick={repeat}
                className="flex items-center gap-2 px-4 py-2 rounded-xl bg-accent text-white hover:bg-accent/90 focus:outline-none focus:ring-2 focus:ring-accent transition-all duration-200 active:scale-95 flex-1"
                aria-label="다시 듣기"
              >
                <RotateCcw className="w-4 h-4" />
                <span>반복</span>
              </button>

              <button
                onClick={onNext}
                className="flex items-center gap-2 px-4 py-2 rounded-xl bg-primary text-white hover:bg-primary/90 focus:outline-none focus:ring-2 focus:ring-primary transition-all duration-200 active:scale-95 flex-1"
                aria-label={idx === items.length - 1 ? "테스트 시작" : "다음 항목"}
              >
                <span>{idx === items.length - 1 ? "테스트" : "다음"}</span>
                <SkipForward className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>
      </div>
    </AppShellMobile>
  );
}
