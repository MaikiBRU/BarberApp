import { SkeletonRows } from "@/components/ui/states";

export default function Loading() {
  return (
    <div className="mx-auto max-w-6xl px-4 py-8 sm:px-6 lg:px-8">
      <SkeletonRows rows={4} />
    </div>
  );
}
