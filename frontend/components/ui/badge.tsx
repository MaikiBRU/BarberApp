import { cn } from "@/lib/cn";
import type { Tone } from "@/lib/status";

const tones: Record<Tone, string> = {
  neutral: "bg-surface-muted text-ink-muted",
  info: "bg-info-soft text-info",
  positive: "bg-positive-soft text-positive",
  warning: "bg-warning-soft text-warning",
  danger: "bg-danger-soft text-danger",
};

type BadgeProps = {
  children: string;
  tone?: Tone;
  className?: string;
};

export function Badge({ children, tone = "neutral", className }: BadgeProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full px-2.5 py-1 text-xs font-medium",
        tones[tone],
        className,
      )}
    >
      {children}
    </span>
  );
}
