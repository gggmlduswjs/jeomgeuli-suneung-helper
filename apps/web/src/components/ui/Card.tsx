import React from "react";
import type { LucideIcon } from "lucide-react";

interface CardProps {
  title: string;
  description?: string;
  icon?: LucideIcon;
  onClick?: () => void;
  className?: string;
  disabled?: boolean;
  children?: React.ReactNode;
  variant?: "default" | "interactive" | "highlight";
}

export default function Card({
  title,
  description,
  icon: Icon,
  onClick,
  className = "",
  disabled = false,
  children,
  variant = "default",
}: CardProps) {
  const isInteractive = variant === "interactive" && !!onClick && !disabled;

  // 안전한 기본 card 스타일 (프로젝트 토큰 없을 때도 보기 좋게)
  const baseClasses =
    "transition-all duration-200 rounded-xl border focus:outline-none " +
    (isInteractive ? "focus:ring-4" : ""); // 포커스링은 interactive일 때만

  const variantClasses: Record<NonNullable<CardProps["variant"]>, string> = {
    default:
      "bg-card border-border p-4 " +
      "bg-white border-gray-200", // fallback
    interactive:
      "card-interactive p-4 hover:bg-card/80 active:scale-95 cursor-pointer " +
      "hover:bg-gray-50", // fallback
    highlight:
      "bg-accent text-black border-accent shadow-lg shadow-accent/20 p-4 " +
      "bg-sky-100 border-sky-200", // fallback
  };

  const disabledClasses = disabled
    ? "opacity-50 pointer-events-none select-none"
    : "";

  const handleKeyDown: React.KeyboardEventHandler<HTMLDivElement> = (e) => {
    if (!isInteractive) return;
    if (e.key === "Enter" || e.key === " ") {
      e.preventDefault();
      onClick?.();
    }
  };

  return (
    <div
      className={`${baseClasses} ${variantClasses[variant]} ${disabledClasses} ${className}`}
      onClick={isInteractive ? onClick : undefined}
      onKeyDown={isInteractive ? handleKeyDown : undefined}
      tabIndex={isInteractive ? 0 : -1}
      role={isInteractive ? "button" : "article"}
      aria-disabled={disabled}
    >
      <div className="flex items-start space-x-4">
        {Icon && (
          <div className="flex-shrink-0">
            <Icon className="w-8 h-8 text-primary text-sky-600" aria-hidden="true" />
          </div>
        )}

        <div className="flex-1 min-w-0">
          <h3 className="h3 mb-2 text-gray-900 font-semibold">{title}</h3>
          {description && (
            <p className="text-secondary text-base leading-relaxed text-gray-600">
              {description}
            </p>
          )}
          {children}
        </div>
      </div>
    </div>
  );
}
