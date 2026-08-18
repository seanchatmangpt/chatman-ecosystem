// ------------------------------------------------------- Container Exec
//
// Real hyperscaler-PaaS-style browser-based shell access (AWS Systems
// Manager Session Manager / GCP Cloud Shell / Azure Cloud Shell "run a
// command in a running instance/pod" equivalent) -- the most sensitive
// capability in this console, so it gets the most defense-in-depth of any
// module in this file tree:
//
//   1. App-level RBAC: owner-only (lib/authz.ts's requireRole(session,
//      "owner")), enforced both by app/api/exec/route.ts and by server.js's
//      /ws/exec upgrade handler -- never just hidden client-side.
//   2. k8s-level RBAC: `create`/`get` on the pods/exec subresource, granted
//      per-namespace (k8s/paas-rbac.yaml), never cluster-wide -- the exact
//      same per-namespace-Role-not-ClusterRole discipline the Secrets/
//      Scheduled-Jobs/Logs modules already use, for the same reason (this
//      is a genuine multi-tenant blast-radius boundary).
//   3. Command allowlist: the REAL security boundary against arbitrary
//      remote code execution. A pods/exec subresource takes a raw
//      `command` array the API server hands straight to the container
//      runtime -- accepting free-form text here would make this literally
//      an RCE backdoor with a UI. Exactly the same discipline
//      lib/scheduled-jobs.ts's `ALLOWED_COMMANDS` already established for
//      CronJob container commands: `ALLOWED_EXEC_COMMANDS` below is a
//      fixed, small, server-side allowlist of command IDS. The caller
//      picks an id, never raw text; `resolveExecCommand` is the one and
//      only place a request's `commandId` touches anything that becomes a
//      real exec `command` array, and it rejects anything unrecognized
//      BEFORE any WebSocket connection to the k8s API is ever opened.
//
// The k8s pods/exec subresource itself is not a normal JSON request/
// response the way every other lib/k8s.ts function is -- it is an HTTP
// connection UPGRADED to a WebSocket (the real mechanism `kubectl exec`
// itself uses; historically SPDY, and -- confirmed live against this
// cluster's real v1.34 API server before this module was written --
// equally reachable over a plain WebSocket upgrade using the
// `v4.channel.k8s.io` subprotocol the API server negotiates for a GET
// request to .../exec). k8sRequest's plain-HTTPS primitive has no upgrade
// support, so this module opens its own `ws` connection using the exact
// same in-cluster ServiceAccount token/CA/host/port every other function
// in this file tree trusts (lib/k8s.ts's new `getInClusterConfig`
// export) -- never a second, driftable credential source.
//
// Wire protocol once connected (v4.channel.k8s.io, RFC-documented by
// k8s's own remotecommand package): every WebSocket frame's first byte is
// a channel number -- 0 stdin (unused here, stdin=false), 1 stdout, 2
// stderr, 3 a final JSON `Status` object once the process exits, 4 resize
// (unused, tty=false). This module demuxes exactly those four channels
// and nothing else.
import { WebSocket } from "ws";
import { getInClusterConfig, type K8sResult } from "@/lib/k8s";

export interface AllowedExecCommand {
  id: AllowedExecCommandId;
  label: string;
  description: string;
  /** The real, fixed argv this id maps to -- never templated with request
   * text, so there is no code path from a caller-supplied string to this
   * array's contents. */
  command: string[];
}

/** The fixed, closed set of command ids -- declared as its own literal
 * union (not derived via `keyof typeof ALLOWED_EXEC_COMMANDS`) so adding a
 * new id without adding a matching allowlist entry is a real compile
 * error, the same discipline lib/scheduled-jobs.ts's AllowedCommandId
 * uses. */
export type AllowedExecCommandId = "cat-facts" | "echo" | "env" | "ls-app";

