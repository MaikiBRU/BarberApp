import { Card } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/states";

export type Metric = {
  label: string;
  value: string;
  hint?: string;
};

export function MetricGrid({ metrics }: { metrics: Metric[] }) {
  return (
    <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
      {metrics.map((metric) => (
        <Card className="p-4" key={metric.label}>
          <p className="text-sm text-ink-muted">{metric.label}</p>
          <p className="mt-2 text-2xl font-semibold tabular-nums">
            {metric.value}
          </p>
          {metric.hint ? (
            <p className="mt-1 text-xs text-ink-muted">{metric.hint}</p>
          ) : null}
        </Card>
      ))}
    </div>
  );
}

export function MetricGridSkeleton() {
  return (
    <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
      {Array.from({ length: 4 }, (_, index) => (
        <Skeleton className="h-24" key={index} />
      ))}
    </div>
  );
}
