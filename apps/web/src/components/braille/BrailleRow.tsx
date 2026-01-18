import BrailleGrid from "./BrailleGrid";
import type { Cell } from "@/lib/brailleMap";

interface BrailleRowProps {
  cells?: Cell[];
  label?: string;
  className?: string;
}

export default function BrailleRow({
  cells = [],
  label = "점자 행",
  className = "",
}: BrailleRowProps) {
  return (
    <div
      className={`flex flex-wrap gap-3 items-center ${className}`}
      role="group"
      aria-label={label}
    >
      {cells.map((c, idx) => {
        // Cell을 "100000" 형태의 문자열로 변환
        const pattern = c.map(dot => dot ? '1' : '0').join('');
        return <BrailleGrid key={`cell-${idx}`} pattern={pattern} size={48} />;
      })}
    </div>
  );
}