/**
 * The fixed, small allowlist -- read-only diagnostic commands only, never
 * arbitrary shell. Mirrored (small, disclosed duplication -- see that
 * file's own header comment) in server.js's `/ws/exec` handler, since
 * server.js sits outside Next's TS module graph and cannot `import` this
 * file directly; this module is the source of truth both files' comments
 * point back to.
 */
export const ALLOWED_EXEC_COMMANDS: Record<AllowedExecCommandId, AllowedExecCommand> = {
  "cat-facts": {
    id: "cat-facts",
    label: "cat /app/facts.json",
    description: "Reads the target container's own /app/facts.json diagnostic file, if present.",
    command: ["cat", "/app/facts.json"],
  },
  echo: {
    id: "echo",
    label: "echo",
    description: "Prints a fixed diagnostic string -- the smallest possible real, harmless exec.",
    command: ["echo", "platform-console container-exec diagnostic"],
  },
  env: {
    id: "env",
    label: "env",
    description: "Lists the target container's own real environment variables.",
    command: ["env"],
  },
  "ls-app": {
    id: "ls-app",
    label: "ls -la /app",
    description: "Lists the contents of the target container's /app directory.",
    command: ["ls", "-la", "/app"],
  },
};

function isAllowedExecCommandId(value: string): value is AllowedExecCommandId {
  return Object.prototype.hasOwnProperty.call(ALLOWED_EXEC_COMMANDS, value as AllowedExecCommandId);
}

/**
 * Resolves a caller-supplied string against the allowlist. Returns the
 * real `AllowedExecCommand` record on a match, `null` on anything else --
 * every caller (app/api/exec/route.ts, server.js's /ws/exec handler) must
 * treat `null` as "reject the request", never fall back to a default
 * command, and must never open the upstream k8s WebSocket until this has
 * already returned non-null.
 */
export function resolveExecCommand(commandId: string): AllowedExecCommand | null {
  return isAllowedExecCommandId(commandId) ? ALLOWED_EXEC_COMMANDS[commandId] : null;
}

/**
 * The platform's own namespaces only -- identical to the Logs module's
 * `PLATFORM_NAMESPACES` (app/app/logs/page.tsx) and to the Role+RoleBinding
 * pairs granted in k8s/paas-rbac.yaml's Container Exec section. Never
 * cluster-wide, never kube-system.
 */
export const EXEC_NAMESPACES = [
  "autofde-lab",
  "gymact",
  "ggen",
  "ggen-marketplace",
  "supabase-demo",
  "platform-console",
] as const;

export type ExecNamespace = (typeof EXEC_NAMESPACES)[number];

export function isExecNamespace(value: string): value is ExecNamespace {
  return (EXEC_NAMESPACES as readonly string[]).includes(value);
}

const EXEC_SUBPROTOCOL = "v4.channel.k8s.io";
const EXEC_TIMEOUT_MS = 10000;
const MAX_OUTPUT_BYTES = 64 * 1024; // generous cap for these small diagnostic commands

export interface ExecResult {
  stdout: string;
  stderr: string;
  /** True when the exec session's own final channel-3 Status object
   * reported "Success" -- i.e. the command inside the container exited 0.
   * False on a non-zero exit OR a truncated/errored session. */
  exitSuccess: boolean;
  /** The raw channel-3 Status message/reason, when the API server sent
   * one (e.g. a non-zero exit's real "command terminated with exit code
   * N"). Never fabricated. */
  statusMessage: string | null;
}

export interface ExecStreamHandlers {
  /** Invoked once per real WebSocket frame on the stdout channel, in
   * arrival order -- lets a caller (the /api/exec route) relay chunks as
   * they arrive instead of only seeing the final buffered result. */
  onStdout?: (chunk: string) => void;
  onStderr?: (chunk: string) => void;
}

