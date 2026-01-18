import { useState, useEffect, useMemo } from "react";
import BrailleCell from "./BrailleCell";
import { brailleAPI } from "@/lib/api/BrailleAPI";
import { normalizeCells } from "@/lib/brailleSafe";

type DotArray = [boolean, boolean, boolean, boolean, boolean, boolean];

interface BrailleStripProps {
  text: string;
  size?: "normal" | "large";
}

export default function BrailleStrip({ text, size = "normal" }: BrailleStripProps) {
  const [cells, setCells] = useState<DotArray[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState<boolean>(false);

  // 크기별 스타일
  const sizeClass = useMemo(() => (size === "large" ? "scale-125 gap-7" : "scale-100 gap-6"), [size]);

  useEffect(() => {
    let cancelled = false;

    const loadCells = async () => {
      setLoading(true);
      setError(null);
      setCells([]);

      try {
        // brailleAPI.convertBraille(text, mode) → 서버 구현에 따라 { ok, cells, error } 또는 직접 배열 반환 가능
        const result = await brailleAPI.convertBraille(text, "word");
        const raw = (result && "cells" in result ? result.cells : result) as unknown;

        // 다양한 형태를 모두 6칸 불리언 배열로 정규화
        const normalized: DotArray[] = normalizeCells(raw as any[]) as unknown as DotArray[];

        if (!cancelled) {
          setCells(Array.isArray(normalized) ? normalized : []);
          // result.ok가 false면 에러 메시지 표시
          const okFlag = typeof result === "object" && result && "ok" in result ? (result as any).ok : true;
          setError(okFlag ? null : ((result as any)?.error ?? "convert_failed"));
        }
      } catch (e: any) {
        console.error("BrailleStrip convertBraille error:", e);
        if (!cancelled) {
          setCells([]);
          setError("conversion_failed");
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    };

    // 공백이나 빈 문자열인 경우 초기화
    if (!text?.trim()) {
      setCells([]);
      setError(null);
      setLoading(false);
    } else {
      loadCells();
    }

    return () => {
      cancelled = true;
    };
  }, [text]);

  return (
    <div
      className={`flex items-center justify-center ${sizeClass}`}
      role="group"
      aria-label={`점자 스트립: ${text || "빈 텍스트"}`}
    >
      {loading ? (
        <div className="text-gray-500 text-sm" aria-live="polite">
          점자 변환 중...
        </div>
      ) : cells.length > 0 ? (
        cells.map((cell, i) => (
          <BrailleCell
            key={`cell-${i}`}
            pattern={Array.isArray(cell) ? cell : ([false, false, false, false, false, false] as DotArray)}
            className="transition-transform"
            active={true}
          />
        ))
      ) : (
        <div className="text-gray-500 text-sm" aria-live="polite">
          {error ? `변환 실패: ${error}` : "표시할 점자가 없습니다."}
        </div>
      )}
    </div>
  );
}
