/**
 * 공통 점자 Dot 컴포넌트
 * 여러 페이지에서 중복 사용되던 Dot 컴포넌트를 통합
 */
interface BrailleDotProps {
  on: boolean;
  className?: string;
}

export function BrailleDot({ on, className = "" }: BrailleDotProps) {
  return (
    <span
      className={`inline-block w-4 h-4 rounded-full mx-0.5 my-0.5 border-2 transition-all duration-200 ${
        on ? "bg-primary border-primary shadow-sm" : "bg-card border-border"
      } ${className}`}
      aria-hidden="true"
    />
  );
}

export default BrailleDot;

