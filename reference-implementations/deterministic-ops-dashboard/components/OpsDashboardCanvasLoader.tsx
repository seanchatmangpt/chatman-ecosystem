"use client";

import dynamic from "next/dynamic";
import { Skeleton } from "@/components/ui/skeleton";
import type { OpsDashboardCanvasProps } from "./OpsDashboardCanvas";

// Same reasoning as components/ops/ops-map-loader.tsx: deck.gl touches
// window/WebGL at module init, so it must never run during SSR.
const OpsDashboardCanvas = dynamic(
  () => import("./OpsDashboardCanvas").then((m) => m.OpsDashboardCanvas),
  {
    ssr: false,
    loading: () => <Skeleton className="h-full w-full rounded-lg" />,
  },
);

export function OpsDashboardCanvasLoader(props: OpsDashboardCanvasProps) {
  return <OpsDashboardCanvas {...props} />;
}
