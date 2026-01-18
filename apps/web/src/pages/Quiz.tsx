import { useEffect, useMemo, useRef, useState } from "react";
import { useNavigate, useSearchParams, useLocation } from "react-router-dom";
import { ArrowLeft, RotateCcw } from "lucide-react";
import type { LessonItem } from "@/lib/normalize";
import type { LessonMode } from "@/store/lessonSession";
import { loadLessonSession, saveLessonSession } from "@/store/lessonSession";
import { brailleAPI } from "@/lib/api/BrailleAPI";
import { learningAPI } from "@/lib/api/LearningAPI";
import { normalizeCells, type Cell } from "@/lib/brailleSafe";
import { localToBrailleCells } from "@/lib/braille";
import type { LearnItem } from "@/types/api";
import useTTS from '../hooks/useTTS';
import useSTT from '../hooks/useSTT';
import useVoiceCommands from '../hooks/useVoiceCommands';
import VoiceService from '../services/VoiceService';
import { useVoiceStore } from '../store/voice';
import BrailleDot from '../components/braille/BrailleDot';

// LearnItem을 LessonItem으로 변환
function convertLearnItemToLessonItem(item: LearnItem): LessonItem {
  const cells: Cell[] = [];
  
  // cell이 있으면 변환
  if (item.cell && Array.isArray(item.cell) && item.cell.length === 6) {
    cells.push(item.cell.map(v => (v ? 1 : 0)) as Cell);
  }
  
  // cells가 있으면 변환
  if (item.cells && Array.isArray(item.cells)) {
    item.cells.forEach(cell => {
      if (Array.isArray(cell) && cell.length === 6) {
        cells.push(cell.map(v => (v ? 1 : 0)) as Cell);
      }
    });
  }
  
  return {
    char: item.char,
    word: item.word,
    sentence: item.sentence,
    name: item.name,
    cells: cells.length > 0 ? cells : undefined,
  } as LessonItem;
}

// 🧩 유틸: 어떤 형태로 와도 6튜플로 변환
function toTuple(x: any): Cell {
  // [1,0,0,0,0,0]
  if (Array.isArray(x) && x.length === 6) return x.map(v => (v ? 1 : 0)) as Cell;
  // {a,b,c,d,e,f}
  if (x && typeof x === "object" && "a" in x) {
    const { a,b,c,d,e,f } = x as any;
    return [a?1:0,b?1:0,c?1:0,d?1:0,e?1:0,f?1:0] as Cell;
  }
  // 비트마스크 0..63
  if (typeof x === "number") {
    const d = (n:number)=> ((x>>(n-1))&1) ? 1 : 0;
    return [d(1),d(2),d(3),d(4),d(5),d(6)] as Cell;
  }
  return [0,0,0,0,0,0] as Cell;
}
function cellsFromItem(it: any): Cell[] {
  // 단일 셀: [1,0,0,0,0,0] 형태
  if (it?.cell) {
    if (Array.isArray(it.cell) && it.cell.length === 6) {
      return [it.cell.map((v: any) => (v ? 1 : 0)) as Cell];
    }
    return [toTuple(it.cell)];
  }
  // 배열 셀들
  if (Array.isArray(it?.cells) && it.cells.length) {
    return it.cells.map(toTuple);
  }
  if (Array.isArray(it?.brailles) && it.brailles.length) {
    return it.brailles.map(toTuple);
  }
  return [];
}

/* ─ UI helpers (LearnStep과 동일 톤) ─ */
const Dot = BrailleDot;
function CellView({ c }: { c: Cell }) {
  const [a, b, c2, d, e, f] = c || [0, 0, 0, 0, 0, 0];
  return (
    <div className="inline-flex flex-col px-3 py-2 rounded-xl border border-border bg-white shadow-toss">
      <div className="flex"><Dot on={!!a} /><Dot on={!!d} /></div>
      <div className="flex"><Dot on={!!b} /><Dot on={!!e} /></div>
      <div className="flex"><Dot on={!!c2}/><Dot on={!!f} /></div>
    </div>
  );
}

/* 정답/문제 텍스트 계산 규칙
   - 문제(점자 셀)는 글자 자체를 사용: char > word > sentence > text
   - 정답은 명칭/발음 우선: name > word > sentence > text > char
*/
const promptText = (it: LessonItem) =>
  it.char ?? it.word ?? it.sentence ?? (it as any).text ?? "";
const answerText = (it: LessonItem) =>
  (it as any).name ?? it.word ?? it.sentence ?? (it as any).text ?? it.char ?? "";

