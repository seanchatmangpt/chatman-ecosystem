/**
 * Mermaid rendering via mmdio's real, typed FlowchartDiagram model --
 * https://github.com/seanchatmangpt/mmdio (checked out locally at
 * `MMDIO_PROJECT_DIR`, default `/Users/sac/mmdio`). mmdio is a Python
 * library: its CLI and FastAPI service are both placeholder stubs except
 * for the `render-flowchart` subcommand added alongside this file, so the
 * only real integration path is a subprocess call into that subcommand --
 * same "shell out, parse JSON stdout, fail closed" bridge discipline
 * lib/container-exec.ts documents for the k8s exec subresource, applied
 * here to a local subprocess instead of a WebSocket.
 *
 * This module owns exactly one job: turn a `MermaidFlowchartInput` (the
 * same small node/edge shape mmdio's CLI validates through its real
 * Pydantic `FlowchartDiagram` model) into Mermaid diagram text, or a
 * `K8sResult`-shaped error -- never a fabricated diagram string. No
 * hand-built Mermaid text lives in this codebase; every render goes
 * through mmdio's typed renderer.
 *
 * Runs on the Node.js runtime only (uses `node:child_process`) --  same
 * constraint as lib/k8s.ts and lib/container-exec.ts.
 */
import { spawnSync } from "node:child_process";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import type { K8sResult } from "./k8s";

export interface MermaidFlowchartNode {
  id: string;
  label: string;
  shape?: string;
}

export interface MermaidFlowchartEdge {
  source: string;
  target: string;
  label?: string;
  style?: string;
}

export interface MermaidFlowchartInput {
  direction?: "TB" | "TD" | "BT" | "LR" | "RL";
  nodes: MermaidFlowchartNode[];
  edges: MermaidFlowchartEdge[];
}

const MMDIO_PROJECT_DIR = process.env.MMDIO_PROJECT_DIR ?? "/Users/sac/mmdio";
const RENDER_TIMEOUT_MS = 10_000;

/**
 * True only when `MMDIO_PROJECT_DIR` looks like a real mmdio checkout
 * (`pyproject.toml` present) -- mirrors lib/k8s.ts's
 * `hasClusterCredentials()` fail-closed-before-attempting convention so
 * callers can render an honest "not configured" state instead of trying
 * and swallowing an ENOENT.
 */
export function hasMmdio(): boolean {
  return fs.existsSync(path.join(MMDIO_PROJECT_DIR, "pyproject.toml"));
}

/**
 * Shells out to `uv run mmdio render-flowchart --json <tmpfile>` inside
 * the mmdio checkout, which validates `input` through mmdio's real
 * `FlowchartDiagram` Pydantic model and renders it via
 * `render_diagram()` (mmdio's only non-stub renderer path). Returns the
 * real Mermaid text on success, or the real stderr (schema/JSON errors,
 * a non-zero exit, a missing `uv`/timeout) as `error` -- never a
 * fabricated fallback diagram.
 */
export function renderFlowchart(input: MermaidFlowchartInput): K8sResult<string> {
  if (!hasMmdio()) {
    return {
      ok: false,
      error: `not configured: no mmdio checkout found at ${MMDIO_PROJECT_DIR} (set MMDIO_PROJECT_DIR)`,
    };
  }

  const tmpFile = path.join(os.tmpdir(), `mmdio-flowchart-${process.pid}-${Date.now()}.json`);
  try {
    fs.writeFileSync(tmpFile, JSON.stringify(input));

    const result = spawnSync(
      "uv",
      ["run", "mmdio", "render-flowchart", "--json", tmpFile],
      {
        cwd: MMDIO_PROJECT_DIR,
        timeout: RENDER_TIMEOUT_MS,
        encoding: "utf8",
      },
    );

    if (result.error) {
      return { ok: false, error: `mmdio subprocess failed to start: ${result.error.message}` };
    }
    if (result.status !== 0) {
      const stderr = (result.stderr ?? "").trim();
      return {
        ok: false,
        error: `mmdio render-flowchart exited ${result.status}${stderr ? `: ${stderr}` : ""}`,
      };
    }
    return { ok: true, data: result.stdout };
  } finally {
    fs.rm(tmpFile, { force: true }, () => {});
  }
}
