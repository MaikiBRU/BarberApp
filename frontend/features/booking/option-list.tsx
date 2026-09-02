import { cn } from "@/lib/cn";

type OptionProps = {
  title: string;
  description?: string | null;
  meta?: string;
  price?: string;
  isSelected: boolean;
  onSelect: () => void;
};

export function OptionRow({
  title,
  description,
  meta,
  price,
  isSelected,
  onSelect,
}: OptionProps) {
  return (
    <button
      aria-pressed={isSelected}
      className={cn(
        "flex w-full items-start justify-between gap-4 rounded-md border px-4 py-3 text-left transition-colors",
        isSelected
          ? "border-brand bg-surface-muted"
          : "border-line hover:border-line-strong",
      )}
      onClick={onSelect}
      type="button"
    >
      <span>
        <span className="block font-medium">{title}</span>
        {description ? (
          <span className="mt-0.5 block text-sm text-ink-muted">
            {description}
          </span>
        ) : null}
        {meta ? (
          <span className="mt-1 block text-sm text-ink-muted">{meta}</span>
        ) : null}
      </span>
      {price ? (
        <span className="shrink-0 font-semibold">{price}</span>
      ) : null}
    </button>
  );
}