/**
 * Opens a real WebSocket connection to one pod's exec subresource, runs
 * exactly one allowlisted command (no stdin, no tty), and resolves once
 * the k8s API server closes the stream. `commandId` is resolved against
 * `ALLOWED_EXEC_COMMANDS` FIRST -- an unrecognized id returns
 * `{ok:false}` immediately and no network connection is ever attempted,
 * the same "reject before touching the k8s API" discipline
 * lib/scheduled-jobs.ts's resolveCommand enforces for CronJobs.
 */
export async function execAllowedCommand(
  namespace: string,
  pod: string,
  container: string,
  commandId: string,
  handlers: ExecStreamHandlers = {},
): Promise<K8sResult<ExecResult>> {
  const command = resolveExecCommand(commandId);
  if (!command) {
    return {
      ok: false,
      error: `commandId must be one of: ${Object.keys(ALLOWED_EXEC_COMMANDS).join(", ")}`,
    };
  }

  const cfg = getInClusterConfig();
  if (!cfg) {
    return {
      ok: false,
      error:
        "not configured: no in-cluster ServiceAccount credentials found -- this only works when running as the platform-console pod",
    };
  }

  const params = new URLSearchParams();
  params.set("container", container);
  params.set("stdout", "true");
  params.set("stderr", "true");
  params.set("stdin", "false");
  params.set("tty", "false");
  for (const token of command.command) params.append("command", token);

  const path = `/api/v1/namespaces/${encodeURIComponent(namespace)}/pods/${encodeURIComponent(pod)}/exec?${params.toString()}`;
  const url = `wss://${cfg.host}:${cfg.port}${path}`;

  return new Promise((resolve) => {
    let stdout = "";
    let stderr = "";
    let exitSuccess = false;
    let statusMessage: string | null = null;
    let settled = false;

    const ws = new WebSocket(url, [EXEC_SUBPROTOCOL], {
      ca: cfg.ca,
      headers: { Authorization: `Bearer ${cfg.token}` },
      rejectUnauthorized: true,
    });

    const timer = setTimeout(() => {
      if (settled) return;
      settled = true;
      ws.terminate();
      resolve({ ok: false, error: `exec timed out after ${EXEC_TIMEOUT_MS}ms` });
    }, EXEC_TIMEOUT_MS);

    ws.on("unexpected-response", (_req, res) => {
      let body = "";
      res.on("data", (chunk) => (body += chunk));
      res.on("end", () => {
        if (settled) return;
        settled = true;
        clearTimeout(timer);
        resolve({
          ok: false,
          error: `exec upgrade rejected: HTTP ${res.statusCode} ${body.slice(0, 500)}`,
        });
      });
    });

    ws.on("message", (data: Buffer) => {
      if (data.length === 0) return;
      const channel = data[0];
      const payload = data.subarray(1);
      if (channel === 1) {
        if (stdout.length < MAX_OUTPUT_BYTES) onStdoutAppend(payload);
      } else if (channel === 2) {
        if (stderr.length < MAX_OUTPUT_BYTES) onStderrAppend(payload);
      } else if (channel === 3) {
        try {
          const status = JSON.parse(payload.toString("utf8")) as {
            status?: string;
            message?: string;
          };
          exitSuccess = status.status === "Success";
          statusMessage = status.message ?? (exitSuccess ? null : status.status ?? null);
        } catch {
          statusMessage = payload.toString("utf8");
        }
      }
    });

    function onStdoutAppend(payload: Buffer) {
      const text = payload.toString("utf8");
      stdout += text;
      handlers.onStdout?.(text);
    }
    function onStderrAppend(payload: Buffer) {
      const text = payload.toString("utf8");
      stderr += text;
      handlers.onStderr?.(text);
    }

    ws.on("close", () => {
      if (settled) return;
      settled = true;
      clearTimeout(timer);
      resolve({ ok: true, data: { stdout, stderr, exitSuccess, statusMessage } });
    });

    ws.on("error", (err) => {
      if (settled) return;
      settled = true;
      clearTimeout(timer);
      resolve({ ok: false, error: `exec WebSocket error: ${err.message}` });
    });
  });
}