// 🧠 퀴즈 정답용 오인식 패턴 사전 (필요하면 점점 추가)
const ANSWER_MISREC_MAP: Record<string, string> = {
  // 자모 이름 발음 흔한 오인식
  "디긋": "디귿",
  "티긋": "티읕",
  "시옷": "시옷", // 그대로지만 나중에 변형 패턴 추가 가능
  "삼 오": "자모", // 필요시 추가
  // 추가 오인식 패턴은 실제 사용 중 발견되는 대로 여기에 추가
};

// 간단한 정규화: 소문자 + 공백/기호 제거
function normalizeAnswerText(raw: string): string {
  return String(raw ?? "")
    .toLowerCase()
    .replace(/[~!@#$%^&*()_+=[\]{};:"/\\|<>""''，､、。．·ㆍ…]/g, " ")
    .replace(/\s+/g, "")
    .trim();
}

// 오인식 보정 적용
function canonicalizeAnswer(raw: string): string {
  let t = normalizeAnswerText(raw);

  // 직접 매핑 확인
  if (ANSWER_MISREC_MAP[t]) {
    return ANSWER_MISREC_MAP[t];
  }

  // 부분 매칭 (텍스트에 오인식 패턴이 포함된 경우)
  for (const [wrong, correct] of Object.entries(ANSWER_MISREC_MAP)) {
    const wrongNormalized = normalizeAnswerText(wrong);
    if (t.includes(wrongNormalized)) {
      t = t.replace(wrongNormalized, normalizeAnswerText(correct));
    }
  }

  return t;
}

// (선택) 아주 단순 유사도: 거의 비슷하면 OK 처리
function simpleSimilarity(a: string, b: string): number {
  if (!a || !b) return 0;
  if (a === b) return 1;
  
  // 글자 하나만 다른 경우 (같은 길이)
  if (a.length === b.length) {
    let diff = 0;
    for (let i = 0; i < a.length; i++) {
      if (a[i] !== b[i]) diff++;
    }
    if (diff === 1) return 0.8; // 한 글자만 다르면 80% 유사도
  }
  
  // 부분 포함
  if (a.includes(b) || b.includes(a)) return 0.7;
  
  return 0;
}

// 🎯 STT 결과와 정답을 유연하게 매칭하는 함수
function isAnswerMatch(userInput: string, correctAnswer: string, item: LessonItem): boolean {
  // 오인식 보정 적용
  const userNorm = canonicalizeAnswer(userInput);
  const correctNorm = canonicalizeAnswer(correctAnswer);

  if (!userNorm || !correctNorm) return false;

  // 1) 완전 일치
  if (userNorm === correctNorm) return true;

  // 2) 자모 특별 처리: "기역" ↔ "ㄱ" 양방향 매칭
  const char = item.char?.trim();
  const name = (item as any).name?.trim();
  
  if (char && name) {
    const charNorm = canonicalizeAnswer(char);
    const nameNorm = canonicalizeAnswer(name);
    
    // "기역"이라고 말했는데 STT가 "ㄱ"으로 인식한 경우
    if ((userNorm === charNorm && correctNorm === nameNorm) ||
        // "ㄱ"이라고 말했는데 STT가 "기역"으로 인식한 경우  
        (userNorm === nameNorm && correctNorm === charNorm)) {
      return true;
    }
  }
  
  // 3) 부분 매칭 (예: "기역"에서 "기"만 인식된 경우)
  if (correctNorm.includes(userNorm) || userNorm.includes(correctNorm)) {
    return true;
  }
  
  // 4) 유사도 기반 (거의 비슷하면 정답 처리)
  if (simpleSimilarity(userNorm, correctNorm) >= 0.75) {
    return true;
  }
  
  return false;
}

export default function Quiz() {
  const nav = useNavigate();
  const [sp] = useSearchParams();
  const { pathname } = useLocation();
  const { speak, stop } = useTTS();
  
  // 경로에서 mode 추출 (직접 진입 대비)
  const pathTail = pathname.split('/').pop() || '';
  const fromPath = (['char','word','sentence'] as LessonMode[]).includes(pathTail as any)
    ? (pathTail as LessonMode) : undefined;

  const mode = (fromPath || (sp.get("mode") as LessonMode) || (loadLessonSession()?.mode) || "char");

  const [pool, setPool] = useState<LessonItem[]>([]);
  const [i, setI] = useState(0);
  const [loading, setLoading] = useState(true);

  const [cells, setCells] = useState<Cell[]>([]);     // 문제로 보여줄 점자 셀
  const [user, setUser] = useState("");               // 사용자가 말하거나 입력한 값
  const [result, setResult] = useState<null | { ok: boolean; answer: string }>(null);

  // STT
  // STT - VoiceService 사용
  const transcript = useVoiceStore(state => state.transcript);
  const inputRef = useRef<HTMLInputElement>(null);

  // 페이지 진입 시 이전 transcript 초기화 (이전 데이터가 자동 처리되지 않도록)
  useEffect(() => {
    useVoiceStore.getState().resetTranscript();
  }, []); // 페이지 로드 시 한 번만 실행

  // 페이지 진입 시 자동 음성 안내
  useEffect(() => {
    const modeNames = {
      'char': '자모',
      'word': '단어', 
      'sentence': '문장'
    };
    const modeName = modeNames[mode as keyof typeof modeNames] || mode;
    const welcomeMessage = `${modeName} 퀴즈 모드입니다. 점자 패턴을 보고 정답을 말해보세요.`;
    
    const timer = setTimeout(() => {
      speak(welcomeMessage);
    }, 500);

    return () => {
      clearTimeout(timer);
    };
  }, [speak, mode]);

  // 데이터 로딩: 세션 → 없으면 재요청
  useEffect(() => {
    let alive = true;
    (async () => {
      const sess = loadLessonSession();
      if (sess?.items?.length) {
        setPool(sess.items);
        setLoading(false);
        return;
      }
      try {
        const { items } = await learningAPI.fetchLearn(mode);
        if (!alive) return;
        const convertedItems = Array.isArray(items)
          ? items.map(convertLearnItemToLessonItem)
          : [];
        setPool(convertedItems);
        saveLessonSession({ mode, items: convertedItems, createdAt: Date.now() });
      } finally {
        if (alive) setLoading(false);
      }
    })();
    return () => { alive = false; };
  }, [mode]);

  const cur = useMemo(() => (i < pool.length ? pool[i] : null), [i, pool]);

  // 현재 문제의 정답과 풀의 모든 정답을 VoiceService에 등록
  useEffect(() => {
    if (!pool.length) return;
    
    // 풀의 모든 정답 추출
    const allAnswers = pool.map(item => {
      const answer = answerText(item).trim();
      return answer;
    }).filter(Boolean);
    
    // 현재 문제의 정답 우선 등록
    const currentAnswer = cur ? answerText(cur).trim() : '';
    const answerList = currentAnswer 
      ? [currentAnswer, ...allAnswers.filter(a => a !== currentAnswer)]
      : allAnswers;
    
    // VoiceService에 정답 목록 전달
    if (answerList.length > 0) {
      VoiceService.setAnswerList(answerList);
      console.log('[Quiz] 정답 목록 등록:', answerList.length, '개');
    }
  }, [pool, cur, i]);

  // 문제가 변경될 때마다 음성 재생
  useEffect(() => {
    if (cur && i >= 0) {
      // 이전 음성 중지
      stop();
      
      // 새 문제 음성 재생
      const answerText = (cur as any).name || cur.word || cur.sentence || cur.char || '';
      if (answerText) {
        const timer = setTimeout(() => {
          speak(answerText);
        }, 300); // 0.3초 후 재생 (음성 중지 후)
        
        return () => clearTimeout(timer);
      }
    }
  }, [cur, i, speak, stop]);

  // ✅ 문제 셀 계산: 아이템 데이터 ➜ (없으면) 변환 API ➜ (없으면) 로컬 폴백
  useEffect(() => {
    let cancelled = false;
    (async () => {
      if (!cur) { setCells([]); return; }

      console.log('[Quiz] Current item:', cur);
      console.log('[Quiz] Item cell:', (cur as any).cell);
      console.log('[Quiz] Item cells:', cur.cells);
      console.log('[Quiz] Item brailles:', cur.brailles);

      // 0) 데이터에 이미 셀이 있으면 그걸로 끝
      const fromData = cellsFromItem(cur);
      console.log('[Quiz] Extracted cells from data:', fromData);
      if (fromData.length) { setCells(fromData); return; }

      // 1) 서버 변환 (404면 건너뜀)
      try {
        const res = await brailleAPI.convertBraille(promptText(cur), mode);
        const norm = normalizeCells(res?.cells ?? []);
        if (!cancelled && norm.length) { setCells(norm.map(toTuple)); return; }
      } catch { /* ignore */ }

      // 2) 로컬 폴백 (한글 미지원이면 빈 배열이 올 수 있음)
      try {
        const bools = localToBrailleCells(promptText(cur)); // boolean[][]
        const tuples = bools.map(b => toTuple(b));
        if (!cancelled) setCells(tuples);
      } catch { if (!cancelled) setCells([]); }
    })();
    return () => { cancelled = true; };
  }, [cur, mode]);

  // STT는 useSTT 훅에서 가져옴
  const { start: startSTT, stop: stopSTT, isListening } = useSTT();

  // TTS는 useTTS 훅에서 가져옴
  const speakPrompt = () => {
    // "점자 문제입니다. 정답을 말하세요." 정도의 안내
    speak("점자 문제입니다. 정답을 말하거나 입력하세요.");
  };

  // 음성 명령 처리 - 네비게이션만 처리 (정답은 transcript로 처리)
  const { onSpeech } = useVoiceCommands({
    home: () => {
      VoiceService.stopSTT();
      nav('/');
    },
    back: () => {
      VoiceService.stopSTT();
      nav('/learn');
    },
    repeat: () => {
      speakPrompt();
    },
    stop: () => {
      if (isListening) stopSTT();
    },
    // submit, clear, next는 제거 - 정답으로 처리되도록
  });

  // 마지막 처리된 transcript 추적 (중복 방지)
  const lastProcessedTranscriptRef = useRef<string>('');
  const lastProcessedTimeRef = useRef<number>(0);
  const isProcessingRef = useRef<boolean>(false); // 처리 중 플래그

  // STT 결과 처리 - 명령 우선, 아니면 정답으로 처리
  useEffect(() => {
    if (!transcript) return;
    
    // GlobalVoiceRecognition이 마이크를 켤 때만 transcript가 생성되므로,
    // isListening 체크 없이 바로 처리 (이전 transcript는 페이지 로드 시 이미 초기화됨)
    
    // 이미 처리 중이면 무시
    if (isProcessingRef.current) {
      console.log('[Quiz] 이미 처리 중 - 무시:', transcript);
      return;
    }
    
    // 중복 처리 방지 (같은 transcript를 1초 이내에 다시 처리하지 않음)
    const now = Date.now();
    if (transcript === lastProcessedTranscriptRef.current && now - lastProcessedTimeRef.current < 1000) {
      console.log('[Quiz] 중복 transcript 무시:', transcript);
      useVoiceStore.getState().resetTranscript();
      return;
    }
    
    // 중간 결과 필터링 제거 - 자모 모드에서는 답안이 짧을 수 있음
    // TranscriptProcessor가 이미 최종 결과만 처리하므로, 추가 필터링 불필요
    
    isProcessingRef.current = true;
    lastProcessedTranscriptRef.current = transcript;
    lastProcessedTimeRef.current = now;
    
    console.log('[Quiz] STT result (최종):', transcript);
    
    // transcript를 즉시 초기화하여 중복 처리 방지
    useVoiceStore.getState().resetTranscript();
    
    // 1) 먼저 음성 명령 처리 시도 (홈, 뒤로, 반복 등)
    const handled = onSpeech(transcript);
    if (handled) {
      // 명령이 처리되었으면 종료
      isProcessingRef.current = false;
      return;
    }
    
    // 2) 명령이 아니면 정답으로 처리
    setUser(transcript);
    // 인식 끝나면 자동 제출
    setTimeout(() => {
      onSubmit(transcript);
      // 제출 후 처리 플래그 리셋 (다음 답안을 받을 수 있도록)
      setTimeout(() => {
        isProcessingRef.current = false;
      }, 1000);
    }, 50);
  }, [transcript, onSpeech]); // isListening 제거 (GlobalVoiceRecognition이 마이크를 켤 때만 transcript 생성)

  const onSubmit = async (val?: string) => {
    if (!cur) return;
    const answer = answerText(cur).trim();  // ex) '기역'
    const userAns = (val ?? user).trim();

    console.log('[Quiz] Answer check:', { userAns, answer, char: cur.char, name: (cur as any).name });

    // 🎯 유연한 매칭 사용
    const ok = userAns.length > 0 && isAnswerMatch(userAns, answer, cur);
    
    if (!ok) {
      await learningAPI.saveReview("wrong", {
        mode, expected: answer, user: userAns, idx: i,
        questionText: promptText(cur),
        questionCells: cells,             // ← 여기가 포인트
      });
    }

    setResult({ ok, answer });
    setTimeout(() => {
      setResult(null);
      setUser("");
      setI((x) => x + 1);
      if (i + 1 >= pool.length) nav("/review", { replace: true });
      else inputRef.current?.focus();
    }, 900);
  };

  const onKeyDown: React.KeyboardEventHandler<HTMLInputElement> = (e) => {
    if (e.key === "Enter") onSubmit();
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-bg text-fg flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin w-8 h-8 border-2 border-primary border-t-transparent rounded-full mx-auto mb-4"></div>
          <div className="text-muted">퀴즈 준비 중…</div>
        </div>
      </div>
    );
  }
  if (!pool.length) {
    return (
      <div className="min-h-screen bg-bg text-fg flex items-center justify-center">
        <div className="text-center text-muted">퀴즈에 필요한 학습 데이터가 없습니다.</div>
      </div>
    );
  }

  const progress = Math.round(((i + 1) / pool.length) * 100);

  return (
    <div className="min-h-screen bg-bg text-fg flex flex-col">
      {/* 헤더 */}
      <header className="bg-white border-b border-border shadow-toss">
        <div className="w-full md:max-w-md md:mx-auto px-4">
          <div className="flex items-center justify-between py-2.5">
            <button
              onClick={() => nav(-1)}
              className="p-3 rounded-2xl hover:bg-card focus:outline-none focus:ring-2 focus:ring-primary"
              aria-label="뒤로 가기"
            >
              <ArrowLeft className="w-6 h-6 text-fg" />
            </button>
            <div className="flex-1 text-center">
              <h1 className="text-lg font-semibold text-fg">자모 퀴즈</h1>
              <div className="text-xs text-muted mt-1">
                {i + 1} / {pool.length} ({mode})
              </div>
            </div>
            <div className="w-12" />
          </div>
        </div>
      </header>

      {/* 본문 */}
      <main className="flex-1 p-3">
        <div className="w-full md:max-w-md md:mx-auto space-y-4">
          {/* 진행률 */}
          <div className="bg-white rounded-2xl p-3 shadow-toss">
            <div className="flex justify-between text-sm text-muted mb-1.5">
              <span>진척도</span>
              <span>{progress}%</span>
            </div>
            <div className="w-full bg-border rounded-full h-2">
              <div className="bg-primary h-2 rounded-full transition-all" style={{ width: `${progress}%` }} />
            </div>
          </div>

          {/* 문제 카드 (문자 대신 점자 셀!) */}
          <div className="bg-white rounded-2xl p-4 shadow-toss text-center">
            {/* 결과 배지: 독립 블록으로 중앙 정렬 → 셀을 밀지 않음 */}
            {result && (
              <div className="mb-3 w-full flex justify-center">
                <div className={`px-3 py-1.5 rounded-xl text-sm ${
                  result.ok ? "bg-success/10 text-success" : "bg-danger/10 text-danger"
                }`}>
                  {result.ok ? "정답입니다!" : `오답입니다. 정답: ${result.answer}`}
                </div>
              </div>
            )}

            {/* 문제: 항상 '점자 셀'을 가운데 노출 */}
            <div className="mb-4 flex justify-center">
              {cells.length ? (
                <div className="inline-flex flex-wrap justify-center gap-3">
                  {cells.map((c, idx) => <CellView key={idx} c={c} />)}
                </div>
              ) : (
                <div className="text-muted text-sm py-8">점자 데이터를 불러오는 중…</div>
              )}
            </div>

            <label className="block text-sm text-muted mb-1.5">정답 입력(예: "디귿")</label>
            <input
              ref={inputRef}
              value={user}
              onChange={(e) => setUser(e.target.value)}
              onKeyDown={onKeyDown}
              placeholder="정확히 입력하세요"
              className="w-full px-4 py-2.5 rounded-xl border border-border bg-card focus:outline-none focus:ring-2 focus:ring-primary"
              autoFocus
            />

            <div className="flex gap-2 mt-3">
              <button
                onClick={speakPrompt}
                className="flex-1 px-4 py-2 rounded-2xl bg-accent text-white hover:bg-accent/90 focus:outline-none focus:ring-2 focus:ring-accent"
              >
                <RotateCcw className="inline w-4 h-4 mr-1" /> 다시 듣기
              </button>

              {/* 음성 입력 버튼 제거 - 화면을 누르는 방식으로 통일 (GlobalVoiceRecognition이 처리) */}

              <button
                onClick={() => onSubmit()}
                disabled={!user.trim().length}
                className="flex-1 px-4 py-2 rounded-2xl bg-primary text-white hover:bg-primary/90 disabled:opacity-50 focus:outline-none focus:ring-2 focus:ring-primary"
              >
                제출
              </button>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}