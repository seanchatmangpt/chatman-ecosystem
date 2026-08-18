"use client";

import { useState } from "react";

/**
 * Copy-to-clipboard + download for a real client-side-generated text
 * blob. Originally built for lib/iac.ts's exportProjectManifest (the
 * "Copy YAML"/download-manifest pair on /projects/[name]/iac); reused
 * as-is -- same component, same approach -- for /quickstart's generated
 * shell script, with `copyLabel`/`mimeType` added so both call sites can
 * label/type themselves correctly instead of forking the component.
 * Download uses a `data:` URL -- this console has no backend file
 * endpoint and doesn't need one: the entire text already exists
 * client-side as a string, so a `data:` URL is the honest, real download
 * mechanism here (not a placeholder).
 */
export default function ManifestActions({
  yamlText,
  fileName,
  copyLabel = "Copy YAML",
  mimeType = "text/yaml",
}: {
  yamlText: string;
  fileName: string;
  copyLabel?: string;
  mimeType?: string;
}) {
  const [copied, setCopied] = useState(false);

  async function onCopy() {
    try {
      await navigator.clipboard.writeText(yamlText);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // Clipboard API unavailable (e.g. insecure context) -- selection is
      // still possible directly from the <pre> below, so this fails quiet.
    }
  }

  const href = `data:${mimeType};charset=utf-8,${encodeURIComponent(yamlText)}`;

  return (
    <div className="flex items-center gap-2">
      <button
        type="button"
        onClick={onCopy}
        className="rounded-md border border-border px-3 py-1.5 text-xs font-medium text-white hover:bg-white/5"
      >
        {copied ? "Copied" : copyLabel}
      </button>
      <a
        href={href}
        download={fileName}
        className="rounded-md bg-accent px-3 py-1.5 text-xs font-medium text-white"
      >
        Download {fileName}
      </a>
    </div>
  );
}
