import { useMemo } from "react";
import { localToBrailleCells } from "@/lib/braille";
import type { DotArray } from "@/types";

type CellBool = [boolean, boolean, boolean, boolean, boolean, boolean];

interface BrailleCellProps {
  keyword?: string;
  pattern?: DotArray;     // 외부에서 넘어오는 임의 배열도 허용 → 내부 정규화
  active?: boolean;
  className?: string;
}

const OFF6: CellBool = [false, false, false, false, false, false];

const normalizeTo6 = (arr?: DotArray | CellBool): CellBool => {
  const out: boolean[] = Array.isArray(arr) ? arr.slice(0, 6) : [];
  while (out.length < 6) out.push(false);
  return out as CellBool;
};

export function BrailleCell({
  keyword,
  pattern,
  active = true,
  className = "",
}: BrailleCellProps) {
  // 점자 패턴 결정 (pattern 우선, 없으면 keyword 변환)
  const braillePattern = useMemo<CellBool>(() => {
    if (!active) return OFF6;
    if (pattern) return normalizeTo6(pattern);

    if (!keyword) return OFF6;

    try {
      // localToBrailleCells는 문자열 → 셀 배열 반환한다고 가정
      const cells = localToBrailleCells(keyword);
      // 한 글자 기준 첫 셀 사용. 없으면 OFF6
      const first = Array.isArray(cells) ? (cells[0] as unknown as DotArray | undefined) : undefined;
      return normalizeTo6(first);
    } catch {
      return OFF6;
    }
  }, [keyword, pattern, active]);

  return (
    <div className={`flex flex-col items-center ${className}`}>
      {/* 점자 셀 시각화 (표준 2x3, column-major) */}
      <div
        className={`grid grid-cols-2 grid-rows-3 gap-1.5 p-2.5 rounded-md ${
          active 
            ? 'bg-background border-2 border-foreground/20 shadow-inner' 
            : 'bg-muted border border-border/50'
        }`}
        role="group"
        aria-label={keyword ? `점자 셀: ${keyword}` : "점자 셀"}
        style={{ width: '48px', height: '72px' }}
      >
        {braillePattern.map((dot, index) => (
          <div
            key={index}
            className={`w-3 h-3 rounded-full transition-all ${
              dot 
                ? active 
                  ? "bg-foreground shadow-sm" 
                  : "bg-muted-foreground/40"
                : "bg-transparent border border-border/30"
            }`}
            aria-hidden={true}
          />
        ))}
      </div>
    </div>
  );
}

export default BrailleCell;
