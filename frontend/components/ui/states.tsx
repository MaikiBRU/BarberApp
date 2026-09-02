import type { ReactNode } from "react";

import { Button } from "@/components/ui/button";
import { cn } from "@/lib/cn";

/** Neutral placeholder while data is loading. */
export function Skeleton({ className }: { className?: string }) {
  return (
    <div
      aria-hidden="true"
      className={cn(
        "animate-pulse rounded-md bg-surface-muted",
        className,
      )}
    />
  );
}

/** A list of skeleton rows sized for a table or agenda. */
export function SkeletonRows({ rows = 3 }: { rows?: number }) {
  return (
    <div className="space-y-3 p-4 sm:p-5" role="status" aria-live="polite">
      <span className="sr-only">Cargando...</span>
      {Array.from({ length: rows }, (_, index) => (
        <Skeleton className="h-16 w-full" key={index} />
      ))}
    </div>
  );
}

type EmptyStateProps = {
  title: string;
  description?: string;
  action?: ReactNode;
};

/**
 * Shown when a request succeeded and there is genuinely nothing to
 * display. Never used for failures: see `ErrorState`.
 */
export function EmptyState({ title, description, action }: EmptyStateProps) {
  return (
    <div className="px-4 py-10 text-center sm:px-6">
      <p className="text-sm font-medium">{title}</p>
      {description ? (
        <p className="mx-auto mt-1 max-w-sm text-sm text-ink-muted">
          {description}
        </p>
      ) : null}
      {action ? <div className="mt-4">{action}</div> : null}
    </div>
  );
}

type ErrorStateProps = {
  title?: string;
  message: string;
  onRetry?: () => void;
  isRetrying?: boolean;
};

/**
 * Shown when a request failed. Kept visually distinct from
 * `EmptyState` so a broken API never reads as "no data yet".
 */
export function ErrorState({
  title = "No se pudieron cargar los datos",
  message,
  onRetry,
  isRetrying = false,
}: ErrorStateProps) {
  return (
    <div
      className="m-4 rounded-md border border-danger/40 bg-danger-soft px-4 py-4 sm:m-5"
      role="alert"
    >
      <p className="text-sm font-semibold text-danger">{title}</p>
      <p className="mt-1 text-sm text-danger/90">{message}</p>
      {onRetry ? (
        <Button
          className="mt-3"
          isLoading={isRetrying}
          onClick={onRetry}
          size="sm"
          variant="secondary"
        >
          Reintentar
        </Button>
      ) : null}
    </div>
  );
}

/** Inline feedback attached to a form submission. */
export function FormMessage({
  tone,
  children,
}: {
  tone: "error" | "success";
  children: ReactNode;
}) {
  const isError = tone === "error";
  return (
    <p
      className={cn(
        "rounded-md px-3 py-2 text-sm",
        isError
          ? "bg-danger-soft text-danger"
          : "bg-positive-soft text-positive",
      )}
      role={isError ? "alert" : "status"}
    >
      {children}
    </p>
  );
}
