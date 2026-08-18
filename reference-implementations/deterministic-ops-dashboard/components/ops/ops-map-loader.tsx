"use client";

import dynamic from "next/dynamic";
import { Skeleton } from "@/components/ui/skeleton";

// deck.gl reads `window`/WebGL at module init, so it must never run during
// SSR — ssr:false is only valid inside a Client Component in the App Router,
// hence this thin wrapper around the server-rendered page below.
const OpsMap = dynamic(() => import("./ops-map").then((m) => m.OpsMap), {
  ssr: false,
  loading: () => <Skeleton className="h-full w-full rounded-lg" />,
});

export function OpsMapLoader() {
  return <OpsMap />;
}
