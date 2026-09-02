import type { Metadata } from "next";
import { Suspense } from "react";

import { SkeletonRows } from "@/components/ui/states";
import { DemoLanding } from "@/features/demo/demo-landing";

export const metadata: Metadata = {
  title: "Demo",
  description:
    "Probá BarberApp sin registrarte: una barbería temporal con turnos reales y los tres roles del producto.",
};

export default function DemoPage() {
  return (
    <Suspense
      fallback={
        <div className="mx-auto max-w-6xl px-4 py-8 sm:px-6 lg:px-8">
          <SkeletonRows rows={4} />
        </div>
      }
    >
      <DemoLanding />
    </Suspense>
  );
}
