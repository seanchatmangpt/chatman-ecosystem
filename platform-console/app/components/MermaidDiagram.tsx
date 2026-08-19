"use client";

/**
 * Renders real Mermaid diagram text (produced server-side by
 * lib/mermaid.ts's mmdio subprocess bridge -- never hand-built here) to SVG
 * client-side via the mermaid.js package, in place of the raw-text <pre>
 * block the mermaid tab previously showed. Mirrors IsoflowTopology.tsx's
 * "use client" + browser-only-render discipline: mermaid.render() touches
 * `document` internally, so this must never run during SSR/RSC.
 *
 * Fails closed like every other module here -- a real render error (bad
 * syntax from mmdio, mermaid.js exception) is shown as an explicit error
 * state, never swallowed into a blank or fabricated diagram.
 */
import { useEffect, useId, useRef, useState } from "react";

export interface MermaidDiagramProps {
  /** Real Mermaid diagram source text, already produced by lib/mermaid.ts. */
  source: string;
}

type RenderState =
  | { status: "loading" }
  | { status: "ok"; svg: string }
  | { status: "error"; message: string };

export function MermaidDiagram({ source }: MermaidDiagramProps) {
  const rawId = useId();
  // mermaid.render() requires a valid DOM id (no colons -- useId() emits
  // ones like ":r4:"), so strip non-alphanumerics.
  const elementId = `mermaid-${rawId.replace(/[^a-zA-Z0-9]/g, "")}`;
  const [state, setState] = useState<RenderState>({ status: "loading" });
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    let cancelled = false;
    setState({ status: "loading" });

    import("mermaid")
      .then(async (mod) => {
        const mermaid = mod.default;
        mermaid.initialize({ startOnLoad: false, theme: "dark", securityLevel: "strict" });
        try {
          const { svg } = await mermaid.render(elementId, source);
          if (!cancelled) setState({ status: "ok", svg });
        } catch (err) {
          if (!cancelled) {
            setState({
              status: "error",
              message: err instanceof Error ? err.message : String(err),
            });
          }
        }
      })
      .catch((err) => {
        if (!cancelled) {
          setState({
            status: "error",
            message: `failed to load mermaid.js: ${err instanceof Error ? err.message : String(err)}`,
          });
        }
      });

    return () => {
      cancelled = true;
    };
  }, [source, elementId]);

  if (state.status === "loading") {
    return (
      <div className="flex h-[300px] w-full items-center justify-center rounded-md bg-black/30 text-xs text-muted-foreground">
        rendering diagram…
      </div>
    );
  }

  if (state.status === "error") {
    return (
      <div className="rounded-md border border-red-900 bg-red-950/30 p-4 text-xs text-red-300">
        mermaid.js render failed: {state.message}
      </div>
    );
  }

  return (
    <div
      ref={containerRef}
      className="overflow-x-auto rounded-md bg-black/30 p-4 [&_svg]:mx-auto [&_svg]:max-w-full"
      // eslint-disable-next-line react/no-danger -- state.svg is mermaid.js's
      // own sanitized output (securityLevel: "strict"), not user HTML.
      dangerouslySetInnerHTML={{ __html: state.svg }}
    />
  );
}

export default MermaidDiagram;
