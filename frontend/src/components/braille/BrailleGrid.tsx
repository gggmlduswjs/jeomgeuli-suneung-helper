import React, { useMemo } from "react";

interface BrailleGridProps {
  /** "100000" 형태의 6비트 문자열 (점1~점6) */
  pattern?: string;
  /** 전체 셀 박스 목표 크기(px) */
  size?: number;
  filledColor?: string; // 기본: sky-500
  emptyColor?: string;  // 기본: gray-200
  label?: React.ReactNode;
  className?: string;
}

/** 6점 점자(2x3) 시각화 컴포넌트 */
export default function BrailleGrid({
  pattern = "000000",
  size = 72,
  filledColor = "#0ea5e9",
  emptyColor = "#e5e7eb",
  label,
  className = "",
}: BrailleGridProps) {
  // dot 크기: 박스 크기의 1/3
  const dotSize = useMemo(() => size / 3, [size]);

  // "1"만 true, 나머지는 false로 정규화하여 6칸 맞춤
  const flags = useMemo<boolean[]>(
    () =>
      pattern
        .replace(/[^01]/g, "0")       // 0/1 이외 문자 방어
        .padEnd(6, "0")
        .slice(0, 6)
        .split("")
        .map((c) => c === "1"),
    [pattern]
  );

  const Dot = (on: boolean, key: number) => (
    <span
      key={key}
      aria-hidden={true}
      style={{
        width: dotSize,
        height: dotSize,
        borderRadius: "50%",
        display: "inline-block",
        background: on ? filledColor : emptyColor,
        boxShadow: on
          ? "0 3px 8px rgba(0,0,0,.25)"
          : "inset 0 0 0 1px rgba(0,0,0,.06)",
      }}
    />
  );

  // 표준 배치: (1·4) / (2·5) / (3·6)
  return (
    <div className={`inline-flex flex-col items-center ${className}`}>
      <div
        className="grid grid-cols-2 gap-x-4 gap-y-4"
        style={{ width: size }}
        role="group"
        aria-label={typeof label === "string" ? `점자 셀: ${label}` : "점자 셀"}
      >
        {Dot(flags[0], 1)} {Dot(flags[3], 4)}
        {Dot(flags[1], 2)} {Dot(flags[4], 5)}
        {Dot(flags[2], 3)} {Dot(flags[5], 6)}
      </div>
      {label && <div className="mt-2 text-sm text-gray-500">{label}</div>}
    </div>
  );
}
