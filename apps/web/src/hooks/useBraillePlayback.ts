import { useEffect, useState, useCallback, useRef, useMemo } from "react";
import useBrailleBLE from "./useBrailleBLE";
import { localToBrailleCells } from "@/lib/braille";
import type { UseBraillePlaybackOptions, DotArray } from "@/types";

export function useBraillePlayback(opts: UseBraillePlaybackOptions = {}) {
  const {
    delayMs = 1200,
    previewMode = "local",
    onEnd,
    onBeforePlay,
    onAfterPlay,
  } = opts;

  // BLE 훅
  const { isConnected, writeText } = useBrailleBLE();

  // 상태
  const [enabled, setEnabled] = useState(false);
  const [queue, setQueue] = useState<string[]>([]);
  const [index, setIndex] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);

  // 프리뷰
  const [currentWord, setCurrentWord] = useState<string>("");
  const [currentCells, setCurrentCells] = useState<DotArray[]>([]);

  // 데모 모드: 미연결이면 true
  const demoMode = !isConnected;

  // 내부 제어용 ref
  const playingRef = useRef(false);
  const abortRef = useRef({ aborted: false });

  // 파생 상태
  const status = useMemo(() => {
    const base = !enabled ? "대기 중" : isPlaying ? "출력 중" : queue.length ? "일시 정지" : "대기 중";
    return demoMode ? `${base} · 데모` : base;
  }, [enabled, isPlaying, queue.length, demoMode]);

  // 프리뷰 설정
  const setPreview = useCallback(
    (word: string) => {
      setCurrentWord(word);
      if (previewMode === "local" && word.trim()) {
        try {
          const cells = localToBrailleCells(word);
          setCurrentCells(cells as unknown as DotArray[]);
        } catch (e) {
          console.warn("[BraillePlayback] preview failed:", e);
          setCurrentCells([]);
        }
      } else {
        setCurrentCells([]);
      }
    },
    [previewMode]
  );

  // 큐 적재(교체)
  const enqueueKeywords = useCallback(
    (kws: string[]) => {
      const list = (kws || []).map((s) => String(s ?? "").trim()).filter(Boolean);
      if (!list.length) return;
      setQueue(list);
      setIndex(0);
      if (enabled) {
        // 기존 루프가 있다면 중단 후 다시 실행
        pause();
        // 다음 틱에서 시작(상태 적용 보장)
        setTimeout(() => start(), 0);
      }
    },
    [enabled]
  );

  // 현재 단어 출력
  const playOnce = useCallback(
    async (word: string, idx: number) => {
      if (!word) return;
      onBeforePlay?.(word, idx);
      setPreview(word);

      if (demoMode) {
        // 데모: 표시만 하고 기다림
        await new Promise((r) => setTimeout(r, delayMs));
      } else {
        // 실제 BLE 출력 - writeText 사용 (API를 통해 점자 변환 후 전송)
        try {
          await writeText(word);
          if (delayMs > 0) {
            await new Promise((r) => setTimeout(r, delayMs));
          }
        } catch (error) {
          console.error("[BraillePlayback] BLE 전송 실패:", error);
          // 에러가 발생해도 데모 모드로 계속 진행
        }
      }

      onAfterPlay?.(word, idx);
    },
    [demoMode, delayMs, setPreview, writeText, onBeforePlay, onAfterPlay]
  );

  // 재생 루프
  const loop = useCallback(async () => {
    if (playingRef.current) return; // 중복 루프 방지
    if (!enabled || !queue.length) return;
    if (!demoMode && !isConnected) return;

    playingRef.current = true;
    abortRef.current.aborted = false;
    setIsPlaying(true);

    try {
      let i = index;
      while (!abortRef.current.aborted && enabled && i < queue.length) {
        const word = queue[i];
        await playOnce(word, i);
        if (abortRef.current.aborted || !enabled) break;
        i += 1;
        setIndex(i); // 외부 UI 갱신
      }

      // 끝까지 갔거나 중단됨
      if (!abortRef.current.aborted && enabled && i >= queue.length) {
        setIsPlaying(false);
        onEnd?.();
      }
    } catch (e) {
      console.error("[BraillePlayback] loop error:", e);
      setIsPlaying(false);
    } finally {
      playingRef.current = false;
    }
  }, [enabled, queue, index, isConnected, demoMode, playOnce, onEnd]);

  // 공개 메서드들
  const start = useCallback(() => {
    if (!enabled || !queue.length) return;
    if (!demoMode && !isConnected) return;
    // 루프 시작(이미 돌고 있으면 무시)
    loop();
  }, [enabled, queue.length, demoMode, isConnected, loop]);

  const pause = useCallback(() => {
    abortRef.current.aborted = true;
    setIsPlaying(false);
    playingRef.current = false;
  }, []);

  const reset = useCallback(() => {
    pause();
    setQueue([]);
    setIndex(0);
    setCurrentWord("");
    setCurrentCells([]);
  }, [pause]);

  const next = useCallback(() => {
    if (!queue.length) return;
    pause();
    setIndex((i) => Math.min(i + 1, queue.length - 1));
    if (enabled) setTimeout(() => start(), 0);
  }, [queue.length, enabled, pause, start]);

  const prev = useCallback(() => {
    if (!queue.length) return;
    pause();
    setIndex((i) => Math.max(i - 1, 0));
    if (enabled) setTimeout(() => start(), 0);
  }, [queue.length, enabled, pause, start]);

  const repeat = useCallback(() => {
    if (!queue.length) return;
    pause();
    if (enabled) setTimeout(() => start(), 0);
  }, [queue.length, enabled, pause, start]);

  const setIndexTo = useCallback(
    (newIndex: number) => {
      if (newIndex < 0 || newIndex >= queue.length) return;
      pause();
      setIndex(newIndex);
      if (enabled) setTimeout(() => start(), 0);
    },
    [queue.length, enabled, pause, start]
  );

  // 인덱스가 바뀌었고 플레이 중이면 루프가 계속해서 이어지도록(루프는 내부에서 index를 증가시키지만,
  // 외부 next/prev/setIndexTo가 호출된 경우를 대비)
  useEffect(() => {
    if (enabled && isPlaying && (demoMode || isConnected)) {
      // 루프가 없다면 다시 시작
      if (!playingRef.current) loop();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [index]);

  // enabled 변화 시 처리
  useEffect(() => {
    if (enabled) {
      if (queue.length && (demoMode || isConnected)) {
        start();
      }
    } else {
      pause();
    }
  }, [enabled, queue.length, demoMode, isConnected, start, pause]);

  // 언마운트 클린업
  useEffect(() => {
    return () => {
      abortRef.current.aborted = true;
      playingRef.current = false;
    };
  }, []);

  return {
    // 상태
    enabled,
    setEnabled,
    queue,
    setQueue, // 교체용
    index,
    isPlaying,
    currentWord,
    currentCells,
    status,
    demoMode,

    // 제어
    enqueueKeywords,
    start,
    pause,
    next,
    prev,
    repeat,
    setIndexTo,
    reset,
  };
}

export default useBraillePlayback;
