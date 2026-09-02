import { cn } from "@/lib/cn";

export const bookingSteps = [
  "Servicio",
  "Barbero",
  "Horario",
  "Confirmar",
] as const;

type StepperProps = {
  activeStep: number;
  onSelect: (step: number) => void;
  maxReachable: number;
};

export function Stepper({
  activeStep,
  onSelect,
  maxReachable,
}: StepperProps) {
  return (
    <ol className="grid grid-cols-4 gap-1.5" role="list">
      {bookingSteps.map((label, index) => {
        const isActive = index === activeStep;
        const isDone = index < activeStep;
        const canGo = index <= maxReachable;

        return (
          <li key={label}>
            <button
              aria-current={isActive ? "step" : undefined}
              className={cn(
                "w-full rounded-md px-2 py-2 text-center text-xs font-semibold transition-colors",
                isActive
                  ? "bg-brand text-on-brand"
                  : isDone
                    ? "bg-accent-soft text-accent"
                    : "bg-surface-muted text-ink-muted",
                canGo ? "cursor-pointer" : "cursor-not-allowed opacity-60",
              )}
              disabled={!canGo}
              onClick={() => onSelect(index)}
              type="button"
            >
              <span className="hidden sm:inline">{index + 1}. </span>
              {label}
            </button>
          </li>
        );
      })}
    </ol>
  );
}
