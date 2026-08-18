"use client";

import dynamic from "next/dynamic";
import type { Model } from "isoflow";

// isoflow renders directly against the DOM (canvas-ish MUI + react-quill
// internals) and has no SSR path -- isoflow.io/docs/quickstart's own
// Next.js guidance is to load it via a client-only dynamic import. This
// component is already "use client"; the dynamic+ssr:false wrapper is what
// actually stops Next from attempting to server-render isoflow's real
// browser-only code during the RSC/SSR pass.
const Isoflow = dynamic(() => import("isoflow").then((mod) => mod.Isoflow), {
  ssr: false,
  loading: () => (
    <div className="flex h-[560px] w-full items-center justify-center rounded-xl border border-border bg-[#111521] text-sm text-muted-foreground">
      loading isometric view…
    </div>
  ),
});

export interface IsoflowTopologyProps {
  model: Model;
}

export function IsoflowTopology({ model }: IsoflowTopologyProps) {
  return (
    <div className="h-[560px] w-full overflow-hidden rounded-xl border border-border">
      <Isoflow
        initialData={{ ...model, fitToView: true, view: model.views[0]?.id }}
        editorMode="EXPLORABLE_READONLY"
        width="100%"
        height="100%"
      />
    </div>
  );
}

export default IsoflowTopology;
